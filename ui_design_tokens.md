# VentaPOS NextGen Rebuild - Visual Design Specification & Tokens

This document serves as the absolute, single source of truth for the visual UI/UX design system and declarative layout architectures of the VentaPOS NextGen Rebuild. In alignment with VentaPOS multi-agent guidelines, all interface structures are defined using the **A2UI Declarative JSON** specification to prevent fragile HTML/CSS generated code.

---

## 1. Typography & Language System

The typography is optimized for quick legibility in fast-paced retail and warehouse environments, prioritizing clarity, hierarchy, and strict Right-to-Left (RTL) rules.

*   **Primary Font Family:** `'Cairo', sans-serif` (The primary font for all labels, descriptions, and user actions).
*   **Monospace Font Family:** `'Courier New', monospace` (Used exclusively for barcode values and system logs).
*   **Numerical Display Rule:** All quantities, prices, calculations, and transaction figures must be displayed as standard Western Arabic numerals (`1, 2, 3...` not Eastern Arabic `١, ٢, ٣...`) to ensure quick processing. Unless explicitly required, monetary totals must be formatted as **whole integers (أرقام صحيحة)**, rounded to the nearest EGP (Egyptian Pound), which matches Egyptian retail practices.
*   **RTL Enforcement:** All page wrappers, inputs, text nodes, and container layout engines must default to `direction: rtl` and `text-align: right`.

### 1.1 Egyptian Market Glossary (لغة سوق مهنية ومبسطة)
To maintain a professional yet accessible Egyptian business tone, the UI must strictly and consistently use the following terms across all screens, labels, prompts, and documentation:

| Standard / Technical Term | Egyptian Market Term (اللفظ بالعامية المهنية) | Purpose / Context |
| :--- | :--- | :--- |
| Customer / Client | **العميل** | Customer profile dropdowns, balance sheets, and invoicing. |
| Product / Inventory Item | **البضاعة** | Product list, stock adjustment panels, and item search fields. |
| Cash Drawer / Safe | **الخزنة** | Cash balances, safe ledger cards, and cashier safe setups. |
| Receipt / Sales Invoice | **الفاتورة** | Transaction receipts, sales lists, and printer layouts. |
| Ledger / DB / Account Book | **الدفتر** | General system accounts, client ledgers, and onboarding steps. |
| Cash | **النقدية** | Cash transactions, down payments, and currency fields. |
| Salesperson / Cashier | **المندوب** | Employee assignments, commission splits, and cashier logins. |
| Down Payment | **مقدم الفاتورة** | Credit invoice initial deposits. |
| Monthly Installment | **القسط الشهري** | Payment schedule lines and credit sales calculator. |
| Connected Terminal | **الأجهزة** | Connected viewer terminals and mobile client counts. |

---

## 2. Visual Theme & Colors

The palette uses high-contrast, professional colors designed to minimize eye strain during long cashier shifts while providing immediate color-coded cues for transactions.

### 2.1 Color Palette Table
| Color Token | Hex Code | Semantic Role | Egyptian Market Context |
| :--- | :--- | :--- | :--- |
| `brand-primary` | `#0f52ba` | Primary Accent | **أزرق الدفتر** (Trust, brand consistency) |
| `brand-secondary`| `#20c997` | Secondary Accent | **أخضر المبيعات** (Active actions, additions) |
| `state-success` | `#28a745` | Success / Positive | **النقدية المتاحة** (Safe increases, verified states) |
| `state-warning` | `#ffc107` | Warning / Alert | **مراجعة وتنبيه** (Warning states, pending actions) |
| `state-danger`  | `#dc3545` | Danger / Critical | **العجز والإنذار** (Canceled keys, cash deficits, errors) |
| `bg-primary`    | `#f8f9fa` | Outer Background | **رمادي الأرضية** (Main page background wrapper) |
| `bg-card`       | `#ffffff` | Content Container | **أبيض الخزينة** (Card containers, tables, lists) |
| `text-primary`  | `#212529` | Primary Text | **أسود الكتابة** (Labels, totals, titles) |
| `text-muted`    | `#6c757d` | Secondary Text | **رمادي باهت** (Subtitles, placeholders) |

