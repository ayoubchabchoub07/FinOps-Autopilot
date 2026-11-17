"""Check the running local Compose stack through its public loopback entry point."""

import argparse
import json
import re
import urllib.error
import urllib.request


def check(base_url: str) -> dict:
    def get(path: str) -> bytes:
        with urllib.request.urlopen(base_url.rstrip("/") + path, timeout=15) as response:
            assert response.status == 200, (path, response.status)
            return response.read()

    assert json.loads(get("/api/health/live")) == {"status": "alive"}
    assert json.loads(get("/api/health/ready")) == {
        "status": "ready",
        "mode": "local",
        "cloud_enabled": False,
    }
    html = get("/").decode()
    assert '<div id="root"></div>' in html
    asset = re.search(r'src="(/assets/[^\"]+\.js)"', html)
    assert asset is not None, "Built React entry asset missing"
    assert len(get(asset.group(1))) > 1000
    assert json.loads(get("/grafana/api/health"))["database"] == "ok"
    assert b"Grafana" in get("/grafana/login")
    try:
        get("/grafana/api/org")
    except urllib.error.HTTPError as exc:
        assert exc.code == 401, "Grafana admin API must require authentication"
    else:
        raise AssertionError("Grafana anonymous admin API unexpectedly accessible")
    return {
        "status": "PASS",
        "api": "ready",
        "react_asset": "served",
        "grafana": "healthy",
        "grafana_auth": "required",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:18000")
    arguments = parser.parse_args()
    print(json.dumps(check(arguments.base_url)))
