# Server Application - Configuration & Environment Memory

This document outlines the boot sequence, environment configurations, constants, external dependencies, and build details for the VentaPOS Server application.

## 1. Application Entry Points
The application follows the standard Django 6.0 initialization pattern:
- **CLI / Development**: `manage.py` serves as the primary administrative tool for running the local server, migrating the database, and collecting static files.
- **Production / Web Server Gateway**: `server_backend/wsgi.py` and `server_backend/asgi.py` expose the application callable for WSGI/ASGI-compatible web servers (e.g., Gunicorn/Uvicorn).

## 2. Boot Sequence & Build Lifecycle
The server provides a `build.sh` script to automate deployment and initialization tasks:
```bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```
**Boot Steps**:
1. Aborts execution immediately if any command fails (`set -o errexit`).
2. Installs Python dependencies via `pip`.
3. Collects static assets (primarily for the Django Admin UI) into a unified directory.
4. Applies database migrations to initialize or update the SQLite schema.

## 3. Environment Configurations (`settings.py`)
Currently, the application relies heavily on hardcoded constants rather than external environment variables (aside from `DJANGO_SETTINGS_MODULE` set implicitly in the entry points).
- **Debug Mode**: `DEBUG = True` (indicating a development or permissive staging environment).
- **Secret Key**: Hardcoded (`django-insecure-h6%5haczx...`).
- **Database**: SQLite3 configured to run locally at `BASE_DIR / 'db.sqlite3'`.
- **Static Files**: Mounted at `STATIC_URL = 'static/'`.
- **Timezone**: Set to `UTC`.

## 4. External Dependencies & Execution Strategy
- **Core Framework**: Django (Version 6.0 generated).
- **Tunneling**: The repository contains `ngrok.exe`. This binary is used to punch a hole through the local firewall, exposing the local Django server to the internet so that remote POS client machines can push their sync payloads to it.
- **Run Command (Local)**:
  1. `python manage.py runserver 0.0.0.0:8000`
  2. In a separate terminal: `ngrok http 8000`
  3. The resulting Ngrok URL must match the hardcoded `CSRF_TRUSTED_ORIGINS` in `settings.py`.
