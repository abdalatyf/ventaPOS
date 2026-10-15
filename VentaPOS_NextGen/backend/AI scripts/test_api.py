import requests
headers = {
    'company-code': '1234',
    'machine-id': 'DEV-MACHINE-001'
}
res = requests.get('http://127.0.0.1:8000/api/v1/default-date/?branch_id=63b94665-6653-4c0f-97f4-38596bd89c84', headers=headers)
print("Status:", res.status_code)
print("Text:", res.text[:200])
