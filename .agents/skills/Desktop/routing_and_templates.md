# 🌐 Exhaustive Routing & Templates Architecture

## Complete URL Pattern Mapping

This table exhaustively maps every exact URL pattern to its specific view function across the Django project (from `sales/sales/urls.py` and `sales/salesapp/urls.py`).

### Admin Routes (`sales/sales/urls.py`)
| Path | Name | View Function/Class | Module |
|---|---|---|---|
| `/admin/` | `index` | `index` | `django.contrib.admin.sites` |
| `/admin/login/` | `login` | `login` | `django.contrib.admin.sites` |
| `/admin/logout/` | `logout` | `logout` | `django.contrib.admin.sites` |
| `/admin/password_change/` | `password_change` | `password_change` | `django.contrib.admin.sites` |
| `/admin/password_change/done/` | `password_change_done` | `password_change_done` | `django.contrib.admin.sites` |

### Auth & Settings (`sales/salesapp/urls.py`)
| Path | Name | View Function/Class | Module |
|---|---|---|---|
| `/` | `login` | `login_view` | `salesapp.views.auth_views` |
| `/logout/` | `logout` | `logout_view` | `salesapp.views.auth_views` |
| `/emergency-reset/` | `emergency_reset` | `emergency_reset_view` | `salesapp.views.auth_views` |
| `/setup-company/` | `setup_company` | `setup_company` | `salesapp.views.auth_views` |
| `/general-settings/` | `general_settings` | `general_settings` | `salesapp.views.auth_views` |
| `/password-change/` | `password_change` | `PasswordChangeView` | `django.contrib.auth.views` |
| `/password-change/done/` | `password_change_done` | `PasswordChangeDoneView` | `django.contrib.auth.views` |
| `/backup-db/` | `download_backup` | `download_backup` | `salesapp.views.backup_views` |
| `/restore-db/` | `restore_backup` | `restore_backup` | `salesapp.views.backup_views` |

### Branches & Dashboard
| Path | Name | View Function/Class | Module |
|---|---|---|---|
| `/select_branch/` | `select_branch` | `select_branch` | `salesapp.views.branch_views` |
| `/set_branch/<int:branch_id>/` | `set_branch` | `set_branch` | `salesapp.views.branch_views` |
| `/dashboard/` | `dashboard` | `dashboard` | `salesapp.views.branch_views` |

### Inventory & Purchases (Module)
| Path | Name | View Function/Class | Module |
|---|---|---|---|
| `/inventory/products/` | `manage_products` | `manage_products` | `salesapp.views.inventory_views` |
| `/inventory/products/delete/<int:pk>/` | `delete_product` | `delete_product` | `salesapp.views.inventory_views` |
| `/inventory/products/update-commission/` | `update_commission` | `update_commission` | `salesapp.views.inventory_views` |
| `/inventory/products/commission/update/` | `update_commission` | `update_commission` | `salesapp.views.inventory_views` |
| `/inventory/products/commission/edit/<int:record_id>/` | `edit_commission_record` | `edit_commission_record` | `salesapp.views.inventory_views` |
| `/inventory/products/commission/delete/<int:record_id>/` | `delete_commission_record` | `delete_commission_record` | `salesapp.views.inventory_views` |
| `/inventory/suppliers/` | `manage_suppliers` | `manage_suppliers` | `salesapp.views.purchase_views` |
| `/inventory/suppliers/delete/<int:pk>/` | `delete_supplier` | `delete_supplier` | `salesapp.views.purchase_views` |
| `/inventory/purchases/` | `manage_purchase_invoices` | `manage_purchase_invoices` | `salesapp.views.purchase_views` |
| `/inventory/purchases/search/` | `search_purchase_invoices` | `search_purchase_invoices` | `salesapp.views.purchase_views` |
| `/inventory/purchases/edit/<int:invoice_id>/` | `edit_purchase_invoice` | `edit_purchase_invoice` | `salesapp.views.purchase_views` |
| `/inventory/purchases/delete/<int:invoice_id>/` | `delete_purchase_invoice` | `delete_purchase_invoice` | `salesapp.views.purchase_views` |
| `/inventory/adjustment/add/` | `add_adjustment` | `add_adjustment` | `salesapp.views.inventory_views` |
| `/product/<int:pk>/ledger/` | `product_ledger` | `product_ledger` | `salesapp.views.inventory_views` |

