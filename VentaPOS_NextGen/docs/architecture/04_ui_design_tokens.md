# Chapter 6: UI Design Tokens & Declarative Elements

# VentaPOS NextGen Rebuild - Visual Design Specification & Tokens

This document serves as the absolute, single source of truth for the visual UI/UX design system and declarative layout architectures of the VentaPOS NextGen Rebuild. In alignment with VentaPOS multi-agent guidelines, all interface structures are defined using the **A2UI Declarative JSON** specification to prevent fragile HTML/CSS generated code.

---

## 1. Typography & Language System

The typography is optimized for quick legibility in fast-paced retail and warehouse environments, prioritizing clarity, hierarchy, and strict Right-to-Left (RTL) rules.

*   **Primary Font Family:** `'Cairo', sans-serif` (The primary font for all labels, descriptions, and user actions).
*   **Monospace Font Family:** `'Courier New', monospace` (Used exclusively for barcode values and system logs).
*   **Numerical Display Rule:** All quantities, prices, calculations, and transaction figures must be displayed as standard Western Arabic numerals (`1, 2, 3...` not Eastern Arabic `Ù¡, Ù¢, Ù£...`) to ensure quick processing. Unless explicitly required, monetary totals must be formatted as **whole integers (Ø£Ø±Ù‚Ø§Ù… ØµØ­ÙŠØ­Ø©)**, rounded to the nearest EGP (Egyptian Pound), which matches Egyptian retail practices.
*   **RTL Enforcement:** All page wrappers, inputs, text nodes, and container layout engines must default to `direction: rtl` and `text-align: right`.

### 1.1 Egyptian Market Glossary (Ù„ØºØ© Ø³ÙˆÙ‚ Ù…Ù‡Ù†ÙŠØ© ÙˆÙ…Ø¨Ø³Ø·Ø©)
To maintain a professional yet accessible Egyptian business tone, the UI must strictly and consistently use the following terms across all screens, labels, prompts, and documentation:

| Standard / Technical Term | Egyptian Market Term (Ø§Ù„Ù„ÙØ¸ Ø¨Ø§Ù„Ø¹Ø§Ù…ÙŠØ© Ø§Ù„Ù…Ù‡Ù†ÙŠØ©) | Purpose / Context |
| :--- | :--- | :--- |
| Customer / Client | **Ø§Ù„Ø¹Ù…ÙŠÙ„** | Customer profile dropdowns, balance sheets, and invoicing. |
| Product / Inventory Item | **Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø©** | Product list, stock adjustment panels, and item search fields. |
| Cash Drawer / Safe | **Ø§Ù„Ø®Ø²Ù†Ø©** | Cash balances, safe ledger cards, and cashier safe setups. |
| Receipt / Sales Invoice | **Ø§Ù„ÙØ§ØªÙˆØ±Ø©** | Transaction receipts, sales lists, and printer layouts. |
| Ledger / DB / Account Book | **Ø§Ù„Ø¯ÙØªØ±** | General system accounts, client ledgers, and onboarding steps. |
| Cash | **Ø§Ù„Ù†Ù‚Ø¯ÙŠØ©** | Cash transactions, down payments, and currency fields. |
| Salesperson / Cashier | **Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨** | Employee assignments, commission splits, and cashier logins. |
| Down Payment | **Ù…Ù‚Ø¯Ù… Ø§Ù„ÙØ§ØªÙˆØ±Ø©** | Credit invoice initial deposits. |
| Monthly Installment | **القسط الشهري** | Payment schedule lines and credit sales calculator. |
| Connected Terminal | **الأجهزة** | Connected viewer terminals and mobile client counts. |
| Revenue / Total Sales | **المبيعات** | Instead of standard "Revenues" or "الإيرادات", used in P&L. |
| Profit / Net Income | **المكسب** | Instead of "Profits" or "أرباح", used in P&L summaries. |
| Sales Commission | **مندبة** | Commission given to a salesperson for selling an item. |
| Collection Commission | **عمولة تحصيل** | Commission for collecting installment payments. |

---

## 2. Visual Theme & Colors

The palette uses high-contrast, professional colors designed to minimize eye strain during long cashier shifts while providing immediate color-coded cues for transactions.

