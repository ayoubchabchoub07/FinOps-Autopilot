"""B03 acceptance tests: offline ingestion, trust boundaries and immutable replay."""

import hashlib
import importlib.util
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from data.generators.synthetic import GeneratorConfig, generate

FIXTURES = Path(__file__).parents[1] / "fixtures/b03"


@pytest.fixture
def api(monkeypatch):
    assert importlib.util.find_spec("data.adapters") is not None, "B03 adapters missing"
    from data.adapters import (
        AwsInventoryAdapter,
        Cur2Adapter,
        OpenCostAdapter,
        PublicDatasetAdapter,
        SyntheticAdapter,
    )

    def no_network(*args, **kwargs):
        raise AssertionError("B03 must not open network connections")

    monkeypatch.setattr(socket, "socket", no_network)
    return dict(
        synthetic=SyntheticAdapter,
        public=PublicDatasetAdapter,
        aws_cur=Cur2Adapter,
        opencost=OpenCostAdapter,
        aws_boto3=AwsInventoryAdapter,
    )


def fixture_bundle(tmp_path, name):
    target = tmp_path / name
    shutil.copytree(FIXTURES / name, target)
    return target / "manifest.json"


def edit_manifest(path, change):
    value = json.loads(path.read_text())
    change(value)
    path.write_text(json.dumps(value), encoding="utf-8")


def replace_payload(manifest, transform):
    value = json.loads(manifest.read_text())
    name, metadata = next(iter(value["files"].items()))
    source = manifest.parent / name
    source.write_bytes(transform(source.read_bytes()))
    metadata["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    metadata["bytes"] = source.stat().st_size
    manifest.write_text(json.dumps(value), encoding="utf-8")


@pytest.mark.parametrize("name", ["public", "aws_cur", "opencost", "aws_boto3"])
def test_authorized_fixtures_ingest_offline_without_changing_sources(api, tmp_path, name):
    manifest = fixture_bundle(tmp_path, name)
    before = {p.name: p.read_bytes() for p in manifest.parent.iterdir()}
    adapter = api[name](manifest)
    adapter.validate_manifest()
    collected = adapter.collect()
    assert len(collected) == 1
    receipts = adapter.write_raw(tmp_path / "lake")
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt["dataset_label"] == "DEMO" and receipt["fixture"] is True
    assert receipt["data_source"] == ("public" if name == "public" else "synthetic")
    assert receipt["source_file"] and receipt["ingestion_run_id"]
    assert receipt["ingested_at"].endswith("Z")
    stored = Path(receipt["raw_path"])
    assert stored.read_bytes() == collected[0].payload
    assert {p.name: p.read_bytes() for p in manifest.parent.iterdir()} == before


def test_synthetic_b02_manifest_preserves_splits_missing_and_credits(api, tmp_path):
    generate(GeneratorConfig(), tmp_path / "source")
    adapter = api["synthetic"](tmp_path / "source/dataset_manifest.json")
    objects = adapter.collect()
    assert {o.role for o in objects} == {"train", "validation", "test"}
    assert sum(o.rows for o in objects) == 2190
    assert all(b"is_anomaly" not in o.payload for o in objects)
    receipts = adapter.write_raw(tmp_path / "lake")
    assert len(receipts) == 3
    assert all(r["cost_basis"] == "unblended" and r["currency"] == "USD" for r in receipts)
    # Companion labels are preserved for lineage, never exposed as cost objects.
    assert len(list((tmp_path / "lake").rglob("labels.csv"))) == 3


def test_replay_and_renamed_source_reuse_original_ingestion(api, tmp_path):
    manifest = fixture_bundle(tmp_path, "public")
    first = api["public"](manifest).write_raw(tmp_path / "lake")
    edit_manifest(
        manifest, lambda m: m["files"].update({"renamed.csv": m["files"].pop("costs.csv")})
    )
    (manifest.parent / "costs.csv").rename(manifest.parent / "renamed.csv")
    second = api["public"](manifest).write_raw(tmp_path / "lake")
    assert first == second
    assert len(list((tmp_path / "lake").rglob("payload"))) == 1


def test_changed_content_creates_revision_without_overwrite(api, tmp_path):
    manifest = fixture_bundle(tmp_path, "public")
    first = api["public"](manifest).write_raw(tmp_path / "lake")
    old = Path(first[0]["raw_path"]).read_bytes()
    replace_payload(manifest, lambda b: b.replace(b"12.50", b"13.50"))
    second = api["public"](manifest).write_raw(tmp_path / "lake")
    assert first[0]["object_id"] != second[0]["object_id"]
    assert Path(first[0]["raw_path"]).read_bytes() == old


@pytest.mark.parametrize("name", ["public", "aws_cur", "opencost", "aws_boto3"])
def test_incompatible_schema_is_rejected_explicitly(api, tmp_path, name):
    manifest = fixture_bundle(tmp_path, name)
    replace_payload(
        manifest,
        lambda b: (
            b.replace(b"ServiceName", b"WrongService")
            .replace(b"line_item_unblended_cost", b"wrong_cost")
            .replace(b"cpu_request_cores", b"wrong_cpu")
            .replace(b"resource_id", b"wrong_id")
        ),
    )
    with pytest.raises(ValueError, match="missing|schema"):
        api[name](manifest).write_raw(tmp_path / "lake")
    assert not (tmp_path / "lake").exists()


@pytest.mark.parametrize(
    "mutation,reason",
    [
        (lambda m: m.update(currency="EUR"), "USD|currency"),
        (lambda m: m.update(cost_basis="amortized"), "cost_basis"),
        (lambda m: m.update(fixture=False), "fixture"),
        (lambda m: m.update(data_source="aws_real"), "data_source"),
        (lambda m: m.pop("license"), "license"),
        (lambda m: m.update(schema_version="unknown/9"), "schema"),
        (lambda m: m["files"]["costs.csv"].update(sha256="0" * 64), "hash"),
        (lambda m: m["files"].update({"../escape.csv": m["files"].pop("costs.csv")}), "path"),
    ],
)
def test_manifest_rejects_untrusted_inputs(api, tmp_path, mutation, reason):
    manifest = fixture_bundle(tmp_path, "public")
    edit_manifest(manifest, mutation)
    with pytest.raises(ValueError, match=reason):
        api["public"](manifest).collect()


@pytest.mark.parametrize(
    "before,after,reason",
    [
        (b"USD", b"EUR", "currency|USD"),
        (b"12.50", b"NaN", "decimal|finite"),
        (b"12.50", b"", "decimal|required"),
        (b"2025-01-01T00:00:00Z", b"2025-01-01T00:00:00", "UTC"),
        (b"BilledCost", b"ServiceName", "duplicate"),
    ],
)
def test_rows_are_validated_even_with_updated_hash(api, tmp_path, before, after, reason):
    manifest = fixture_bundle(tmp_path, "public")
    replace_payload(manifest, lambda b: b.replace(before, after))
    with pytest.raises(ValueError, match=reason):
        api["public"](manifest).collect()


@pytest.mark.parametrize("target", ["payload", "source_manifest.json", "ingestion_manifest.json"])
def test_corrupted_raw_is_not_silently_reused(api, tmp_path, target):
    manifest = fixture_bundle(tmp_path, "public")
    receipt = api["public"](manifest).write_raw(tmp_path / "lake")[0]
    (Path(receipt["raw_path"]).parent / target).write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="corrupt|incomplete"):
        api["public"](manifest).write_raw(tmp_path / "lake")


