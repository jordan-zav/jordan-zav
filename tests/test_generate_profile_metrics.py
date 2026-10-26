from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from scripts import generate_profile_metrics as metrics


def test_list_all_repos_uses_public_endpoint_without_token(monkeypatch):
    requested = []

    def fake_json(url):
        requested.append(url)
        return [{"name": "public", "fork": False}] if url.endswith("page=1") else []

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(metrics, "github_json", fake_json)

    assert metrics.list_all_repos() == [{"name": "public", "fork": False}]
    assert requested[0].startswith(f"https://api.github.com/users/{metrics.USER}/repos")


def test_aggregate_languages_rejects_incomplete_results(monkeypatch):
    def fake_json(url):
        if "broken" in url:
            raise RuntimeError("unavailable")
        return {"Python": 75, "HTML": 25}

    monkeypatch.setattr(metrics, "github_json", fake_json)
    with pytest.raises(RuntimeError, match="unavailable"):
        metrics.aggregate_languages(
            [{"name": "ok", "languages_url": "ok"}, {"name": "bad", "languages_url": "broken"}]
        )


def test_main_writes_svg_at_repository_root(monkeypatch, tmp_path):
    script = tmp_path / "scripts" / "generate_profile_metrics.py"
    script.parent.mkdir()
    script.write_text("", encoding="utf-8")
    monkeypatch.setattr(metrics, "__file__", str(script))
    monkeypatch.setattr(metrics, "list_all_repos", lambda: [{"name": "repo"}])
    monkeypatch.setattr(metrics, "aggregate_languages", lambda _repos: {"Python": 100})

    assert metrics.main() == 0
    output = Path(tmp_path / metrics.OUTPUT)
    assert output.is_file()
    assert "Python" in output.read_text(encoding="utf-8")


def test_token_never_switches_to_private_repositories(monkeypatch):
    requested = []
    public = {"name": "public", "fork": False, "private": False}

    def fake_json(url):
        requested.append(url)
        return [public, {"name": "secret", "private": True}, {"name": "fork", "fork": True}] if url.endswith("page=1") else []

    monkeypatch.setenv("GITHUB_TOKEN", "test-token-not-real")
    monkeypatch.setattr(metrics, "github_json", fake_json)
    assert metrics.list_all_repos() == [public]
    assert all(f"/users/{metrics.USER}/repos?" in url for url in requested)


def test_aggregate_never_requests_private_or_fork_languages(monkeypatch):
    requested = []

    def fake_json(url):
        requested.append(url)
        return {"Python": 10}

    monkeypatch.setattr(metrics, "github_json", fake_json)
    assert metrics.aggregate_languages([
        {"private": True, "languages_url": "private"},
        {"fork": True, "languages_url": "fork"},
        {"languages_url": "public"},
    ]) == {"Python": 10}
    assert requested == ["public"]


@pytest.mark.parametrize("languages", [{}, None])
def test_failed_refresh_preserves_previous_svg(monkeypatch, tmp_path, languages):
    script = tmp_path / "scripts" / "generate_profile_metrics.py"
    output = tmp_path / metrics.OUTPUT
    output.write_text("previous valid SVG", encoding="utf-8")
    monkeypatch.setattr(metrics, "__file__", str(script))
    monkeypatch.setattr(metrics, "list_all_repos", lambda: [{"name": "repo"}])

    def aggregate(_repos):
        if languages is None:
            raise URLError("temporary outage")
        return languages

    monkeypatch.setattr(metrics, "aggregate_languages", aggregate)
    assert metrics.main() == 1
    assert output.read_text(encoding="utf-8") == "previous valid SVG"


def test_request_retries_temporary_network_failure(monkeypatch):
    calls = []
    sleeps = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def read(self):
            return b'{"Python": 42}'

    def open_url(_request, timeout):
        calls.append(timeout)
        if len(calls) < 3:
            raise URLError("offline")
        return Response()

    monkeypatch.setattr(metrics.urllib.request, "urlopen", open_url)
    monkeypatch.setattr(metrics.time, "sleep", sleeps.append)
    assert metrics.github_json("https://api.github.com/test") == {"Python": 42}
    assert sleeps == [1, 2]
    assert len(calls) == 3


@pytest.mark.parametrize("status,headers", [(401, {}), (403, {}), (429, {}), (429, {"Retry-After": "120"})])
def test_authentication_and_long_rate_limits_fail_without_retry(monkeypatch, status, headers):
    calls = []

    def open_url(_request, timeout):
        calls.append(timeout)
        raise HTTPError("https://api.github.com/test", status, "error", headers, None)

    def unexpected_sleep(_delay):
        pytest.fail("must not retry this error")

    monkeypatch.setattr(metrics.urllib.request, "urlopen", open_url)
    monkeypatch.setattr(metrics.time, "sleep", unexpected_sleep)
    with pytest.raises(HTTPError):
        metrics.github_json("https://api.github.com/test")
    assert len(calls) == 1


def test_server_failure_retries_are_bounded(monkeypatch):
    calls = []
    sleeps = []

    def open_url(_request, timeout):
        calls.append(timeout)
        raise HTTPError("https://api.github.com/test", 503, "unavailable", {}, None)

    monkeypatch.setattr(metrics.urllib.request, "urlopen", open_url)
    monkeypatch.setattr(metrics.time, "sleep", sleeps.append)
    with pytest.raises(HTTPError):
        metrics.github_json("https://api.github.com/test")
    assert len(calls) == 3
    assert sleeps == [1, 2]
