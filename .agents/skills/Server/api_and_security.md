# Server Application - API & Security Memory

This document maps the exact flow of data exchange, network calls, middleware, and security configurations in the VentaPOS Server application.

## 1. Network & API Definitions

### Endpoints Exposed
- **URL**: `/api/v1/sync/push/`
  - **Method**: `POST`
  - **Controller**: `SyncIngestView.as_view()`
  - **Description**: The primary ingestion endpoint for client machines to push their local database state to the centralized server.
- **URL**: `/admin/`
  - **Controller**: Standard Django Admin Site
  - **Description**: Exposes the data viewing and license management portal.

### Routing Hierarchy
1. `server_backend/urls.py`: Mounts `sync_api.urls` to the root `''`.
2. `sync_api/urls.py`: Routes `api/v1/sync/push/` to the class-based view `SyncIngestView`.

## 2. API Contract Expected (JSON Payload)
The `SyncIngestView` expects a root JSON object with two primary keys:
```json
{
  "machine_id": "string (unique hardware footprint)",
  "payload": {
    "company_settings": { ... },
    "branches": [ ... ],
    "salespeople": [ ... ],
    "inventory": [ ... ],
    "receipts": [ 
       { 
         "items": [ ... ],
         "payments": [ ... ] 
       }
    ],
    "expenses": [ ... ],
    "stock_transactions": [ ... ]
  }
}
```

## 3. Security & Access Control

### A. Environment-Level Security (`server_backend/settings.py`)
- **ALLOWED_HOSTS**: Set to `['*']`. This disables standard Django host-header validation to seamlessly support dynamic Ngrok tunnels without constant redeployment.
- **CSRF_TRUSTED_ORIGINS**: Explicitly trusts requests originating from the Ngrok tunnel (`['https://jargonal-colourationally-buddy.ngrok-free.dev']`).

### B. Endpoint-Level Security
- **CSRF Exemption**: `SyncIngestView` is decorated with `@method_decorator(csrf_exempt, name='dispatch')`. Because client POS applications do not manage browser-based CSRF tokens (they are standalone desktop/mobile clients), CSRF validation is disabled for this specific endpoint.

### C. Application-Level Authentication (The Gatekeeper Pattern)
Instead of standard JWT or Session authentication, the application uses a hardware-bound "License" mechanism:
1. Every POST request must include a `machine_id`.
2. The server queries the `ServerLicense` table looking for an exact match where `is_active=True`.
3. **Rejection**: If the machine footprint is unknown, or if an administrator has toggled `is_active=False`, the server hard-rejects the payload with a `403 Forbidden` status.

### Middleware Stack
The standard Django middleware stack is active (Security, Session, Common, CsrfView, Auth, Messages, XFrameOptions), but its strictness is selectively bypassed for the sync endpoint via `csrf_exempt` and dynamic host allowances.
