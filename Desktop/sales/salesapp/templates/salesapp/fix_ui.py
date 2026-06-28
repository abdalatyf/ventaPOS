import os
import glob

# Files that need mojibake fix (untracked ones)
untracked = [
    'edit_pending_receipt.html',
    'pending_receipts.html',
    'invoices_report.html',
    'manage_devices.html'
]

# All template files
files = glob.glob('*.html')

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            
        if f in untracked and 'Ã˜' in content or 'Ø' in content:
            # Reverse Mojibake
            print(f'Fixing Mojibake in {f}')
            try:
                content = content.encode('cp1252').decode('utf-8')
            except Exception as e:
                print('Mojibake fix failed:', e)

        # Apply Tabler Classes safely
        content = content.replace('class="card shadow-sm mb-4"', 'class="card card-sm border-0 shadow-sm mb-4"')
        content = content.replace('class="card shadow-sm border-0"', 'class="card card-sm border-0 shadow-sm"')
        content = content.replace('class="card shadow-sm"', 'class="card card-sm border-0 shadow-sm"')
        content = content.replace('class="card shadow mb-4"', 'class="card card-sm border-0 shadow-sm mb-4"')
        
        # Don't overwrite existing bg-primary etc
        content = content.replace('class="card-header"', 'class="card-header bg-primary text-white"')
        content = content.replace('class="card-header py-3"', 'class="card-header bg-primary text-white py-3"')
        
        content = content.replace('class="table table-bordered table-sm"', 'class="table table-vcenter card-table table-striped"')
        content = content.replace('class="table table-hover align-middle mb-0"', 'class="table table-vcenter card-table table-striped"')
        content = content.replace('class="table table-bordered table-hover"', 'class="table table-vcenter card-table table-striped"')
        content = content.replace('class="table table-bordered"', 'class="table table-vcenter card-table table-striped"')
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
            
    except Exception as e:
        print(f'Error processing {f}: {e}')
