# VentaPOS Server - Admin Sync API Contract

This document defines the RESTful API endpoints required to support the new Manager-level admin features from the Mobile App. The API is documented in strict OpenAPI 3.1 JSON format.

## Architectural Notes
1. **Authentication:** All requests MUST include `company_code` and `machine_id`. The server validates that the `machine_id` is tied to an active Manager/CloudUser account, NOT a Salesperson account.
2. **Offline Resilience:** Because the mobile app works offline, the endpoints accept a `last_modified` timestamp from the mobile device to handle conflict resolution.

## OpenAPI Specification

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "VentaPOS Admin Sync API",
    "version": "1.0.0",
    "description": "Endpoints allowing Manager-level Mobile Apps to sync administrative changes (Products, Users, Settings) back to the central server."
  },
  "paths": {
    "/api/v1/sync/admin-push/": {
      "post": {
        "summary": "Unified Admin Sync Push",
        "operationId": "syncAdminPush",
        "description": "A single unified endpoint to sync Products, Users, and Settings in one transaction, preventing partial failures and reducing HTTP overhead.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["company_code", "machine_id", "payload"],
                "properties": {
                  "company_code": { "type": "string", "example": "VTS-1029" },
                  "machine_id": { "type": "string", "example": "UUID-DEVICE-MANAGER" },
                  "payload": {
                    "type": "object",
                    "properties": {
                      "products": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "local_id": { "type": "integer" },
                            "name": { "type": "string" },
                            "initial_quantity": { "type": "integer" },
                            "initial_purchase_price": { "type": "number" },
                            "action": { "type": "string", "enum": ["CREATE", "UPDATE", "DELETE"] }
                          }
                        }
                      },
                      "users": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "local_id": { "type": "integer" },
                            "name": { "type": "string" },
                            "branch_id": { "type": "integer" },
                            "offline_pin": { "type": "string" },
                            "action": { "type": "string", "enum": ["CREATE", "UPDATE", "DELETE"] }
                          }
                        }
                      },
                      "settings": {
                        "type": "object",
                        "properties": {
                          "company_name": { "type": "string" },
                          "footer_text": { "type": "string" }
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
          "200": {
            "description": "All admin entities synced successfully",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "synced_products": { "type": "array", "items": { "type": "integer" } },
                    "synced_users": { "type": "array", "items": { "type": "integer" } }
                  }
                }
              }
            }
          },
          "403": { "description": "Forbidden. Machine ID does not belong to a Manager." }
        }
      }
    }
  }
}
```
