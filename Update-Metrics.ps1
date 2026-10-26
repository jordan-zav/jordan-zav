param(
    [string]$GitHubCli,
    [switch]$CheckOnly,
    [switch]$Managed
)

$ErrorActionPreference = 'Stop'
$localRunner = Join-Path $PSScriptRoot '.devresources.runner.ps1'
if (-not $Managed -and (Test-Path -LiteralPath $localRunner)) {
    & $localRunner -ScriptPath $PSCommandPath -ScriptParameters @{
        Managed = $true; CheckOnly = [bool]$CheckOnly; GitHubCli = $GitHubCli
    }
    exit $LASTEXITCODE
}

$logRoot = Join-Path $env:LOCALAPPDATA 'jordan-zav\profile-metrics\logs'
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$logPath = Join-Path $logRoot ((Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '_' + $PID + '.log')
$env:GH_PROMPT_DISABLED = '1'
$env:GIT_TERMINAL_PROMPT = '0'

function Write-Log([string]$Message) {
    $line = (Get-Date -Format o) + ' ' + $Message
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
    Write-Host $line
}

function Invoke-GitHub([string[]]$CommandArguments) {
    $savedPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = & $GitHubCli @CommandArguments 2>&1
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $savedPreference }
    if ($code -ne 0) {
        throw ('GitHub CLI failed (' + $code + '): ' + ($output -join [Environment]::NewLine))
    }
    return ($output -join [Environment]::NewLine)
}

try {
    if (-not $GitHubCli) { $GitHubCli = (Get-Command gh.exe -ErrorAction Stop).Source }
    if (-not (Test-Path -LiteralPath $GitHubCli -PathType Leaf)) {
        throw 'GitHub CLI not found. Run Setup-Automation.ps1 with gh installed.'
    }
    Write-Log 'Checking the public profile metrics workflow.'
    $workflow = Invoke-GitHub -CommandArguments @('api', 'repos/jordan-zav/jordan-zav/actions/workflows/metrics.yml') |
        ConvertFrom-Json
    if ($workflow.state -ne 'active') { throw 'The metrics workflow is not active.' }
    if ($CheckOnly) {
        Write-Log 'PASS: workflow accessible. CheckOnly did not request an update.'
    } else {
        $null = Invoke-GitHub -CommandArguments @('workflow', 'run', 'metrics.yml', '--repo', 'jordan-zav/jordan-zav', '--ref', 'main')
        Write-Log 'Update requested successfully. Generation and commit run on GitHub, not in the local checkout.'
        Write-Log 'Run results: https://github.com/jordan-zav/jordan-zav/actions/workflows/metrics.yml'
    }
    exit 0
} catch {
    Write-Log ('ERROR: ' + $_.Exception.Message)
    exit 1
}
