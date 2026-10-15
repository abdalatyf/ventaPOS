# Project: Venta POS - Settings Overhaul

## Architecture
- Django application with a main app called `salesapp` under `sales/`.
- Frontend consists of HTML templates including `base.html`.
- Internal pages and tabs within Management, Reports, and Settings need to be audited.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Audit & Evaluation | Explore and document sub-pages in Mgmt, Reports, Settings from base.html. Evaluate utility (Keep/Merge/Remove). Produce a unified Markdown report. | none | DONE |
| 2 | Settings UX Overhaul | Design and implement a clean, modern, and logical Settings dashboard/layout based on the M1 report. Refactor sidebar and internal templates. | M1 | DONE |

## Interface Contracts
- The final report from M1 should be a markdown file detailing the maps and Keep/Merge/Remove recommendations.
- M3 must maintain all existing functionality in the Settings section.
