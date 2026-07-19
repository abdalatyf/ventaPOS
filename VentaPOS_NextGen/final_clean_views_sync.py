import re

with open('backend/api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove ViewerAuthView
content = re.sub(r'^class ViewerAuthView[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)
# 2. Remove SyncPushView
content = re.sub(r'^class SyncPushView[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)
# 3. Remove SyncPullView
content = re.sub(r'^class SyncPullView[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)
# 4. Remove ConfirmReceiptsView
content = re.sub(r'^class ConfirmReceiptsView[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)

# 5. Remove X-Company-Code and company_code checks from LicenseStatusView
content = re.sub(r'[ \t]*company_code = request\.headers\.get\("X-Company-Code", ""\)\.strip\(\)\n', '', content)
content = re.sub(r'[ \t]*if not company_code:\n[ \t]*return Response\([^)]+\)\n', '', content)

with open('backend/api/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed cloud sync endpoints and X-Company-Code checks.")
