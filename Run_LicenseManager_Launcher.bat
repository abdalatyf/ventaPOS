@echo off
chcp 65001 >nul
title VentaPOS License Manager Launcher
cd /d "%~dp0"

if exist "%~dp0LicenseManager" (
    cd /d "%~dp0LicenseManager"
)

echo ========================================================
echo  VentaPOS License Manager Launcher [Live Console Mode]
echo ========================================================
echo Current directory: %CD%

set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

if exist "..\VentaPOS_NextGen\venv\Scripts\python.exe" (
    echo Starting VentaPOS License Manager using VentaPOS_NextGen venv...
    "..\VentaPOS_NextGen\venv\Scripts\python.exe" -u launcher.py
    goto :end
)

if exist "venv\Scripts\python.exe" (
    echo Starting VentaPOS License Manager using local venv...
    "venv\Scripts\python.exe" -u launcher.py
    goto :end
)

if exist "dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe" (
    echo Warning: Virtual environment not found. Starting compiled executable...
    "dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe"
    goto :end
)

echo [ERROR] Could not find virtual environment Python (..\VentaPOS_NextGen\venv\Scripts\python.exe or venv\Scripts\python.exe)
echo         or compiled executable (dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe).

:end
echo.
echo ========================================================
echo Process exited with code %ERRORLEVEL%.
echo Press any key to close this console window.
pause
