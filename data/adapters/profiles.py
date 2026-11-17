"""Restricted local fixture profiles; no remote/provider client is implemented."""

import csv
import io
import json
from decimal import Decimal

from data.contracts import CATALOG, validate_value
from data.generators.synthetic import LABEL_FIELDS, OBSERVATION_FIELDS

PROFILES = {
    "synthetic": ("cloud_costs", "synthetic-costs/1.0", "synthetic", "unblended", "cost_amount"),
    "public": ("cloud_costs", "public-focus-fixture/1.0", "public", "billed", "BilledCost"),
    "aws_cur": (
        "cloud_costs",
        "cur2-fixture/1.0",
        "synthetic",
        "unblended",
        "line_item_unblended_cost",
    ),
    "opencost": (
        "k8s_usage",
        "opencost-projection-fixture/1.0",
        "synthetic",
        "allocated_estimate",
        "allocated_cost_amount",
    ),
    "aws_boto3": (
        "resource_inventory",
        "inventory-projection-fixture/1.0",
        "synthetic",
        None,
        None,
    ),
}
PUBLIC_FIELDS = {
    "x_SourceRecordId": "string",
    "ChargePeriodStart": "utc",
    "BillingAccountId": "string",
    "ServiceName": "string",
    "BilledCost": "decimal",
    "BillingCurrency": "currency",
}
CUR_FIELDS = {
    "identity_line_item_id": "string",
    "line_item_usage_start_date": "utc",
    "line_item_usage_account_id": "string",
    "line_item_product_code": "string",
    "line_item_unblended_cost": "decimal",
    "line_item_currency_code": "currency",
}


def csv_records(payload: bytes, required) -> list[dict]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""), strict=True)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)):
            raise ValueError("duplicate CSV headers")
        if set(required) - set(fields):
            raise ValueError(f"schema missing fields: {sorted(set(required) - set(fields))}")
        rows = list(reader)
        if not rows or any(None in row or None in row.values() for row in rows):
            raise ValueError("schema: empty file or incompatible CSV row width")
        return rows
    except (UnicodeError, csv.Error) as exc:
        raise ValueError("schema: invalid UTF-8 CSV") from exc


def validate_payload(profile: str, payload: bytes) -> list[dict]:
    if profile == "synthetic":
        rows = csv_records(payload, OBSERVATION_FIELDS)
        for row in rows:
            if set(row) & {"is_anomaly", "baseline_cost", "injected_delta", "event_type"}:
                raise ValueError("schema: labels cannot be cost observations")
            for name in OBSERVATION_FIELDS:
                kind = {
                    "usage_start_time": "utc",
                    "usage_date": "date",
                    "currency": "currency",
                }.get(name, "string")
                if name == "cost_amount":
                    validate_value(
                        name, row[name] or None, "decimal", row["observation_status"] == "missing"
                    )
                else:
                    validate_value(name, row[name], kind)
            if row["cost_basis"] != "unblended" or row["data_source"] != "synthetic":
                raise ValueError("cost_basis or data_source mismatch")
            if row["dataset_label"] != "DEMO":
                raise ValueError("synthetic dataset_label must be DEMO")
            if row["observation_status"] not in {"missing", "observed", "zero_observed"}:
                raise ValueError("invalid observation_status")
            if (row["cost_amount"] == "") != (row["observation_status"] == "missing"):
                raise ValueError("missing cost/status mismatch")
            if row["observation_status"] == "zero_observed" and Decimal(row["cost_amount"]) != 0:
                raise ValueError("zero_observed requires zero cost_amount")
            if row["usage_start_time"][:10] != row["usage_date"]:
                raise ValueError("usage_date mismatch")
        key = "source_record_id"
    elif profile in {"public", "aws_cur"}:
        fields = PUBLIC_FIELDS if profile == "public" else CUR_FIELDS
        rows = csv_records(payload, fields)
        for row in rows:
            for name, kind in fields.items():
                validate_value(name, row[name], kind)
        key = "x_SourceRecordId" if profile == "public" else "identity_line_item_id"
    else:
        try:
            rows = json.loads(payload)
        except (ValueError, UnicodeError) as exc:
            raise ValueError("schema: invalid JSON projection") from exc
        if not isinstance(rows, list) or not rows:
            raise ValueError("schema: nonempty JSON array required")
        fields = CATALOG["datasets"][PROFILES[profile][0]]["fields"]
        omitted = {"data_source", "source_file", "ingestion_run_id", "ingested_at", "run_id"}
        for row in rows:
            if not isinstance(row, dict) or fields.keys() - omitted - row.keys():
                raise ValueError("schema: missing projection fields")
            for name, spec in fields.items():
                if name not in omitted:
                    validate_value(name, row[name], spec["type"], spec["nullable"])
        key = None
    if key and len({row[key] for row in rows}) != len(rows):
        raise ValueError(f"duplicate {key} within source file")
    return rows


def validate_labels(payload: bytes, observations: list[dict]) -> int:
    labels = csv_records(payload, LABEL_FIELDS)
    ids = [row["source_record_id"] for row in labels]
    if len(ids) != len(set(ids)) or set(ids) != {row["source_record_id"] for row in observations}:
        raise ValueError("label/observation identities mismatch")
    return len(labels)
