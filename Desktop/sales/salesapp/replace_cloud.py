import os

dir_path = r'D:\Projects\VentaPOS\Desktop\sales\salesapp\templates\salesapp'
words = ['سحابة', 'سحابي', 'السحابة', 'السحابي']

for filename in os.listdir(dir_path):
    if not filename.endswith('.html'): continue
    filepath = os.path.join(dir_path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    found = False
    for w in words:
        if w in content: found = True
    
    if found:
        print(f'\n--- {filename} ---')
        for i, line in enumerate(content.splitlines()):
            for w in words:
                if w in line:
                    print(f'{i+1}: {line.strip()}')
                    break
