# VentaPOS NextGen - Master Documentation Hub

Welcome to the VentaPOS NextGen Documentation Hub. This directory contains all technical, architectural, and business guidelines required to build, maintain, and scale the application.

## 1. Business & Product Rules (`/business`)
*Core rules about how the POS should function and look.*
- [Product Vision](./business/product.md) - Product Context
- [Workflow Rules](./business/workflow.md) - Workflow Guidelines
- [Tech Stack](./business/tech-stack.md) - Tech Stack
- [UI Localization Guidelines](./business/product-guidelines.md) - Product Guidelines
- [Tracks](./business/tracks.md) - Tracks Registry

## 2. Architecture (`/architecture`)
*Deep technical blueprints and design systems.*
- [00 Master Index](./architecture/00_master_index.md) - VentaPOS NextGen - Architecture Manual
- [01 Executive Summary](./architecture/01_executive_summary.md) - VentaPOS NextGen Rebuild - Project Scope & Milestones
- [02 Architecture Overview](./architecture/02_architecture_overview.md) - Enterprise Blueprint: Orchestrating a 12-Agent Swarm
- [03 Core Components](./architecture/03_core_components.md) - Target Requirements Specification (PRD)
- [04 Data Models](./architecture/04_data_models.md) - Target Database Schema
- [05 Integration Points](./architecture/05_integration_points_and_apis.md) - Integration Points & API Contracts
- [06 UI Design Tokens](./architecture/06_ui_design_tokens.md) - UI Design Tokens & Declarative Elements
- [07 Mobile Architecture](./architecture/07_mobile_architecture.md) - VentaPOS Mobile Architecture
- [08 Mobile Screens Plan](./architecture/08_mobile_screens_plan.md) - VentaPOS Mobile - Screens Implementation Plan
- [Frontend Architecture](./architecture/frontend_architecture.md) - VentaPOS NextGen - Frontend Architecture & Developer Guide

## 3. Technical Specs (`/technical`)
*API definitions, schemas, and test cases.*
- [API Contract (OpenAPI)](./technical/api_contract.md) - عقد واجهات برمجة التطبيقات (API Contract)
- [Database Schema](./technical/database_schema.md) - هيكل قاعدة البيانات (Database Schema)
- [Backend Models](./technical/backend_models_doc.md) - Backend Models Documentation
- [Parity Tests](./technical/parity_tests_doc.md) - VentaPOS NextGen — Parity Test Strategy Documentation

## 4. Feature Documentation (`/features`)
*Detailed documentation for specific pages and features, generated dynamically by AI agents.*
- [Inventory Management](./features/inventory_management.md) - Inventory Management & Time-Machine Ledger
- [POS & Receipts](./features/pos_and_receipts.md) - POS & Receipts Documentation
- [Procurement & Suppliers](./features/procurement.md) - المشتريات والموردين (Procurement)
- [Reports & Tools](./features/reports_and_tools.md) - تقارير النظام وأدوات الإدارة (Reports & Tools)
- [Settings & Security](./features/settings_and_security.md) - Settings and Security
- [Backend Micro-Features](./features/backend_micro_features.md) - Backend Helper APIs (Commissions, Adjustments, Suggestions, Date)
- [System Init & Admin Tools](./features/system_init_and_tools.md) - System Initialization & Admin Tools

---

## 5. Missing Documentation (TODO)
*The following features, pages, or API endpoints exist in the codebase but do not yet have dedicated feature documentation.*

### Frontend Pages
- **Branch Selection (`BranchSelection.jsx`)**: Needs documentation for branch switching and related API (`/api/branches/`).
- **Expenses (`Expenses.jsx`)**: Expense tracking is missing from POS & Reports docs (API: `/api/expenses/`).
- **Purchase Invoices & Suppliers (`PurchaseEntry.jsx`, `SearchPurchases.jsx`)**: The complete purchasing flow and supplier management (APIs: `/api/purchase-invoices/`, `/api/suppliers/`).
- **System Initialization & Setup (`SystemInit.jsx`, `Setup.jsx`)**: The initial setup wizard and first-time configuration (API: `/api/init/`).
- **Search Modules (`SearchReceipts.jsx`)**: Detailed documentation on receipt searching and filtering capabilities.
- **Smart Import Tool (`settings/tabs/SmartImportTab.jsx`)**: Excel import tool functionality (API: `/api/tools/smart-import/`).
- **System Logs (`settings/tabs/LogsTab.jsx`)**: Action logs viewer (API: `/api/action-logs/`).
