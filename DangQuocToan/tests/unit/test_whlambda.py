import sys
import types
import os
import builtins
import urllib.error
import time

# Ensure importing WHLambda doesn't fail on boto3 dependency during unit tests
sys.modules.setdefault("boto3", types.SimpleNamespace(client=lambda *a, **k: None))

# Make sure we can import from the modules directory
MODULES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "modules")
MODULES_DIR = os.path.abspath(MODULES_DIR)
if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

import WHLambda  # noqa: E402  (import after path tweaks)


class DummyResponse:
    def __init__(self, code=200, delay_ms=10):
        self._code = code
        self._delay_ms = delay_ms

    def __enter__(self):
        # Simulate network latency
        time.sleep(self._delay_ms / 1000.0)
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self._code


def test_crawl_url_success(monkeypatch):
    def fake_urlopen(req, timeout=5):
        return DummyResponse(code=200, delay_ms=5)

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    availability, latency, status = WHLambda.crawl_url("https://example.com")

    assert availability == 1
    assert status == 200
    assert latency >= 0


def test_crawl_url_http_error(monkeypatch):
    def fake_urlopen(req, timeout=5):
        raise urllib.error.HTTPError(
            url=req.full_url if hasattr(req, "full_url") else "https://example.com",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=None,
        )

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    availability, latency, status = WHLambda.crawl_url("https://example.com")

    assert availability == 0
    assert status == 503
    assert latency >= 0


def test_crawl_url_generic_exception(monkeypatch):
    def fake_urlopen(req, timeout=5):
        raise TimeoutError("timeout")

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    availability, latency, status = WHLambda.crawl_url("https://example.com")

    assert availability == 0
    assert status == 0
    assert latency == 0.0

