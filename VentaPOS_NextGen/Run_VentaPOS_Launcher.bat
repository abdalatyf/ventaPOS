@echo off
chcp 65001 >nul
title VentaPOS Launcher
cd /d "%~dp0"

echo ========================================================
echo  VentaPOS Desktop Launcher [Live Console Mode]
echo ========================================================
echo Current directory: %CD%

set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

rem Check if frontend exists to build
if not exist "frontend\package.json" goto :skip_frontend_build
echo [1/2] Building latest React Frontend...
cd frontend
call npm.cmd run build
if errorlevel 1 goto :frontend_build_failed
cd ..
goto :skip_frontend_build

:frontend_build_failed
echo [ERROR] Frontend build failed with errorlevel %ERRORLEVEL%.
cd ..
goto :end

:skip_frontend_build
rem Check Python in virtual environment
if not exist "venv\Scripts\python.exe" goto :check_dist_exe
echo [2/2] Starting VentaPOS via Python in live console mode...
"venv\Scripts\python.exe" -u launcher.py
goto :end

:check_dist_exe
if not exist "dist\VentaPOS\VentaPOS.exe" goto :not_found
echo [2/2] Warning: Virtual environment not found. Starting compiled executable...
"dist\VentaPOS\VentaPOS.exe"
goto :end

:not_found
echo [ERROR] Could not find virtual environment Python: venv\Scripts\python.exe
echo         or compiled executable: dist\VentaPOS\VentaPOS.exe

:end
echo.
echo ========================================================
echo Process exited with code %ERRORLEVEL%.
echo Press any key to close this console window.
pause