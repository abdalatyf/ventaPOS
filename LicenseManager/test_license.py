import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from licenses.utils.crypto import LicenseGenerator

def test_my_code():
    print("--- License Verification Tool ---")
    
    # 1. Default Data
    my_machine_id = "DISK-5822-S9J1"  # Same Machine ID used for the client
    
    # Enter one of the generated codes
    code_to_test = input("Enter License Code (xxxx-xxxx...): ")

    print(f"\nValidating code for Machine ID: {my_machine_id}...")
    
    # Call validation function
    result = LicenseGenerator.validate(code_to_test, my_machine_id)

    if result["valid"]:
        print("✅ VALID LICENSE!")
        print(f"📦 Product ID: {result['product_id']}")
        print(f"📅 Start Date: {result['start_month']}/{result['start_year']}")
    else:
        print("❌ INVALID LICENSE!")
        # Note: The error text itself comes from crypto.py (might be in Arabic if not changed there)
        print(f"Reason: {result['error']}")

if __name__ == "__main__":
    test_my_code()