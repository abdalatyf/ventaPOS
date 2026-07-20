# VentaPOS Mobile - Visual UI/UX & Flow Plan

This document maps the exact visual experience and user flow for the Mobile App, ensuring it perfectly mirrors the Desktop application's structure and feel.

## 1. Onboarding & Mode Selection (شاشة البداية واختيار الوضع)
When the user opens the mobile app for the first time, they will see a clean, modern interface presenting two main paths:
*   **تسجيل الدخول السحابي (Online Hybrid):** A login form asking for Username and Password. Once authenticated, the app connects to the server, fetches the company data, and determines if the user is a Manager or a Salesperson.
*   **تهيئة عبر الكابل (Offline USB):** A screen instructing the user to connect their phone to the Desktop PC via USB to pull the database file securely without internet.

## 2. The Main Sidebar (القائمة الجانبية)
The Mobile Sidebar will be a slide-out drawer (`Drawer` in Flutter) that strictly replicates the 5-section architecture of the Desktop App `base.html`:

### القسم الأول: المبيعات (Sales)
*   **إضافة فاتورة (Add Receipt):** The core Point of Sale screen. Includes product search, barcode scanning, and cart management.
*   **بحث وتعديل الفواتير (Search Receipts):** A search grid to view historical invoices. *(Note: Returns/Refunds are view-only on mobile).*

### القسم الثاني: المشتريات والمصروفات (Purchases & Expenses)
*   *This section is primarily for Managers.*
*   **المصروفات (Expenses):** Allows recording daily branch expenses (e.g., electricity, petty cash).

### القسم الثالث: التأسيس والإدارة (Management) - *[Manager Only]*
*   **إدارة المناديب (Manage Salespersons):** A screen to list all salespeople. A floating "Add" button opens a Modal Bottom Sheet to quickly create a new salesperson.
*   **الأصناف والتسعير (Manage Products):** The inventory list showing quantities and purchase prices. Includes the ability to add new products or adjust stock.

### القسم الرابع: التقارير والتحليلات (Reports & Analytics)
*   **ملخصات الداشبورد (Dashboard):** The main landing page. A clean, list-based dashboard showing the current month's "صافي الخزينة" (Net Cash) and "أفضل المنتجات مبيعاً" (Top Selling Products), with a month/year filter at the top.
*   **إحصائيات المبيعات (Sales Reports):** Detailed breakdowns. Salespersons only see their own numbers; Managers see all branches.

### القسم الخامس: الأدوات (Tools)
*   **الربط أونلاين / مركز المزامنة (Sync Hub):** A dedicated screen showing the cloud connection status. Features a manual "مزامنة الآن" (Sync Now) button, and displays the "Last Synced At" timestamp.
*   **تسجيل الخروج (Logout):** Returns the user to the Mode Selection screen.

## 3. Manager vs. Salesperson Experience
The UI dynamically adapts based on the logged-in role:
*   **Salesperson (المندوب):** The "Management" section is completely hidden. The Dashboard only shows their personal sales targets and net cash. They cannot see product purchase prices.
*   **Manager (المدير):** Sees the full 5-section sidebar. The Dashboard aggregates data across the entire branch (or all branches). They have access to the Add/Edit Modal Bottom Sheets for Products and Users.

## 4. Visual Identity (الهوية البصرية)
The mobile app will use the exact same color palette as the Tabler-based Desktop app:
*   **Primary Accent:** `#1A4571` (Navy Blue) for headers and primary buttons.
*   **Success/Action:** `#1DA068` (Green) for the "Checkout" or "Sync" buttons.
*   **Background:** `#F4F6F8` (Light Gray) to give cards and lists a floating, elevated appearance.
*   **Typography:** The `Cairo` font family will be used globally to ensure perfect Arabic readability.
