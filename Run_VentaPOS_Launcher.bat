@echo off
title VentaPOS Launcher
cd /d "%~dp0"

if exist "%~dp0VentaPOS_NextGen" (
    cd /d "%~dp0VentaPOS_NextGen"
)

if exist "dist\VentaPOS\VentaPOS.exe" (
    echo Starting compiled VentaPOS...
    start "" "dist\VentaPOS\VentaPOS.exe"
    exit /b 0
)

if exist "venv\Scripts\pythonw.exe" (
    echo Starting VentaPOS in development mode (pythonw)...
    start "" "venv\Scripts\pythonw.exe" launcher.py
    exit /b 0
)

if exist "venv\Scripts\python.exe" (
    echo Starting VentaPOS in development mode (python)...
    start "" "venv\Scripts\python.exe" launcher.py
    exit /b 0
)

echo [ERROR] Could not find compiled executable or virtual environment python.
pause
