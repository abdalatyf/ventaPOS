# Chapter 5: Integration Points & API Contracts

# VentaPOS NextGen REST API Contract

Ù‡Ø°Ø§ Ø§Ù„Ù…Ø³ØªÙ†Ø¯ ÙŠÙ…Ø«Ù„ Ø§Ù„Ø¹Ù‚Ø¯ Ø§Ù„Ø¨Ø±Ù…Ø¬ÙŠ Ø§Ù„Ù…ÙˆØ­Ø¯ (API Contract) Ù„Ù„Ù†Ø³Ø®Ø© Ø§Ù„Ù…Ø·ÙˆØ±Ø© **VentaPOS NextGen Rebuild** Ù…ØªÙˆØ§ÙÙ‚Ø§Ù‹ Ù…Ø¹ Ù…ÙˆØ§ØµÙØ§Øª **OpenAPI 3.1.0**.

---

## ðŸ”’ 1. Ø§Ù„Ø³ÙŠØ§Ø³Ø© Ø§Ù„Ø£Ù…Ù†ÙŠØ© ÙˆØ§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ù‡ÙˆÙŠØ© (Authentication & Security)

ØªØ¯Ø¹Ù… Ø§Ù„Ø¨ÙˆØ§Ø¨Ø© Ø®ÙŠØ§Ø±ÙŠÙ† Ù„Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„ØµÙ„Ø§Ø­ÙŠØ§Øª Ø­Ø³Ø¨ Ù†ÙˆØ¹ Ø§Ù„Ø¹Ù…ÙŠÙ„ Ø§Ù„Ù…ØªØµÙ„:
1. **Ø§Ù„ØªØ­Ù‚Ù‚ Ø§Ù„Ù…Ø³ØªÙ†Ø¯ Ø¥Ù„Ù‰ Ø±Ù…Ø² Ø§Ù„ÙˆØµÙˆÙ„ (JWT Bearer Token):** ÙˆÙŠØ³ØªØ®Ø¯Ù… ÙÙŠ ÙˆØ§Ø¬Ù‡Ø§Øª Ø§Ù„ÙˆÙŠØ¨ (React) ÙˆÙ…Ø³ØªØ®Ø¯Ù…ÙŠ Ø§Ù„Ø³Ø­Ø§Ø¨Ø© (Cloud Viewers) Ø¹Ø¨Ø± ØªØ±ÙˆÙŠØ³Ø© Ø§Ù„Ø·Ù„Ø¨:
   `Authorization: Bearer <JWT_TOKEN>`
2. **Ø§Ù„ØªØ­Ù‚Ù‚ Ø§Ù„Ù…Ø³ØªÙ†Ø¯ Ø¥Ù„Ù‰ Ù…Ø¹Ø±Ù Ø§Ù„Ø¬Ù‡Ø§Ø² ÙˆØ±Ù…Ø² Ø§Ù„Ø´Ø±ÙƒØ© (Machine & Company Headers):** ÙˆÙŠØ³ØªØ®Ø¯Ù… Ù„Ù…Ø²Ø§Ù…Ù†Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø¨ÙŠÙ† Ø§Ù„Ø£Ø¬Ù‡Ø²Ø© Ø§Ù„Ù…Ø­Ù„ÙŠØ© (Desktop/Mobile) ÙˆØ§Ù„Ø®Ø§Ø¯Ù… Ø§Ù„Ù…Ø±ÙƒØ²ÙŠ Ø¹Ø¨Ø± Ø§Ù„ØªØ±ÙˆÙŠØ³Ø§Øª Ø§Ù„ØªØ§Ù„ÙŠØ©:
   - `X-Machine-ID`: Ø§Ù„Ù…Ø¹Ø±Ù Ø§Ù„ÙØ±ÙŠØ¯ Ù„Ù„Ø¬Ù‡Ø§Ø² Ø§Ù„Ù…Ø­Ù„ÙŠ (Hardware UUID).
   - `X-Company-Code`: Ø§Ù„Ø±Ù…Ø² Ø§Ù„ØªØ¹Ø±ÙŠÙÙŠ Ù„Ù„Ø´Ø±ÙƒØ© Ø§Ù„Ù…ÙƒÙˆÙ† Ù…Ù† 4 Ø£Ø±Ù‚Ø§Ù… Ù„Ø±Ø¨Ø· Ø§Ù„Ø£Ø¬Ù‡Ø²Ø© Ø¨Ø§Ù„Ø®Ø²ÙŠÙ†Ø© Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ©.

---

## ðŸŒ 2. Ø®ÙˆØ§Ø¯Ù… Ø§Ù„Ù†Ø¸Ø§Ù… (Server Configurations)

ØªÙ… Ø¥Ø¹Ø¯Ø§Ø¯ Ø§Ù„Ù†Ø¸Ø§Ù… Ù„Ù„Ø¹Ù…Ù„ Ø¹Ù„Ù‰ Ø¨ÙŠØ¦Ø§Øª Ù…ØªØ¹Ø¯Ø¯Ø© Ù…Ø¹ Ø¯Ø¹Ù… Ø§Ù„Ø£Ù†ÙØ§Ù‚ Ø§Ù„Ø¢Ù…Ù†Ø© Ù„Ù„ØªØ·ÙˆÙŠØ± Ø§Ù„Ù…Ø­Ù„ÙŠ:

*   **Ø§Ù„Ø®Ø§Ø¯Ù… Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ (Production Server):**
    `https://api.ventapos.com/v1`
*   **Ø®Ø§Ø¯Ù… Ø§Ù„ØªØ·ÙˆÙŠØ± ÙˆØ§Ù„Ù…Ø²Ø§Ù…Ù†Ø© Ø§Ù„Ù…Ø­Ù„ÙŠ (Local Tunneling Server - Ngrok):**
    `https://jargonal-colourationally-buddy.ngrok-free.dev/api/v1` (ÙŠÙØ³ØªØ®Ø¯Ù… Ù„Ø±Ø¨Ø· Ù†Ù‚Ø§Ø· Ø§Ù„Ø¨ÙŠØ¹ Ø§Ù„Ù…Ø­Ù„ÙŠØ© ÙˆØªØ®Ø·ÙŠ Ø¬Ø¯Ø±Ø§Ù† Ø§Ù„Ø­Ù…Ø§ÙŠØ©).

---

## ðŸ” 3. Ø·Ø¨Ù‚Ø© ØªØ±Ø¬Ù…Ø© Ø§Ù„Ø­Ù‚ÙˆÙ„ (SQLite-to-Django Translation Layer)

Ù„ØªØ¬Ù†Ø¨ Ø­Ø¯ÙˆØ« Ø£ÙŠ ÙÙ‚Ø¯Ø§Ù† ÙÙŠ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª (Data Dropping) Ø£Ø«Ù†Ø§Ø¡ Ø¹Ù…Ù„ÙŠØ§Øª Ø§Ù„Ù…Ø²Ø§Ù…Ù†Ø© ÙˆØ§Ù„Ø³Ø­Ø¨ (Pull/Push) Ø¨ÙŠÙ† Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ø­Ù„ÙŠØ© (SQLite) ÙˆÙ‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ø±ÙƒØ²ÙŠØ© (PostgreSQL)ØŒ ÙŠÙ‚ÙˆÙ… Ø§Ù„Ù†Ø¸Ø§Ù… Ø¨ØªØ±Ø¬Ù…Ø© Ø§Ù„Ø­Ù‚ÙˆÙ„ ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹ ÙƒØ§Ù„ØªØ§Ù„ÙŠ:

### Ø£) Ø¬Ø¯ÙˆÙ„ Ø§Ù„Ù…Ù†ØªØ¬Ø§Øª / Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© (Inventory Items Mapping)
| Django Backend Field (PostgreSQL) | Local SQLite Field | Description |
| :--- | :--- | :--- |
| `local_id` | `id` | Ø§Ù„Ù…Ø¹Ø±Ù Ø§Ù„ÙØ±ÙŠØ¯ Ù„Ù„Ù…Ù†ØªØ¬ Ù…Ø­Ù„ÙŠØ§Ù‹ |
| `quantity` | `initial_quantity` | Ø±ØµÙŠØ¯ Ø§Ù„Ù…Ø®Ø²ÙˆÙ† Ø§Ù„Ø§ÙØªØªØ§Ø­ÙŠ |
| `purchase_price` | `initial_purchase_price` | Ø³Ø¹Ø± ØªÙƒÙ„ÙØ© Ø´Ø±Ø§Ø¡ Ø§Ù„Ù…Ù†ØªØ¬ |
| `salesperson_commission_amount` | `initial_commission_amount` | Ù‚ÙŠÙ…Ø© Ø¹Ù…ÙˆÙ„Ø© Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨ |
| `created_at_local` | `created_at` | ØªØ§Ø±ÙŠØ® Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ù…Ù†ØªØ¬ Ù…Ø­Ù„ÙŠØ§Ù‹ |

