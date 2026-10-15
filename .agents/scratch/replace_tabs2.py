import os
import re

tpl_dir = r"D:\exe\venta_pos\sales\salesapp\templates\salesapp"
files = ["import_wizard.html"]
replacement = "{% include 'salesapp/partials/_settings_tabs.html' %}"

for f in files:
    path = os.path.join(tpl_dir, f)
    if not os.path.exists(path): continue
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    idx1 = content.find('<ul class="nav nav-tabs')
    if idx1 != -1:
        idx2 = content.find('</ul>', idx1) + 5
        content = content[:idx1] + replacement + content[idx2:]
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"Updated {f} successfully.")
