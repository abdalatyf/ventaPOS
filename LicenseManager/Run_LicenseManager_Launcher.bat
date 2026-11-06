@echo off
chcp 65001 >nul
title VentaPOS License Manager Launcher
cd /d "%~dp0"

echo ========================================================
echo  VentaPOS License Manager Launcher [Live Console Mode]
echo ========================================================
echo Current directory: %CD%

set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

if not exist "..\VentaPOS_NextGen\venv\Scripts\python.exe" goto :check_local_venv
echo Starting VentaPOS License Manager using VentaPOS_NextGen venv...
"..\VentaPOS_NextGen\venv\Scripts\python.exe" -u launcher.py
goto :end

:check_local_venv
if not exist "venv\Scripts\python.exe" goto :check_dist_exe
echo Starting VentaPOS License Manager using local venv...
"venv\Scripts\python.exe" -u launcher.py
goto :end

:check_dist_exe
if not exist "dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe" goto :not_found
echo Warning: Virtual environment not found. Starting compiled executable...
"dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe"
goto :end

:not_found
echo [ERROR] Could not find virtual environment Python:
echo         ..\VentaPOS_NextGen\venv\Scripts\python.exe or venv\Scripts\python.exe
echo         or compiled executable: dist\VentaPOS_LicenseManager\VentaPOS_LicenseManager.exe

:end
echo.
echo ========================================================
echo Process exited with code %ERRORLEVEL%.
echo Press any key to close this console window.
pause