### Ø¨) Ø¬Ø¯ÙˆÙ„ Ø§Ù„ÙÙˆØ§ØªÙŠØ± (Receipts Mapping)
| Django Backend Field (PostgreSQL) | Local SQLite Field | Description |
| :--- | :--- | :--- |
| `local_id` | `id` | Ø§Ù„Ø±Ù‚Ù… Ø§Ù„Ù…Ø³Ù„Ø³Ù„ Ù„Ù„ÙØ§ØªÙˆØ±Ø© Ù…Ø­Ù„ÙŠØ§Ù‹ |
| `local_branch_id` | `branch_id` | Ù…Ø¹Ø±Ù Ø§Ù„ÙØ±Ø¹ Ø§Ù„Ù…Ù†Ø³ÙˆØ¨ Ù„Ù„ÙØ§ØªÙˆØ±Ø© |
| `local_salesperson_id` | `salesperson_id` | Ù…Ø¹Ø±Ù Ù…Ù†Ø¯ÙˆØ¨ Ø§Ù„Ù…Ø¨ÙŠØ¹Ø§Øª |
| `created_at_local` | `created_at` | ØªØ§Ø±ÙŠØ® ÙˆÙˆÙ‚Øª Ø¥Ù†Ø´Ø§Ø¡ Ø§Ù„ÙØ§ØªÙˆØ±Ø© Ù…Ø­Ù„ÙŠØ§Ù‹ |
| `customer_phone` | `phone_number` | Ø±Ù‚Ù… Ù‡Ø§ØªÙ Ø§Ù„Ø¹Ù…ÙŠÙ„ |
| `customer_address` | `address` | Ø¹Ù†ÙˆØ§Ù† Ø§Ù„Ø¹Ù…ÙŠÙ„ |
| `customer_area` | `area` | Ù…Ù†Ø·Ù‚Ø© Ø£Ùˆ Ø­ÙŠ Ø§Ù„Ø¹Ù…ÙŠÙ„ |

---

## ðŸ’³ 4. Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ø£Ù‚Ø³Ø§Ø· ÙˆÙØ§ØªÙˆØ±Ø© Ø§Ù„Ø§Ø³ØªØ­Ù‚Ø§Ù‚ (25th Billing Rule)

ÙŠÙ„ØªØ²Ù… Ø§Ù„Ù†Ø¸Ø§Ù… Ø¨Ø§Ù„Ù…Ø¹Ø§ÙŠÙŠØ± Ø§Ù„ØªØ§Ù„ÙŠØ© Ù„Ø¥Ø¯Ø§Ø±Ø© Ø¹Ù…Ù„ÙŠØ§Øª Ø§Ù„Ø¨ÙŠØ¹ Ø¨Ø§Ù„ØªÙ‚Ø³ÙŠØ· ÙˆÙ…Ù†Ø¹ Ø§Ù„ØªÙ„Ø§Ø¹Ø¨:
*   **ØªØ³Ù…ÙŠØ© Ø§Ù„Ù…ÙØ§ØªÙŠØ­ (Normalization Key Names):** ÙŠØ¬Ø¨ Ø§Ø³ØªØ®Ø¯Ø§Ù… ÙƒÙ„Ù…Ø© `"installments"` Ø¨Ø¯Ù„Ø§Ù‹ Ù…Ù† `"payments"` Ø£Ùˆ `"installment_payments"`.
*   **ØªØ§Ø±ÙŠØ® Ø§Ù„Ø§Ø³ØªØ­Ù‚Ø§Ù‚ (Due Date Key):** Ø¯Ø§Ø®Ù„ Ù…ØµÙÙˆÙØ© Ø§Ù„Ø£Ù‚Ø³Ø§Ø·ØŒ ÙŠØ¬Ø¨ Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ø­Ù‚Ù„ `"payment_date"` Ø¨Ø¯Ù„Ø§Ù‹ Ù…Ù† `"date"` Ø£Ùˆ `"due_date"`.
*   **Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ù€ 25 Ù…Ù† ÙƒÙ„ Ø´Ù‡Ø±:** ÙŠØªÙ… ØªÙˆÙ„ÙŠØ¯ ØªÙˆØ§Ø±ÙŠØ® Ø§Ù„Ø£Ù‚Ø³Ø§Ø· ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹ Ù„ØªØ¨Ø¯Ø£ Ù…Ù† ÙŠÙˆÙ… **25 ÙÙŠ Ø§Ù„Ø´Ù‡Ø± Ø§Ù„ØªØ§Ù„ÙŠ** Ù„ØªØ§Ø±ÙŠØ® Ø§Ù„Ø¨ÙŠØ¹. ÙŠÙØ­Ø¸Ø± ØªØ¹Ø¯ÙŠÙ„ Ù‡Ø°Ù‡ Ø§Ù„ØªÙˆØ§Ø±ÙŠØ® ÙŠØ¯ÙˆÙŠØ§Ù‹ ÙˆØªØ¹ØªØ¨Ø± Ø§Ù„Ù…Ø®Ø§Ù„ÙØ© Ù…Ø­Ø§ÙˆÙ„Ø© ØªÙ„Ø§Ø¹Ø¨ Ø¨Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª.
*   **Ù…Ù†Ø¹ Ø§Ù„ØªÙƒØ±Ø§Ø± (Collision Prevention):** ÙŠØªÙ… Ø§Ù„Ø§Ø¹ØªÙ…Ø§Ø¯ ÙƒÙ„ÙŠØ§Ù‹ Ø¹Ù„Ù‰ Ø§Ù„Ù‡Ø§Ø´ Ø§Ù„ØªØ´ÙÙŠØ±ÙŠ Ø§Ù„ÙØ±ÙŠØ¯ Ø§Ù„ÙØ±Ø¯ÙŠ Ù„Ù„ÙØ§ØªÙˆØ±Ø© `receipt_hash` Ù„Ø¶Ù…Ø§Ù† Ø¹Ø¯Ù… Ø­Ø¯ÙˆØ« ØªØ¯Ø§Ø®Ù„ Ø¨ÙŠÙ† Ø§Ù„ÙÙˆØ§ØªÙŠØ± Ø§Ù„ÙˆØ§Ø±Ø¯Ø© Ù…Ù† Ø£Ø¬Ù‡Ø²Ø© Ù…Ø®ØªÙ„ÙØ©.

---

## ðŸ’¬ 5. Ù„ØºØ© Ø§Ù„Ø³ÙˆÙ‚ Ø§Ù„Ù…Ù‡Ù†ÙŠØ© Ø§Ù„Ù…Ø¨Ø³Ø·Ø© Ù„Ù„ÙˆØ§Ø¬Ù‡Ø§Øª ÙˆØ§Ù„Ø£Ø®Ø·Ø§Ø¡ (RTL & Arabic Language Policy)

ØªÙ…Øª ØµÙŠØ§ØºØ© Ø±Ø³Ø§Ø¦Ù„ Ø§Ù„Ø£Ø®Ø·Ø§Ø¡ ÙˆØªÙˆØµÙŠÙ Ø§Ù„ÙƒÙŠØ§Ù†Ø§Øª Ø¨Ù„ØºØ© Ø³ÙˆÙ‚ Ù…Ù‡Ù†ÙŠØ© ÙˆÙ…Ø¨Ø³Ø·Ø© Ù‚Ø±ÙŠØ¨Ø© Ù„ØªØ¬Ù‘Ø§Ø± Ø§Ù„Ø³ÙˆÙ‚ Ø§Ù„Ù…ØµØ±ÙŠ Ø¯ÙˆÙ† Ø§Ø¨ØªØ°Ø§Ù„ØŒ Ù…Ø¹ Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ù…Ø³Ù…ÙŠØ§Øª Ø§Ù„ØªØ§Ù„ÙŠØ©:
*   **Ø§Ù„Ø¹Ù…ÙŠÙ„** (ÙˆÙ„ÙŠØ³ Ø§Ù„Ø²Ø¨ÙˆÙ† Ø£Ùˆ Ø§Ù„Ù…Ø´ØªØ±ÙŠ).
*   **Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© / Ø§Ù„Ù…Ù†ØªØ¬** (Ø¨Ø¯Ù„Ø§Ù‹ Ù…Ù† Ø§Ù„Ù…Ø§Ø¯Ø© Ø£Ùˆ Ø§Ù„ØµÙ†Ù).
*   **Ø§Ù„Ø®Ø²Ù†Ø© / Ø§Ù„Ù…Ø§Ù„ÙŠØ©** (Ø¨Ø¯Ù„Ø§Ù‹ Ù…Ù† Ø§Ù„ØµÙ†Ø¯ÙˆÙ‚ Ø£Ùˆ Ø§Ù„Ù†Ù‚Ø¯ÙŠØ© Ø§Ù„ØµØ§ÙÙŠØ©).
*   **Ø§Ù„ÙØ§ØªÙˆØ±Ø©** (Ø¨Ø¯Ù„Ø§Ù‹ Ù…Ù† Ø§Ù„Ø¥ÙŠØµØ§Ù„ Ø£Ùˆ Ø§Ù„Ù…Ø³ØªÙ†Ø¯ Ø§Ù„Ù…Ø¹Ø§Ù…Ù„Ø§ØªÙŠ).
*   **Ø§Ù„Ø¯ÙØªØ±** (Ø¨Ø¯Ù„Ø§Ù‹ Ù…Ù† Ø§Ù„Ø£Ø±Ø´ÙŠÙ Ø£Ùˆ Ø§Ù„Ù†Ø¸Ø§Ù… Ø§Ù„Ù…Ø§Ù„ÙŠ).
*   **Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨** (Ø¨Ø¯Ù„Ø§Ù‹ Ù…Ù† Ø§Ù„Ù…ÙˆØ¸Ù Ø£Ùˆ Ø§Ù„ÙƒØ§Ø´ÙŠØ±).

