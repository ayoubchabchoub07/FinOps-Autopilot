"""Readiness must be useful without AWS, credentials or datasets."""

import importlib.util

import pytest


def factory():
    try:
        available = importlib.util.find_spec("backend.app.main")
    except ModuleNotFoundError:
        available = None
    assert available is not None, "B01 API is not implemented"
    from backend.app.main import create_app

    return create_app


def test_liveness_and_readiness_after_local_startup():
    create_app = factory()
    from fastapi.testclient import TestClient

    with TestClient(create_app({})) as client:
        assert client.get("/health/live").json() == {"status": "alive"}
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready", "mode": "local", "cloud_enabled": False}


def test_readiness_does_not_claim_ready_before_startup_or_after_shutdown():
    create_app = factory()
    from fastapi.testclient import TestClient

    app = create_app({})
    client = TestClient(app)
    assert client.get("/health/ready").status_code == 503
    with TestClient(app) as started:
        assert started.get("/health/ready").status_code == 200
    assert client.get("/health/ready").status_code == 503


@pytest.mark.parametrize(
    "config",
    [
        {"FINOPS_MODE": "aws-real"},
        {"FINOPS_AWS_ENABLED": "true"},
        {"FINOPS_AWS_ENABLED": "typo"},
        {"FINOPS_LLM_PROVIDER": "bedrock"},
    ],
)
def test_unsupported_cloud_configuration_is_not_ready_but_remains_live(config):
    create_app = factory()
    from fastapi.testclient import TestClient

    with TestClient(create_app(config)) as client:
        assert client.get("/health/live").status_code == 200
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json()["reason"] == "local_configuration_required"
        assert "AWS_SECRET_ACCESS_KEY" not in response.text
