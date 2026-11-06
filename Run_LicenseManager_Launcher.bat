@echo off
title VentaPOS License Manager Launcher
cd /d "%~dp0"

if exist "%~dp0LicenseManager" (
    cd /d "%~dp0LicenseManager"
)

echo ========================================================
echo  VentaPOS License Manager Launcher
echo ========================================================
echo Current directory: %CD%

if exist "dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe" (
    echo Starting compiled VentaPOS License Manager...
    "dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe"
    goto :end
)

if exist "..\VentaPOS_NextGen\venv\Scripts\python.exe" (
    echo Starting VentaPOS License Manager using VentaPOS_NextGen venv...
    "..\VentaPOS_NextGen\venv\Scripts\python.exe" launcher.py
    goto :end
)

if exist "venv\Scripts\python.exe" (
    echo Starting VentaPOS License Manager using local venv...
    "venv\Scripts\python.exe" launcher.py
    goto :end
)

echo [ERROR] Could not find compiled executable (dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe)
echo         or virtual environment Python (venv\Scripts\python.exe).

:end
echo.
echo ========================================================
echo Process exited with code %ERRORLEVEL%.
echo Press any key to close this console window.
pause
