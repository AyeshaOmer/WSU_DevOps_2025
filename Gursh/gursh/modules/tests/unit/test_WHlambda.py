# tests/unit/test_whlambda.py
import urllib.error
from gursh.modules import WHLambda  # adjust path if needed


class DummyResponse:
    def __init__(self, code=200): self._code = code
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def getcode(self): return self._code


def test_crawl_url_success(monkeypatch):
    def fake_urlopen(req, timeout=5): return DummyResponse(200)
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    a, l, s = WHLambda.crawl_url("https://example.com")
    assert a == 1 and s == 200 and l >= 0


def test_crawl_url_http_error(monkeypatch):
    def fake_urlopen(req, timeout=5):
        raise urllib.error.HTTPError(url="https://example.com", code=503,
                                     msg="Service Unavailable", hdrs=None, fp=None)
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    a, l, s = WHLambda.crawl_url("https://example.com")
    assert a == 0 and s == 503


def test_crawl_url_generic_exception(monkeypatch):
    def fake_urlopen(req, timeout=5): raise TimeoutError("timeout")
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    a, l, s = WHLambda.crawl_url("https://example.com")
    assert (a, s, l) == (0, 0, 0.0)
