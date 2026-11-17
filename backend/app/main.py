"""B01 health-only API. No cloud clients or data pipeline are initialized."""

import json
import logging
import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

logger = logging.getLogger("uvicorn.error")


def create_app(environment: Mapping[str, str] | None = None) -> FastAPI:
    config = dict(os.environ if environment is None else environment)
    local_valid = (
        config.get("FINOPS_MODE", "local") == "local"
        and config.get("FINOPS_AWS_ENABLED", "false").lower() == "false"
        and config.get("FINOPS_LLM_PROVIDER", "mock") == "mock"
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.started = True
        logger.info(json.dumps({"event": "startup", "local_configuration_valid": local_valid}))
        try:
            yield
        finally:
            application.state.started = False
            logger.info(json.dumps({"event": "shutdown"}))

    application = FastAPI(title="FinOps Autopilot local API", lifespan=lifespan)
    application.state.started = False

    @application.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "alive"}

    @application.get("/health/ready")
    async def ready() -> JSONResponse:
        if not application.state.started:
            return JSONResponse({"status": "not_ready", "reason": "not_started"}, status_code=503)
        if not local_valid:
            return JSONResponse(
                {"status": "not_ready", "reason": "local_configuration_required"}, status_code=503
            )
        return JSONResponse({"status": "ready", "mode": "local", "cloud_enabled": False})

    return application


app = create_app()
