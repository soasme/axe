import base64

import pytest

from axe import fetch
from axe.fetch import _auth_header, fetch_url, fetch_uv


def test_auth_header_absent_by_default(monkeypatch):
    monkeypatch.delenv("UV_RELEASES_USERNAME", raising=False)
    monkeypatch.delenv("UV_RELEASES_PASSWORD", raising=False)
    assert _auth_header("UV_RELEASES") is None


@pytest.mark.parametrize("prefix", ["UV_RELEASES", "PYTHON_BUILD_STANDALONE_RELEASES"])
def test_auth_header_from_env(monkeypatch, prefix):
    monkeypatch.setenv(f"{prefix}_USERNAME", "alice")
    monkeypatch.setenv(f"{prefix}_PASSWORD", "s3cret")
    header = _auth_header(prefix)
    assert header == "Basic " + base64.b64encode(b"alice:s3cret").decode()


def test_auth_header_password_only(monkeypatch):
    monkeypatch.delenv("UV_RELEASES_USERNAME", raising=False)
    monkeypatch.setenv("UV_RELEASES_PASSWORD", "token")
    assert _auth_header("UV_RELEASES") == "Basic " + base64.b64encode(b":token").decode()


def test_fetch_url_sends_authorization(monkeypatch):
    seen = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"payload"

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["auth"] = request.get_header("Authorization")
        return FakeResponse()

    monkeypatch.setattr(fetch.urllib.request, "urlopen", fake_urlopen)
    assert fetch_url("https://mirror.corp/file", "Basic abc") == b"payload"
    assert seen == {"url": "https://mirror.corp/file", "auth": "Basic abc"}


def test_fetch_uv_uses_custom_releases_url(monkeypatch, tmp_path):
    monkeypatch.setenv("AXE_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UV_RELEASES_USERNAME", "alice")
    monkeypatch.setenv("UV_RELEASES_PASSWORD", "s3cret")
    calls = []

    def fake_fetch_url(url, auth=None):
        calls.append((url, auth))
        data = b"uv archive bytes"
        if url.endswith(".sha256"):
            import hashlib

            return hashlib.sha256(data).hexdigest().encode() + b"  file"
        return data

    monkeypatch.setattr(fetch, "fetch_url", fake_fetch_url)
    path = fetch_uv("0.10.6", "linux", "amd64", "https://mirror.corp/uv")

    expected_auth = "Basic " + base64.b64encode(b"alice:s3cret").decode()
    assert all(url.startswith("https://mirror.corp/uv/0.10.6/uv-") for url, _ in calls)
    assert all(auth == expected_auth for _, auth in calls)
    assert path.read_bytes() == b"uv archive bytes"
