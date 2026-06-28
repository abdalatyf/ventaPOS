# VentaPOS API Contract (Mobile Sync & Manager Dashboard)

This document defines the OpenAPI 3.1 specifications for the new Mobile endpoints added in Phase 2.

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "VentaPOS Sync API",
    "version": "1.0.0",
    "description": "API definition for Mobile App sync, pending receipts ingestion, and Manager Dashboard."
  },
  "paths": {
    "/api/branches/": {
      "get": {
        "summary": "List all branches",
        "responses": { "200": { "description": "Success" } }
      },
      "post": {
        "summary": "Create a new branch",
        "responses": { "201": { "description": "Created" } }
      }
    },
    "/api/branches/{id}/": {
      "get": {
        "summary": "Get branch details",
        "responses": { "200": { "description": "Success" } }
      },
      "put": {
        "summary": "Update branch",
        "responses": { "200": { "description": "Updated" } }
      },
      "delete": {
        "summary": "Delete branch",
        "responses": { "204": { "description": "Deleted" } }
      }
    },
    "/api/salespeople/": {
      "get": {
        "summary": "List all salespeople",
        "responses": { "200": { "description": "Success" } }
      },
      "post": {
        "summary": "Create a new salesperson",
        "responses": { "201": { "description": "Created" } }
      }
    },
    "/api/salespeople/{id}/": {
      "get": {
        "summary": "Get salesperson details",
        "responses": { "200": { "description": "Success" } }
      },
      "put": {
        "summary": "Update salesperson",
        "responses": { "200": { "description": "Updated" } }
      },
      "delete": {
        "summary": "Delete salesperson",
        "responses": { "204": { "description": "Deleted" } }
      }
    },
    "/api/v1/sync/mobile-push/": {
      "post": {
        "summary": "Push new receipts and pending items from Mobile",
        "description": "Receives receipts and stages them as 'Pending' (is_confirmed = False) for the Desktop to approve.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "machine_id": {
                    "type": "string"
                  },
                  "payload": {
                    "type": "object",
                    "properties": {
                      "receipts": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "receipt_hash": { "type": "string" },
                            "local_id": { "type": "integer" },
                            "receipt_number": { "type": "integer" },
                            "branch_id": { "type": "integer" },
                            "salesperson_id": { "type": "integer" },
                            "customer_name": { "type": "string" },
                            "phone_number": { "type": "string" },
                            "address": { "type": "string" },
                            "area": { "type": "string" },
                            "total_amount": { "type": "number" },
                            "down_payment": { "type": "number" },
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
                                  "price": { "type": "number" }
                                }
                              }
                            },
                            "installments": {
                              "type": "array",
                              "items": {
                                "type": "object",
                                "properties": {
                                  "payment_date": { "type": "string", "format": "date" },
                                  "amount": { "type": "number" }
                                }
                              }
                            }
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
          "200": {
            "description": "Success",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "message": { "type": "string", "example": "Cloud Viewer push data received and staged." },
                    "synced_receipt_ids": {
                      "type": "array",
                      "items": { "type": "integer" },
                      "description": "List of local_ids that were successfully saved as pending on the server"
                    }
                  }
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sync/manager-dashboard/": {
      "get": {
        "summary": "Get Manager Dashboard Metrics",
        "description": "Calculates Net Cash, Estimated Profit, and Top Products for the current machine ID.",
        "parameters": [
          {
            "name": "machine_id",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Success",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "dashboard": {
                      "type": "object",
                      "properties": {
                        "net_cash": { "type": "number", "example": 15000.5 },
                        "estimated_profit": { "type": "number", "example": 4500.0 },
                        "top_products": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "properties": {
                              "product_name": { "type": "string", "example": "Laptop ABC" },
                              "quantity_sold": { "type": "integer", "example": 25 }
                            }
                          }
                        }
                      }
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
    "/api/v1/inventory-items/{id}/ledger/": {
      "get": {
        "summary": "Product Ledger & Financial Analysis",
        "description": "Returns Stock Movements and Financial Analysis for a specific inventory item.",
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "integer"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Success",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "stock_movements": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "type": { "type": "string" },
                          "year": { "type": "integer" },
                          "month": { "type": "integer" },
                          "quantity": { "type": "integer" },
                          "price": { "type": "number" },
                          "description": { "type": "string" },
                          "invoice_number": { "type": "integer" },
                          "supplier": { "type": "string" },
                          "receipt_number": { "type": "integer" },
                          "is_cash_sale": { "type": "boolean" }
                        }
                      }
                    },
                    "financial_analysis": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "year": { "type": "integer" },
                          "month": { "type": "integer" },
                          "cash_sales_revenue": { "type": "number" },
                          "cash_profit": { "type": "number" },
                          "installment_sales_revenue": { "type": "number" },
                          "installment_profit": { "type": "number" },
                          "commission_expenses": { "type": "number" },
                          "units_sold": { "type": "integer" }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```
