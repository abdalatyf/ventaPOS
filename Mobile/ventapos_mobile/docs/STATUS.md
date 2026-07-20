# VentaPOS Mobile - Development Status

This document tracks the ongoing development of the new **VentaPOS Mobile App** built using Flutter 3.38+ with a Clean Architecture approach and Riverpod state management. It covers both completed milestones and pending tasks.

---

## 🏗️ Phase 1: Project Scaffolding & Setup
**Status:** In Progress (🟡)

### Completed (✅)
- **Framework Setup:** Initialized a brand new Flutter project `ventapos_mobile`.
- **Core Dependencies Added:** 
  - State Management: `flutter_riverpod`, `riverpod_annotation`
  - Database & Local Storage: `sqflite`, `shared_preferences`
  - Networking: `dio`
  - Routing: `go_router`
  - Code Generation: `freezed_annotation`, `json_annotation`
  - UI Utilities: `google_fonts`
- **Clean Architecture Folders:** Scaffolded the foundational folder structure (`lib/core`, `lib/features`).

### Pending (⏳)
- **Dev Dependencies Setup:** Add code generators (`build_runner`, `freezed`, `json_serializable`, `riverpod_generator`).

---

## 🔐 Phase 2: Role-Based Core System & Database
**Status:** In Progress (🟡)

### Completed (✅)
- **Database Helper (SQLite):** Build the local database tables for branches, inventory, and receipts (Offline-First support).

### Pending (⏳)
- **Authentication & Roles:** Implement the logic to distinguish between `Manager` and `Salesperson`.
- **Offline Setup Form:** Create the local configuration flow for offline salespersons.

---

## 🛒 Phase 3: POS & Cart Features
**Status:** Pending (⏳)

### Pending (⏳)
- **Riverpod Cart Provider:** Build a reactive shopping cart that handles complex price calculations and installments safely.
- **Local Temporary Products:** Allow offline salespersons to add temporary items to the cart during internet outages.
- **Invoice Drafts:** Save completed sales as drafts (`is_exported = 0`) to local SQLite.

---

## 📊 Phase 4: Dashboard & Role UI
**Status:** Pending (⏳)

### Pending (⏳)
- **Manager Dashboard:** Display complete branch metrics, team performance, and top products.
- **Salesperson Dashboard:** Restrict view to personal daily sales and pending drafts.

---

## 🔄 Phase 5: Sync Engine
**Status:** Pending (⏳)

### Pending (⏳)
- **API Client:** Configure Dio to communicate with the VentaPOS NextGen local desktop server.
- **Draft Exporter:** Implement the push mechanism to send local receipts to the main system.

---

*Note: This document will be continually updated as development progresses.*
