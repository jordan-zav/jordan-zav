from __future__ import annotations

import html
import json
import os
import urllib.request


USER = "jordan-zav"
OUTPUT = "metrics.svg"
COLORS = {
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "JavaScript": "#f1e05a",
    "Jupyter Notebook": "#DA5B0B",
    "Shell": "#89e051",
    "Batchfile": "#C1F12E",
    "PowerShell": "#012456",
    "TypeScript": "#3178c6",
    "Astro": "#ff5d01",
}


def github_json(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "jordan-zav-profile-readme",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def list_public_repos() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USER}/repos?type=owner&sort=updated&per_page=100&page={page}"
        batch = github_json(url)
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(repo for repo in batch if not repo.get("fork"))
        page += 1
    return repos


def aggregate_languages(repos: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for repo in repos:
        languages_url = repo.get("languages_url")
        if not languages_url:
            continue
        languages = github_json(languages_url)
        if not isinstance(languages, dict):
            continue
        for language, bytes_count in languages.items():
            totals[language] = totals.get(language, 0) + int(bytes_count)
    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))


def svg_bar(language: str, value: int, total: int, y: int) -> str:
    percentage = value / total * 100 if total else 0
    width = max(4, int(percentage * 4.6))
    color = COLORS.get(language, "#8b949e")
    safe_language = html.escape(language)
    return (
        f'<text x="24" y="{y}" fill="#c9d1d9" font-size="14">{safe_language}</text>'
        f'<text x="520" y="{y}" fill="#8b949e" font-size="13" text-anchor="end">{percentage:.1f}%</text>'
        f'<rect x="24" y="{y + 10}" width="460" height="10" rx="5" fill="#21262d"/>'
        f'<rect x="24" y="{y + 10}" width="{width}" height="10" rx="5" fill="{color}"/>'
    )


def render_svg(repos: list[dict], languages: dict[str, int]) -> str:
    visible_languages = list(languages.items())[:8]
    total = sum(languages.values())
    repo_count = len(repos)
    language_count = len(languages)
    height = 178 + len(visible_languages) * 44
    rows = "\n".join(
        svg_bar(language, value, total, 150 + index * 44)
        for index, (language, value) in enumerate(visible_languages)
    )
    return f"""<svg width="560" height="{height}" viewBox="0 0 560 {height}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
<title id="title">Jordan Zavaleta GitHub language metrics</title>
<desc id="desc">Dynamic language summary generated from public GitHub repositories.</desc>
<rect width="560" height="{height}" rx="12" fill="#0d1117"/>
<text x="24" y="38" fill="#58a6ff" font-family="Segoe UI, Arial, sans-serif" font-size="22" font-weight="700">GitHub Profile Metrics</text>
<text x="24" y="68" fill="#c9d1d9" font-family="Segoe UI, Arial, sans-serif" font-size="14">Public repositories analyzed: {repo_count}</text>
<text x="24" y="92" fill="#c9d1d9" font-family="Segoe UI, Arial, sans-serif" font-size="14">Languages detected: {language_count}</text>
<text x="24" y="124" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="13">Most used languages by bytes across public source repositories</text>
<g font-family="Segoe UI, Arial, sans-serif">
{rows}
</g>
</svg>
"""


def main() -> None:
    repos = list_public_repos()
    languages = aggregate_languages(repos)
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as file:
        file.write(render_svg(repos, languages))


if __name__ == "__main__":
    main()
