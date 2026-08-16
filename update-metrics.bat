@echo off
REM Script para actualizar y pushear las métricas del perfil de GitHub
REM Este script genera el SVG con las estadísticas y actualiza el repositorio

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Colores para output (necesita Windows 10+)
for /F %%A in ('echo prompt $H ^| cmd') do set "BS=%%A"

echo.
echo ============================================================
echo  Actualizador de Métricas del Perfil de GitHub
echo ============================================================
echo.

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado o no está en el PATH
    exit /b 1
)

REM Verificar que GITHUB_TOKEN está configurado
if not defined GITHUB_TOKEN (
    echo [ADVERTENCIA] GITHUB_TOKEN no está configurado
    echo Configúralo como variable de entorno para mejor rendimiento
    echo.
)

REM Sincronizar antes de generar para evitar conflictos con GitHub Actions
echo [INFO] Sincronizando la rama local...
git pull --rebase --autostash
if errorlevel 1 (
    echo [ERROR] No se pudo sincronizar el repositorio
    exit /b 1
)

REM Ejecutar el script Python
echo [INFO] Generando métricas...
python scripts\generate_profile_metrics.py
if errorlevel 1 (
    echo [ERROR] Falló la generación de métricas
    exit /b 1
)

echo.
echo [INFO] Verificando cambios en Git...
git status --porcelain | findstr "metrics.svg" >nul
if errorlevel 1 (
    echo [INFO] Sin cambios en metrics.svg - nada que actualizar
    exit /b 0
)

echo.
echo [INFO] Preparando cambios...
git add metrics.svg

echo [INFO] Creando commit...
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm"') do set "timestamp=%%i"
git commit -m "chore: actualizar métricas del perfil [%timestamp%]"

echo.
echo [INFO] Haciendo push...
git push

if errorlevel 1 (
    echo [ERROR] Falló el push
    exit /b 1
)

echo.
echo ============================================================
echo [EXITO] Métricas actualizadas y pushed correctamente!
echo ============================================================
echo.

exit /b 0
