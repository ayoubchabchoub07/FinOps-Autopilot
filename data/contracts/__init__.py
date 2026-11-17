"""Versioned logical contracts, independent of ETL and cloud services."""

import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

CATALOG = json.loads(Path(__file__).with_name("catalog.json").read_text(encoding="utf-8"))
ENUMS = {
    "source": {"synthetic", "public", "aws_real"},
    "billed_basis": {"unblended", "amortized", "billed"},
    "allocated_basis": {"allocated_estimate"},
    "observation": {"observed", "missing", "zero_observed"},
    "scope": {"global", "account", "service", "team"},
    "severity": {"low", "medium", "high", "critical"},
    "alert_status": {"open", "acknowledged", "resolved"},
    "policy": {"not_evaluated", "allow", "deny"},
    "approval": {"pending", "approved", "rejected"},
    "execution": {"not_executed", "running", "succeeded", "failed"},
}


def validate_value(field: str, value: object, kind: str, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    try:
        if kind in ENUMS:
            valid = isinstance(value, str) and value in ENUMS[kind]
        elif kind == "currency":
            valid = value == "USD"
        elif kind == "string":
            valid = isinstance(value, str) and bool(value.strip())
        elif kind in ("decimal", "nonnegative"):
            if not isinstance(value, str) or not re.fullmatch(r"-?\d+(\.\d+)?", value):
                raise ValueError("decimal string required")
            number = Decimal(value)
            valid = number.is_finite() and (kind != "nonnegative" or number >= 0)
        elif kind == "integer":
            valid = type(value) is int and value >= 0
        elif kind == "utc":
            parsed = datetime.fromisoformat(value)
            valid = (
                "T" in value and parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)
            )
        elif kind == "date":
            valid = date.fromisoformat(value).isoformat() == value
        elif kind == "month":
            valid = bool(re.fullmatch(r"\d{4}-\d{2}", value))
            date.fromisoformat(value + "-01")
        elif kind == "object":
            valid = isinstance(value, dict)
        elif kind == "strings":
            valid = isinstance(value, list) and all(isinstance(v, str) and v for v in value)
        else:
            raise ValueError(f"unknown type {kind}")
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise ValueError(f"{field}: invalid {kind.upper() if kind == 'utc' else kind}") from exc
    if not valid:
        raise ValueError(f"{field}: expected {kind.upper() if kind == 'utc' else kind}")


def validate_record(dataset: str, record: dict) -> None:
    """Validate without normalization, imputation, currency conversion or mutation."""
    if dataset not in CATALOG["datasets"] or not isinstance(record, dict):
        raise ValueError("unknown dataset or invalid record")
    fields = CATALOG["datasets"][dataset]["fields"]
    missing = fields.keys() - record.keys()
    if missing:
        raise ValueError(f"{dataset}: missing fields {sorted(missing)}")
    if record.keys() - fields.keys():
        raise ValueError(f"{dataset}: schema has unknown fields")
    for name, spec in fields.items():
        validate_value(name, record[name], spec["type"], spec["nullable"])
    if dataset == "cloud_costs":
        if record["usage_start_time"][:10] != record["usage_date"]:
            raise ValueError("usage_date does not match UTC usage_start_time")
        if (record["cost_amount"] is None) != (record["observation_status"] == "missing"):
            raise ValueError("missing amount requires missing observation_status and vice versa")
        if record["observation_status"] == "zero_observed" and Decimal(record["cost_amount"]) != 0:
            raise ValueError("zero_observed requires zero cost_amount")
    if dataset == "ml_forecast":
        low, high = record["prediction_lower"], record["prediction_upper"]
        if (low is None) != (high is None):
            raise ValueError("prediction interval requires both bounds or neither")
        if low is not None and not Decimal(low) <= Decimal(record["predicted_cost"]) <= Decimal(
            high
        ):
            raise ValueError("prediction interval is inconsistent")
    if dataset == "ml_anomalies" and Decimal(record["expected_cost"]) == 0:
        if record["deviation_pct"] is not None:
            raise ValueError("deviation_pct must be null when expected_cost is zero")
    if dataset == "optimization_recommendations" and record["risk_score"] is not None:
        if Decimal(record["risk_score"]) > 100:
            raise ValueError("risk_score exceeds 100")
