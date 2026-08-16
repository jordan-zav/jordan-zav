# Script para configurar automatización en Windows Task Scheduler
# EJECUTAR COMO ADMINISTRADOR

param(
    [ValidateSet("09:00", "12:00", "18:00", "21:00")]
    [string]$Time = "09:00"
)

# Verificar permisos de administrador
$isAdmin = [Security.Principal.WindowsIdentity]::GetCurrent().Groups -contains 'S-1-5-32-544'
if (-not $isAdmin) {
    Write-Host "[ERROR] Este script debe ejecutarse como Administrador" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para ejecutar como administrador:"
    Write-Host "1. Abre PowerShell como Administrador"
    Write-Host "2. Ejecuta: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process"
    Write-Host "3. Ejecuta: .\Setup-Automation.ps1"
    exit 1
}

Write-Host ""
Write-Host "============================================================"
Write-Host " Configurador de Automatización - GitHub Profile Metrics"
Write-Host "============================================================"
Write-Host ""
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = Join-Path $scriptDir "update-metrics.bat"

# Validar que el archivo .bat existe
if (-not (Test-Path $batPath)) {
    Write-Host "[ERROR] No se encontró: $batPath" -ForegroundColor Red
    exit 1
}

$taskPath = "\GitHub Profile\"
$taskName = "Update Metrics"

Write-Host "[INFO] Configurando tarea automática..."
Write-Host "  Script: $batPath"
Write-Host "  Hora: $Time (diariamente)"
Write-Host ""

try {
    # Crear acción
    $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`"" -WorkingDirectory $scriptDir

    # Crear desencadenadores (diariamente a la hora especificada y al iniciar sesión)
    $triggerDaily = New-ScheduledTaskTrigger -Daily -At $Time
    $triggerLogon = New-ScheduledTaskTrigger -AtLogOn
    $triggers = @($triggerDaily, $triggerLogon)

    # Crear principal (ejecutar con privilegios elevados)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

    # Configurar opciones
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew

    # Registrar la tarea
    Register-ScheduledTask -TaskPath $taskPath -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Force | Out-Null

    Write-Host "[EXITO] Tarea registrada correctamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "La tarea se ejecutará:"
    Write-Host "  - Diariamente a las $Time"
    Write-Host "  - Cada vez que se inicie sesión (encendido del equipo)"
    Write-Host ""
}
catch {
    Write-Host "[ERROR] No se pudo registrar la tarea: $_" -ForegroundColor Red
    exit 1
}

Write-Host "============================================================"
Write-Host ""