---

## ðŸ“‹ 6. Ø¹Ù‚Ø¯ Ù…ÙˆØ§ØµÙØ§Øª OpenAPI 3.1.0 (JSON Specification)

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "VentaPOS NextGen REST API",
    "version": "1.0.0",
    "description": "ÙˆØ§Ø¬Ù‡Ø© Ø¨Ø±Ù…Ø¬Ø© Ø§Ù„ØªØ·Ø¨ÙŠÙ‚Ø§Øª Ø§Ù„Ù…Ø·ÙˆØ±Ø© Ù„Ù†Ø¸Ø§Ù… VentaPOS Ù„Ø¥Ø¯Ø§Ø±Ø© Ø§Ù„Ù…Ø¨ÙŠØ¹Ø§Øª ÙˆØ§Ù„Ù…Ø®Ø§Ø²Ù† ÙˆØ§Ù„Ù…Ø²Ø§Ù…Ù†Ø© Ø§Ù„Ø³Ø­Ø§Ø¨ÙŠØ©."
  },
  "servers": [
    {
      "url": "https://api.ventapos.com/v1",
      "description": "Ø®Ø§Ø¯Ù… Ø§Ù„Ø³Ø­Ø§Ø¨Ø© Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ (Ø§Ù„Ø¥Ù†ØªØ§Ø¬)"
    },
    {
      "url": "https://jargonal-colourationally-buddy.ngrok-free.dev/api/v1",
      "description": "Ù†ÙÙ‚ Ø§Ù„ØªØ·ÙˆÙŠØ± ÙˆØ§Ù„Ù…Ø²Ø§Ù…Ù†Ø© Ø§Ù„Ù…Ø­Ù„ÙŠ (Ngrok)"
    }
  ],
  "security": [
    {
      "JWTAuth": []
    }
  ],
  "paths": {
    "/api/v1/auth/demo/": {
      "post": {
        "summary": "ØªØ³Ø¬ÙŠÙ„ Ø¯Ø®ÙˆÙ„ Ù„Ù„ÙˆØ¶Ø¹ Ø§Ù„ØªØ¬Ø±ÙŠØ¨ÙŠ (Demo Mode)",
        "description": "ÙŠØ³Ù…Ø­ Ù„Ù„ØªØ·Ø¨ÙŠÙ‚ Ø¨Ø§Ù„Ø¯Ø®ÙˆÙ„ Ù ÙŠ ÙˆØ¶Ø¹ Ø§Ù„Ù‚Ø±Ø§Ø¡Ø© ÙˆØ§Ù„ØªØ¬Ø±Ø¨Ø© Ù…Ø¹ Ø¨ÙŠØ§Ù†Ø§Øª ÙˆÙ‡Ù…ÙŠØ© Ø¨Ø¯ÙˆÙ† ØªØ±Ø®ÙŠØµ Ù Ø¹Ø§Ù„.",
        "responses": {
          "200": {
            "description": "ØªÙ… Ø§Ù„Ø¯Ø®ÙˆÙ„ Ù„Ù„ÙˆØ¶Ø¹ Ø§Ù„ØªØ¬Ø±ÙŠØ¨ÙŠ.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "token": { "type": "string" },
                    "company_name": { "type": "string" }
                  }
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/auth/recover/": {
      "post": {
        "summary": "Ø§Ø³ØªØ±Ø¯Ø§Ø¯ ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±",
        "description": "ÙŠØ³Ù…Ø­ Ù„Ù„Ù…Ø¯ÙŠØ± Ø¨ØªØ¹ÙŠÙŠÙ† ÙƒÙ„Ù…Ø© Ø³Ø± Ø¬Ø¯ÙŠØ¯Ø© Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… ÙƒÙˆØ¯ Ø§Ù„Ø§Ø³ØªØ±Ø¯Ø§Ø¯.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "recovery_code": { "type": "string" },
                  "new_password": { "type": "string" }
                }
              }
            }
          }
        },
        "responses": {
          "200": { "description": "ØªÙ… ØªØºÙŠÙŠØ± ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±" }
        }
      }
    },
    "/api/v1/auth/viewer/": {
      "post": {
        "summary": "ØªÙˆØ«ÙŠÙ‚ Ù…Ø³ØªØ®Ø¯Ù… Ø§Ù„Ø³Ø­Ø§Ø¨Ø© (Cloud Viewer)",
        "description": "ÙŠØ³Ù…Ø­ Ù‡Ø°Ø§ Ø§Ù„Ù…Ø³Ø§Ø± Ù„Ù…Ø³ØªØ®Ø¯Ù…ÙŠ Ø§Ù„Ø³Ø­Ø§Ø¨Ø© Ø£Ùˆ Ø§Ù„Ù…Ù„Ø§Ùƒ Ø¨Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø¯Ø®ÙˆÙ„ Ù„Ù„ÙˆØµÙˆÙ„ Ø¥Ù„Ù‰ ØªÙØ§ØµÙŠÙ„ Ø§Ù„Ø¯ÙØªØ± ÙˆØ§Ù„Ù…Ø¨ÙŠØ¹Ø§Øª.",
        "security": [],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["company_code", "username", "password_hash"],
                "properties": {
                  "company_code": {
                    "type": "string",
                    "maxLength": 4,
                    "description": "Ø±Ù…Ø² Ø§Ù„Ø´Ø±ÙƒØ© Ø§Ù„Ù…ÙƒÙˆÙ† Ù…Ù† 4 Ø£Ø±Ù‚Ø§Ù….",
                    "example": "1234"
                  },
                  "username": {
                    "type": "string",
                    "description": "Ø§Ø³Ù… Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù… Ø§Ù„Ù…Ø³Ø¬Ù„.",
                    "example": "ahmed_manager"
                  },
                  "password_hash": {
                    "type": "string",
                    "description": "Ø§Ù„Ù‡Ø§Ø´ Ø§Ù„ØªØ´ÙÙŠØ±ÙŠ Ù„ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ± Ø§Ù„Ø®Ø§ØµØ© Ø¨Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù….",
                    "example": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "ØªÙ… Ø§Ù„ØªØ­Ù‚Ù‚ Ø¨Ù†Ø¬Ø§Ø­ ÙˆØ¥Ø±Ø¬Ø§Ø¹ Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø§ØªØµØ§Ù„ Ø¨Ø§Ù„Ø®Ø²Ù†Ø© Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ©.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": {
                      "type": "string",
                      "example": "success"
                    },
                    "master_machine_id": {
                      "type": "string",
                      "example": "mac-uuid-777-888"
                    },
                    "user": {
                      "type": "object",
                      "properties": {
                        "username": { "type": "string", "example": "1234-ahmed_manager" },
                        "role": { "type": "string", "example": "VIEWER" },
                        "local_id": { "type": "integer", "example": 1 }
                      }
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø¯Ø®ÙˆÙ„ Ù†Ø§Ù‚ØµØ© Ø£Ùˆ ØºÙŠØ± ØµØ­ÙŠØ­Ø©.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø¯Ø®ÙˆÙ„ Ù†Ø§Ù‚ØµØ©ØŒ ÙŠØ±Ø¬Ù‰ ÙƒØªØ§Ø¨Ø© Ø±Ù…Ø² Ø§Ù„Ø´Ø±ÙƒØ© ÙˆØ§Ø³Ù… Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù… ÙƒØ§Ù…Ù„Ø§Ù‹."
                }
              }
            }
          },
          "401": {
            "description": "Ø®Ø·Ø£ ÙÙŠ ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ± Ø£Ùˆ Ø§Ø³Ù… Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù….",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "ØºÙŠØ± Ù…ØµØ±Ø­ Ø¨Ø§Ù„Ø¯Ø®ÙˆÙ„ØŒ ÙŠØ±Ø¬Ù‰ Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ø³Ù… Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù… Ø£Ùˆ ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ± Ø§Ù„Ø®Ø§ØµØ© Ø¨Ø§Ù„Ø®Ø²Ù†Ø©."
                }
              }
            }
          },
          "403": {
            "description": "Ø§Ø´ØªØ±Ø§Ùƒ Ø§Ù„Ø³Ø­Ø§Ø¨Ø© Ù…Ø¹Ø·Ù„ Ø£Ùˆ Ù…Ù†ØªÙ‡ÙŠ Ø§Ù„ØµÙ„Ø§Ø­ÙŠØ©.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "Ø§Ù„Ø§Ø´ØªØ±Ø§Ùƒ Ø§Ù„Ø³Ø­Ø§Ø¨ÙŠ Ù„Ù„Ø´Ø±ÙƒØ© Ø§Ù†ØªÙ‡Ù‰ Ø£Ùˆ Ù…Ø¹Ø·Ù„ØŒ ÙŠØ±Ø¬Ù‰ Ø§Ù„ØªØ¬Ø¯ÙŠØ¯ Ù„ØªØªÙ…ÙƒÙ† Ù…Ù† Ø§Ù„Ø¯Ø®ÙˆÙ„."
                }
              }
            }
          },
          "404": {
            "description": "Ø±Ù…Ø² Ø§Ù„Ø´Ø±ÙƒØ© ØºÙŠØ± Ù…ÙˆØ¬ÙˆØ¯.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "Ø±Ù…Ø² Ø§Ù„Ø´Ø±ÙƒØ© Ø§Ù„Ù…ÙƒØªÙˆØ¨ ØºÙŠØ± Ù…Ø³Ø¬Ù„ ÙÙŠ Ø§Ù„Ø¯ÙØªØ±ØŒ ÙŠØ±Ø¬Ù‰ Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø±Ù‚Ù…."
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sync/push/": {
      "post": {
        "summary": "Ø¥Ø±Ø³Ø§Ù„ ÙˆÙ…Ø²Ø§Ù…Ù†Ø© Ø§Ù„ÙÙˆØ§ØªÙŠØ± ÙˆØ§Ù„Ø¨ÙŠØ§Ù†Ø§Øª (Sync Push Ingestion)",
        "description": "ÙŠØ³Ù…Ø­ Ù„Ù„Ø£Ø¬Ù‡Ø²Ø© Ø§Ù„Ù…Ø­Ù„ÙŠØ© Ø¨Ø¯ÙØ¹ Ø§Ù„ÙÙˆØ§ØªÙŠØ± ÙˆØ§Ù„Ø£Ù‚Ø³Ø§Ø· ÙˆØ§Ù„Ù…ØµØ±ÙˆÙØ§Øª ÙˆØ§Ù„Ù…Ù†ØªØ¬Ø§Øª ÙˆØªØ¹Ø¯ÙŠÙ„Ø§ØªÙ‡Ø§ Ø¯ÙØ¹Ø© ÙˆØ§Ø­Ø¯Ø© Ø¨Ø·Ø±ÙŠÙ‚Ø© Ø°Ø±ÙŠØ© (Atomic Transaction) Ù„Ø¶Ù…Ø§Ù† Ø§ØªØ³Ø§Ù‚ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø¨Ø§Ù„Ø®Ø§Ø¯Ù….",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["machine_id", "payload"],
                "properties": {
                  "machine_id": {
                    "type": "string",
                    "description": "Ø§Ù„Ù…Ø¹Ø±Ù Ø§Ù„ÙØ±ÙŠØ¯ Ù„Ù„Ø¬Ù‡Ø§Ø² Ø§Ù„Ù…Ø­Ù„ÙŠ Ø§Ù„Ø±Ø§Ø³Ù„ Ù„Ù„Ø¨ÙŠØ§Ù†Ø§Øª."
                  },
                  "payload": {
                    "type": "object",
                    "properties": {
                      "company_settings": {
                        "type": "object",
                        "properties": {
                          "name": { "type": "string" },
                          "description": { "type": "string" },
                          "phone1": { "type": "string" },
                          "phone2": { "type": "string" },
                          "footer_text": { "type": "string" }
                        }
                      },
                      "branches": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "id": { "type": "integer" },
                            "name": { "type": "string" }
                          }
                        }
                      },
                      "salespeople": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "id": { "type": "integer" },
                            "branch_id": { "type": "integer" },
                            "name": { "type": "string" }
                          }
                        }
                      },
                      "inventory": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "id": { "type": "integer" },
                            "branch_id": { "type": "integer" },
                            "name": { "type": "string" },
                            "quantity": { "type": "integer" },
                            "purchase_price": { "type": "string" },
                            "commission": { "type": "string" },
                            "created_at": { "type": "string", "format": "date-time" }
                          }
                        }
                      },
                      "receipts": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "required": ["receipt_hash", "id", "receipt_number", "total_amount", "is_cash_sale"],
                          "properties": {
                            "receipt_hash": {
                              "type": "string",
                              "description": "Ø§Ù„Ù‡Ø§Ø´ Ø§Ù„Ø£Ù…Ù†ÙŠ Ø§Ù„ÙØ±ÙŠØ¯ Ù„Ù„ÙØ§ØªÙˆØ±Ø© Ù„Ù…Ù†Ø¹ Ø§Ù„ØªÙƒØ±Ø§Ø± ÙˆØ§Ù„ØªØµØ§Ø¯Ù…."
                            },
                            "id": { "type": "integer" },
                            "receipt_number": { "type": "integer" },
                            "branch_id": { "type": "integer" },
                            "salesperson_id": { "type": "integer" },
                            "customer_name": { "type": "string" },
                            "phone_number": { "type": "string" },
                            "address": { "type": "string" },
                            "area": { "type": "string" },
                            "total_amount": { "type": "string" },
                            "down_payment": { "type": "string" },
                            "installment_system": { "type": "string" },
                            "sale_year": { "type": "integer" },
                            "sale_month": { "type": "integer" },
                            "is_cash_sale": { "type": "boolean" },
                            "created_at": { "type": "string", "format": "date-time" },
                            "items": {
                              "type": "array",
                              "items": {
                                "type": "object",
                                "properties": {
                                  "product_id": { "type": "integer" },
                                  "product_name": { "type": "string" },
                                  "quantity": { "type": "integer" },
                                  "price": { "type": "string" }
                                }
                              }
                            },
                            "installments": {
                              "type": "array",
                              "description": "Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ø£Ù‚Ø³Ø§Ø· Ø§Ù„Ù…Ø³ØªØ­Ù‚Ø© Ù„Ù„ÙØ§ØªÙˆØ±Ø©.",
                              "items": {
                                "type": "object",
                                "required": ["payment_date", "amount"],
                                "properties": {
                                  "payment_date": {
                                    "type": "string",
                                    "format": "date",
                                    "description": "ØªØ§Ø±ÙŠØ® Ø§Ø³ØªØ­Ù‚Ø§Ù‚ Ø§Ù„Ù‚Ø³Ø· (ÙŠØ¬Ø¨ Ø£Ù† ÙŠØ®Ø¶Ø¹ Ù„Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ù€ 25)."
                                  },
                                  "amount": {
                                    "type": "string",
                                    "description": "Ù‚ÙŠÙ…Ø© Ø§Ù„Ù‚Ø³Ø· Ø§Ù„Ù…Ø§Ù„ÙŠ."
                                  }
                                }
                              }
                            }
                          }
                        }
                      },
                      "expenses": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "id": { "type": "integer" },
                            "branch_id": { "type": "integer" },
                            "amount": { "type": "string" },
                            "description": { "type": "string" },
                            "expense_year": { "type": "integer" },
                            "expense_month": { "type": "integer" },
                            "created_at": { "type": "string", "format": "date-time" }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "ØªÙ…Øª Ù…Ø²Ø§Ù…Ù†Ø© Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© ÙˆØ§Ù„ÙÙˆØ§ØªÙŠØ± ÙˆØ­ÙØ¸Ù‡Ø§ Ø¨Ø§Ù„Ø¯ÙØªØ± Ø¨Ù†Ø¬Ø§Ø­.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "message": { "type": "string", "example": "ØªÙ… Ù…Ø²Ø§Ù…Ù†Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª ÙˆØ­ÙØ¸ Ø§Ù„ÙÙˆØ§ØªÙŠØ± Ø¨Ø§Ù„Ø¯ÙØªØ± Ø¨Ù†Ø¬Ø§Ø­." },
                    "receipts_processed": { "type": "integer", "example": 5 }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Ø®Ø·Ø£ ÙÙŠ Ø¨Ù†ÙŠØ© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ø±Ø³Ù„Ø© Ø£Ùˆ ÙØ´Ù„ Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø­Ù‚ÙˆÙ„ Ø§Ù„Ù…ÙˆØ­Ø¯Ø© (Data Validation Mismatch).",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„ÙØ§ØªÙˆØ±Ø© ØºÙŠØ± Ù…Ø·Ø§Ø¨Ù‚Ø© Ø£Ùˆ Ù†Ø§Ù‚ØµØ©ØŒ ÙŠØ±Ø¬Ù‰ Ù…Ø±Ø§Ø¬Ø¹Ø© Ø§Ù„Ø¯ÙØªØ± ÙˆØ§Ù„ØªØ£ÙƒØ¯ Ù…Ù† Ø­Ù‚ÙˆÙ„ Ø§Ù„Ø£Ù‚Ø³Ø§Ø· ÙˆØªÙˆØ§Ø±ÙŠØ®Ù‡Ø§."
                }
              }
            }
          },
          "403": {
            "description": "Ø±Ø®ØµØ© Ø§Ù„Ø¬Ù‡Ø§Ø² Ù…Ù†ØªÙ‡ÙŠØ© Ø§Ù„ØµÙ„Ø§Ø­ÙŠØ© Ø£Ùˆ ØºÙŠØ± Ù†Ø´Ø·Ø©.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "Ø§Ù„Ø§Ø´ØªØ±Ø§Ùƒ Ø§Ù„Ø³Ø­Ø§Ø¨ÙŠ Ø§Ù†ØªÙ‡Ù‰ØŒ ÙŠØ±Ø¬Ù‰ Ø§Ù„ØªØ¬Ø¯ÙŠØ¯ Ù„ØªØªÙ…ÙƒÙ† Ù…Ù† Ù…Ø²Ø§Ù…Ù†Ø© Ø§Ù„ÙÙˆØ§ØªÙŠØ±."
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sync/pull/": {
      "get": {
        "summary": "Ø³Ø­Ø¨ ØªØ­Ø¯ÙŠØ«Ø§Øª Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª (Sync Pull View - GET)",
        "description": "Ø¬Ù„Ø¨ ØªØ­Ø¯ÙŠØ«Ø§Øª Ø§Ù„Ø¨Ø¶Ø§Ø¦Ø¹ØŒ Ø§Ù„ÙØ±ÙˆØ¹ØŒ Ø§Ù„Ù…Ù†Ø§Ø¯ÙŠØ¨ØŒ Ø§Ù„ÙÙˆØ§ØªÙŠØ±ØŒ ÙˆØ§Ù„Ù…ØµØ§Ø±ÙŠÙ Ø§Ù„ØªÙŠ ØªÙ… Ø¥Ø¶Ø§ÙØªÙ‡Ø§ Ø¨Ø¹Ø¯ ØªØ§Ø±ÙŠØ® Ø¢Ø®Ø± Ù…Ø²Ø§Ù…Ù†Ø© Ù„Ù„ÙØ±Ø¹ Ø£Ùˆ Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨.",
        "parameters": [
          {
            "name": "machine_id",
            "in": "query",
            "required": true,
            "schema": { "type": "string" }
          },
          {
            "name": "last_sync",
            "in": "query",
            "required": true,
            "schema": { "type": "string", "format": "date-time" },
            "description": "ØªØ§Ø±ÙŠØ® Ø¢Ø®Ø± Ù…Ø²Ø§Ù…Ù†Ø© ØªÙ… Ø³Ø­Ø¨Ù‡Ø§ Ù…Ø­Ù„ÙŠØ§Ù‹."
          },
          {
            "name": "company_code",
            "in": "query",
            "required": false,
            "schema": { "type": "string" }
          },
          {
            "name": "role",
            "in": "query",
            "required": false,
            "schema": { "type": "string" }
          },
          {
            "name": "salesperson_id",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          }
        ],
        "responses": {
          "200": {
            "description": "Ù‚Ø§Ø¦Ù…Ø© ØªØ­Ø¯ÙŠØ«Ø§Øª Ø§Ù„ÙƒÙŠØ§Ù†Ø§Øª Ø§Ù„ØªÙŠ Ø·Ø±Ø£Øª Ø¹Ù„Ù‰ Ø§Ù„Ø³ÙŠØ±ÙØ± Ù…Ø¹ Ø­Ù‚ÙˆÙ„ SQLite Ø§Ù„Ù…ØªØ±Ø¬Ù…Ø©.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/SyncPullResponse" }
              }
            }
          },
          "403": {
            "description": "ØºÙŠØ± Ù…ØµØ±Ø­ Ù„Ù„Ø¬Ù‡Ø§Ø² Ø¨Ø§Ù„Ø³Ø­Ø¨ Ù„Ø§Ù†ØªÙ‡Ø§Ø¡ Ø§Ù„ØªØ±Ø®ÙŠØµ.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "Ø§Ù„Ø§Ø´ØªØ±Ø§Ùƒ Ø§Ù„Ø³Ø­Ø§Ø¨ÙŠ ØºÙŠØ± ÙØ¹Ø§Ù„ØŒ ÙŠØ±Ø¬Ù‰ Ù…Ø±Ø§Ø¬Ø¹Ø© Ø¥Ø¯Ø§Ø±Ø© Ø§Ù„ØªØ±Ø®ÙŠØµ Ø¨Ø§Ù„Ø´Ø±ÙƒØ©."
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "Ø³Ø­Ø¨ ØªØ­Ø¯ÙŠØ«Ø§Øª Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª (Sync Pull View - POST)",
        "description": "Ù…Ø·Ø§Ø¨Ù‚ Ù„Ø·Ø±ÙŠÙ‚Ø© GET ÙˆÙ„ÙƒÙ† ÙŠØ¯Ø¹Ù… Ø¥Ø±Ø³Ø§Ù„ Ø§Ù„Ù…ØªØºÙŠØ±Ø§Øª Ø§Ù„Ø£Ù…Ù†ÙŠØ© Ø¯Ø§Ø®Ù„ Ø¬Ø³Ù… Ø§Ù„Ø·Ù„Ø¨ (Body) Ù„ØªÙØ§Ø¯ÙŠ Ø¸Ù‡ÙˆØ± Ø±Ù…ÙˆØ² Ø§Ù„ØªØ¹Ø±ÙŠÙ ÙÙŠ Ø§Ù„Ø±ÙˆØ§Ø¨Ø·.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["machine_id", "last_sync"],
                "properties": {
                  "machine_id": { "type": "string" },
                  "last_sync": { "type": "string", "format": "date-time" },
                  "company_code": { "type": "string" },
                  "role": { "type": "string" },
                  "salesperson_id": { "type": "integer" }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Ù‚Ø§Ø¦Ù…Ø© ØªØ­Ø¯ÙŠØ«Ø§Øª Ø§Ù„ÙƒÙŠØ§Ù†Ø§Øª Ø§Ù„Ù†Ø§Ø¬Ø­Ø©.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/SyncPullResponse" }
              }
            }
          },
          "400": {
            "description": "Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø·Ù„Ø¨ Ø®Ø§Ø·Ø¦Ø©.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" }
              }
            }
          }
        }
      }
    },
    "/api/v1/sync/confirm-receipts/": {
      "post": {
        "summary": "ØªØ£ÙƒÙŠØ¯ Ø§Ø³ØªÙ„Ø§Ù… ÙÙˆØ§ØªÙŠØ± Ø§Ù„Ù‡ÙˆØ§ØªÙ Ø§Ù„Ù…Ø­Ù…ÙˆÙ„Ø©",
        "description": "ÙŠÙ‚ÙˆÙ… Ø§Ù„Ø¬Ù‡Ø§Ø² Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ (Master POS) Ø¨ØªØ£ÙƒÙŠØ¯ Ø§Ø³ØªÙ„Ø§Ù… ÙÙˆØ§ØªÙŠØ± Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨ÙŠÙ† ÙˆØªØ«Ø¨ÙŠØªÙ‡Ø§ Ø¨Ø§Ù„Ø®Ø²Ù†Ø© Ù„Ø¥Ù„ØºØ§Ø¡ Ø­Ø§Ù„Ø© Ø§Ù„Ø§Ù†ØªØ¸Ø§Ø± (is_confirmed = true).",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["machine_id", "receipt_hashes"],
                "properties": {
                  "machine_id": { "type": "string" },
                  "receipt_hashes": {
                    "type": "array",
                    "items": { "type": "string" },
                    "description": "Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ù‡Ø§Ø´ Ù„Ù„ÙÙˆØ§ØªÙŠØ± Ø§Ù„Ù…Ø±Ø§Ø¯ ØªØ£ÙƒÙŠØ¯Ù‡Ø§."
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "ØªÙ… ØªØ£ÙƒÙŠØ¯ Ø§Ù„ÙÙˆØ§ØªÙŠØ± Ø¨Ù†Ø¬Ø§Ø­.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "updated_count": { "type": "integer", "example": 3 }
                  }
                }
              }
            }
          },
          "403": {
            "description": "ØºÙŠØ± Ù…ØµØ±Ø­ Ù„Ù„Ø¬Ù‡Ø§Ø² Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "ØºÙŠØ± Ù…ØµØ±Ø­ Ù„Ù„Ø¬Ù‡Ø§Ø² Ø¨ØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø­Ø³Ø§Ø¨ Ø§Ù„Ù…Ø§Ù„ÙŠØŒ ÙŠØ±Ø¬Ù‰ Ù…Ø±Ø§Ø¬Ø¹Ø© Ø¥Ø¯Ø§Ø±Ø© Ø§Ù„Ø®Ø²Ù†Ø©."
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/products/": {
      "get": {
        "summary": "Ø¹Ø±Ø¶ Ø¨Ø¶Ø§Ø¹Ø© Ø§Ù„ÙØ±Ø¹ (Products List)",
        "description": "Ø¬Ù„Ø¨ Ù‚Ø§Ø¦Ù…Ø© Ø¨Ø¶Ø§Ø¹Ø© Ø§Ù„ÙØ±Ø¹ Ø§Ù„Ø­Ø§Ù„ÙŠØ© Ù…Ø¹ Ø­Ø³Ø§Ø¨ ÙƒÙ…ÙŠØ© Ø±ØµÙŠØ¯ Ø§Ù„Ù…Ø®Ø²ÙˆÙ† Ø§Ù„ÙØ¹Ù„ÙŠ Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ Ù…Ø¹Ø§Ø¯Ù„Ø© Ø§Ù„Ø²Ù…Ù† Ø§Ù„ØªØ±Ø§Ø¬Ø¹ÙŠ.",
        "parameters": [
          {
            "name": "branch_id",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          },
          {
            "name": "month",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          },
          {
            "name": "year",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          }
        ],
        "responses": {
          "200": {
            "description": "ØªÙ… Ø¬Ù„Ø¨ Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ø¨Ø¶Ø§Ø¦Ø¹ Ø§Ù„Ù…ØªØ§Ø­Ø© Ø¨Ø§Ù„Ø®Ø²Ù†Ø©.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": { "$ref": "#/components/schemas/ProductSchema" }
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "Ø¥Ø¶Ø§ÙØ© Ø£Ùˆ ØªØ¹Ø¯ÙŠÙ„ Ø¨Ø¶Ø§Ø¹Ø© (Add/Modify Product)",
        "description": "Ø¥Ø¯Ø®Ø§Ù„ Ø¨Ø¶Ø§Ø¹Ø© Ø¬Ø¯ÙŠØ¯Ø© Ù„Ù„Ø¯ÙØªØ± Ø£Ùˆ ØªØ¹Ø¯ÙŠÙ„ Ø£Ø³Ø¹Ø§Ø± Ø§Ù„ØªÙƒÙ„ÙØ© ÙˆØ¹Ù…ÙˆÙ„Ø§Øª Ø§Ù„Ù…Ù†Ø§Ø¯ÙŠØ¨.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/ProductSchema" }
            }
          }
        },
        "responses": {
          "201": {
            "description": "ØªÙ… ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© Ø¨Ø§Ù„Ø¯ÙØªØ± Ø¨Ù†Ø¬Ø§Ø­.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "product": { "$ref": "#/components/schemas/ProductSchema" }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Ø®Ø·Ø£ ÙÙŠ Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„ØµÙ†Ù.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "ÙØ´Ù„ Ø¥Ø¶Ø§ÙØ© Ø§Ù„ØµÙ†ÙØŒ ÙŠØ±Ø¬Ù‰ ÙƒØªØ§Ø¨Ø© Ø§Ø³Ù… Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© ÙˆØ³Ø¹Ø± Ø§Ù„ØªÙƒÙ„ÙØ© Ø¨Ø´ÙƒÙ„ ØµØ­ÙŠØ­."
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/receipts/": {
      "get": {
        "summary": "Ø§Ø³ØªØ¹Ø±Ø§Ø¶ ÙÙˆØ§ØªÙŠØ± Ø§Ù„Ù…Ø¨ÙŠØ¹Ø§Øª (Search & Filter Receipts)",
        "description": "Ù‚Ø§Ø¦Ù…Ø© Ø¨ÙÙˆØ§ØªÙŠØ± Ø§Ù„Ù…Ø¨ÙŠØ¹Ø§Øª Ø§Ù„Ø¬Ø§Ø±ÙŠØ© ÙˆØ§Ù„Ø£Ù‚Ø³Ø§Ø· Ø§Ù„Ù…Ø³ØªØ­Ù‚Ø© ÙˆØ§Ù„Ù…Ø­ØµÙ„Ø© Ù…Ø¹ ÙÙ„ØªØ±Ø© Ø­Ø³Ø¨ Ø§Ù„ÙØ±Ø¹ Ø£Ùˆ Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨ Ø£Ùˆ Ø§Ù„Ø¹Ù…ÙŠÙ„.",
        "parameters": [
          {
            "name": "branch_id",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          },
          {
            "name": "salesperson_id",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          },
          {
            "name": "is_cash_sale",
            "in": "query",
            "required": false,
            "schema": { "type": "boolean" }
          }
        ],
        "responses": {
          "200": {
            "description": "Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„ÙÙˆØ§ØªÙŠØ± Ø§Ù„Ù…Ø·Ù„ÙˆØ¨Ø©.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": { "$ref": "#/components/schemas/ReceiptSchema" }
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "Ø¥ØµØ¯Ø§Ø± ÙØ§ØªÙˆØ±Ø© Ø¨ÙŠØ¹ Ø¬Ø¯ÙŠØ¯Ø© (Create Sale Receipt)",
        "description": "ØªØ³Ø¬ÙŠÙ„ Ø¹Ù…Ù„ÙŠØ© Ø¨ÙŠØ¹ Ù†Ù‚Ø¯ÙŠØ© Ø£Ùˆ Ø¨Ø§Ù„ØªÙ‚Ø³ÙŠØ· Ø¨Ø§Ù„Ø®Ø²Ù†Ø©. Ù…Ù„Ø§Ø­Ø¸Ø©: Ù‡Ø°Ù‡ Ø§Ù„Ø¹Ù…Ù„ÙŠØ© ØªØ®ØµÙ… Ù…Ù† Ø±ØµÙŠØ¯ Ø§Ù„ÙÙˆØ§ØªÙŠØ± Ø§Ù„Ù…ØªØ§Ø­Ø© Ù„Ù„Ø±Ø®ØµØ© Ø§Ù„Ù†Ø´Ø·Ø© (Invoices Balance).",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/ReceiptSchema" }
            }
          }
        },
        "responses": {
          "201": {
            "description": "ØªÙ… Ø¥ØµØ¯Ø§Ø± Ø§Ù„ÙØ§ØªÙˆØ±Ø© ÙˆØ­Ø³Ø§Ø¨ Ø§Ù„Ø£Ù‚Ø³Ø§Ø· ÙˆÙÙ‚ Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ù€ 25 Ø¨Ù†Ø¬Ø§Ø­.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "receipt_number": { "type": "integer", "example": 1022 },
                    "receipt_hash": { "type": "string", "example": "a4f89d09c6238b1f2095f87b8d009211c47dfd6e3c3b03698a96d13a6df91278" }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª ØºÙŠØ± ØµØ§Ù„Ø­Ø© Ø£Ùˆ ÙØ´Ù„ Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø³Ù„Ø§Ù…ØªÙ‡Ø§.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "Ø­Ø³Ø§Ø¨Ø§Øª Ø§Ù„ÙØ§ØªÙˆØ±Ø© Ø®Ø§Ø·Ø¦Ø©ØŒ Ø§Ù„Ù‚ÙŠÙ…Ø© Ø§Ù„Ø¥Ø¬Ù…Ø§Ù„ÙŠØ© Ù„Ø§ ØªØ·Ø§Ø¨Ù‚ Ø£Ø³Ø¹Ø§Ø± Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© Ø§Ù„Ù…Ø¨Ø§Ø¹Ø©."
                }
              }
            }
          },
          "403": {
            "description": "ÙØ´Ù„ Ø¥ØµØ¯Ø§Ø± Ø§Ù„ÙØ§ØªÙˆØ±Ø© Ø¨Ø³Ø¨Ø¨ Ø§Ù†ØªÙ‡Ø§Ø¡ Ø¨Ø§Ù‚Ø© Ø§Ù„ØªØ±Ø®ÙŠØµ Ø£Ùˆ Ù†ÙØ§Ø¯ Ø§Ù„Ø±ØµÙŠØ¯ Ø§Ù„Ù…ØªØ§Ø­ Ù…Ù† Ø§Ù„ÙÙˆØ§ØªÙŠØ±.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "Ù„Ø§ ÙŠÙ…ÙƒÙ† Ø·Ø¨Ø§Ø¹Ø© Ø£Ùˆ Ø¥ØµØ¯Ø§Ø± Ø§Ù„ÙØ§ØªÙˆØ±Ø©ØŒ Ø±ØµÙŠØ¯ Ø§Ù„ÙÙˆØ§ØªÙŠØ± Ø§Ù„Ù…Ø³Ù…ÙˆØ­ Ø¨Ù‡ Ù„Ù„Ø±Ø®ØµØ© Ù‚Ø¯ Ù†ÙØ¯. ÙŠØ±Ø¬Ù‰ Ø§Ù„Ø´Ø­Ù† Ø£ÙˆÙ„Ø§Ù‹."
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/expenses/": {
      "get": {
        "summary": "Ø§Ø³ØªØ¹Ø±Ø§Ø¶ Ù…ØµØ±ÙˆÙØ§Øª Ø§Ù„ÙØ±Ø¹ (Branch Expenses)",
        "description": "Ø¬Ù„Ø¨ Ø§Ù„Ù…ØµØ§Ø±ÙŠÙ Ø§Ù„Ø¬Ø§Ø±ÙŠØ© ÙˆØ§Ù„Ø¹Ù…ÙˆÙ…ÙŠØ© Ø§Ù„Ù…Ø³Ø¬Ù„Ø© Ø¨Ø§Ù„Ø®Ø²ÙŠÙ†Ø© Ù„ÙØ±Ø¹ Ù…Ø¹ÙŠÙ†.",
        "parameters": [
          {
            "name": "branch_id",
            "in": "query",
            "required": true,
            "schema": { "type": "integer" }
          },
          {
            "name": "year",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          },
          {
            "name": "month",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          }
        ],
        "responses": {
          "200": {
            "description": "Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ù…ØµØ±ÙˆÙØ§Øª Ø§Ù„Ø®Ø§ØµØ© Ø¨Ø§Ù„ÙØ±Ø¹.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": { "$ref": "#/components/schemas/ExpenseSchema" }
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "ØªØ³Ø¬ÙŠÙ„ Ø¨Ù†Ø¯ Ù…ØµØ±ÙˆÙØ§Øª (Track Branch Expense)",
        "description": "Ø¥Ø¶Ø§ÙØ© Ø¨Ù†Ø¯ Ù…Ù†ØµØ±Ù Ù…Ø§Ù„ÙŠ Ø¬Ø¯ÙŠØ¯ Ù„Ø®Ø²ÙŠÙ†Ø© Ø§Ù„ÙØ±Ø¹ Ù…Ø¹ Ø±Ø¨Ø·Ù‡ Ø¨Ø§Ù„Ø¯ÙØªØ± Ø§Ù„Ø³Ù†ÙˆÙŠ ÙˆØ§Ù„Ø´Ù‡Ø±ÙŠ.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/ExpenseSchema" }
            }
          }
        },
        "responses": {
          "201": {
            "description": "ØªÙ… ØªØ¯ÙˆÙŠÙ† Ø§Ù„Ù…ØµØ±ÙˆÙ Ø¨Ø§Ù„Ø¯ÙØªØ± Ø§Ù„Ù…Ø§Ù„ÙŠ Ù„Ù„ÙØ±Ø¹ Ø¨Ù†Ø¬Ø§Ø­.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "expense": { "$ref": "#/components/schemas/ExpenseSchema" }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Ø§Ù„Ù…Ø¨Ù„Øº Ø§Ù„Ù…Ø§Ù„ÙŠ Ø£Ùˆ Ø§Ù„ÙˆØµÙ Ø§Ù„Ù…Ø³Ø¬Ù„ ØºÙŠØ± ØµØ­ÙŠØ­.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "ÙØ´Ù„ ØªØ¯ÙˆÙŠÙ† Ø§Ù„Ù…ØµØ±ÙˆÙØŒ ÙŠØ±Ø¬Ù‰ Ø§Ù„ØªØ£ÙƒØ¯ Ù…Ù† ÙƒØªØ§Ø¨Ø© Ù‚ÙŠÙ…Ø© Ø¨Ù†Ø¯ Ø§Ù„Ù…ØµØ±ÙˆÙØ§Øª ÙˆØªØ­Ø¯ÙŠØ¯ Ø§Ù„ÙØ±Ø¹."
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "ErrorResponse": {
        "type": "object",
        "required": ["status", "message"],
        "properties": {
          "status": {
            "type": "string",
            "example": "error"
          },
          "message": {
            "type": "string",
            "description": "Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£ Ø§Ù„Ù…ÙˆØ¬Ù‡Ø© Ù„Ù„Ù…Ø³ØªØ®Ø¯Ù… Ø¨Ù„ØºØ© Ø³ÙˆÙ‚ Ù…Ø¨Ø³Ø·Ø© Ù„Ø¹Ø±Ø¶Ù‡Ø§ Ù…Ø¨Ø§Ø´Ø±Ø© Ø¨Ø§Ù„ÙˆØ§Ø¬Ù‡Ø©.",
            "example": "Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„ÙØ§ØªÙˆØ±Ø© ØºÙŠØ± Ù…Ø·Ø§Ø¨Ù‚Ø© Ø£Ùˆ Ù†Ø§Ù‚ØµØ©ØŒ ÙŠØ±Ø¬Ù‰ Ù…Ø±Ø§Ø¬Ø¹Ø© Ø§Ù„Ø¯ÙØªØ± ÙˆØ§Ù„ØªØ£ÙƒØ¯ Ù…Ù† Ø­Ù‚ÙˆÙ„ Ø§Ù„Ø£Ù‚Ø³Ø§Ø·."
          }
        }
      },
      "ProductSchema": {
        "type": "object",
        "required": ["name", "branch_id", "initial_quantity", "initial_purchase_price"],
        "properties": {
          "id": { "type": "integer", "description": "Ø§Ù„Ù…Ø¹Ø±Ù Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ Ø¨Ø§Ù„Ø¯ÙØªØ± Ø§Ù„Ù…Ø±ÙƒØ²ÙŠ" },
          "name": { "type": "string", "description": "Ø§Ø³Ù… Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© / Ø§Ù„Ù…Ù†ØªØ¬" },
          "branch_id": { "type": "integer", "description": "Ø§Ù„ÙØ±Ø¹ Ø§Ù„Ù…Ù†Ø³ÙˆØ¨ Ù„Ù‡ Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø©" },
          "initial_quantity": { "type": "integer", "description": "Ø§Ù„Ù…Ø®Ø²ÙˆÙ† Ø§Ù„Ø§ÙØªØªØ§Ø­ÙŠ Ù„Ù„ÙØ±Ø¹" },
          "initial_purchase_price": { "type": "integer", "description": "Ø³Ø¹Ø± Ø´Ø±Ø§Ø¡ ÙˆØªÙƒÙ„ÙØ© Ø§Ù„Ù‚Ø·Ø¹Ø© Ø¨Ø§Ù„Ø®Ø²Ù†Ø©" },
          "initial_commission_amount": { "type": "integer", "description": "Ø¹Ù…ÙˆÙ„Ø© Ø§Ù„Ù…Ù†Ø¯ÙˆØ¨ Ø§Ù„Ø§ÙØªØªØ§Ø­ÙŠØ© Ù„Ù„Ù…Ø¨ÙŠØ¹Ø§Øª" },
          "initial_month": { "type": "integer", "example": 6 },
          "initial_year": { "type": "integer", "example": 2026 },
          "current_stock": { "type": "integer", "readOnly": true, "description": "Ø±ØµÙŠØ¯ Ø§Ù„Ù…Ø®Ø²ÙˆÙ† Ø§Ù„ÙØ¹Ù„ÙŠ Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ Ø§Ù„Ø­Ø³Ø§Ø¨ Ø§Ù„ØªØ±Ø§Ø¬Ø¹ÙŠ" }
        }
      },
      "ReceiptSchema": {
        "type": "object",
        "required": ["branch_id", "total_amount", "is_cash_sale", "receipt_hash", "items"],
        "properties": {
          "receipt_hash": { "type": "string", "description": "Ø§Ù„ØªÙˆÙ‚ÙŠØ¹ Ø§Ù„ØªØ´ÙÙŠØ±ÙŠ Ù„Ù„ÙØ§ØªÙˆØ±Ø© Ù„Ù…Ù†Ø¹ ØªØ¯Ø§Ø®Ù„ Ø§Ù„Ø­Ø³Ø§Ø¨Ø§Øª Ø§Ù„Ù…Ø§Ù„ÙŠØ©" },
          "receipt_number": { "type": "integer", "description": "Ø±Ù‚Ù… Ù…Ø³Ù„Ø³Ù„ Ø§Ù„ÙØ§ØªÙˆØ±Ø© Ù…Ø­Ù„ÙŠØ§Ù‹ Ø¨Ø§Ù„ÙØ±Ø¹" },
          "branch_id": { "type": "integer", "description": "Ø§Ù„ÙØ±Ø¹ Ø§Ù„ØµØ§Ø¯Ø± Ù…Ù†Ù‡ Ø§Ù„ÙØ§ØªÙˆØ±Ø©" },
          "salesperson_id": { "type": "integer", "nullable": true },
          "customer_name": { "type": "string", "description": "Ø§Ø³Ù… Ø§Ù„Ø¹Ù…ÙŠÙ„ Ø§Ù„Ù…Ø³Ø¬Ù„ Ø¨Ø§Ù„ÙØ§ØªÙˆØ±Ø©" },
          "customer_phone": { "type": "string", "nullable": true },
          "customer_address": { "type": "string", "nullable": true },
          "customer_area": { "type": "string", "nullable": true },
          "total_amount": { "type": "integer", "description": "Ø¥Ø¬Ù…Ø§Ù„ÙŠ Ø§Ù„Ù‚ÙŠÙ…Ø© Ø§Ù„Ù…Ø§Ù„ÙŠØ© Ù„Ù„ÙØ§ØªÙˆØ±Ø©" },
          "down_payment": { "type": "integer", "description": "Ù…Ù‚Ø¯Ù… Ø§Ù„Ø¯ÙØ¹ Ø§Ù„Ù†Ù‚Ø¯ÙŠ ÙÙŠ Ø­Ø§Ù„Ø© Ø§Ù„Ø¨ÙŠØ¹ Ø¨Ø§Ù„Ù‚Ø³Ø·" },
          "sale_month": { "type": "integer", "example": 6 },
          "sale_year": { "type": "integer", "example": 2026 },
          "is_cash_sale": { "type": "boolean", "description": "Ù‡Ù„ Ø§Ù„Ù…Ø¹Ø§Ù…Ù„Ø© Ù†Ù‚Ø¯ÙŠØ© Ø¨Ø§Ù„ÙƒØ§Ù…Ù„ (Ù†Ù‚Ø¯ÙŠØ©) Ø£Ù… Ø¨Ø§Ù„Ø£Ù‚Ø³Ø§Ø·" },
          "items": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["inventory_item_id", "quantity", "unit_price"],
              "properties": {
                "inventory_item_id": { "type": "integer", "description": "Ù…Ø¹Ø±Ù Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© Ø¨Ø§Ù„Ø¯ÙØªØ±" },
                "quantity": { "type": "integer", "description": "Ø§Ù„ÙƒÙ…ÙŠØ© Ø§Ù„Ù…Ø´ØªØ±Ø§Ø©" },
                "unit_price": { "type": "integer", "description": "Ø³Ø¹Ø± Ø¨ÙŠØ¹ Ø§Ù„Ù‚Ø·Ø¹Ø© Ø¨Ø§Ù„ÙØ§ØªÙˆØ±Ø©" }
              }
            }
          },
          "installments": {
            "type": "array",
            "description": "Ù…ØµÙÙˆÙØ© ØªÙˆØ§Ø±ÙŠØ® ÙˆÙ‚ÙŠÙ… Ø§Ø³ØªØ­Ù‚Ø§Ù‚ Ø£Ù‚Ø³Ø§Ø· Ø§Ù„Ø¹Ù…ÙŠÙ„.",
            "items": {
              "type": "object",
              "required": ["payment_date", "amount"],
              "properties": {
                "payment_date": { "type": "string", "format": "date", "description": "ØªØ§Ø±ÙŠØ® Ø§Ù„Ù‚Ø³Ø· Ø§Ù„Ø´Ù‡Ø±ÙŠ (Ù‚Ø§Ø¹Ø¯Ø© 25)" },
                "amount": { "type": "integer", "description": "Ù…Ø¨Ù„Øº Ø§Ù„Ù‚Ø³Ø· Ø§Ù„Ù…Ø³ØªØ­Ù‚" }
              }
            }
          }
        }
      },
      "ExpenseSchema": {
        "type": "object",
        "required": ["branch_id", "amount", "description"],
        "properties": {
          "id": { "type": "integer" },
          "branch_id": { "type": "integer" },
          "amount": { "type": "integer", "description": "Ù‚ÙŠÙ…Ø© Ø§Ù„Ù…ØµØ±ÙˆÙ Ø§Ù„Ù…Ø¯ÙÙˆØ¹ Ù…Ù† Ø§Ù„Ø®Ø²Ù†Ø©" },
          "description": { "type": "string", "description": "Ø³Ø¨Ø¨ ØµØ±Ù Ø§Ù„Ù…Ø¨Ù„Øº Ø¨Ø§Ù„ØªÙØµÙŠÙ„" },
          "expense_year": { "type": "integer", "example": 2026 },
          "expense_month": { "type": "integer", "example": 6 },
          "created_at": { "type": "string", "format": "date-time" }
        }
      },
      "SyncPullResponse": {
        "type": "object",
        "properties": {
          "status": { "type": "string", "example": "success" },
          "products": {
            "type": "array",
            "items": {
              "type": "object",
              "description": "Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø¨Ø¶Ø§Ø¹Ø© Ø§Ù„Ù…ØªØ±Ø¬Ù…Ø© Ù„Ù€ SQLite",
              "properties": {
                "id": { "type": "integer", "description": "ÙŠØªØ±Ø¬Ù… Ù„Ù€ local_id" },
                "name": { "type": "string" },
                "branch_id": { "type": "integer" },
                "initial_quantity": { "type": "integer" },
                "initial_purchase_price": { "type": "integer" },
                "initial_commission_amount": { "type": "integer" },
                "initial_month": { "type": "integer" },
                "initial_year": { "type": "integer" }
              }
            }
          },
          "receipts": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "integer", "description": "ÙŠØªØ±Ø¬Ù… Ù„Ù€ local_id" },
                "receipt_hash": { "type": "string" },
                "receipt_number": { "type": "integer" },
                "branch_id": { "type": "integer" },
                "salesperson_id": { "type": "integer", "nullable": true },
                "customer_name": { "type": "string" },
                "phone_number": { "type": "string", "description": "ÙŠØªØ±Ø¬Ù… Ù„Ù€ customer_phone" },
                "address": { "type": "string", "description": "ÙŠØªØ±Ø¬Ù… Ù„Ù€ customer_address" },
                "area": { "type": "string", "description": "ÙŠØªØ±Ø¬Ù… Ù„Ù€ customer_area" },
                "total_amount": { "type": "integer" },
                "down_payment": { "type": "integer" },
                "is_cash_sale": { "type": "boolean" },
                "sale_month": { "type": "integer" },
                "sale_year": { "type": "integer" },
                "created_at": { "type": "string", "format": "date-time", "description": "ÙŠØªØ±Ø¬Ù… Ù„Ù€ created_at_local" }
              }
            }
          },
          "expenses": {
            "type": "array",
            "items": { "$ref": "#/components/schemas/ExpenseSchema" }
          },
          "installments": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "integer" },
                "receipt_id": { "type": "integer" },
                "payment_month": { "type": "integer" },
                "payment_year": { "type": "integer" },
                "amount": { "type": "integer" }
              }
            }
          },
          "branches": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "integer" },
                "name": { "type": "string" }
              }
            }
          },
          "users": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "integer" },
                "name": { "type": "string" },
                "branch_id": { "type": "integer" }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## ðŸ“¢ 7. Ù…ØªØ·Ù„Ø¨Ø§Øª ÙˆØ§Ø¬Ù‡Ø© Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù… ÙˆÙ…Ø²Ø§Ù…Ù†Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ù„Ù„ÙˆØ§Ø¬Ù‡Ø§Øª (React Integration)

