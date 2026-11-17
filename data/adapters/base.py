"""Local manifests and immutable RAW storage, independent of any ETL."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from uuid import uuid4

from data.adapters.profiles import PROFILES, validate_labels, validate_payload


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def load_object(payload: bytes) -> dict:
    try:

        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key}")
                result[key] = value
            return result

        value = json.loads(payload, object_pairs_hook=pairs)
        if not isinstance(value, dict):
            raise ValueError("object required")
        return value
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"invalid manifest: {exc}") from exc


@dataclass(frozen=True)
class RawObject:
    source_file: str
    role: str
    payload: bytes
    rows: int
    labels: bytes | None = None


class LocalAdapter:
    """Common collect/validate_manifest/write_raw interface; local files only."""

    profile: str

    def __init__(self, manifest: Path):
        self.manifest_path = Path(manifest).resolve(strict=True)

    def _read_source(self, name: str, metadata: dict) -> bytes:
        path = PurePosixPath(name)
        if (
            not name
            or "\\" in name
            or ":" in name
            or path.is_absolute()
            or any(part in {"..", "."} for part in name.split("/"))
        ):
            raise ValueError("source path must remain inside manifest directory")
        source = (self.manifest_path.parent / name).resolve()
        if not source.is_relative_to(self.manifest_path.parent):
            raise ValueError("source path escapes manifest directory")
        if not isinstance(metadata, dict) or not source.is_file():
            raise ValueError("source path or file metadata invalid")
        if source.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("local source exceeds 64 MiB limit")
        payload = source.read_bytes()
        if metadata.get("sha256") != digest(payload):
            raise ValueError(f"source hash mismatch: {name}")
        if metadata.get("bytes") != len(payload):
            raise ValueError(f"source byte count mismatch: {name}")
        return payload

    def _collect(self) -> tuple[dict, bytes, list[RawObject]]:
        raw_manifest = self.manifest_path.read_bytes()
        manifest = load_object(raw_manifest)
        dataset, schema, source, basis, cost_field = PROFILES[self.profile]
        for key, expected in {
            "schema_version": schema,
            "data_source": source,
            "dataset_label": "DEMO",
        }.items():
            if manifest.get(key) != expected:
                raise ValueError(f"manifest {key}: expected {expected}")
        for key in ("license", "provenance"):
            if not isinstance(manifest.get(key), str) or not manifest[key].strip():
                raise ValueError(f"manifest {key} required")
        files = manifest.get("files")
        if not isinstance(files, dict) or not files or len(files) > 100:
            raise ValueError("manifest files must contain 1..100 entries")
        if self.profile == "synthetic":
            expected = {
                f"{s}{suffix}.csv"
                for s in ("train", "validation", "test")
                for suffix in ("", "_labels")
            }
            if set(files) != expected:
                raise ValueError("synthetic schema requires three splits and separate labels")
        else:
            if manifest.get("fixture") is not True:
                raise ValueError("only explicitly declared local fixture inputs are enabled")
            expected = {
                "dataset": dataset,
                "cost_basis": basis,
                "currency": "USD" if basis else None,
                "source_cost_field": cost_field,
            }
            for key, value in expected.items():
                if manifest.get(key) != value:
                    raise ValueError(f"manifest {key}: expected {value}")
            for key in ("dataset_version", "source_uri", "cost_method"):
                if not isinstance(manifest.get(key), str) or not manifest[key].strip():
                    raise ValueError(f"manifest {key} required")
        # Capture bytes once; validation and writing use the same snapshot (no TOCTOU reread).
        payloads = {name: self._read_source(name, meta) for name, meta in files.items()}
        objects = []
        seen_observation_ids = set()
        for name, payload in payloads.items():
            if self.profile == "synthetic" and name.endswith("_labels.csv"):
                continue
            rows = validate_payload(self.profile, payload)
            if self.profile == "synthetic":
                ids = {row["source_record_id"] for row in rows}
                if ids & seen_observation_ids:
                    raise ValueError("synthetic partition identities overlap")
                seen_observation_ids.update(ids)
            if type(files[name].get("rows")) is not int or files[name]["rows"] != len(rows):
                raise ValueError(f"source row count mismatch: {name}")
            role = Path(name).stem if self.profile == "synthetic" else files[name].get("role")
            if role not in {"train", "validation", "test", "fixture"}:
                raise ValueError("manifest role must identify a split or fixture")
            if self.profile != "synthetic" and role != "fixture":
                raise ValueError("local fixture cannot be promoted to a training partition")
            labels = None
            if self.profile == "synthetic":
                labels = payloads[f"{role}_labels.csv"]
                count = validate_labels(labels, rows)
                if files[f"{role}_labels.csv"].get("rows") != count:
                    raise ValueError("label row count mismatch")
            objects.append(
                RawObject(str(self.manifest_path.parent / name), role, payload, len(rows), labels)
            )
        return manifest, raw_manifest, objects

    def validate_manifest(self) -> dict:
        """Validate provenance, local profile, all source hashes, rows and labels."""
        return self._collect()[0]

    def collect(self) -> list[RawObject]:
        return self._collect()[2]

    def write_raw(self, root: Path) -> list[dict]:
        manifest, source_manifest, objects = self._collect()
        dataset, schema, source, basis, cost_field = PROFILES[self.profile]
        root = Path(root).resolve()
        if root == self.manifest_path.parent or root.is_relative_to(self.manifest_path.parent):
            raise ValueError("RAW destination must be separate from source directory")
        run_id = str(uuid4())
        ingested_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        receipts = []
        for obj in objects:
            identity = dict(
                adapter=self.profile,
                schema_version=schema,
                role=obj.role,
                source_sha256=digest(obj.payload),
                cost_basis=basis,
                currency="USD" if basis else None,
                labels_sha256=digest(obj.labels) if obj.labels is not None else None,
            )
            object_id = digest(json_bytes(identity))
            folder = root / dataset / source / self.profile / object_id
            if folder.is_symlink() or not folder.resolve().is_relative_to(root):
                raise ValueError("RAW path escapes storage root")
            folder.parent.mkdir(parents=True, exist_ok=True)
            try:
                folder.mkdir()
            except FileExistsError:
                try:
                    body = (folder / "ingestion_manifest.json").read_bytes()
                    receipt = load_object(body)
                    valid = (folder / "COMPLETED").read_text() == digest(body)
                    valid &= receipt["object_id"] == object_id
                    valid &= all(receipt[k] == v for k, v in identity.items())
                    valid &= (folder / "payload").read_bytes() == obj.payload
                    valid &= (
                        digest((folder / "source_manifest.json").read_bytes())
                        == receipt["source_manifest_sha256"]
                    )
                    if obj.labels is not None:
                        valid &= (folder / "labels.csv").read_bytes() == obj.labels
                    if not valid:
                        raise ValueError("hash mismatch")
                except (OSError, KeyError, ValueError, TypeError) as exc:
                    raise ValueError(
                        f"corrupt or incomplete RAW object {object_id}; preserved"
                    ) from exc
            else:
                receipt = dict(
                    identity,
                    contract_version="1.0",
                    object_id=object_id,
                    dataset=dataset,
                    data_source=source,
                    dataset_label="DEMO",
                    fixture=self.profile != "synthetic",
                    source_file=obj.source_file,
                    ingestion_run_id=run_id,
                    ingested_at=ingested_at,
                    rows=obj.rows,
                    raw_path=str(folder / "payload"),
                    source_manifest_sha256=digest(source_manifest),
                    source_cost_field=cost_field,
                    cost_method="native field preserved; no FX or aggregation",
                    license=manifest["license"],
                    provenance=manifest["provenance"],
                )
                payloads = {
                    "payload": obj.payload,
                    "source_manifest.json": source_manifest,
                    "ingestion_manifest.json": json_bytes(receipt),
                }
                if obj.labels is not None:
                    payloads["labels.csv"] = obj.labels
                # Exclusive writes + completion marker last. Failed/interrupted objects are
                # retained, never overwritten or returned as successful ingestions.
                for name, payload in payloads.items():
                    with (folder / name).open("xb") as stream:
                        stream.write(payload)
                with (folder / "COMPLETED").open("x", encoding="ascii") as stream:
                    stream.write(digest(payloads["ingestion_manifest.json"]))
            receipts.append(receipt)
        return receipts