### Sales, Receipts & Collections (Module)
| Path | Name | View Function/Class | Module |
|---|---|---|---|
| `/receipts/add/` | `add_receipt` | `add_receipt` | `salesapp.views.receipt_views` |
| `/receipts/search/` | `search_receipts` | `search_receipts` | `salesapp.views.receipt_views` |
| `/receipts/edit/<int:receipt_id>/` | `edit_receipt` | `edit_receipt` | `salesapp.views.receipt_views` |
| `/receipts/print/<int:receipt_id>/` | `print_single_receipt_view` | `print_single_receipt_view` | `salesapp.views.print_views` |
| `/receipts/print_batch/` | `print_batch_receipts` | `print_batch_receipts_view` | `salesapp.views.print_views` |
| `/receipt/delete/<int:pk>/` | `delete_receipt` | `delete_receipt` | `salesapp.views.receipt_views` |
| `/receipt/delete-all/` | `delete_all_receipts` | `delete_all_receipts` | `salesapp.views.receipt_views` |
| `/api/customer-suggestions/` | `get_customer_suggestions` | `get_customer_suggestions` | `salesapp.views.receipt_views` |
| `/api/product-suggestions/` | `product_suggestions_api` | `product_suggestions_api` | `salesapp.views.receipt_views` |
| `/collections/` | `manage_collections` | `manage_collections` | `salesapp.views.collections_views` |
| `/reports/sales/` | `sales_reports` | `sales_reports` | `salesapp.views.report_views` |
| `/reports/invoices/` | `invoices_report` | `invoices_report` | `salesapp.views.report_views` |

### Sub-settings & Expenses
| Path | Name | View Function/Class | Module |
|---|---|---|---|
| `/settings/branches/` | `manage_branches` | `manage_branches` | `salesapp.views.settings_views` |
| `/settings/branches/edit/<int:pk>/` | `edit_branch` | `edit_branch` | `salesapp.views.settings_views` |
| `/settings/branches/delete/<int:pk>/` | `delete_branch` | `delete_branch` | `salesapp.views.settings_views` |
| `/settings/salespersons/` | `manage_salespersons` | `manage_salespersons` | `salesapp.views.settings_views` |
| `/settings/salespersons/edit/<int:pk>/` | `edit_salesperson` | `edit_salesperson` | `salesapp.views.settings_views` |
| `/settings/salespersons/delete/<int:pk>/` | `delete_salesperson` | `delete_salesperson` | `salesapp.views.settings_views` |
| `/settings/subscription/` | `subscription_dashboard` | `subscription_dashboard` | `salesapp.views.subscription_views` |
| `/settings/import-legacy/` | `smart_import_wizard` | `smart_import_wizard` | `salesapp.views.import_views` |
| `/expenses/` | `manage_expenses` | `manage_expenses` | `salesapp.views.expense_views` |
| `/expenses/delete/<int:pk>/` | `delete_expense` | `delete_expense` | `salesapp.views.expense_views` |
| `/activate/` | `activate_app` | `activate_app_view` | `salesapp.views.subscription_views` |
| `/shutdown-app/` | `shutdown_app` | `exit_app` | `salesapp.views.utility_views` |


## Template Inheritance Hierarchy

