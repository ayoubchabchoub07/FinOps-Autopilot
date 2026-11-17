import importlib.util
from pathlib import Path


def test_configure_preserves_existing_env_and_password(tmp_path):
    assert importlib.util.find_spec("scripts.tasks") is not None, "B01 tasks are not implemented"
    from scripts.tasks import configure

    (tmp_path / ".env.example").write_text("FINOPS_MODE=local\n")
    (tmp_path / ".env").write_text("FINOPS_MODE=custom\n")
    secret = tmp_path / ".local/secrets/grafana-admin-password"
    secret.parent.mkdir(parents=True)
    secret.write_text("existing-test-password-do-not-change")
    configure(tmp_path)
    assert (tmp_path / ".env").read_text() == "FINOPS_MODE=custom\n"
    assert secret.read_text() == "existing-test-password-do-not-change"


def test_configure_creates_local_random_password_without_printing_it(tmp_path, capsys):
    assert importlib.util.find_spec("scripts.tasks") is not None, "B01 tasks are not implemented"
    from scripts.tasks import configure

    (tmp_path / ".env.example").write_text("FINOPS_MODE=local\n")
    configure(tmp_path)
    secret = Path(tmp_path / ".local/secrets/grafana-admin-password").read_text()
    assert len(secret) >= 32
    assert secret not in capsys.readouterr().out
    assert (tmp_path / ".env").read_text() == "FINOPS_MODE=local\n"
    configure(tmp_path)
    assert Path(tmp_path / ".local/secrets/grafana-admin-password").read_text() == secret
