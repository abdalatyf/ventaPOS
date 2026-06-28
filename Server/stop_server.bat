@echo off
echo ===================================================
echo Stopping VentaPOS Central Server on port 8000
echo ===================================================

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    if "%%a" NEQ "0" (
        echo Killing PID %%a...
        taskkill /F /PID %%a 2>nul
    )
)

echo Done.
pause
