# Tech Stack: VentaPOS NextGen

## Primary Languages & Frameworks
- **Backend:** Python 3.12+, Django 5.x, Django REST Framework (DRF)
- **Frontend:** React (Vite), Tabler UI (Bootstrap 5)
- **Database:** SQLite (local `db_system.sqlite3` and `business_data.sqlite3`)

## Key Tools & Dependencies
- **E2E Testing:** Playwright
- **Package Managers:** `pip` for Python, `npm` for Node.js
- **PDF Generation:** `wkhtmltopdf` (via backend OS calls)
- **Printing:** `SumatraPDF.exe` (via backend OS calls)

## Architecture
- **Single Source of Truth (Database):** The database schema is strictly defined and managed by the backend. Do not hallucinate table structures. Refer to `docs/database_schema.md` for current relationships.
- **API Contracts:** The frontend communicates with the backend via REST endpoints. Refer to `docs/api_contract.md`.

## Active Skills
- `django-pro`: Utilize for any backend/ORM/Django modifications.
- `react-modernization`: Utilize for any frontend React hooks/state optimization.
