# Workflow Guidelines

## 1. Context-Driven Development (CDD)

All AI agents and developers MUST proactively read the following context files **before** starting any session or task:

1. [`docs/index.md`](../index.md) — Master documentation hub
2. [`docs/business/workflow.md`](./workflow.md) — This file (dev workflow rules)
3. `task_plan.md` — Current task plan (if one exists)

> [!WARNING]
> Failure to read these context files before writing code, modifying the architecture, or making decisions is a **strict violation** of the VentaPOS NextGen workflow.

---

## 2. Continuous Documentation & GitHub MCP Sync

> **ENFORCED RULE:** Every time the AI makes a code commit (using standard git or GitHub MCP), the AI MUST synchronously update the corresponding documentation in the same workflow. Documentation is never left behind the code.

### What must be updated:

| Code Change | Required Doc Update |
| :--- | :--- |
| Django model change | `architecture/02_data_models.md` (when created) |
| API endpoint added/changed | `architecture/03_api_contract.md` (when created), relevant `features/*.md` |
| React component added | `architecture/06_frontend_architecture.md`, `index.md` TODO section |
| UI design token change | `architecture/04_ui_design_tokens.md` |
| Business rule change | Relevant `features/*.md` document |

### GitHub MCP Protocol:

- Use `create_or_update_file` or `push_files` to push code **and** documentation changes together
- Never push code without updating the corresponding docs

---

## 3. Architecture Rules

### Database

- **SQLite + WAL mode** — the only supported database engine
- **Single-tenant** — no `Tenant` model, no tenant FKs on any model
- **Integer primary keys** (`AutoField` / `BigAutoField`) — not UUIDs
- **Soft delete** — all models use `is_deleted` flag with `ActiveManager`
- No direct schema changes without updating `architecture/02_data_models.md` first

### Authentication

- **Single admin user** — no multi-user roles
- **DRF `TokenAuthentication`** — one admin password for the system
- **Recovery code** — stored in `client_license` table (special license type)

### Desktop Environment

- Backend and frontend both run **locally** on the cashier's machine
- **PyWebView** wraps the React SPA in a native desktop window
- Backend MAY interact directly with the local OS (e.g., `os.startfile()` for printing)

---

## 4. Code Quality Rules

### Security

- **IDOR checks** — all API endpoints must verify object ownership (branch-scoped)
- No raw SQL — use Django ORM exclusively
- Validate all user input server-side (serializer-level validation)

### Performance

- **N+1 query prevention** — use `select_related()` and `prefetch_related()` on all querysets
- **Pagination** — all list endpoints must be paginated
- Profile database queries in development using Django Debug Toolbar or `django.db.connection.queries`

### Testing

- **E2E testing** — comprehensive end-to-end tests for all critical flows
- **Parity tests** — ensure backend calculations match frontend display (see `technical/parity_tests_doc.md`)
- All tests must pass before merging

### UI / RTL

- The UI **MUST** be verified for Arabic RTL compatibility on every feature
- Use Egyptian market terminology: العميل, البضاعة, الخزنة, الفاتورة, الدفتر, النقدية, المندوب
- Tone: professional but easy Egyptian Arabic (لغة سوق مهنية ومبسطة)

---

## 5. Python Script Execution Rule

> **ENFORCED RULE:** When executing a Python script (`.py`) in the terminal, you MUST prepend the `python` command:
> ```
> python script.py        ✅ Correct
> .\script.py             ❌ Wrong — triggers Windows file association prompt
> ```
