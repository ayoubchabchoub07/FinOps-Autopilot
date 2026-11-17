"""Portable B01 task entry point; commands are always run from the repo root."""

import argparse
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def configure(root: Path = ROOT) -> None:
    """Prepare local files without overwriting existing configuration or secrets."""
    env_path = root / ".env"
    if not env_path.exists():
        with env_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write((root / ".env.example").read_text(encoding="utf-8"))
    password = root / ".local/secrets/grafana-admin-password"
    password.parent.mkdir(parents=True, exist_ok=True)
    if not password.exists():
        descriptor = os.open(password, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(secrets.token_urlsafe(32))
    if len(password.read_text(encoding="utf-8").strip()) < 16:
        raise ValueError("Grafana local password must contain at least 16 characters")
    if os.name == "posix":
        # Compose bind-mounts the file without UID remapping. The private parent
        # protects host access while the mounted file is readable by Grafana UID 472.
        password.parent.chmod(0o700)
        password.chmod(0o644)
    print("Local configuration prepared; existing files preserved. Password is not printed.")


def run(command: list[str], cwd: Path = ROOT) -> None:
    print("Running: " + " ".join(command), flush=True)
    environment = dict(os.environ, UV_CACHE_DIR=str(ROOT / ".uv-cache"))
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=(
            "configure",
            "setup",
            "dev",
            "test",
            "lint",
            "format-check",
            "typecheck",
            "build",
            "down",
            "smoke",
        ),
    )
    args = parser.parse_args()
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm") or "npm"
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    ruff = ROOT / ".venv" / ("Scripts/ruff.exe" if os.name == "nt" else "bin/ruff")
    try:
        if args.action == "configure":
            configure()
        elif args.action == "setup":
            run(["uv", "sync", "--frozen"])
            run([npm, "ci", "--ignore-scripts"], ROOT / "frontend")
            configure()
        elif args.action == "dev":
            configure()
            run(["docker", "compose", "up", "--build", "-d", "--wait", "--wait-timeout", "180"])
        elif args.action == "down":
            run(["docker", "compose", "down"])
        elif args.action == "test":
            run([str(python), "-m", "pytest", "-q"])
            run([npm, "run", "test", "--", "--run"], ROOT / "frontend")
        elif args.action == "lint":
            run([str(ruff), "check", "backend", "scripts"])
            run([npm, "run", "lint"], ROOT / "frontend")
        elif args.action == "format-check":
            run([str(ruff), "format", "--check", "backend", "scripts"])
            run([npm, "run", "format-check"], ROOT / "frontend")
        elif args.action in ("typecheck", "build"):
            run([npm, "run", args.action], ROOT / "frontend")
        elif args.action == "smoke":
            address = subprocess.check_output(
                ["docker", "compose", "port", "web", "8080"], cwd=ROOT, text=True
            ).strip()
            if not address.startswith("127.0.0.1:") or "\n" in address:
                raise ValueError("Expected one loopback web binding from Compose")
            run([sys.executable, str(ROOT / "scripts/smoke.py"), "--base-url", f"http://{address}"])
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Local task failed: {exc}\n")


if __name__ == "__main__":
    main()
