import sys

def fix_file(filename):
    with open(filename, 'r', encoding='utf8') as f:
        c = f.read()
    
    print("File " + filename + ":")
    print("  Count double quotes: " + str(c.count('MinValueValidator("0.00")')))
    print("  Count single quotes: " + str(c.count("MinValueValidator('0.00')")))
    
    new_c = c.replace('MinValueValidator("0.00")', 'MinValueValidator(Decimal("0.00"))')
    new_c = new_c.replace("MinValueValidator('0.00')", 'MinValueValidator(Decimal("0.00"))')
    
    if new_c != c:
        if 'from decimal import Decimal' not in new_c:
            new_c = 'from decimal import Decimal\n' + new_c
        with open(filename, 'w', encoding='utf8') as f:
            f.write(new_c)
        print('  -> Fixed ' + filename)

fix_file('api/models.py')
fix_file('api/migrations/0001_initial.py')
