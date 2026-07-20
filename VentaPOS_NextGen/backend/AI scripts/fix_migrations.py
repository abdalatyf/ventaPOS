import re

def fix():
    filename = 'api/migrations/0001_initial.py'
    with open(filename, 'r', encoding='utf-8') as f:
        c = f.read()

    # Find the corrupted MinValueValidator and replace it
    # We use regex to match anything that looks like Decimal(\0.00\) or similar
    c = re.sub(r'MinValueValidator\(Decimal\([^)]*\)\)', 'MinValueValidator(Decimal("0.00"))', c)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(c)

    print("Fixed migrations!")

fix()
