param(
    [ValidatePattern('^([01][0-9]|2[0-3]):[0-5][0-9]$')]
    [string]$Time = '09:00'
)

$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'Update-Metrics.ps1'
$cliPath = (Get-Command gh.exe -ErrorAction Stop).Source
$powershellPath = Join-Path $PSHOME 'powershell.exe'
$userId = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskPath = '\GitHub Profile\'
$taskName = 'Update Metrics'

if (-not (Test-Path -LiteralPath $scriptPath)) { throw 'Update-Metrics.ps1 is missing.' }
$arguments = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' +
    $scriptPath + '" -GitHubCli "' + $cliPath + '"'
$action = New-ScheduledTaskAction -Execute $powershellPath -Argument $arguments -WorkingDirectory $PSScriptRoot
$triggers = @(
    (New-ScheduledTaskTrigger -Daily -At $Time),
    (New-ScheduledTaskTrigger -AtLogOn -User $userId)
)
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskPath $taskPath -TaskName $taskName -Action $action -Trigger $triggers `
    -Principal $principal -Settings $settings -Force | Out-Null
Write-Host "Task configured for $Time and this user's logon."
Write-Host "Current checkout: $PSScriptRoot"
Write-Host 'The task requests the GitHub workflow; it does not pull, rebase or commit local files.'
