# Copyright (c) 2026 Jordan Zavaleta
# This file is part of jordan-zav.
# jordan-zav is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import html
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


# Configuración
USER = "jordan-zav"
OUTPUT = "metrics.svg"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Configurar logging
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)
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
    """Realiza una solicitud autenticada a la API de GitHub."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "jordan-zav-profile-readme",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            # Never retry authentication failures or hammer a rate-limited API.
            # Long waits are left to the next scheduled run; keep the existing SVG.
            retryable = error.code in {500, 502, 503, 504}
            delay = 2 ** attempt
            retry_after = error.headers.get("Retry-After") if error.headers else None
            if retry_after is not None:
                try:
                    delay = max(delay, float(retry_after))
                except ValueError:
                    raise error
            if not retryable or delay > 30 or attempt == 2:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            delay = 2 ** attempt
        logger.warning("Temporary GitHub API failure; retrying in %s seconds", delay)
        time.sleep(delay)
    raise RuntimeError("GitHub request did not complete")


def list_all_repos() -> list[dict]:
    """Obtiene solo repositorios publicos del perfil, excluyendo forks."""
    repos: list[dict] = []
    page = 1
    logger.info("Obteniendo repositorios...")

    try:
        while True:
            url = f"https://api.github.com/users/{USER}/repos?type=owner&sort=full_name&per_page=100&page={page}"
            logger.debug(f"Consultando página {page}...")
            batch = github_json(url)

            if not isinstance(batch, list):
                raise ValueError("Unexpected GitHub repository response")
            if not batch:
                break

            repos.extend(repo for repo in batch if not repo.get("fork") and not repo.get("private"))
            page += 1

        logger.info(f"✓ Se encontraron {len(repos)} repositorios")
        return repos
    except Exception as e:
        logger.error(f"✗ Error al obtener repositorios: {e}")
        raise


def aggregate_languages(repos: list[dict]) -> dict[str, int]:
    """Agrega y cuenta los bytes de código por lenguaje de todos los repositorios."""
    totals: dict[str, int] = {}
    logger.info("Analizando lenguajes de programación...")

    for index, repo in enumerate(repos, 1):
        repo_name = repo.get("name", "unknown")
        if repo.get("private") or repo.get("fork"):
            continue
        languages_url = repo.get("languages_url")

        if not languages_url:
            raise ValueError(f"Missing language URL for {repo_name}")

        languages = github_json(languages_url)
        if not isinstance(languages, dict):
            raise ValueError(f"Unexpected language response for {repo_name}")
        for language, bytes_count in languages.items():
            totals[language] = totals.get(language, 0) + int(bytes_count)

    result = dict(sorted(totals.items(), key=lambda item: (-item[1], item[0])))
    logger.info(f"✓ Se detectaron {len(result)} lenguajes")
    return result


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
<desc id="desc">Language summary generated only from public, non-fork GitHub repositories.</desc>
<rect width="560" height="{height}" rx="12" fill="#0d1117"/>
<text x="24" y="38" fill="#58a6ff" font-family="Segoe UI, Arial, sans-serif" font-size="22" font-weight="700">GitHub Profile Metrics</text>
<text x="24" y="68" fill="#c9d1d9" font-family="Segoe UI, Arial, sans-serif" font-size="14">Total repositories analyzed: {repo_count}</text>
<text x="24" y="92" fill="#c9d1d9" font-family="Segoe UI, Arial, sans-serif" font-size="14">Languages detected: {language_count}</text>
<text x="24" y="124" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="13">Language share by bytes in public source repositories</text>
<g font-family="Segoe UI, Arial, sans-serif">
{rows}
</g>
</svg>
"""


def main() -> int:
    """Genera el archivo SVG con las métricas del perfil de GitHub."""
    try:
        logger.info("=" * 60)
        logger.info(
            f"Iniciando generación de métricas ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        )
        logger.info("=" * 60)

        repos = list_all_repos()
        languages = aggregate_languages(repos)

        if not languages:
            raise ValueError("No language data received; preserving the existing SVG")

        output_path = Path(__file__).resolve().parents[1] / OUTPUT
        svg_content = render_svg(repos, languages)

        temporary_path = output_path.with_suffix(".svg.tmp")
        temporary_path.write_text(svg_content, encoding="utf-8", newline="\n")
        temporary_path.replace(output_path)

        logger.info(f"✓ Archivo generado exitosamente: {output_path}")
        logger.info("=" * 60)
        return 0

    except KeyboardInterrupt:
        logger.warning("Proceso interrumpido por el usuario.")
        return 130
    except Exception as e:
        logger.error(f"✗ Error fatal: {e}")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
