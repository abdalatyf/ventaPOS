import requests
import json

url = 'http://localhost:8000/api/v1/receipts/'
# Get the first receipt
r = requests.get(url, params={'limit': 1})
if r.status_code == 200:
    receipts = r.json().get('results', [])
    if receipts:
        first = receipts[0]
        r_id = first['id']
        print(f"Editing receipt: {r_id}")
        put_url = f"{url}{r_id}/"
        payload = {
            "customer_name": first["customer_name"],
            "sale_month": first["sale_month"],
            "sale_year": first["sale_year"],
            "sale_items": first["sale_items"]
        }
        res = requests.put(put_url, json=payload)
        print(res.status_code)
        print(res.text)
    else:
        print("No receipts")
else:
    print(r.status_code, r.text)
