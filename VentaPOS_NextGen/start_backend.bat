@echo off
echo Starting VentaPOS Backend...
cd backend
call ..\venv\Scripts\activate.bat
python manage.py runserver
pause