### 2.2 Color-Shifting Pending Queue Rule
The pending receipt synchronization queue status badge must change colors dynamically based on the number of un-synced local receipts:
*   **0 Pending Receipts (مستقر):** Background `#28a745` (Success Green). Text: "الدفتر مُزامن بالكامل" (Fully Synced).
*   **1 to 5 Pending Receipts (تنبيه):** Background `#ffc107` (Warning Yellow). Text: "مطلوب مزامنة (X فواتير معلقة)" (Sync required for X invoices).
*   **Over 5 Pending Receipts (حرج):** Background `#dc3545` (Critical Red). Text: "عاجل: تراكم فواتير معلقة (X فاتورة)" (Alert: queue backlogged by X invoices).

---

## 3. Shadows, Borders & Layout Rules

*   **Elevation & Shadows:**
    *   `shadow-sm` (Cards, Inputs): `0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03)`
    *   `shadow-md` (Dropdowns, modals): `0 4px 6px -1px rgba(0,0,0,0.08), 0 2px 4px -1px rgba(0,0,0,0.04)`
    *   `shadow-lg` (Popups, alerts): `0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)`
*   **Borders & Dividers:** `1px solid #e9ecef`.
*   **Corners / Border Radius:**
    *   `radius-sm` (Badges, buttons): `4px`
    *   `radius-md` (Input fields, small items): `8px`
    *   `radius-lg` (Page card containers, wizards): `12px`
*   **Interactive Target Size:** Minimum tap/click target for any button or interactive element must be `48px * 48px` to support field operations on tablets and touchscreens.

---

## 4. A2UI Declarative JSON Specification

The following declarative JSON specifications define the precise layout, properties, metadata, and validation requirements for the core screens of the VentaPOS NextGen Rebuild.

### 4.1 Login Page (`login_page`)
A centered layout designed for secure credential inputs by the salesperson (المندوب) to open the safe.

```json
{
  "$schema": "https://a2ui.google.dev/v0.9/schema.json",
  "screenId": "login_page",
  "title": "بوابة دخول المندوب - VentaPOS",
  "direction": "rtl",
  "root": {
    "id": "root_viewport",
    "type": "Viewport",
    "properties": {
      "backgroundColor": "#f8f9fa",
      "alignment": "center"
    },
    "children": [
      {
        "id": "login_card",
        "type": "Card",
        "properties": {
          "width": "420px",
          "padding": "32px",
          "borderRadius": "12px",
          "elevation": "medium",
          "backgroundColor": "#ffffff",
          "border": "1px solid #e9ecef"
        },
        "children": [
          {
            "id": "logo_container",
            "type": "Container",
            "properties": {
              "alignment": "center",
              "marginBottom": "24px"
            },
            "children": [
              {
                "id": "app_logo",
                "type": "Image",
                "properties": {
                  "src": "/assets/venta_logo.png",
                  "height": "60px",
                  "alt": "شعار فينتا POS"
                }
              }
            ]
          },
          {
            "id": "login_title",
            "type": "Text",
            "properties": {
              "text": "بوابة دخول المندوب",
              "fontSize": "22px",
              "fontWeight": "bold",
              "color": "#212529",
              "alignment": "center",
              "marginBottom": "8px"
            }
          },
          {
            "id": "login_subtitle",
            "type": "Text",
            "properties": {
              "text": "برجاء إدخال بيانات الهوية لفتح الخزنة والوصول للدفتر",
              "fontSize": "14px",
              "color": "#6c757d",
              "alignment": "center",
              "marginBottom": "24px"
            }
          },
          {
            "id": "username_field",
            "type": "TextInput",
            "properties": {
              "id": "username",
              "label": "اسم المستخدم للمندوب",
              "placeholder": "أدخل اسم المستخدم الخاص بك",
              "type": "text",
              "required": true,
              "autoFocus": true,
              "marginBottom": "16px"
            }
          },
          {
            "id": "password_field",
            "type": "TextInput",
            "properties": {
              "id": "password",
              "label": "كلمة المرور السرية",
              "placeholder": "أدخل كلمة المرور الخاصة بك",
              "type": "password",
              "required": true,
              "marginBottom": "24px"
            }
          },
          {
            "id": "submit_login_btn",
            "type": "Button",
            "properties": {
              "text": "تسجيل الدخول وفتح الخزنة",
              "variant": "primary",
              "width": "100%",
              "height": "48px"
            },
            "actions": {
              "onClick": {
                "intent": "SUBMIT_LOGIN",
                "payload": {
                  "username": "{{username.value}}",
                  "password": "{{password.value}}"
                }
              }
            }
          }
        ]
      }
    ]
  }
}
```

