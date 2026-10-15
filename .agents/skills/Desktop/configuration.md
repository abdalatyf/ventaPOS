# POS Project Configuration

This document outlines the core configuration settings, server boot sequence, database routing logic, and optimization pragmas for the Venta POS system.

## 1. Waitress Server Boot Sequence (`run_app.py`)

The application is bundled and executed locally with a PyWebview frontend and a Waitress WSGI backend. The boot sequence is carefully ordered to ensure secure database decryption and robust port allocation:

1. **Django Setup:** 
   - Sets the `DJANGO_SETTINGS_MODULE` environment variable to `sales.settings`.
   - Calls `django.setup()` to initialize the framework.
2. **Database Security Initialization (`initialize_database_security`):**
   - Cleans up any leftover temporary `-wal` or `-shm` files.
   - If a legacy unencrypted database (`business_data.bin`) exists, it encrypts it into `business_data.enc`.
   - Decrypts `business_data.enc` into a temporary runtime SQLite file (`~sys_runtime_cache_v1.tmp`) for extremely fast memory/disk hybrid access.
3. **Backup Restoration & Migrations:**
   - Checks for a pending restore (`restore_pending.bin`), and if found, encrypts and replaces the main encrypted DB.
   - Runs `ensure_databases_are_ready()`, triggering `migrate` for both `system` and `default` databases to ensure schemas are up-to-date.
4. **Auto-Save Worker:**
   - Starts a daemon background thread (`auto_save_worker`) that runs every 5 minutes to flush WAL checkpoints and atomically encrypt/save the runtime database back to the persistent encrypted file.
5. **Server Initialization:**
   - Locates a dynamically available free port (`get_free_port()`).
   - Starts the Waitress WSGI server (`serve`) in a background thread, binding to `127.0.0.1` on the found port with 6 worker threads.
   - Waits 2 seconds for the server to properly boot.
6. **PyWebview Launch:**
   - Opens the native OS window using `webview.create_window` pointing to the local Waitress URL.
   - Binds the `cleanup_on_exit` callback to the window's `closed` event, ensuring the system safely flushes data, closes Django DB connections, encrypts the final database state, and cleans up the temporary runtime database upon exit.

## 2. Dual-Database Routing Logic (`salesapp/db_router.py`)

The system implements a dual-database architecture splitting the application data from the system/licensing data. This logic is handled by `SystemRouter`:

*   **`system` Database (`~sys_lic_runtime.tmp`):**
    *   Dedicated to handling authentication, sessions, admin logs, and licensing.
    *   Matches app labels: `auth`, `contenttypes`, `sessions`, `admin`.
    *   Matches specific models: `clientlicense`, `usedlicense`, `licensehistory`.
*   **`default` Database (`~sys_runtime_cache_v1.tmp`):**
    *   Serves all business logic (invoices, inventory, receipts, settings).
    *   Handles everything not explicitly routed to the `system` database.
*   **Routing Behaviors:**
    *   `db_for_read` and `db_for_write` correctly route queries based on the app labels and specific system model names.
    *   `allow_migrate` strictly enforces schema creation for system models in the `system` DB and business models in the `default` DB.
    *   `allow_relation` blindly returns `True` to allow application logic to loosely relate cross-database entities where necessary.

## 3. Local Offline Settings (`settings.py`)

As a locally running desktop POS application wrapped by PyInstaller, standard Django settings are heavily modified for an offline environment:

*   **Path Resolution:** `BASE_DIR` attempts to resolve `sys._MEIPASS` if the app is frozen (PyInstaller runtime environment). Otherwise, it defaults to the standard parent directory.
*   **Database Storage Paths:** 
    *   Uses `LOCALAPPDATA` (e.g., `C:\Users\<User>\AppData\Local\VentaPOS`).
    *   If `LOCALAPPDATA` isn't found, falls back to `~\AppData\Local\VentaPOS`.
    *   The system creates the directory and attempts to apply the "Hidden" file attribute (Windows `0x02`) to the DB folder.
*   **Security & Debug:**
    *   `DEBUG = False`
    *   `ALLOWED_HOSTS = ['*']` (Relies on local Waitress binding and pywebview for security).
    *   `CSRF_TRUSTED_ORIGINS` includes Ngrok URLs for potential tunneling/remote testing contexts.
*   **Static Assets:** Served entirely locally using `whitenoise.middleware.WhiteNoiseMiddleware` reading from `STATIC_ROOT` (`staticfiles`).
*   **Sessions:** Configured to save on every request (`SESSION_SAVE_EVERY_REQUEST = True`), expiring on browser close (`SESSION_EXPIRE_AT_BROWSER_CLOSE = True`), heavily customized for single-user desktop software behavior.

## 4. SQLite WAL Pragmas

To optimize SQLite for concurrent reads and writes, the application intercepts the Django `connection_created` signal to inject specific pragmas immediately after opening any SQLite database connection (`default` or `system`):

*   `PRAGMA synchronous = NORMAL;`: Reduces disk syncing to balance speed and safety in WAL mode.
*   `PRAGMA journal_mode = WAL;`: Enables Write-Ahead Logging, significantly improving concurrent access and preventing "database is locked" errors.
*   `PRAGMA cache_size = -64000;`: Allocates 64MB of memory for the page cache to massively speed up reads.
*   `PRAGMA temp_store = MEMORY;`: Forces temporary tables and indices to be stored in RAM instead of disk.
*   `PRAGMA busy_timeout = 5000;`: Forces the connection to wait up to 5000 milliseconds (5 seconds) when encountering a lock before raising an exception.
