# Tech Stack

## Architecture

**Offline-First, Single-Tenant Desktop Application**

Both the backend (Django) and frontend (React) run locally on the cashier's machine. There is no cloud server or remote database — all data is stored in a local SQLite database. The desktop window is provided by PyWebView, which embeds a native webview to render the React frontend.

> [!IMPORTANT]
> This is a **single-tenant** system. There is no `Tenant` model, no tenant foreign keys, and no multi-tenancy logic. Each installation is one company with one or more branches.

---

## Components

### Backend (Server)

| Component | Version / Details |
| :--- | :--- |
| **Python** | 3.12+ |
| **Django** | 5.x |
| **Django REST Framework** | Token-based authentication (single admin user) |
| **Database** | **SQLite** with **WAL mode** (Write-Ahead Logging for concurrent read/write) |
| **Primary Keys** | `AutoField` / `BigAutoField` (integer IDs, **not UUIDs**) |
| **PDF Generation** | ReportLab / WeasyPrint (local PDF rendering) |
| **Printing** | `os.startfile()` + SumatraPDF for silent local printing |

### Frontend (Desktop / Web)

| Component | Version / Details |
| :--- | :--- |
| **React** | 19 |
| **Vite** | Build toolchain |
| **Tabler UI** | Component library |
| **Auth** | DRF `TokenAuthentication` — single admin password |
| **Language** | Arabic RTL — Egyptian market terminology |

### Desktop Wrapper

| Component | Details |
| :--- | :--- |
| **PyWebView** | Embeds the React SPA in a native desktop window |
| **Target OS** | Windows (primary) |

### Testing

| Component | Details |
| :--- | :--- |
| **Backend** | Django test framework, pytest |
| **E2E** | Comprehensive end-to-end testing suite |

### Development Tooling

| Component | Details |
| :--- | :--- |
| **AI Agent Framework** | Google Antigravity 2.0 Multi-Agent Setup |
| **Version Control** | Git + GitHub MCP for automated commits |

---

## Key Design Decisions

| Decision | Rationale |
| :--- | :--- |
| SQLite over PostgreSQL | Offline-first desktop app — no server installation required |
| WAL mode | Enables concurrent reads during writes without locking |
| Integer PKs over UUIDs | Simpler, faster for single-tenant local database |
| Single admin (no roles) | Target users are small retail shops with one admin |
| No fixed selling price | Cashier enters price per sale — common in Egyptian wholesale |
| Integer quantities only | No fractional units |
| Monthly date system | Reports and ledgers operate on month/year, not daily |
| Soft delete (`is_deleted`) | All models use `ActiveManager` to filter deleted records |
| No barcode/SKU | Products identified by name only |
| `os.startfile()` printing | Permitted because backend runs on the same local machine |

---

## Deferred / Out of Scope

| Item | Status |
| :--- | :--- |
| Mobile App (Flutter) | **Deferred** — not in current scope |
| Cloud Sync Server | **Deferred** — not in current scope |
| PostgreSQL | **Removed** — replaced by SQLite |
| Multi-tenancy | **Removed** — single-tenant architecture |
| Multi-user roles | **Not planned** — single admin only |
