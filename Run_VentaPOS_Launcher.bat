@echo off
title VentaPOS Launcher
cd /d "%~dp0"

if exist "%~dp0VentaPOS_NextGen" (
    cd /d "%~dp0VentaPOS_NextGen"
)

echo ========================================================
echo  VentaPOS Desktop Launcher
echo ========================================================
echo Current directory: %CD%

if exist "dist\VentaPOS\VentaPOS.exe" (
    echo Starting compiled VentaPOS application...
    "dist\VentaPOS\VentaPOS.exe"
    goto :end
)

if exist "venv\Scripts\python.exe" (
    echo Starting VentaPOS in development mode via Python...
    "venv\Scripts\python.exe" launcher.py
    goto :end
)

echo [ERROR] Could not find compiled executable (dist\VentaPOS\VentaPOS.exe)
echo         or virtual environment Python (venv\Scripts\python.exe).

:end
echo.
echo ========================================================
echo Process exited with code %ERRORLEVEL%.
echo Press any key to close this console window.
pause