### 4.2 Onboarding Wizard Steps (`onboarding_wizard`)
A step-by-step wizard to setup the company profile, master administrator account, and seed the initial main branch and safe balance.

```json
{
  "$schema": "https://a2ui.google.dev/v0.9/schema.json",
  "screenId": "onboarding_wizard",
  "title": "إعداد وتهيئة النظام لأول مرة",
  "direction": "rtl",
  "root": {
    "id": "wizard_viewport",
    "type": "Viewport",
    "properties": {
      "backgroundColor": "#f8f9fa",
      "alignment": "center",
      "padding": "24px"
    },
    "children": [
      {
        "id": "wizard_card",
        "type": "Card",
        "properties": {
          "width": "640px",
          "padding": "32px",
          "borderRadius": "12px",
          "elevation": "medium",
          "backgroundColor": "#ffffff"
        },
        "children": [
          {
            "id": "wizard_header",
            "type": "Text",
            "properties": {
              "text": "إعداد وتشغيل الدفتر لأول مرة",
              "fontSize": "24px",
              "fontWeight": "bold",
              "color": "#0f52ba",
              "alignment": "center",
              "marginBottom": "24px"
            }
          },
          {
            "id": "steps_indicator",
            "type": "StepsIndicator",
            "properties": {
              "currentStep": 1,
              "steps": [
                {"number": 1, "label": "بيانات المحل"},
                {"number": 2, "label": "حساب المدير"},
                {"number": 3, "label": "الفرع والخزنة"}
              ],
              "marginBottom": "32px"
            }
          },
          {
            "id": "step_1_container",
            "type": "Container",
            "properties": {
              "visible": "{{steps_indicator.currentStep == 1}}",
              "marginBottom": "24px"
            },
            "children": [
              {
                "id": "company_name",
                "type": "TextInput",
                "properties": {
                  "label": "اسم المحل أو الشركة التجارية",
                  "placeholder": "مثال: محلات النور التجارية",
                  "required": true,
                  "marginBottom": "16px"
                }
              },
              {
                "id": "business_type",
                "type": "Dropdown",
                "properties": {
                  "label": "نوع النشاط التجاري",
                  "placeholder": "اختر نوع النشاط",
                  "options": [
                    {"value": "retail", "label": "تجارة تجزئة"},
                    {"value": "wholesale", "label": "تجارة جملة"},
                    {"value": "distribution", "label": "توزيع ومندوبين"}
                  ],
                  "required": true,
                  "marginBottom": "16px"
                }
              },
              {
                "id": "company_phone",
                "type": "TextInput",
                "properties": {
                  "label": "رقم تليفون المحل",
                  "placeholder": "مثال: 01012345678",
                  "type": "tel",
                  "required": true
                }
              }
            ]
          },
          {
            "id": "step_2_container",
            "type": "Container",
            "properties": {
              "visible": "{{steps_indicator.currentStep == 2}}",
              "marginBottom": "24px"
            },
            "children": [
              {
                "id": "admin_username",
                "type": "TextInput",
                "properties": {
                  "label": "اسم المستخدم للمدير المسؤول",
                  "placeholder": "أدخل اسم مستخدم الحساب الرئيسي",
                  "required": true,
                  "marginBottom": "16px"
                }
              },
              {
                "id": "admin_password",
                "type": "TextInput",
                "properties": {
                  "label": "كلمة المرور للمدير",
                  "placeholder": "أدخل كلمة مرور قوية",
                  "type": "password",
                  "required": true,
                  "marginBottom": "16px"
                }
              },
              {
                "id": "admin_password_confirm",
                "type": "TextInput",
                "properties": {
                  "label": "تأكيد كلمة المرور للمدير",
                  "placeholder": "أعد كتابة كلمة المرور",
                  "type": "password",
                  "required": true
                }
              }
            ]
          },
          {
            "id": "step_3_container",
            "type": "Container",
            "properties": {
              "visible": "{{steps_indicator.currentStep == 3}}",
              "marginBottom": "24px"
            },
            "children": [
              {
                "id": "branch_name",
                "type": "TextInput",
                "properties": {
                  "label": "اسم الفرع الأول الرئيسي",
                  "placeholder": "مثال: الفرع الرئيسي - القاهرة",
                  "value": "الفرع الرئيسي",
                  "required": true,
                  "marginBottom": "16px"
                }
              },
              {
                "id": "initial_cash",
                "type": "TextInput",
                "properties": {
                  "label": "القيمة الافتتاحية لنقدية الخزنة (ج.م)",
                  "placeholder": "أدخل قيمة النقدية المتاحة في الخزنة حالياً",
                  "type": "number",
                  "value": "0",
                  "required": true
                }
              }
            ]
          },
          {
            "id": "wizard_controls",
            "type": "Row",
            "properties": {
              "mainAxisAlignment": "spaceBetween",
              "gap": "16px"
            },
            "children": [
              {
                "id": "prev_btn",
                "type": "Button",
                "properties": {
                  "text": "السابق",
                  "variant": "outline",
                  "disabled": "{{steps_indicator.currentStep == 1}}",
                  "width": "120px"
                },
                "actions": {
                  "onClick": {
                    "intent": "PREVIOUS_STEP"
                  }
                }
              },
              {
                "id": "next_btn",
                "type": "Button",
                "properties": {
                  "text": "{{steps_indicator.currentStep == 3 ? 'حفظ وإنشاء الدفتر' : 'التالي'}}",
                  "variant": "primary",
                  "width": "160px"
                },
                "actions": {
                  "onClick": {
                    "intent": "NEXT_STEP"
                  }
                }
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 4.3 Dashboard Screen (`dashboard`)
Provides critical overview stats. Includes cards for the Safe (الخزنة), total Sales (المبيعات), active Terminals (الأجهزة), and the color-shifting pending queue sync indicator.

```json
{
  "$schema": "https://a2ui.google.dev/v0.9/schema.json",
  "screenId": "dashboard",
  "title": "لوحة المتابعة الرئيسية - VentaPOS",
  "direction": "rtl",
  "root": {
    "id": "dashboard_viewport",
    "type": "Viewport",
    "properties": {
      "backgroundColor": "#f8f9fa",
      "padding": "24px"
    },
    "children": [
      {
        "id": "dashboard_header",
        "type": "Row",
        "properties": {
          "mainAxisAlignment": "spaceBetween",
          "crossAxisAlignment": "center",
          "marginBottom": "24px"
        },
        "children": [
          {
            "id": "header_title_col",
            "type": "Column",
            "children": [
              {
                "id": "main_title",
                "type": "Text",
                "properties": {
                  "text": "لوحة متابعة الفرع",
                  "fontSize": "24px",
                  "fontWeight": "bold",
                  "color": "#212529"
                }
              },
              {
                "id": "branch_sub",
                "type": "Text",
                "properties": {
                  "text": "مرحباً بك، يعرض الدفتر تقرير الأداء الحالي للفرع الرئيسي",
                  "fontSize": "14px",
                  "color": "#6c757d"
                }
              }
            ]
          },
          {
            "id": "sync_status_badge",
            "type": "Badge",
            "properties": {
              "value": "{{sync_queue.pending_count}}",
              "text": "{{sync_queue.pending_count == 0 ? 'الدفتر مُزامن بالكامل' : (sync_queue.pending_count <= 5 ? 'مطلوب مزامنة (' + sync_queue.pending_count + ' فواتير معلقة)' : 'عاجل: تراكم فواتير معلقة (' + sync_queue.pending_count + ' فاتورة)')}}",
              "variant": "{{sync_queue.pending_count == 0 ? 'success' : (sync_queue.pending_count <= 5 ? 'warning' : 'danger')}}",
              "color": "{{sync_queue.pending_count == 0 ? '#28a745' : (sync_queue.pending_count <= 5 ? '#ffc107' : '#dc3545')}}",
              "padding": "8px 16px",
              "borderRadius": "20px",
              "fontSize": "13px",
              "fontWeight": "bold"
            },
            "actions": {
              "onClick": {
                "intent": "TRIGGER_CLOUD_SYNC"
              }
            }
          }
        ]
      },
      {
        "id": "kpi_grid",
        "type": "Grid",
        "properties": {
          "columns": 3,
          "gap": "20px",
          "marginBottom": "24px"
        },
        "children": [
          {
            "id": "kpi_safe",
            "type": "Card",
            "properties": {
              "padding": "20px",
              "borderRadius": "8px",
              "borderRight": "4px solid #28a745",
              "backgroundColor": "#ffffff"
            },
            "children": [
              {
                "id": "safe_label",
                "type": "Text",
                "properties": {
                  "text": "نقدية الخزنة",
                  "fontSize": "14px",
                  "color": "#6c757d",
                  "marginBottom": "8px"
                }
              },
              {
                "id": "safe_value",
                "type": "Text",
                "properties": {
                  "text": "٤٥,٠٠٠ ج.م",
                  "fontSize": "28px",
                  "fontWeight": "black",
                  "color": "#212529"
                }
              },
              {
                "id": "safe_description",
                "type": "Text",
                "properties": {
                  "text": "النقدية الحالية المتوفرة في درج الخزينة",
                  "fontSize": "12px",
                  "color": "#495057",
                  "marginTop": "4px"
                }
              }
            ]
          },
          {
            "id": "kpi_sales",
            "type": "Card",
            "properties": {
              "padding": "20px",
              "borderRadius": "8px",
              "borderRight": "4px solid #0f52ba",
              "backgroundColor": "#ffffff"
            },
            "children": [
              {
                "id": "sales_label",
                "type": "Text",
                "properties": {
                  "text": "المبيعات الإجمالية",
                  "fontSize": "14px",
                  "color": "#6c757d",
                  "marginBottom": "8px"
                }
              },
              {
                "id": "sales_value",
                "type": "Text",
                "properties": {
                  "text": "١٢٨,٥٠٠ ج.م",
                  "fontSize": "28px",
                  "fontWeight": "black",
                  "color": "#212529"
                }
              },
              {
                "id": "sales_description",
                "type": "Text",
                "properties": {
                  "text": "إجمالي مبيعات الفواتير النقدية والآجلة هذا الشهر",
                  "fontSize": "12px",
                  "color": "#495057",
                  "marginTop": "4px"
                }
              }
            ]
          },
          {
            "id": "kpi_devices",
            "type": "Card",
            "properties": {
              "padding": "20px",
              "borderRadius": "8px",
              "borderRight": "4px solid #6c757d",
              "backgroundColor": "#ffffff"
            },
            "children": [
              {
                "id": "devices_label",
                "type": "Text",
                "properties": {
                  "text": "الأجهزة النشطة",
                  "fontSize": "14px",
                  "color": "#6c757d",
                  "marginBottom": "8px"
                }
              },
              {
                "id": "devices_value",
                "type": "Text",
                "properties": {
                  "text": "٤ أجهزة",
                  "fontSize": "28px",
                  "fontWeight": "black",
                  "color": "#212529"
                }
              },
              {
                "id": "devices_description",
                "type": "Text",
                "properties": {
                  "text": "أجهزة المندوبين والكاشير النشطة في الشبكة",
                  "fontSize": "12px",
                  "color": "#495057",
                  "marginTop": "4px"
                }
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 4.4 Checkout POS Screen (`checkout_pos`)
The core checkout workspace. It integrates customer (العميل) selection, adding items/goods (البضاعة), entering down payments (مقدم الفاتورة), and rendering the non-editable monthly installments due on the 25th of each month according to system rules.

```json
{
  "$schema": "https://a2ui.google.dev/v0.9/schema.json",
  "screenId": "checkout_pos",
  "title": "نافذة تسجيل المبيعات والفاتورة",
  "direction": "rtl",
  "root": {
    "id": "checkout_viewport",
    "type": "Viewport",
    "properties": {
      "backgroundColor": "#f4f6fa",
      "padding": "16px"
    },
    "children": [
      {
        "id": "pos_grid",
        "type": "Grid",
        "properties": {
          "columns": 12,
          "gap": "16px"
        },
        "children": [
          {
            "id": "pos_left_col",
            "type": "Container",
            "properties": {
              "gridSpan": 8
            },
            "children": [
              {
                "id": "items_card",
                "type": "Card",
                "properties": {
                  "title": "بضائع الفاتورة الحالية",
                  "padding": "16px",
                  "marginBottom": "16px"
                },
                "children": [
                  {
                    "id": "product_search_row",
                    "type": "Row",
                    "properties": {
                      "gap": "12px",
                      "marginBottom": "16px"
                    },
                    "children": [
                      {
                        "id": "product_search",
                        "type": "TextInput",
                        "properties": {
                          "placeholder": "ابحث باسم البضاعة أو امسح الباركود...",
                          "autoFocus": true,
                          "flex": 1
                        }
                      },
                      {
                        "id": "add_product_btn",
                        "type": "Button",
                        "properties": {
                          "text": "إضافة البضاعة",
                          "variant": "primary"
                        },
                        "actions": {
                          "onClick": {
                            "intent": "ADD_SELECTED_PRODUCT_TO_RECEIPT"
                          }
                        }
                      }
                    ]
                  },
                  {
                    "id": "receipt_items_table",
                    "type": "DataTable",
                    "properties": {
                      "columns": [
                        {"id": "index", "label": "م", "width": "5%"},
                        {"id": "product_name", "label": "البضاعة (اسم الصنف)", "width": "45%"},
                        {"id": "quantity", "label": "الكمية", "width": "15%"},
                        {"id": "unit_price", "label": "سعر الوحدة", "width": "15%"},
                        {"id": "total", "label": "الإجمالي", "width": "15%"},
                        {"id": "actions", "label": "إجراءات", "width": "5%"}
                      ],
                      "rows": "{{receipt.items}}",
                      "emptyStateText": "لم يتم إضافة بضاعة للفاتورة بعد."
                    }
                  }
                ]
              }
            ]
          },
          {
            "id": "pos_right_col",
            "type": "Container",
            "properties": {
              "gridSpan": 4
            },
            "children": [
              {
                "id": "checkout_settings_card",
                "type": "Card",
                "properties": {
                  "title": "تفاصيل الفاتورة والتحصيل",
                  "padding": "16px"
                },
                "children": [
                  {
                    "id": "customer_selector",
                    "type": "Dropdown",
                    "properties": {
                      "label": "العميل",
                      "placeholder": "اختر العميل من الدفتر...",
                      "options": "{{customers_list}}",
                      "required": true,
                      "marginBottom": "12px"
                    }
                  },
                  {
                    "id": "salesperson_selector",
                    "type": "Dropdown",
                    "properties": {
                      "label": "المندوب المسؤول",
                      "placeholder": "اختر المندوب...",
                      "options": "{{salespersons_list}}",
                      "required": true,
                      "marginBottom": "12px"
                    }
                  },
                  {
                    "id": "billing_type_selector",
                    "type": "Dropdown",
                    "properties": {
                      "label": "نوع الفاتورة",
                      "options": [
                        {"value": "cash", "label": "بيع نقدي فوراً"},
                        {"value": "installments", "label": "بيع بالتقسيط (دفتر الآجل)"}
                      ],
                      "value": "{{receipt.type}}",
                      "marginBottom": "16px"
                    }
                  },
                  {
                    "id": "summary_section",
                    "type": "Container",
                    "properties": {
                      "backgroundColor": "#f8f9fa",
                      "padding": "12px",
                      "borderRadius": "6px",
                      "marginBottom": "16px"
                    },
                    "children": [
                      {
                        "id": "total_display_row",
                        "type": "Row",
                        "properties": {
                          "mainAxisAlignment": "spaceBetween",
                          "marginBottom": "8px"
                        },
                        "children": [
                          {
                            "id": "total_label",
                            "type": "Text",
                            "properties": {"text": "إجمالي البضاعة:", "fontWeight": "bold"}
                          },
                          {
                            "id": "total_val",
                            "type": "Text",
                            "properties": {"text": "{{receipt.total_amount}} ج.م", "fontWeight": "bold", "color": "#212529"}
                          }
                        ]
                      }
                    ]
                  },
                  {
                    "id": "installment_panel",
                    "type": "Container",
                    "properties": {
                      "visible": "{{receipt.type == 'installments'}}",
                      "marginBottom": "16px"
                    },
                    "children": [
                      {
                        "id": "down_payment_input",
                        "type": "TextInput",
                        "properties": {
                          "id": "down_payment",
                          "label": "مقدم الفاتورة (النقدية المستلمة)",
                          "placeholder": "مثال: 1000",
                          "type": "number",
                          "value": "{{receipt.down_payment}}",
                          "marginBottom": "12px"
                        }
                      },
                      {
                        "id": "installments_count_input",
                        "type": "TextInput",
                        "properties": {
                          "id": "installments_count",
                          "label": "عدد الأقساط الشهرية",
                          "placeholder": "مثال: 6",
                          "type": "number",
                          "value": "{{receipt.installments_count}}",
                          "marginBottom": "12px"
                        }
                      },
                      {
                        "id": "installment_rule_alert",
                        "type": "Text",
                        "properties": {
                          "text": "تنبيه الدفتر: تُستحق الأقساط تلقائياً في يوم 25 من كل شهر ميلادي ابتداءً من الشهر القادم ولا يمكن تعديل تواريخ الاستحقاق.",
                          "fontSize": "11px",
                          "color": "#dc3545",
                          "fontWeight": "bold",
                          "marginBottom": "12px"
                        }
                      },
                      {
                        "id": "calculated_monthly_amount",
                        "type": "Row",
                        "properties": {
                          "mainAxisAlignment": "spaceBetween",
                          "marginBottom": "12px"
                        },
                        "children": [
                          {
                            "id": "monthly_amt_lbl",
                            "type": "Text",
                            "properties": {"text": "قيمة القسط الشهري:"}
                          },
                          {
                            "id": "monthly_amt_val",
                            "type": "Text",
                            "properties": {
                              "text": "{{(receipt.total_amount - receipt.down_payment) / receipt.installments_count}} ج.م",
                              "fontWeight": "bold",
                              "color": "#0f52ba"
                            }
                          }
                        ]
                      },
                      {
                        "id": "installments_schedule_label",
                        "type": "Text",
                        "properties": {
                          "text": "جدول الأقساط المستحقة (غير قابل للتعديل):",
                          "fontSize": "13px",
                          "fontWeight": "bold",
                          "color": "#495057",
                          "marginBottom": "8px"
                        }
                      },
                      {
                        "id": "installments_table",
                        "type": "DataTable",
                        "properties": {
                          "columns": [
                            {"id": "due_date", "label": "تاريخ الاستحقاق (يوم 25)", "width": "60%"},
                            {"id": "amount", "label": "قيمة القسط", "width": "40%"}
                          ],
                          "rows": "{{receipt.generated_installments}}",
                          "disabled": true,
                          "readOnly": true
                        }
                      }
                    ]
                  },
                  {
                    "id": "submit_receipt_btn",
                    "type": "Button",
                    "properties": {
                      "text": "حفظ الفاتورة وترحيلها للدفتر",
                      "variant": "success",
                      "width": "100%",
                      "height": "48px"
                    },
                    "actions": {
                      "onClick": {
                        "intent": "SUBMIT_RECEIPT_CHECKOUT"
                      }
                    }
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 4.5 License Activation Screen (`license_activation`)
Renders license activation key validation forms. Includes Machine ID and active metadata logs. The input key uses custom alphanumeric checks to exclude `0`, `1`, `I`, and `O` (to prevent typing errors).

```json
{
  "$schema": "https://a2ui.google.dev/v0.9/schema.json",
  "screenId": "license_activation",
  "title": "شاشة تفعيل رخصة الدفتر والسيستم",
  "direction": "rtl",
  "root": {
    "id": "activation_viewport",
    "type": "Viewport",
    "properties": {
      "backgroundColor": "#f8f9fa",
      "alignment": "center",
      "padding": "24px"
    },
    "children": [
      {
        "id": "activation_card",
        "type": "Card",
        "properties": {
          "width": "500px",
          "padding": "32px",
          "borderRadius": "12px",
          "elevation": "medium",
          "backgroundColor": "#ffffff"
        },
        "children": [
          {
            "id": "activation_title",
            "type": "Text",
            "properties": {
              "text": "تنشيط رخصة VentaPOS",
              "fontSize": "22px",
              "fontWeight": "bold",
              "color": "#0f52ba",
              "alignment": "center",
              "marginBottom": "8px"
            }
          },
          {
            "id": "activation_desc",
            "type": "Text",
            "properties": {
              "text": "أدخل كود التفعيل لتوسيع صلاحيات الدفتر أو شحن رصيد الفواتير.",
              "fontSize": "13px",
              "color": "#6c757d",
              "alignment": "center",
              "marginBottom": "24px"
            }
          },
          {
            "id": "system_info_box",
            "type": "Container",
            "properties": {
              "backgroundColor": "#f1f3f5",
              "padding": "16px",
              "borderRadius": "8px",
              "marginBottom": "24px",
              "border": "1px solid #e9ecef"
            },
            "children": [
              {
                "id": "machine_id_row",
                "type": "Row",
                "properties": {
                  "mainAxisAlignment": "spaceBetween",
                  "marginBottom": "12px"
                },
                "children": [
                  {
                    "id": "machine_id_lbl",
                    "type": "Text",
                    "properties": {"text": "معرّف الجهاز (Machine ID):", "fontSize": "13px", "fontWeight": "bold"}
                  },
                  {
                    "id": "machine_id_val",
                    "type": "Text",
                    "properties": {"text": "{{system.machine_id}}", "fontSize": "13px", "color": "#0f52ba", "fontStyle": "monospace"}
                  }
                ]
              },
              {
                "id": "lic_type_row",
                "type": "Row",
                "properties": {
                  "mainAxisAlignment": "spaceBetween",
                  "marginBottom": "8px"
                },
                "children": [
                  {
                    "id": "lic_type_lbl",
                    "type": "Text",
                    "properties": {"text": "نوع الباقة الحالية:", "fontSize": "13px"}
                  },
                  {
                    "id": "lic_type_val",
                    "type": "Text",
                    "properties": {"text": "{{system.license_package_name}}", "fontSize": "13px", "fontWeight": "bold"}
                  }
                ]
              },
              {
                "id": "lic_expiry_row",
                "type": "Row",
                "properties": {
                  "mainAxisAlignment": "spaceBetween",
                  "marginBottom": "8px"
                },
                "children": [
                  {
                    "id": "lic_expiry_lbl",
                    "type": "Text",
                    "properties": {"text": "تاريخ انتهاء الصلاحية:", "fontSize": "13px"}
                  },
                  {
                    "id": "lic_expiry_val",
                    "type": "Text",
                    "properties": {"text": "{{system.license_expiry_date}}", "fontSize": "13px", "fontWeight": "bold"}
                  }
                ]
              },
              {
                "id": "lic_balance_row",
                "type": "Row",
                "properties": {
                  "mainAxisAlignment": "spaceBetween"
                },
                "children": [
                  {
                    "id": "lic_balance_lbl",
                    "type": "Text",
                    "properties": {"text": "رصيد الفواتير المتاح بالخزنة:", "fontSize": "13px"}
                  },
                  {
                    "id": "lic_balance_val",
                    "type": "Text",
                    "properties": {"text": "{{system.invoices_balance}} فاتورة", "fontSize": "13px", "fontWeight": "bold"}
                  }
                ]
              }
            ]
          },
          {
            "id": "activation_key_input",
            "type": "TextInput",
            "properties": {
              "id": "activation_key",
              "label": "كود تفعيل الرخصة الجديد (Activation Key)",
              "placeholder": "XXXX-XXXX-XXXX-XXXX",
              "required": true,
              "textTransform": "uppercase",
              "validationPattern": "^[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$",
              "validationMessage": "برجاء كتابة الكود بشكل صحيح. لا يحتوي الكود على أرقام 0 أو 1 أو حروف I أو O لمنع الأخطاء.",
              "marginBottom": "24px"
            }
          },
          {
            "id": "activate_btn",
            "type": "Button",
            "properties": {
              "text": "تفعيل وتسجيل بالدفتر",
              "variant": "primary",
              "width": "100%",
              "height": "48px"
            },
            "actions": {
              "onClick": {
                "intent": "SUBMIT_ACTIVATION_KEY",
                "payload": {
                  "activation_key": "{{activation_key.value}}"
                }
              }
            }
          }
        ]
      }
    ]
  }
}
```
