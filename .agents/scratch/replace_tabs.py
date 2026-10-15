import os
import re

tpl_dir = r"D:\exe\venta_pos\sales\salesapp\templates\salesapp"

settings_files = [
    "general_settings.html",
    "manage_branches.html",
    "manage_salespersons.html",
    "manage_expenses.html",
    "smart_import_wizard.html",
    "subscription_dashboard.html"
]

inventory_files = [
    "manage_products.html",
    "manage_suppliers.html",
    "manage_purchase_invoices.html",
    "search_purchase_invoices.html"
]

def replace_tabs(files, replacement):
    for f in files:
        path = os.path.join(tpl_dir, f)
        if not os.path.exists(path):
            print(f"Skipping {f}, not found.")
            continue
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        
        # We will use string.find to find <ul class="nav nav-tabs
        # and string.find to find </ul>
        idx1 = content.find('<ul class="nav nav-tabs')
        if idx1 != -1:
            idx2 = content.find('</ul>', idx1)
            if idx2 != -1:
                idx2 += 5
                old_content = content[idx1:idx2]
                content = content[:idx1] + replacement + content[idx2:]
                with open(path, "w", encoding="utf-8") as file:
                    file.write(content)
                print(f"Updated {f} successfully.")
            else:
                print(f"Failed to find </ul> in {f}")
        else:
            print(f"Failed to find <ul class=\"nav nav-tabs in {f}")

replace_tabs(settings_files, "{% include 'salesapp/partials/_settings_tabs.html' %}")
replace_tabs(inventory_files, "{% include 'salesapp/partials/_inventory_tabs.html' %}")
