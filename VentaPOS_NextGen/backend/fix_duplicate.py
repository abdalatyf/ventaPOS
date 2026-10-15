import os

views_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\views.py"
with open(views_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.startswith("def build_date_range_q("):
        skip = True
    
    if not skip:
        new_lines.append(line)
        
    if skip and line.strip() == "return q_start | q_mid | q_end":
        skip = False

with open(views_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
