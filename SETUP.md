# Profile metrics automation

The generator summarizes language bytes in public, non-fork repositories owned
by jordan-zav. Private repositories and project deliverables are excluded even
when an authentication token is present. It does not rewrite the profile text.

## GitHub Actions

The Metrics workflow generates metrics.svg and commits that file when it
changes. It uses the built-in GitHub Actions token; no personal access token or
private-repository access is required. The workflow grants contents write
permission for its generated commit.

The daily cloud fallback is scheduled at 14:17 UTC, or 09:17 in Lima. GitHub may
delay scheduled runs. A manual run is available under Actions → Metrics → Run
workflow. Updates to the generator also trigger a run. Concurrent updates are
serialized.

Transient network and server failures receive bounded retries. Authentication
or sustained API failures stop generation and preserve the previous SVG;
incomplete repository data is never committed as a successful refresh.
API rate-limit handling follows the
[GitHub REST API guidance](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api).

## Windows task at 09:00

Install GitHub CLI and authenticate the current Windows user using gh auth login
with an account allowed to run this repository's workflow. Do not store tokens
in repository files. Run Setup-Automation.ps1 from the checkout you intend to
keep. Re-run it after moving the checkout. Replacing an existing elevated task
may require an administrator session.

The task requests the same cloud workflow at 09:00 and at this user's logon.
It catches up after a missed run when the user is logged in and the network is
available. Two retries are configured at five-minute intervals. The explicit
GitHub CLI path avoids a stale Task Scheduler PATH.

Update-Metrics.ps1 dispatches the workflow without modifying the local Git
checkout. This avoids rebase conflicts with cloud-generated metrics. Successful
dispatch means GitHub accepted the request; the actual generation result is
reported in Actions. The daily cloud fallback works with this PC switched off.

Run update-metrics.bat -CheckOnly to verify workflow access without dispatching
an update. Run update-metrics.bat to request an update. The local DevResources
runner is used when present. Logs are stored outside Git under
LOCALAPPDATA/jordan-zav/profile-metrics/logs; GitHub stores the generation logs.

## Local development

Run the Python tests and Ruff checks using the repository's DEVRESOURCES_RUN.cmd
on configured workstations. The generator can also run directly with Python
3.11. An optional GITHUB_TOKEN raises API limits while keeping the same
public-only scope. The README's biography and project descriptions are edited
manually; the daily job updates only metrics.svg.
