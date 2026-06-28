@echo off
echo ===================================================
echo VentaPOS Central Server
echo ===================================================
echo Starting Django Server on port 8000...

cd /d "%~dp0"
venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

pause
