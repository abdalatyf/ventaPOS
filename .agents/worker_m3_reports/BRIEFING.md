# BRIEFING — 2026-09-01T03:20:00+03:00

## Mission
Refactor the 7 report pages and verify ReceiptsReport in VentaPOS NextGen frontend to strictly match REPORTS_AGREEMENT.md, UI_UX_RULES.md, TABLE_UX_GUIDELINES.md, utilizing formatUtils.js and ReportAutocomplete.jsx.

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: d:\Projects\VentaPOS\.agents\worker_m3_reports
- Original parent: d11e6e43-8b57-4a1e-9692-d7682ea08eff
- Milestone: Milestone 3 (R3: Refactor 7 Report Pages)

## 🔒 Key Constraints
- Adhere strictly to REPORTS_AGREEMENT.md and requirements.md.
- Import standard utilities from `src/utils/formatUtils.js` (`fmtNum`, `toArabic`, `toEnglish`, `formatMMYYYY`).
- Use `ReportAutocomplete` for dynamic subfilters (Product, Salesperson, Area, etc.) instead of raw unbounded selects.
- Wrap tables in `ReportTable` with sticky headers and toolbar.
- Fluid containers (`container-fluid`).
- Zero console errors, zero build failures (`npm run build` must pass).
- Genuine implementations only.

## Current Parent
- Conversation ID: d11e6e43-8b57-4a1e-9692-d7682ea08eff
- Updated: 2026-09-01T03:20:00+03:00

## Task Summary
- **What to build**: Full refactoring of 7 report pages + ReceiptsReport check:
  1. `DashboardReport.jsx`
  2. `SalespersonPerformanceReport.jsx`
  3. `InventoryMovementReport.jsx`
  4. `ProfitAndLossReport.jsx`
  5. `AveragesReport.jsx`
  6. `InstallmentsReport.jsx`
  7. `ExpensesReport.jsx`
  8. `ReceiptsReport.jsx`
- **Success criteria**: All pages conform to REPORTS_AGREEMENT.md, proper backend array extraction, formatUtils, ReportAutocomplete, ReportTable layout, and `npm run build` passes with exit code 0.

## Change Tracker
- **Files modified**:
  - `DashboardReport.jsx`: 2-card layout, fixed purchases drill-down link, formatUtils integration.
  - `SalespersonPerformanceReport.jsx`: Array extraction fix (`data.salespersons`), 7 KPI summary cards, grouped table headers, ReportAutocomplete.
  - `InventoryMovementReport.jsx`: Array extraction fix (`data.items`), 10 exact columns, 8 KPI summary cards, ReportAutocomplete.
  - `ProfitAndLossReport.jsx`: 7 exact columns, 6 KPI cards, cash '---' handling, ReportAutocomplete.
  - `AveragesReport.jsx`: 7 exact per-unit columns, zero summary cards per spec, ReportAutocomplete.
  - `InstallmentsReport.jsx`: 9 exact columns, MM/YYYY formatting, ReportAutocomplete, sale range filters.
  - `ExpensesReport.jsx`: 4 exact columns, 3 subfilters, 2 KPI summary cards, formatUtils.
  - `ReceiptsReport.jsx`: Standard formatUtils integration, ReportAutocomplete, numeric input fix, aggregate cards.
- **Build status**: `npm run build` passed (exit code 0). 108 backend tests passed (exit code 0).
- **Pending issues**: None.

## Quality Status
- **Build/test result**: All frontend and backend builds/tests pass cleanly.
- **Lint status**: clean.
- **Tests added/modified**: Verified against 108 existing backend tests and production frontend bundle build.
