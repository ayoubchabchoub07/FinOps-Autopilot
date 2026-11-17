"""Local-only RAW ingestion CLI. No downloads, SDK calls or transformation."""

import argparse
import json
from pathlib import Path

from data.adapters import (
    AwsInventoryAdapter,
    Cur2Adapter,
    OpenCostAdapter,
    PublicDatasetAdapter,
    SyntheticAdapter,
)

ADAPTERS = dict(
    synthetic=SyntheticAdapter,
    public=PublicDatasetAdapter,
    aws_cur=Cur2Adapter,
    opencost=OpenCostAdapter,
    aws_boto3=AwsInventoryAdapter,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", choices=ADAPTERS, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipts = ADAPTERS[args.adapter](args.manifest).write_raw(args.raw_root)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"RAW ingestion refused: {exc}\n")
    print(
        json.dumps(
            dict(
                status="INGESTED_OR_REUSED",
                dataset_label="DEMO",
                objects=[r["object_id"] for r in receipts],
                rows=sum(r["rows"] for r in receipts),
            )
        )
    )


if __name__ == "__main__":
    main()
