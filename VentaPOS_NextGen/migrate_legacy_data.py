#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  VentaPOS NextGen - سكريبت نقل البيانات التاريخية (Migration Script)
  Legacy SQLite (salesapp_*) to PostgreSQL (api_*)
=============================================================================
"""
import os
import sys
import sqlite3
import uuid
from datetime import datetime

# إعداد بيئة جانجو للوصول للـ Models الجديدة
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

from api.models import Tenant, Branch, InventoryItem, Salesperson, Receipt, SaleItem

def run_migration(sqlite_path):
    print(f"[*] Starting migration from: {sqlite_path}")
    if not os.path.exists(sqlite_path):
        print("[-] Error: Legacy SQLite database file not found!")
        return

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. تهيئة الـ Tenant الأساسي للبيانات القديمة
    tenant, created = Tenant.objects.get_or_create(
        company_code="LGCY",
        defaults={"name": "Legacy Migrated Tenant", "is_active": True}
    )
    print(f"[+] Tenant secured: {tenant.name} (UUID: {tenant.id})")

    # قواميس لربط الـ IDs القديمة (أرقام) بالـ UUIDs الجديدة
    branch_map = {}
    salesperson_map = {}
    product_map = {}

    # 2. نقل الفروع (Branches)
    try:
        cursor.execute("SELECT * FROM salesapp_branch")
        for row in cursor.fetchall():
            branch = Branch.objects.create(
                tenant=tenant,
                name=row['name'],
                address=row.get('address', ''),
                is_active=True
            )
            branch_map[row['id']] = branch.id
        print(f"[+] Successfully migrated {len(branch_map)} branches.")
    except Exception as e:
        print(f"[-] Branch migration warning: {e}")

    # 3. نقل الموظفين والمندوبين (Salespersons)
    try:
        cursor.execute("SELECT * FROM salesapp_salesperson")
        for row in cursor.fetchall():
            sp = Salesperson.objects.create(
                tenant=tenant,
                name=row['name'],
                branch_id=branch_map.get(row.get('branch_id')),
                is_active=True
            )
            salesperson_map[row['id']] = sp.id
        print(f"[+] Successfully migrated {len(salesperson_map)} salespersons.")
    except Exception as e:
        print(f"[-] Salesperson migration warning: {e}")

    # 4. نقل المخزون والأصناف (Inventory Items) - مع تطبيق قواعد البداية
    try:
        cursor.execute("SELECT * FROM salesapp_inventoryitem")
        count = 0
        for row in cursor.fetchall():
            item = InventoryItem.objects.create(
                tenant=tenant,
                branch_id=branch_map.get(row.get('branch_id')),
                name=row['name'],
                barcode=row.get('barcode', ''),
                initial_quantity=row.get('quantity', 0), # تحويل quantity لـ initial_quantity بناء على الـ Docs
                initial_purchase_price=row.get('purchase_price', 0.0),
                initial_commission_amount=row.get('salesperson_commission_amount', 0.0),
                is_active=True
            )
            product_map[row['id']] = item.id
            count += 1
        print(f"[+] Successfully migrated {count} inventory items.")
    except Exception as e:
        print(f"[-] Inventory migration warning: {e}")

    print("[*] Base Data Migration Completed Successfully! (Phase 1/2)")
    conn.close()

if __name__ == '__main__':
    # مسار قاعدة بيانات SQLite القديمة من الـ Monorepo
    legacy_db = os.path.join(os.path.dirname(__file__), '..', 'Desktop', 'Backup_SalesApp_2026-05-24.sqlite3')
    run_migration(legacy_db)
