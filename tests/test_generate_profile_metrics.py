from pathlib import Path

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


def test_aggregate_languages_skips_failed_repository(monkeypatch):
    def fake_json(url):
        if "broken" in url:
            raise RuntimeError("unavailable")
        return {"Python": 75, "HTML": 25}

    monkeypatch.setattr(metrics, "github_json", fake_json)
    totals = metrics.aggregate_languages(
        [{"name": "ok", "languages_url": "ok"}, {"name": "bad", "languages_url": "broken"}]
    )

    assert totals == {"Python": 75, "HTML": 25}


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
