@echo off
title VentaPOS License Manager Launcher
cd /d "%~dp0"

if exist "%~dp0LicenseManager" (
    cd /d "%~dp0LicenseManager"
)

if exist "dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe" (
    echo Starting compiled VentaPOS License Manager...
    start "" "dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe"
    exit /b 0
)

if exist "..\VentaPOS_NextGen\venv\Scripts\pythonw.exe" (
    echo Starting VentaPOS License Manager (pythonw)...
    start "" "..\VentaPOS_NextGen\venv\Scripts\pythonw.exe" launcher.py
    exit /b 0
)

if exist "..\VentaPOS_NextGen\venv\Scripts\python.exe" (
    echo Starting VentaPOS License Manager (python)...
    start "" "..\VentaPOS_NextGen\venv\Scripts\python.exe" launcher.py
    exit /b 0
)

if exist "venv\Scripts\pythonw.exe" (
    echo Starting VentaPOS License Manager with local venv (pythonw)...
    start "" "venv\Scripts\pythonw.exe" launcher.py
    exit /b 0
)

if exist "venv\Scripts\python.exe" (
    echo Starting VentaPOS License Manager with local venv (python)...
    start "" "venv\Scripts\python.exe" launcher.py
    exit /b 0
)

echo [ERROR] Could not find compiled executable or virtual environment python.
pause
