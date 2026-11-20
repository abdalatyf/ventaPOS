# VentaPOS NextGen — Agent Instructions Pointer

> [!IMPORTANT]
> **Single Deduplicated Rulebook**: To eliminate 2x–3x prompt duplication across workspace config files, all prior governance rules from `GEMINI.md` §0–§8 have been preserved verbatim (with new engineering standards added) inside **`.agents/rules/rules.md`** (`trigger: always_on`).

## Primary Authoritative Documents (Read First)

1. **`.agents/rules/rules.md`** — **Master Rules & Engineering Governance** (`trigger: always_on`):
   - Preserves all prior governance rules: §0 Application Overview, §1 SSoT Protocol, §2 Desktop Runtime Environment (`VentaPOS_NextGen` & `LicenseManager`), §3 All 10 Red Lines, §4 Core Business Rules (§4.1–§4.7), §5 Application Lifecycle, §6 UI/UX & Language Principles, §7 Mandatory 5-Phase Workflow, and §8 Developer Protocols & Strict English-Only Agent Communication Rule.
   - Enforces the 4 mandatory engineering rule sets: **§9 `APP_BIBLE.md` Synchronization**, **§10 Django Engineering Rules**, **§11 React Engineering Rules**, and **§12 PyInstaller Safety Rules**.

2. **`APP_BIBLE.md`** — **Supreme Architecture & Codebase Single Source of Truth** (repo root):
   - Living reference for system topology, dev vs. frozen runtime lifecycle, SQLite models & migrations, API contracts, React routes & hooks, PyInstaller specs, and command cheat sheets.
   - **Mandatory Sync**: Read relevant sections before editing, update matching sections in the same turn as code edits, and explicitly report which sections were updated in your final response.

## Subproject Reference Docs (Reconciled with `APP_BIBLE.md`)

- `VentaPOS_NextGen/requirements.md` — Domain models, stock/commission math, and active API catalog.
- `VentaPOS_NextGen/UI_UX_RULES.md` — Visual identity, 2-Scroll table architecture, and 10 audited Arabic reports.
- `VentaPOS_NextGen/TODO.md` — Master task and bug tracker.
- `LicenseManager/requirements.md` & `LicenseManager/TODO.md` — 80-bit licensing, Supabase fail-closed auth/audit, and quota matrix.

*All agent thinking, plans, subagent messages, and user responses MUST be strictly in English.*
