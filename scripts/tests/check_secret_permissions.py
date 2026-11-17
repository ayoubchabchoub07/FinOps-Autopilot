"""Standalone Linux regression for host privacy and Compose file-secret access."""

import os
import stat
import tempfile
from pathlib import Path

from scripts.tasks import configure


def main() -> None:
    if os.name != "posix":
        raise SystemExit("Run this check on Linux, including the documented Python container")
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / ".env.example").write_text("FINOPS_MODE=local\n")
        configure(root)
        secret = root / ".local/secrets/grafana-admin-password"
        assert stat.S_IMODE(secret.parent.stat().st_mode) == 0o700
        assert stat.S_IMODE(secret.stat().st_mode) == 0o644
        original = secret.read_bytes()
        configure(root)
        assert secret.read_bytes() == original
    print(
        "PASS: private host directory 0700; bind-mounted secret readable as 0644; contents preserved"
    )


if __name__ == "__main__":
    main()