def test_cli_reports_replay_without_duplicate_objects(tmp_path):
    assert importlib.util.find_spec("data.adapters") is not None, "B03 CLI missing"
    command = [
        sys.executable,
        "-m",
        "data.adapters",
        "--adapter",
        "public",
        "--manifest",
        str(FIXTURES / "public/manifest.json"),
        "--raw-root",
        str(tmp_path / "raw"),
    ]
    first = subprocess.run(command, capture_output=True, text=True, check=True)
    second = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(first.stdout)["objects"] == json.loads(second.stdout)["objects"]
    assert len(list(tmp_path.rglob("payload"))) == 1


def test_synthetic_cross_partition_id_leak_is_rejected(api, tmp_path):
    generate(GeneratorConfig(), tmp_path / "source")
    manifest = tmp_path / "source/dataset_manifest.json"
    value = json.loads(manifest.read_text())
    train_id = (manifest.parent / "train.csv").read_text().splitlines()[1].split(",")[0]
    test_id = (manifest.parent / "test.csv").read_text().splitlines()[1].split(",")[0]
    for name in ("test.csv", "test_labels.csv"):
        path = manifest.parent / name
        path.write_bytes(path.read_bytes().replace(test_id.encode(), train_id.encode()))
        value["files"][name]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        value["files"][name]["bytes"] = path.stat().st_size
    manifest.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="partition"):
        api["synthetic"](manifest).collect()


def test_labels_are_not_public_observations(api, tmp_path):
    manifest = fixture_bundle(tmp_path, "public")
    edit_manifest(manifest, lambda m: m["files"]["costs.csv"].update(role="train"))
    # Public fixtures cannot acquire an approved training role by metadata alone.
    with pytest.raises(ValueError, match="fixture"):
        api["public"](manifest).collect()


def test_incomplete_raw_is_preserved_on_retry(api, tmp_path):
    manifest = fixture_bundle(tmp_path, "public")
    receipt = api["public"](manifest).write_raw(tmp_path / "lake")[0]
    folder = Path(receipt["raw_path"]).parent
    (folder / "COMPLETED").unlink()  # Test-owned temporary object only.
    with pytest.raises(ValueError, match="incomplete"):
        api["public"](manifest).write_raw(tmp_path / "lake")
    assert Path(receipt["raw_path"]).exists()


def test_synthetic_zero_observed_cannot_hide_a_nonzero_cost(api, tmp_path):
    generate(GeneratorConfig(), tmp_path / "source")
    manifest = tmp_path / "source/dataset_manifest.json"
    value = json.loads(manifest.read_text())
    source = manifest.parent / "train.csv"
    source.write_bytes(source.read_bytes().replace(b",observed,", b",zero_observed,", 1))
    value["files"]["train.csv"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    value["files"]["train.csv"]["bytes"] = source.stat().st_size
    manifest.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="zero_observed"):
        api["synthetic"](manifest).collect()
