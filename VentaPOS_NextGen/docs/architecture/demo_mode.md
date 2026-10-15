# Demo Mode Architecture

This document outlines the architecture and workflow for the VentaPOS NextGen Demo Mode (الوضع التجريبي) and the Post-Activation Flow.

## 1. Overview

To provide clients with an immediate, frictionless trial experience (Zero-Friction), VentaPOS NextGen boots directly into a **Demo Mode** on the very first launch. 
- The standard System Initialization wizard (`SystemInit`) has been completely removed.
- The user is dropped into a fully populated, functioning POS environment with rich dummy data.
- The `CompanyTab` in settings is locked (Read-Only) to prevent customizing the receipts before purchasing the system.

## 2. Database Seeding Strategy

The Demo Mode relies on an automated database seeding mechanism:
- **`init_demo_db.py` Script**: Automatically runs on the first system start if no company settings exist.
- It generates realistic Egyptian dummy data (inventory items, previous receipts, suppliers, and a Lifetime Demo license assigned to `DEMO_MACHINE`).
- It creates a master admin user (`admin`) with an **empty password** (`""`), allowing seamless bypass of the login screen via `/auth/demo/`.

## 3. Activation Flow & Post-Activation Setup

While in Demo Mode, the user sees a persistent UI banner:
> **"النسخة التجريبية - كافة البيانات المعروضة وهمية. للتفعيل الكامل اضغط هنا"** 

When the user activates the system from the **Subscription Tab**:
1. The backend (`LicenseActivateView`) validates the license cryptographically.
2. **Data Wipe**: If activating from Demo Mode, all demo data (Receipts, Invoices, Items, Branches, Company Settings) are permanently deleted.
3. **Redirect to Setup**: The frontend automatically redirects the user to `/activation-setup`.
4. **Post-Activation Wizard**: The user is forced to enter their real Company Name and details.
5. **Optional Password**: The user is presented with an optional field to set an Admin Password. If left blank, the system remains password-free for easy access.

## 4. Intelligent Security Toggle

To maximize user flexibility, the system allows toggling password protection via the **Security Tab**:
- The UI checks the `GET /api/v1/auth/has-password/` endpoint to determine the current state.
- **Enable Password**: If the system has no password, the user can toggle the switch ON and enter a new password (no old password required).
- **Disable Password**: If the system is protected, the user can toggle the switch OFF, which only prompts for the *current* password to confirm the action, passing an empty string to the backend to remove the password.

## 5. Security & Isolation

- **License Generator**: The tool used to generate activation keys (`LicenseManager`) is strictly an offline developer tool and is **not** bundled with VentaPOS NextGen.
- **Demo Limitations**: The company receipt header cannot be altered in demo mode, effectively watermarking all printed trial receipts with "نسخة تجريبية VentaPOS".
