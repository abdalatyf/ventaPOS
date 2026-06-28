import re
import sys

files = ['general_settings.html', 'manage_branches.html', 'manage_salespersons.html', 'manage_expenses.html', 'import_wizard.html', 'subscription_dashboard.html']
snippets = []

for f in files:
    with open(f, 'r', encoding='utf-8') as fp:
        content = fp.read()
    match = re.search(r'<ul class="nav nav-tabs.*?</ul\>', content, re.DOTALL)
    if match:
        snippets.append(match.group(0))
    else:
        print(f + ' missing snippet')

if len(set(snippets)) == 1:
    print('All snippets are identical!')
else:
    print('Snippets are NOT identical!')
    for i, s in enumerate(snippets):
        print(f"--- Snippet {i+1} length: {len(s)}")
