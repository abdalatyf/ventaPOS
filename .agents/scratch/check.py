import os

files = [
    'general_settings.html',
    'manage_branches.html',
    'manage_salespersons.html',
    'manage_expenses.html',
    'import_wizard.html',
    'subscription_dashboard.html'
]

base_dir = r'd:\exe\venta_pos\sales\salesapp\templates\salesapp'
snippets = []

for file in files:
    with open(os.path.join(base_dir, file), 'r', encoding='utf-8') as f:
        content = f.read()
        start = content.find('<ul class=\"nav nav-tabs')
        end = content.find('</ul>', start) + 5
        if start != -1:
            snippets.append(content[start:end])
        else:
            print(f'Nav tabs not found in {file}')
            snippets.append('')

if len(snippets) == len(files):
    first = snippets[0]
    all_match = all(s == first for s in snippets)
    if all_match:
        print('All 6 templates contain the exact same nav-tabs snippet.')
    else:
        print('Mismatch in nav-tabs snippets.')
        for i, s in enumerate(snippets):
            if s != first:
                print(f'Mismatch in {files[i]}')
                # Let s print what is different
                print(s[:100])
