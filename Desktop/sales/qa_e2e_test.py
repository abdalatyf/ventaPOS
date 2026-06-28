import requests
import json
import uuid

SERVER_URL = "https://jargonal-colourationally-buddy.ngrok-free.dev"
MACHINE_ID = "E2E_QA_MACHINE_123"

def print_result(step, response):
    print(f"--- {step} ---")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response (text): {response.text[:200]}")
    print()

print("Starting E2E QA Hybrid Cloud Tests via ngrok...")

# 1. Test Sync Push (Simulate Two-Way Sync Push from Viewer)
payload = {
    'machine_id': MACHINE_ID,
    'payload': {
        'company_settings': {'name': 'QA Test Company'},
        'receipts': [
            {
                'receipt_hash': str(uuid.uuid4()),
                'id': 999,
                'receipt_number': 9001,
                'branch_id': 1,
                'total_amount': 500,
                'down_payment': 0,
                'sale_year': 2026,
                'sale_month': 6,
                'is_cash_sale': True,
                'items': []
            }
        ]
    }
}

try:
    print("Testing Two-Way Sync (Push to Central Server via ngrok)...")
    res = requests.post(f"{SERVER_URL}/api/v1/sync/push/", json=payload, timeout=10)
    print_result("Sync Push", res)

    # 2. Test Lockout / Auth (Download Setup)
    print("Testing Initial Sync / Authentication (Pull from Central Server via ngrok)...")
    res2 = requests.get(f"{SERVER_URL}/api/v1/sync/download-setup/?token=INVALID_TOKEN", timeout=10)
    print_result("Download Setup (Invalid Auth)", res2)

except Exception as e:
    print(f"Connection error: {e}")
