@echo off
chcp 65001 >nul
title VentaPOS Launcher
cd /d "%~dp0"

if exist "%~dp0VentaPOS_NextGen" (
    cd /d "%~dp0VentaPOS_NextGen"
)

echo ========================================================
echo  VentaPOS Desktop Launcher [Live Console Mode]
echo ========================================================
echo Current directory: %CD%

set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

rem Step 1: Always build the latest frontend if frontend directory exists
if exist "frontend\package.json" (
    echo [1/2] Building latest React Frontend (frontend/dist)...
    pushd frontend
    call npm run build
    if errorlevel 1 (
        echo [ERROR] Frontend build failed!
        popd
        echo.
        echo Press any key to close this console window.
        pause
        exit /b 1
    )
    popd
)

rem Step 2: Run launcher via Python virtual environment in foreground
if exist "venv\Scripts\python.exe" (
    echo [2/2] Starting VentaPOS via Python in live console mode...
    "venv\Scripts\python.exe" -u launcher.py
    goto :end
)

if exist "dist\VentaPOS\VentaPOS.exe" (
    echo [2/2] Warning: Virtual environment not found. Starting compiled executable...
    "dist\VentaPOS\VentaPOS.exe"
    goto :end
)

echo [ERROR] Could not find virtual environment Python (venv\Scripts\python.exe)
echo         or compiled executable (dist\VentaPOS\VentaPOS.exe).

:end
echo.
echo ========================================================
echo Process exited with code %ERRORLEVEL%.
echo Press any key to close this console window.
pause
