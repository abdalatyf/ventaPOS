# VentaPOS Mobile - Database & Sync Plan

This document establishes the SQLite offline database schema upgrades required to support Manager-level modifications. It acts as the absolute Single Source of Truth for the Mobile App's SQLite layer, documented in strict **SQL DDL**.

## 1. Schema Upgrades (SQL DDL)

To support offline staging and sync conflict resolution, the following schema additions must be executed via the local Flutter SQLite migration engine:

```sql
-- 1. Extend the Inventory table to track unconfirmed offline products
ALTER TABLE inventory 
ADD COLUMN is_confirmed_by_desktop BOOLEAN NOT NULL DEFAULT 1;

ALTER TABLE inventory 
ADD COLUMN local_sync_action TEXT DEFAULT NULL; -- 'CREATE', 'UPDATE', 'DELETE'

-- 2. Extend the Users table to track salesperson modifications
ALTER TABLE users 
ADD COLUMN is_synced BOOLEAN NOT NULL DEFAULT 1;

ALTER TABLE users 
ADD COLUMN local_sync_action TEXT DEFAULT NULL;

-- 3. Extend the Config table to store the active User Role
ALTER TABLE config 
ADD COLUMN active_role TEXT DEFAULT 'SALESPERSON'; -- 'MANAGER' or 'SALESPERSON'
```

## 2. Sync State Management

For complex objects or receipts, the existing `pending_sync_states` table is utilized. If a Manager modifies a product or user offline, the app performs a two-step local commit:
1. Update the actual table (`inventory` or `users`) and set `is_synced = 0` / `local_sync_action = 'UPDATE'`.
2. Insert a serialized snapshot into `pending_sync_states` for the background worker to consume.

```sql
CREATE TABLE IF NOT EXISTS pending_sync_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL, -- 'PRODUCT', 'USER', 'SETTINGS', 'RECEIPT'
    entity_local_id INTEGER NOT NULL,
    action TEXT NOT NULL, -- 'CREATE', 'UPDATE', 'DELETE'
    payload_json TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    last_error TEXT
);
```

## 3. Background Sync Engine Flow

The background sync engine runs every 60 seconds while the app is active, executing the following logic:

1. **Query Pending:** `SELECT * FROM pending_sync_states WHERE retry_count < 5;`
2. **Batch:** Aggregate the rows into the `products`, `users`, and `settings` arrays defined in the OpenAPI contract.
3. **Push:** POST the payload to `/api/v1/sync/admin-push/`.
4. **On Success (HTTP 200):**
    *   DELETE the successfully synced rows from `pending_sync_states`.
    *   UPDATE `inventory` SET `is_confirmed_by_desktop = 1`, `local_sync_action = NULL`.
    *   UPDATE `users` SET `is_synced = 1`, `local_sync_action = NULL`.
5. **On Failure:**
    *   Increment `retry_count` and log the `last_error`.
