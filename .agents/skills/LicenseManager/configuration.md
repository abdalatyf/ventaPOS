# LicenseManager - Configuration & Environment

This document maps the main entry points, environment configurations, constants, external dependencies, and local execution steps for the LicenseManager application.

## 1. Boot Sequence & Entry Points
The application follows the standard Django initialization process.

1.  **Entry Command**: The developer executes `python manage.py runserver` from the root directory (`D:\Projects\VentaPOS\LicenseManager`).
2.  **Environment Setup**: `manage.py` sets the `DJANGO_SETTINGS_MODULE` environment variable to `core.settings`.
3.  **Settings Resolution**: Django imports `core/settings.py` and loads all configurations.
4.  **Database Connection**: Django connects to the local SQLite database defined in `DATABASES`.
5.  **App Registry**: Django loads all installed apps, including the custom `licenses` app.
6.  **URL Routing**: Incoming HTTP requests are routed through `core.urls` to the appropriate functions in `licenses.views`.

## 2. Environment Variables & Constants

The application currently relies entirely on hardcoded constants within the source code rather than external `.env` files.

### In `core/settings.py`:
*   `DEBUG`: `True` (Currently set for development. MUST be `False` in production).
*   `SECRET_KEY`: `'django-insecure-pmwa6)4dmwtcdykry@qts9ebq@huw1wzu-^#9o!wei809!b!gk'` (The standard Django secret key for session signing).
*   `MASTER_PASSWORD`: `"123"` (The hardcoded password required to access the application dashboard).
*   `ALLOWED_HOSTS`: `[]` (Empty, meaning it only accepts requests from localhost/127.0.0.1).

### In `licenses/utils/crypto.py`:
*   `SECRET_KEY`: `b"JqxQQAKo0BbI76tknaKlhd0rC9hDcam_bqJywXmaXHqAKkVPRZhzgRjHX-zME11enx2oB8o_ivJCn2pXBX-Pow"` (The cryptographic key used to generate HMAC-SHA256 signatures for licenses. **Critical for security**).
*   `BASE_YEAR`: `2025` (The reference year used for compressing the start date into a single byte).
*   `CHARSET`: `"ABCDEFGHJKLMNPQRSTUVWXYZ23456789"` (Custom base32 alphabet for license codes).

## 3. Database Configuration
*   **Engine**: `django.db.backends.sqlite3`
*   **Location**: `BASE_DIR / 'db.sqlite3'` (Stored locally in the project root).
*   No external database services (PostgreSQL, MySQL) are required for local execution.

## 4. Dependencies
While there is no `requirements.txt` explicitly tracking exact versions, the required packages are defined by the environment:
*   **Python**: Version 3.10 or higher.
*   **Django**: Version 6.0 (Based on the generated header comments in `settings.py`).
*   **Virtual Environment**: The project relies on a local `venv` directory (`D:\Projects\VentaPOS\LicenseManager\venv`) to isolate dependencies.

## 5. Local Execution Instructions
To run this application locally on a Windows machine:
1.  Open PowerShell/CMD in `D:\Projects\VentaPOS\LicenseManager`.
2.  Activate the virtual environment:
    ```powershell
    .\venv\Scripts\Activate
    ```
3.  Ensure database migrations are applied (optional if `db.sqlite3` already has the schema):
    ```powershell
    python manage.py migrate
    ```
4.  Start the development server:
    ```powershell
    python manage.py runserver
    ```
5.  Open a web browser and navigate to `http://127.0.0.1:8000`.
6.  Enter the password `"123"` to log in.
