import os
import io

dir_path = r'D:\Projects\VentaPOS\Desktop\sales\salesapp\templates\salesapp'
replacements = [
    ('\u0627\u0644\u0633\u062d\u0627\u0628\u064a', '\u0623\u0648\u0646\u0644\u0627\u064a\u0646'),
    ('\u0633\u062d\u0627\u0628\u064a', '\u0623\u0648\u0646\u0644\u0627\u064a\u0646'),
    ('\u0627\u0644\u0633\u062d\u0627\u0628\u0629', '\u0627\u0644\u0623\u0648\u0646\u0644\u0627\u064a\u0646'),
    ('\u0633\u062d\u0627\u0628\u0629', '\u0623\u0648\u0646\u0644\u0627\u064a\u0646'),
]

for filename in os.listdir(dir_path):
    if not filename.endswith('.html'): continue
    filepath = os.path.join(dir_path, filename)
    with io.open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for old, new in replacements:
        content = content.replace(old, new)
        
    if content != original_content:
        with io.open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Replaced in {filename}')
