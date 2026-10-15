## 2026-07-04T01:22:17Z
<USER_REQUEST>
You are an Environment & Integration Explorer for VentaPOS NextGen POS Entry screen testing.
Your working directory is: d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_3

Objective:
Investigate the environment, server execution setup, database state, and test runner setup.
1. Check how the backend server is launched (e.g., python main.py, manage.py runserver, uvicorn, gunicorn, etc.) and what port it runs on.
2. Check how the frontend dev server is launched (e.g., npm run dev, vite, etc.) and confirm standard port 5173.
3. Locate the active SQLite database file (e.g., db.sqlite3 or similar), inspect existing table structures/data, check if seed data exists or if seed scripts exist (`migrate_legacy_data.py` or similar).
4. Verify if any test runner (pytest, vitest, cypress, playwright, requests script, etc.) exists in the repository or can be used for UI and API E2E testing.

Inputs to read:
- `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\orchestrator_1\PROJECT.md`
- `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\ORIGINAL_REQUEST.md`

Output:
Write your complete analysis report to `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_3\analysis.md` and deliver your `handoff.md` in your working directory.
When finished, send a message to parent with the key findings and path to your handoff report.
</USER_REQUEST>
