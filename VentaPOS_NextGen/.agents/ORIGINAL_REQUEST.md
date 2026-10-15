# Original User Request

## Initial Request — 2026-07-04T01:20:13Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Thoroughly test the newly implemented Add Receipt (POS Entry) screen to verify both Cash Sale and Installment flows, payload integrity, and backend database recording.

Working directory: D:\Projects\VentaPOS\VentaPOS_NextGen

## Requirements

### R1. UI Functional Testing
Test the frontend component at `http://localhost:5173/pos`. Verify that the "Cash Sale" toggle correctly hides/shows customer and installment sections, and that the Product and Customer autocomplete fields fetch data correctly from the backend.

### R2. End-to-End Submission Testing
Successfully submit at least one Cash Sale invoice and one Installment Sale invoice. Verify that the frontend correctly calculates subtotals, installment shifts, and down payments.

### R3. Backend Data Integrity Verification
After submission, query the backend database (SQLite/Django) to verify that the `Receipt`, `SaleItem`, and `InstallmentPayment` records were saved exactly as submitted, with correct hashes and tenant isolation.

## Acceptance Criteria

### Testing Deliverables
- [ ] A documented test run of the Cash Sale flow, confirming successful 201 response.
- [ ] A documented test run of the Installment flow, confirming the installment dates start on the correct month.
- [ ] Database queries confirming the records exist and mathematical totals match the expected values.