### 2.1 Color Palette Table
| Color Token | Hex Code | Semantic Role | Egyptian Market Context |
| :--- | :--- | :--- | :--- |
| `brand-primary` | `#0f52ba` | Primary Accent | **Ø£Ø²Ø±Ù‚ Ø§Ù„Ø¯ÙØªØ±** (Trust, brand consistency) |
| `brand-secondary`| `#20c997` | Secondary Accent | **Ø£Ø®Ø¶Ø± Ø§Ù„Ù…Ø¨ÙŠØ¹Ø§Øª** (Active actions, additions) |
| `state-success` | `#28a745` | Success / Positive | **Ø§Ù„Ù†Ù‚Ø¯ÙŠØ© Ø§Ù„Ù…ØªØ§Ø­Ø©** (Safe increases, verified states) |
| `state-warning` | `#ffc107` | Warning / Alert | **Ù…Ø±Ø§Ø¬Ø¹Ø© ÙˆØªÙ†Ø¨ÙŠÙ‡** (Warning states, pending actions) |
| `state-danger`  | `#dc3545` | Danger / Critical | **Ø§Ù„Ø¹Ø¬Ø² ÙˆØ§Ù„Ø¥Ù†Ø°Ø§Ø±** (Canceled keys, cash deficits, errors) |
| `bg-primary`    | `#f8f9fa` | Outer Background | **Ø±Ù…Ø§Ø¯ÙŠ Ø§Ù„Ø£Ø±Ø¶ÙŠØ©** (Main page background wrapper) |
| `bg-card`       | `#ffffff` | Content Container | **Ø£Ø¨ÙŠØ¶ Ø§Ù„Ø®Ø²ÙŠÙ†Ø©** (Card containers, tables, lists) |
| `text-primary`  | `#212529` | Primary Text | **Ø£Ø³ÙˆØ¯ Ø§Ù„ÙƒØªØ§Ø¨Ø©** (Labels, totals, titles) |
| `text-muted`    | `#6c757d` | Secondary Text | **Ø±Ù…Ø§Ø¯ÙŠ Ø¨Ø§Ù‡Øª** (Subtitles, placeholders) |

### 2.2 Color-Shifting Pending Queue Rule
The pending receipt synchronization queue status badge must change colors dynamically based on the number of un-synced local receipts:
*   **0 Pending Receipts (Ù…Ø³ØªÙ‚Ø±):** Background `#28a745` (Success Green). Text: "Ø§Ù„Ø¯ÙØªØ± Ù…ÙØ²Ø§Ù…Ù† Ø¨Ø§Ù„ÙƒØ§Ù…Ù„" (Fully Synced).
*   **1 to 5 Pending Receipts (ØªÙ†Ø¨ÙŠÙ‡):** Background `#ffc107` (Warning Yellow). Text: "Ù…Ø·Ù„ÙˆØ¨ Ù…Ø²Ø§Ù…Ù†Ø© (X ÙÙˆØ§ØªÙŠØ± Ù…Ø¹Ù„Ù‚Ø©)" (Sync required for X invoices).
*   **Over 5 Pending Receipts (Ø­Ø±Ø¬):** Background `#dc3545` (Critical Red). Text: "Ø¹Ø§Ø¬Ù„: ØªØ±Ø§ÙƒÙ… ÙÙˆØ§ØªÙŠØ± Ù…Ø¹Ù„Ù‚Ø© (X ÙØ§ØªÙˆØ±Ø©)" (Alert: queue backlogged by X invoices).

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
A centered layout designed for secure credential inputs by the salesperson (Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨) to open the safe.