Ù„ØªÙØ¹ÙŠÙ„ Ø§Ù„ØªØ±Ø§Ø¨Ø· Ø§Ù„Ø³Ù„Ø³ Ø¨ÙŠÙ† ÙˆØ§Ø¬Ù‡Ø© Ø§Ù„ÙˆÙŠØ¨ ÙˆØ§Ù„Ù€ API:
1. **Ø§Ù„Ø§Ø´ØªØ±Ø§Ùƒ Ø§Ù„Ù…Ù†ØªÙ‡ÙŠ (Subscription Expired):** ÙŠØ¬Ø¨ Ø¹Ù„Ù‰ ØªØ·Ø¨ÙŠÙ‚ React Ø§Ù„ØªÙ‚Ø§Ø· Ø±Ù…Ø² Ø§Ù„Ø®Ø·Ø£ `403 Forbidden` Ø¨Ø±Ø³Ø§Ù„Ø© `"Ø§Ù„Ø§Ø´ØªØ±Ø§Ùƒ Ø§Ù„Ø³Ø­Ø§Ø¨ÙŠ Ø§Ù†ØªÙ‡Ù‰"` ÙˆØªÙˆØ¬ÙŠÙ‡ Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù… Ù…Ø¨Ø§Ø´Ø±Ø© Ù„ØµÙØ­Ø© ØªÙØ¹ÙŠÙ„ Ø¨Ø§Ù‚Ø© Ø§Ù„ØªØ±Ø®ÙŠØµ Ù„Ø¥Ø¯Ø®Ø§Ù„ ÙƒÙˆØ¯ Ø§Ù„Ø´Ø­Ù† Ø§Ù„Ø¬Ø¯ÙŠØ¯.
2. **Ù…Ù†Ø¹ ØªØ¹Ø¯ÙŠÙ„ ØªÙˆØ§Ø±ÙŠØ® Ø§Ù„Ø£Ù‚Ø³Ø§Ø· Ø¨Ø§Ù„ÙˆØ§Ø¬Ù‡Ø©:** ÙŠØ¬Ø¨ Ø¹Ù„Ù‰ ÙˆØ§Ø¬Ù‡Ø© ØªØ¹Ø¯ÙŠÙ„ Ø§Ù„ÙÙˆØ§ØªÙŠØ± ØªØ¹Ø·ÙŠÙ„ Ø£ÙŠ Ø­Ù‚ÙˆÙ„ ØªØ³Ù…Ø­ Ø¨ØªØºÙŠÙŠØ± ØªÙˆØ§Ø±ÙŠØ® Ø§Ù„Ø£Ù‚Ø³Ø§Ø· ÙŠØ¯ÙˆÙŠÙ‹Ø§ØŒ Ø­ÙŠØ« ÙŠÙ‚ÙˆÙ… Ø§Ù„Ø³ÙŠØ±ÙØ± Ø¨Ø­Ø³Ø§Ø¨Ù‡Ø§ ØªÙ„Ù‚Ø§Ø¦ÙŠÙ‹Ø§ Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ ÙŠÙˆÙ… 25 ÙÙŠ Ø§Ù„Ø´Ù‡ÙˆØ± Ø§Ù„Ù…ØªØªØ§Ù„ÙŠØ©.
3. **Ø§Ù„ØªØµÙ…ÙŠÙ… Ø§Ù„Ù…ØªØ¬Ø§ÙˆØ¨ RTL:** Ø¬Ù…ÙŠØ¹ Ø±Ø¯ÙˆØ¯ ÙØ¹Ù„ Ø±Ø³Ø§Ø¦Ù„ Ø§Ù„ØªØ£ÙƒÙŠØ¯ ÙˆØ§Ù„Ø®Ø·Ø£ Ø§Ù„Ù…Ø³ØªÙ„Ù…Ø© Ù…Ù† Ø§Ù„Ù€ API ÙŠØ¬Ø¨ Ø£Ù† ØªÙØ¹Ø±Ø¶ Ø¨Ø§ØªØ¬Ø§Ù‡ Ø§Ù„ÙŠÙ…ÙŠÙ† Ø¥Ù„Ù‰ Ø§Ù„ÙŠØ³Ø§Ø± (Right-to-Left) ÙˆÙ…ØªÙ†Ø§Ø³Ù‚Ø© Ù…Ø¹ Ø§Ù„Ù…ØµØ·Ù„Ø­Ø§Øª Ø§Ù„Ù…Ù‡Ù†ÙŠØ© Ø§Ù„Ù…ØªÙÙ‚ Ø¹Ù„ÙŠÙ‡Ø§ ÙÙŠ Ù…Ø³ØªÙ†Ø¯ Ø§Ù„ØªØµÙ…ÙŠÙ….