The frontend relies strictly on Django's template engine extending from a single base layout.
- `base.html`: The core container containing global headers, the custom sidebar, global CSS/JS, Print modals, HTMX includes, Zoom logic, and printing JS logic.
- All functional view templates inherit directly from `salesapp/base.html` using `{% extends 'salesapp/base.html' %}` and inject content via `{% block content %}`. Examples:
  - `add_receipt.html` extends `base.html`
  - `edit_receipt.html` extends `base.html`
  - `manage_purchase_invoices.html` extends `base.html`
  - `edit_purchase_invoice.html` extends `base.html`
  - `search_receipts.html` extends `base.html`
  - `general_settings.html` extends `base.html`
  - `dashboard.html` extends `base.html`
- Includes are also utilized: e.g., `receipt_list_rows.html` is an HTMX partial or standard Django include rendered dynamically.


## Front-end AJAX Interactions (`templates/salesapp/`)

Every AJAX integration across the frontend is listed below without summarization.

### 1. Print Batch Logic (The 3-Second Sleep in `base.html`)
In `base.html`, the async `startSmartBatchPrint(url, totalReceipts)` function handles iterating over all receipts dynamically and dispatching them to the printer in batches to prevent Windows Print Spooler overload and avoid paper jams.
- It iterates `for (let offset = 0; offset < totalReceipts; offset += limit)` where `limit = 5` receipts per batch.
- It initiates a `fetch(url)` POST request containing `FormData` (`selected_printer`, `offset`, `limit`).
- It attaches the Django CSRF Token directly into the headers via `X-CSRFToken: document.querySelector('[name=csrfmiddlewaretoken]').value`.
- **The 3-Second Pause Logic:** Upon a successful iteration where `data.status === 'success'`, and if there are more receipts left to print (`completedReceipts < totalReceipts`):
  ```javascript
  if (completedReceipts < totalReceipts && !isCancelled) {
      statusText.innerText = "⏸️ استراحة الطابعة لتجنب التكدس...";
      await new Promise(resolve => setTimeout(resolve, 3000));
  }
  ```
  This explicit 3000ms delay (`setTimeout`) stalls the next loop iteration exactly 3 seconds to guarantee that the hardware printer processes the buffered documents smoothly and without jamming.

### 2. Single Print Execution (`base.html`)
- `executeSinglePrint()` fires an AJAX `fetch(url)` POST request using `FormData` just for `selected_printer` and sends `X-CSRFToken`. 
- Handles the UI loading bar asynchronously until it resolves `if (response.ok)`.

### 3. Legacy PDF Export Generation (`base.html`)
- `startPrintProcess(url, itemCount, msPerItem)` triggers a `fetch(url, { signal: signal })` GET request passing an `AbortController` signal to allow cancellation.
- Parses the response as a blob `return response.blob();`.
- Replaces the DOM by invoking a temporary element download `a.download = ...; a.click();`.

### 4. Autocomplete / Suggestions Fetch APIs
Multiple templates trigger `fetch()` asynchronously while typing inside the search input box (`input.addEventListener('input', ...)`). These requests reach REST-like Django endpoints.
- **`add_receipt.html` and `edit_receipt.html`:**
  - Product Search: Triggers `fetch('/api/product-suggestions/?term=${encodeURIComponent(term)}&month=${saleM}&year=${saleY}')`. Expects an array response and maps it.
  - Customer Search (Area, Name, Phone, Address): Triggers `fetch('/api/customer-suggestions/?term=${encodeURIComponent(term)}&field=${field.type}&salesperson_id=${spId}&current_area=${encodeURIComponent(currentArea)}&current_name=${encodeURIComponent(currentName)}')`.
- **`manage_purchase_invoices.html` and `edit_purchase_invoice.html`:**
  - Product Search: Triggers `fetch('/api/product-suggestions/?term=${encodeURIComponent(term)}&month=${invM}&year=${invY}')`. Yields available product data.

### 5. Download Backup AJAX (`general_settings.html`)
- A direct async call inside a script block to initiate a database backup securely without a full page refresh:
  ```javascript
  const response = await fetch("{% url 'download_backup' %}");
  ```
  Parses `response.blob()` similarly to print PDF logic and forces an `a.download = "DB_Backup.sqlite3"` action directly.