```json
{
  "$schema": "https://a2ui.google.dev/v0.9/schema.json",
  "screenId": "login_page",
  "title": "Ø¨ÙˆØ§Ø¨Ø© Ø¯Ø®ÙˆÙ„ Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨ - VentaPOS",
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
                  "alt": "Ø´Ø¹Ø§Ø± ÙÙŠÙ†ØªØ§ POS"
                }
              }
            ]
          },
          {
            "id": "login_title",
            "type": "Text",
            "properties": {
              "text": "Ø¨ÙˆØ§Ø¨Ø© Ø¯Ø®ÙˆÙ„ Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨",
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
              "text": "Ø¨Ø±Ø¬Ø§Ø¡ Ø¥Ø¯Ø®Ø§Ù„ Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù‡ÙˆÙŠØ© Ù„ÙØªØ­ Ø§Ù„Ø®Ø²Ù†Ø© ÙˆØ§Ù„ÙˆØµÙˆÙ„ Ù„Ù„Ø¯ÙØªØ±",
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
              "label": "Ø§Ø³Ù… Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù… Ù„Ù„Ù…Ù†Ø¯ÙˆØ¨",
              "placeholder": "Ø£Ø¯Ø®Ù„ Ø§Ø³Ù… Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù… Ø§Ù„Ø®Ø§Øµ Ø¨Ùƒ",
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
              "label": "ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ± Ø§Ù„Ø³Ø±ÙŠØ©",
              "placeholder": "Ø£Ø¯Ø®Ù„ ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ± Ø§Ù„Ø®Ø§ØµØ© Ø¨Ùƒ",
              "type": "password",
              "required": true,
              "marginBottom": "24px"
            }
          },
          {
            "id": "submit_login_btn",
            "type": "Button",
            "properties": {
              "text": "ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø¯Ø®ÙˆÙ„ ÙˆÙØªØ­ Ø§Ù„Ø®Ø²Ù†Ø©",
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
  "title": "Ø¥Ø¹Ø¯Ø§Ø¯ ÙˆØªÙ‡ÙŠØ¦Ø© Ø§Ù„Ù†Ø¸Ø§Ù… Ù„Ø£ÙˆÙ„ Ù…Ø±Ø©",
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
              "text": "Ø¥Ø¹Ø¯Ø§Ø¯ ÙˆØªØ´ØºÙŠÙ„ Ø§Ù„Ø¯ÙØªØ± Ù„Ø£ÙˆÙ„ Ù…Ø±Ø©",
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
                {"number": 1, "label": "Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ø­Ù„"},
                {"number": 2, "label": "Ø­Ø³Ø§Ø¨ Ø§Ù„Ù…Ø¯ÙŠØ±"},
                {"number": 3, "label": "Ø§Ù„ÙØ±Ø¹ ÙˆØ§Ù„Ø®Ø²Ù†Ø©"}
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
                  "label": "Ø§Ø³Ù… Ø§Ù„Ù…Ø­Ù„ Ø£Ùˆ Ø§Ù„Ø´Ø±ÙƒØ© Ø§Ù„ØªØ¬Ø§Ø±ÙŠØ©",
                  "placeholder": "Ù…Ø«Ø§Ù„: Ù…Ø­Ù„Ø§Øª Ø§Ù„Ù†ÙˆØ± Ø§Ù„ØªØ¬Ø§Ø±ÙŠØ©",
                  "required": true,
                  "marginBottom": "16px"
                }
              },
              {
                "id": "business_type",
                "type": "Dropdown",
                "properties": {
                  "label": "Ù†ÙˆØ¹ Ø§Ù„Ù†Ø´Ø§Ø· Ø§Ù„ØªØ¬Ø§Ø±ÙŠ",
                  "placeholder": "Ø§Ø®ØªØ± Ù†ÙˆØ¹ Ø§Ù„Ù†Ø´Ø§Ø·",
                  "options": [
                    {"value": "retail", "label": "ØªØ¬Ø§Ø±Ø© ØªØ¬Ø²Ø¦Ø©"},
                    {"value": "wholesale", "label": "ØªØ¬Ø§Ø±Ø© Ø¬Ù…Ù„Ø©"},
                    {"value": "distribution", "label": "ØªÙˆØ²ÙŠØ¹ ÙˆÙ…Ù†Ø¯ÙˆØ¨ÙŠÙ†"}
                  ],
                  "required": true,
                  "marginBottom": "16px"
                }
              },
              {
                "id": "company_phone",
                "type": "TextInput",
                "properties": {
                  "label": "Ø±Ù‚Ù… ØªÙ„ÙŠÙÙˆÙ† Ø§Ù„Ù…Ø­Ù„",
                  "placeholder": "Ù…Ø«Ø§Ù„: 01012345678",
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
                  "label": "Ø§Ø³Ù… Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù… Ù„Ù„Ù…Ø¯ÙŠØ± Ø§Ù„Ù…Ø³Ø¤ÙˆÙ„",
                  "placeholder": "Ø£Ø¯Ø®Ù„ Ø§Ø³Ù… Ù…Ø³ØªØ®Ø¯Ù… Ø§Ù„Ø­Ø³Ø§Ø¨ Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ",
                  "required": true,
                  "marginBottom": "16px"
                }
              },
              {
                "id": "admin_password",
                "type": "TextInput",
                "properties": {
                  "label": "ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ± Ù„Ù„Ù…Ø¯ÙŠØ±",
                  "placeholder": "Ø£Ø¯Ø®Ù„ ÙƒÙ„Ù…Ø© Ù…Ø±ÙˆØ± Ù‚ÙˆÙŠØ©",
                  "type": "password",
                  "required": true,
                  "marginBottom": "16px"
                }
              },
              {
                "id": "admin_password_confirm",
                "type": "TextInput",
                "properties": {
                  "label": "ØªØ£ÙƒÙŠØ¯ ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ± Ù„Ù„Ù…Ø¯ÙŠØ±",
                  "placeholder": "Ø£Ø¹Ø¯ ÙƒØªØ§Ø¨Ø© ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±",
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
                  "label": "Ø§Ø³Ù… Ø§Ù„ÙØ±Ø¹ Ø§Ù„Ø£ÙˆÙ„ Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ",
                  "placeholder": "Ù…Ø«Ø§Ù„: Ø§Ù„ÙØ±Ø¹ Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ - Ø§Ù„Ù‚Ø§Ù‡Ø±Ø©",
                  "value": "Ø§Ù„ÙØ±Ø¹ Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ",
                  "required": true,
                  "marginBottom": "16px"
                }
              },
              {
                "id": "initial_cash",
                "type": "TextInput",
                "properties": {
                  "label": "Ø§Ù„Ù‚ÙŠÙ…Ø© Ø§Ù„Ø§ÙØªØªØ§Ø­ÙŠØ© Ù„Ù†Ù‚Ø¯ÙŠØ© Ø§Ù„Ø®Ø²Ù†Ø© (Ø¬.Ù…)",
                  "placeholder": "Ø£Ø¯Ø®Ù„ Ù‚ÙŠÙ…Ø© Ø§Ù„Ù†Ù‚Ø¯ÙŠØ© Ø§Ù„Ù…ØªØ§Ø­Ø© ÙÙŠ Ø§Ù„Ø®Ø²Ù†Ø© Ø­Ø§Ù„ÙŠØ§Ù‹",
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
                  "text": "Ø§Ù„Ø³Ø§Ø¨Ù‚",
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
                  "text": "{{steps_indicator.currentStep == 3 ? 'Ø­ÙØ¸ ÙˆØ¥Ù†Ø´Ø§Ø¡ Ø§Ù„Ø¯ÙØªØ±' : 'Ø§Ù„ØªØ§Ù„ÙŠ'}}",
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
Provides critical overview stats. Includes cards for the Safe (Ø§Ù„Ø®Ø²Ù†Ø©), total Sales (Ø§Ù„Ù…Ø¨ÙŠØ¹Ø§Øª), active Terminals (Ø§Ù„Ø£Ø¬Ù‡Ø²Ø©), and the color-shifting pending queue sync indicator.

```json
{
  "$schema": "https://a2ui.google.dev/v0.9/schema.json",
  "screenId": "dashboard",
  "title": "Ù„ÙˆØ­Ø© Ø§Ù„Ù…ØªØ§Ø¨Ø¹Ø© Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ© - VentaPOS",
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
                  "text": "Ù„ÙˆØ­Ø© Ù…ØªØ§Ø¨Ø¹Ø© Ø§Ù„ÙØ±Ø¹",
                  "fontSize": "24px",
                  "fontWeight": "bold",
                  "color": "#212529"
                }
              },
              {
                "id": "branch_sub",
                "type": "Text",
                "properties": {
                  "text": "Ù…Ø±Ø­Ø¨Ø§Ù‹ Ø¨ÙƒØŒ ÙŠØ¹Ø±Ø¶ Ø§Ù„Ø¯ÙØªØ± ØªÙ‚Ø±ÙŠØ± Ø§Ù„Ø£Ø¯Ø§Ø¡ Ø§Ù„Ø­Ø§Ù„ÙŠ Ù„Ù„ÙØ±Ø¹ Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ",
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
              "text": "{{sync_queue.pending_count == 0 ? 'Ø§Ù„Ø¯ÙØªØ± Ù…ÙØ²Ø§Ù…Ù† Ø¨Ø§Ù„ÙƒØ§Ù…Ù„' : (sync_queue.pending_count <= 5 ? 'Ù…Ø·Ù„ÙˆØ¨ Ù…Ø²Ø§Ù…Ù†Ø© (' + sync_queue.pending_count + ' ÙÙˆØ§ØªÙŠØ± Ù…Ø¹Ù„Ù‚Ø©)' : 'Ø¹Ø§Ø¬Ù„: ØªØ±Ø§ÙƒÙ… ÙÙˆØ§ØªÙŠØ± Ù…Ø¹Ù„Ù‚Ø© (' + sync_queue.pending_count + ' ÙØ§ØªÙˆØ±Ø©)')}}",
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
                  "text": "Ù†Ù‚Ø¯ÙŠØ© Ø§Ù„Ø®Ø²Ù†Ø©",
                  "fontSize": "14px",
                  "color": "#6c757d",
                  "marginBottom": "8px"
                }
              },
              {
                "id": "safe_value",
                "type": "Text",
                "properties": {
                  "text": "Ù¤Ù¥,Ù Ù Ù  Ø¬.Ù…",
                  "fontSize": "28px",
                  "fontWeight": "black",
                  "color": "#212529"
                }
              },
              {
                "id": "safe_description",
                "type": "Text",
                "properties": {
                  "text": "Ø§Ù„Ù†Ù‚Ø¯ÙŠØ© Ø§Ù„Ø­Ø§Ù„ÙŠØ© Ø§Ù„Ù…ØªÙˆÙØ±Ø© ÙÙŠ Ø¯Ø±Ø¬ Ø§Ù„Ø®Ø²ÙŠÙ†Ø©",
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
                  "text": "Ø§Ù„Ù…Ø¨ÙŠØ¹Ø§Øª Ø§Ù„Ø¥Ø¬Ù…Ø§Ù„ÙŠØ©",
                  "fontSize": "14px",
                  "color": "#6c757d",
                  "marginBottom": "8px"
                }
              },
              {
                "id": "sales_value",
                "type": "Text",
                "properties": {
                  "text": "Ù¡Ù¢Ù¨,Ù¥Ù Ù  Ø¬.Ù…",
                  "fontSize": "28px",
                  "fontWeight": "black",
                  "color": "#212529"
                }
              },
              {
                "id": "sales_description",
                "type": "Text",
                "properties": {
                  "text": "Ø¥Ø¬Ù…Ø§Ù„ÙŠ Ù…Ø¨ÙŠØ¹Ø§Øª Ø§Ù„ÙÙˆØ§ØªÙŠØ± Ø§Ù„Ù†Ù‚Ø¯ÙŠØ© ÙˆØ§Ù„Ø¢Ø¬Ù„Ø© Ù‡Ø°Ø§ Ø§Ù„Ø´Ù‡Ø±",
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
                  "text": "Ø§Ù„Ø£Ø¬Ù‡Ø²Ø© Ø§Ù„Ù†Ø´Ø·Ø©",
                  "fontSize": "14px",
                  "color": "#6c757d",
                  "marginBottom": "8px"
                }
              },
              {
                "id": "devices_value",
                "type": "Text",
                "properties": {
                  "text": "Ù¤ Ø£Ø¬Ù‡Ø²Ø©",
                  "fontSize": "28px",
                  "fontWeight": "black",
                  "color": "#212529"
                }
              },
              {
                "id": "devices_description",
                "type": "Text",
                "properties": {
                  "text": "Ø£Ø¬Ù‡Ø²Ø© Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨ÙŠÙ† ÙˆØ§Ù„ÙƒØ§Ø´ÙŠØ± Ø§Ù„Ù†Ø´Ø·Ø© ÙÙŠ Ø§Ù„Ø´Ø¨ÙƒØ©",
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
The core checkout workspace. It integrates customer (Ø§Ù„Ø¹Ù…ÙŠÙ„) selection, adding items/goods (Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø©), entering down payments (Ù…Ù‚Ø¯Ù… Ø§Ù„ÙØ§ØªÙˆØ±Ø©), and rendering the non-editable monthly installments due on the 25th of each month according to system rules.

```json
{
  "$schema": "https://a2ui.google.dev/v0.9/schema.json",
  "screenId": "checkout_pos",
  "title": "Ù†Ø§ÙØ°Ø© ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ù…Ø¨ÙŠØ¹Ø§Øª ÙˆØ§Ù„ÙØ§ØªÙˆØ±Ø©",
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
                  "title": "Ø¨Ø¶Ø§Ø¦Ø¹ Ø§Ù„ÙØ§ØªÙˆØ±Ø© Ø§Ù„Ø­Ø§Ù„ÙŠØ©",
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
                          "placeholder": "Ø§Ø¨Ø­Ø« Ø¨Ø§Ø³Ù… Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© Ø£Ùˆ Ø§Ù…Ø³Ø­ Ø§Ù„Ø¨Ø§Ø±ÙƒÙˆØ¯...",
                          "autoFocus": true,
                          "flex": 1
                        }
                      },
                      {
                        "id": "add_product_btn",
                        "type": "Button",
                        "properties": {
                          "text": "Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø©",
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
                        {"id": "index", "label": "Ù…", "width": "5%"},
                        {"id": "product_name", "label": "Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© (Ø§Ø³Ù… Ø§Ù„ØµÙ†Ù)", "width": "45%"},
                        {"id": "quantity", "label": "Ø§Ù„ÙƒÙ…ÙŠØ©", "width": "15%"},
                        {"id": "unit_price", "label": "Ø³Ø¹Ø± Ø§Ù„ÙˆØ­Ø¯Ø©", "width": "15%"},
                        {"id": "total", "label": "Ø§Ù„Ø¥Ø¬Ù…Ø§Ù„ÙŠ", "width": "15%"},
                        {"id": "actions", "label": "Ø¥Ø¬Ø±Ø§Ø¡Ø§Øª", "width": "5%"}
                      ],
                      "rows": "{{receipt.items}}",
                      "emptyStateText": "Ù„Ù… ÙŠØªÙ… Ø¥Ø¶Ø§ÙØ© Ø¨Ø¶Ø§Ø¹Ø© Ù„Ù„ÙØ§ØªÙˆØ±Ø© Ø¨Ø¹Ø¯."
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
                  "title": "ØªÙØ§ØµÙŠÙ„ Ø§Ù„ÙØ§ØªÙˆØ±Ø© ÙˆØ§Ù„ØªØ­ØµÙŠÙ„",
                  "padding": "16px"
                },
                "children": [
                  {
                    "id": "customer_selector",
                    "type": "Dropdown",
                    "properties": {
                      "label": "Ø§Ù„Ø¹Ù…ÙŠÙ„",
                      "placeholder": "Ø§Ø®ØªØ± Ø§Ù„Ø¹Ù…ÙŠÙ„ Ù…Ù† Ø§Ù„Ø¯ÙØªØ±...",
                      "options": "{{customers_list}}",
                      "required": true,
                      "marginBottom": "12px"
                    }
                  },
                  {
                    "id": "salesperson_selector",
                    "type": "Dropdown",
                    "properties": {
                      "label": "Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨ Ø§Ù„Ù…Ø³Ø¤ÙˆÙ„",
                      "placeholder": "Ø§Ø®ØªØ± Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨...",
                      "options": "{{salespersons_list}}",
                      "required": true,
                      "marginBottom": "12px"
                    }
                  },
                  {
                    "id": "billing_type_selector",
                    "type": "Dropdown",
                    "properties": {
                      "label": "Ù†ÙˆØ¹ Ø§Ù„ÙØ§ØªÙˆØ±Ø©",
                      "options": [
                        {"value": "cash", "label": "Ø¨ÙŠØ¹ Ù†Ù‚Ø¯ÙŠ ÙÙˆØ±Ø§Ù‹"},
                        {"value": "installments", "label": "Ø¨ÙŠØ¹ Ø¨Ø§Ù„ØªÙ‚Ø³ÙŠØ· (Ø¯ÙØªØ± Ø§Ù„Ø¢Ø¬Ù„)"}
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
                            "properties": {"text": "Ø¥Ø¬Ù…Ø§Ù„ÙŠ Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø©:", "fontWeight": "bold"}
                          },
                          {
                            "id": "total_val",
                            "type": "Text",
                            "properties": {"text": "{{receipt.total_amount}} Ø¬.Ù…", "fontWeight": "bold", "color": "#212529"}
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
                          "label": "Ù…Ù‚Ø¯Ù… Ø§Ù„ÙØ§ØªÙˆØ±Ø© (Ø§Ù„Ù†Ù‚Ø¯ÙŠØ© Ø§Ù„Ù…Ø³ØªÙ„Ù…Ø©)",
                          "placeholder": "Ù…Ø«Ø§Ù„: 1000",
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
                          "label": "Ø¹Ø¯Ø¯ Ø§Ù„Ø£Ù‚Ø³Ø§Ø· Ø§Ù„Ø´Ù‡Ø±ÙŠØ©",
                          "placeholder": "Ù…Ø«Ø§Ù„: 6",
                          "type": "number",
                          "value": "{{receipt.installments_count}}",
                          "marginBottom": "12px"
                        }
                      },
                      {
                        "id": "installment_rule_alert",
                        "type": "Text",
                        "properties": {
                          "text": "ØªÙ†Ø¨ÙŠÙ‡ Ø§Ù„Ø¯ÙØªØ±: ØªÙØ³ØªØ­Ù‚ Ø§Ù„Ø£Ù‚Ø³Ø§Ø· ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹ ÙÙŠ ÙŠÙˆÙ… 25 Ù…Ù† ÙƒÙ„ Ø´Ù‡Ø± Ù…ÙŠÙ„Ø§Ø¯ÙŠ Ø§Ø¨ØªØ¯Ø§Ø¡Ù‹ Ù…Ù† Ø§Ù„Ø´Ù‡Ø± Ø§Ù„Ù‚Ø§Ø¯Ù… ÙˆÙ„Ø§ ÙŠÙ…ÙƒÙ† ØªØ¹Ø¯ÙŠÙ„ ØªÙˆØ§Ø±ÙŠØ® Ø§Ù„Ø§Ø³ØªØ­Ù‚Ø§Ù‚.",
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
                            "properties": {"text": "Ù‚ÙŠÙ…Ø© Ø§Ù„Ù‚Ø³Ø· Ø§Ù„Ø´Ù‡Ø±ÙŠ:"}
                          },
                          {
                            "id": "monthly_amt_val",
                            "type": "Text",
                            "properties": {
                              "text": "{{(receipt.total_amount - receipt.down_payment) / receipt.installments_count}} Ø¬.Ù…",
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
                          "text": "Ø¬Ø¯ÙˆÙ„ Ø§Ù„Ø£Ù‚Ø³Ø§Ø· Ø§Ù„Ù…Ø³ØªØ­Ù‚Ø© (ØºÙŠØ± Ù‚Ø§Ø¨Ù„ Ù„Ù„ØªØ¹Ø¯ÙŠÙ„):",
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
                            {"id": "due_date", "label": "ØªØ§Ø±ÙŠØ® Ø§Ù„Ø§Ø³ØªØ­Ù‚Ø§Ù‚ (ÙŠÙˆÙ… 25)", "width": "60%"},
                            {"id": "amount", "label": "Ù‚ÙŠÙ…Ø© Ø§Ù„Ù‚Ø³Ø·", "width": "40%"}
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
                      "text": "Ø­ÙØ¸ Ø§Ù„ÙØ§ØªÙˆØ±Ø© ÙˆØªØ±Ø­ÙŠÙ„Ù‡Ø§ Ù„Ù„Ø¯ÙØªØ±",
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
  "title": "Ø´Ø§Ø´Ø© ØªÙØ¹ÙŠÙ„ Ø±Ø®ØµØ© Ø§Ù„Ø¯ÙØªØ± ÙˆØ§Ù„Ø³ÙŠØ³ØªÙ…",
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
              "text": "ØªÙ†Ø´ÙŠØ· Ø±Ø®ØµØ© VentaPOS",
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
              "text": "Ø£Ø¯Ø®Ù„ ÙƒÙˆØ¯ Ø§Ù„ØªÙØ¹ÙŠÙ„ Ù„ØªÙˆØ³ÙŠØ¹ ØµÙ„Ø§Ø­ÙŠØ§Øª Ø§Ù„Ø¯ÙØªØ± Ø£Ùˆ Ø´Ø­Ù† Ø±ØµÙŠØ¯ Ø§Ù„ÙÙˆØ§ØªÙŠØ±.",
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
                    "properties": {"text": "Ù…Ø¹Ø±Ù‘Ù Ø§Ù„Ø¬Ù‡Ø§Ø² (Machine ID):", "fontSize": "13px", "fontWeight": "bold"}
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
                    "properties": {"text": "Ù†ÙˆØ¹ Ø§Ù„Ø¨Ø§Ù‚Ø© Ø§Ù„Ø­Ø§Ù„ÙŠØ©:", "fontSize": "13px"}
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
                    "properties": {"text": "ØªØ§Ø±ÙŠØ® Ø§Ù†ØªÙ‡Ø§Ø¡ Ø§Ù„ØµÙ„Ø§Ø­ÙŠØ©:", "fontSize": "13px"}
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
                    "properties": {"text": "Ø±ØµÙŠØ¯ Ø§Ù„ÙÙˆØ§ØªÙŠØ± Ø§Ù„Ù…ØªØ§Ø­ Ø¨Ø§Ù„Ø®Ø²Ù†Ø©:", "fontSize": "13px"}
                  },
                  {
                    "id": "lic_balance_val",
                    "type": "Text",
                    "properties": {"text": "{{system.invoices_balance}} ÙØ§ØªÙˆØ±Ø©", "fontSize": "13px", "fontWeight": "bold"}
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
              "label": "ÙƒÙˆØ¯ ØªÙØ¹ÙŠÙ„ Ø§Ù„Ø±Ø®ØµØ© Ø§Ù„Ø¬Ø¯ÙŠØ¯ (Activation Key)",
              "placeholder": "XXXX-XXXX-XXXX-XXXX",
              "required": true,
              "textTransform": "uppercase",
              "validationPattern": "^[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$",
              "validationMessage": "Ø¨Ø±Ø¬Ø§Ø¡ ÙƒØªØ§Ø¨Ø© Ø§Ù„ÙƒÙˆØ¯ Ø¨Ø´ÙƒÙ„ ØµØ­ÙŠØ­. Ù„Ø§ ÙŠØ­ØªÙˆÙŠ Ø§Ù„ÙƒÙˆØ¯ Ø¹Ù„Ù‰ Ø£Ø±Ù‚Ø§Ù… 0 Ø£Ùˆ 1 Ø£Ùˆ Ø­Ø±ÙˆÙ I Ø£Ùˆ O Ù„Ù…Ù†Ø¹ Ø§Ù„Ø£Ø®Ø·Ø§Ø¡.",
              "marginBottom": "24px"
            }
          },
          {
            "id": "activate_btn",
            "type": "Button",
            "properties": {
              "text": "ØªÙØ¹ÙŠÙ„ ÙˆØªØ³Ø¬ÙŠÙ„ Ø¨Ø§Ù„Ø¯ÙØªØ±",
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


### 4.6 Profit and Loss Report (profit_and_loss_report)

```json
{
  "id": "profit_and_loss_report",
  "type": "page",
  "layout": "vcenter",
  "title": "الأرباح والخسائر",
  "elements": [
    {
      "type": "filter_bar",
      "inputs": [
        { "type": "select", "name": "salesperson", "icon": "IconUser", "label": "البائع" },
        { "type": "select", "name": "report_type", "icon": "IconFileAnalytics", "label": "نوع التقرير", "options": ["both", "average", "total"] },
        { "type": "select", "name": "sale_type", "icon": "IconFilter", "label": "نوع البيع", "options": ["all", "cash", "installment"] },
        { "type": "text", "name": "search", "icon": "IconSearch", "label": "بحث عام" }
      ],
      "style_rules": { "input_group": true }
    },
    {
      "type": "summary_cards",
      "layout": "row",
      "columns": 6,
      "cards": [
        { "label": "المبيعات", "color": "text-azure" },
        { "label": "ثمن الشراء", "color": "text-danger" },
        { "label": "الربح الكاش", "color": "text-warning" },
        { "label": "ربح القسط", "color": "text-warning" },
        { "label": "المصروفات", "link": "/reports/expenses" },
        { "label": "الربح الصافي", "color": "text-success", "bg": "bg-success-lt" }
      ]
    },
    {
      "type": "table",
      "id": "profit_loss_table",
      "sortable": true,
      "default_sort": "local_id",
      "columns": [
        "كود الصنف", "الاسم", "ثمن الشراء", "الكمية",
        "سعر الكاش / للمتوسط", "سعر القسط / للمتوسط",
        "الربح / للمتوسط", "إجمالي الكاش / للمبيعات",
        "إجمالي / للمبيعات"
      ]
    }
  ]
}
```

