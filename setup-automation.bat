@echo off
REM Script para registrar la tarea automática en Windows Task Scheduler
REM Ejecutar como Administrador

echo.
echo ============================================================
echo  Configurador de Automatización - Task Scheduler
echo ============================================================
echo.

REM Verificar permisos de administrador
net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Este script debe ejecutarse como Administrador
    echo.
    echo Por favor:
    echo 1. Haz clic derecho en este archivo
    echo 2. Selecciona "Ejecutar como administrador"
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup-Automation.ps1"

echo.
echo ============================================================
echo.
echo Para cambiar la configuración o la hora en el futuro:
echo 1. Abre el Programador de tareas (Task Scheduler)
echo 2. Navega a: Biblioteca de tareas -> GitHub Profile -> Update Metrics
echo 3. Haz clic derecho -> Propiedades
echo 4. En la pestaña Desencadenadores, edita o elimina las reglas.
echo.
echo ============================================================
echo.
pause
