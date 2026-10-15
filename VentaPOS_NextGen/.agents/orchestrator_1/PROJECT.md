# Project: VentaPOS NextGen POS Entry Testing

## Architecture
- Frontend: Single Page Application / Web POS at `http://localhost:5173/pos`
- Backend: Python / Django REST API backend with SQLite database
- Models: `Receipt`, `SaleItem`, `InstallmentPayment`, `Product`, `Customer`
- Core Functionalities Under Test:
  1. UI Functional Behavior (Cash Sale toggle hiding/showing customer/installment sections, autocomplete for Product and Customer)
  2. E2E Receipt Submissions (Cash Sale & Installment Sale flows, subtotal/tax/discount math, down payments, installment schedule start date calculation)
  3. Backend Data Integrity (SQLite/Django database record validation, cryptographic/hash integrity, tenant isolation, exact financial math matching)

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & Infra Verification | Analyze backend & frontend code, identify DB location, running services, endpoints | None | DONE |
| 2 | UI & End-to-End Submission Testing | Test Cash & Installment sales, frontend calculations, autocomplete, API response 201 | M1 | DONE |
| 3 | Backend Data Integrity Verification | Run DB queries to verify Receipt, SaleItem, InstallmentPayment records, hashes, tenant isolation | M2 | DONE |

## Interface Contracts
### POS Entry UI ↔ Backend API
- Product search endpoints
- Customer search endpoints
- Receipt submission API
