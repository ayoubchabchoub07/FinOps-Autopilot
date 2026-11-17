import importlib.util

import pytest


@pytest.fixture
def contracts():
    assert importlib.util.find_spec("data.contracts") is not None, "B03 contracts missing"
    from data.contracts import validate_record

    return validate_record


def cloud_row():
    return dict(
        usage_start_time="2025-01-01T00:00:00Z",
        usage_date="2025-01-01",
        account_id="demo",
        service_name="compute",
        region=None,
        resource_id=None,
        team=None,
        cost_amount="-1.23456789",
        currency="USD",
        cost_basis="unblended",
        charge_type="credit",
        source_record_id="row-1",
        data_source="synthetic",
        source_file="fixture.csv",
        ingestion_run_id="run-1",
        ingested_at="2026-11-17T00:00:00Z",
        observation_status="observed",
    )


def test_credit_precision_and_missing_are_preserved(contracts):
    row = cloud_row()
    contracts("cloud_costs", row)
    assert row["cost_amount"] == "-1.23456789"
    row.update(cost_amount=None, observation_status="missing")
    contracts("cloud_costs", row)
    row["observation_status"] = "observed"
    with pytest.raises(ValueError, match="missing"):
        contracts("cloud_costs", row)


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"usage_date": "2025-01-02"}, "usage_date"),
        ({"cost_amount": 0.1}, "decimal"),
        ({"cost_basis": "allocated_estimate"}, "cost_basis"),
        ({"currency": "EUR"}, "currency|USD"),
        ({"account_id": ""}, "account_id"),
        ({"ingested_at": "2025-01-01"}, "UTC"),
    ],
)
def test_invalid_contract_values_are_rejected(contracts, changes, reason):
    row = cloud_row()
    row.update(changes)
    with pytest.raises(ValueError, match=reason):
        contracts("cloud_costs", row)


def test_inventory_does_not_invent_metrics(contracts):
    row = dict(
        snapshot_at="2025-01-01T00:00:00Z",
        account_id="demo",
        region="demo-1",
        resource_type="volume",
        resource_id="demo-volume",
        state="available",
        tags={},
        attachment_state=None,
        cloudformation_stack_id=None,
        metrics_coverage={},
        data_source="synthetic",
        run_id="demo",
        source_file="fixture.json",
        ingestion_run_id="raw-demo",
        ingested_at="2026-11-17T00:00:00Z",
    )
    contracts("resource_inventory", row)
    row["metrics_coverage"] = "100%"
    with pytest.raises(ValueError, match="metrics_coverage"):
        contracts("resource_inventory", row)


@pytest.mark.parametrize(
    "dataset,row,bad_field,bad_value",
    [
        (
            "finops_budgets",
            dict(
                period_month="2025-01",
                scope_type="account",
                scope_id="demo",
                budget_amount="100.00",
                currency="USD",
                owner="demo-owner",
                source="local-fixture",
                effective_at="2025-01-01T00:00:00Z",
            ),
            "budget_amount",
            "-1",
        ),
        (
            "ml_forecast",
            dict(
                generated_at="2025-01-01T00:00:00Z",
                target_date="2025-01-02",
                account_id="demo",
                service_name="compute",
                predicted_cost="10",
                prediction_lower="9",
                prediction_upper="11",
                model_version="fixture",
                training_dataset_version="fixture",
                run_id="demo",
                data_source="synthetic",
                currency="USD",
                cost_basis="unblended",
            ),
            "prediction_lower",
            "12",
        ),
        (
            "ml_anomalies",
            dict(
                event_id="demo",
                usage_date="2025-01-01",
                account_id="demo",
                service_name="compute",
                actual_cost="1",
                expected_cost="0",
                deviation="1",
                deviation_pct=None,
                anomaly_score=None,
                severity="low",
                model_version="fixture",
                status="open",
                evidence={},
                run_id="demo",
                currency="USD",
                cost_basis="unblended",
                data_source="synthetic",
            ),
            "deviation_pct",
            "100",
        ),
        (
            "optimization_recommendations",
            dict(
                recommendation_id="demo",
                resource_id="demo-volume",
                resource_type="volume",
                finding_type="fixture",
                evidence={},
                current_cost_estimate=None,
                proposed_cost_estimate=None,
                expected_monthly_savings=None,
                risk_score="0",
                risk_reasons=[],
                policy_result="not_evaluated",
                proposal_status="draft",
                stack_id=None,
                pull_request_url=None,
                change_set_arn=None,
                approval_status="pending",
                execution_status="not_executed",
                currency="USD",
                cost_basis="unblended",
            ),
            "risk_score",
            "101",
        ),
    ],
)
def test_future_contracts_validate_without_implementing_producers(
    contracts, dataset, row, bad_field, bad_value
):
    contracts(dataset, row)
    row[bad_field] = bad_value
    with pytest.raises(ValueError, match=bad_field.split("_")[0]):
        contracts(dataset, row)


def test_missing_and_unknown_fields_fail(contracts):
    row = cloud_row()
    del row["source_file"]
    with pytest.raises(ValueError, match="source_file"):
        contracts("cloud_costs", row)
    row = cloud_row()
    row["invented_metric"] = "0"
    with pytest.raises(ValueError, match="unknown"):
        contracts("cloud_costs", row)
