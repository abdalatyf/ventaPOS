import os

dir_path = r'D:\Projects\VentaPOS\Desktop\sales\salesapp\templates\salesapp'
replacements = [
    ('السحابي', 'أونلاين'),
    ('سحابي', 'أونلاين'),
    ('السحابة', 'الأونلاين'),
    ('سحابة', 'أونلاين'),
]

for filename in os.listdir(dir_path):
    if not filename.endswith('.html'): continue
    filepath = os.path.join(dir_path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for old, new in replacements:
        content = content.replace(old, new)
        
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Replaced in {filename}')
