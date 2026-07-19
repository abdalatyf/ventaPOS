import re

with open('backend/api/tools_views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove ActionLog and Tenant from imports
content = content.replace('ActionLog, ', '')
content = content.replace('Tenant', '')
content = content.replace('Branch, \n', 'Branch\n')
content = content.replace(', \n)', '\n)')

# 2. Rewrite ToolsBaseView
old_tools_base = r'class ToolsBaseView\(APIView\):[\s\S]*?return super\(\)\.dispatch\(request, \*args, \*\*kwargs\)'
new_tools_base = '''class ToolsBaseView(APIView):
    permission_classes = [IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        from .models import Branch
        branch = Branch.objects.filter(is_deleted=False).first()
        request.branch = branch
        return super().dispatch(request, *args, **kwargs)'''

content = re.sub(old_tools_base, new_tools_base, content, count=1)

# 3. Clean up tenant references
content = content.replace('tenant=self.request.tenant, ', '')
content = content.replace(', tenant=self.request.tenant', '')
content = content.replace('tenant=self.request.tenant', '')
content = content.replace('tenant=request.tenant, ', '')
content = content.replace(', tenant=request.tenant', '')
content = content.replace('tenant=request.tenant', '')

with open('backend/api/tools_views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Tools views updated.")
