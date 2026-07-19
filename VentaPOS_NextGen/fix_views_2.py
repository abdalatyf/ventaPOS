import re

with open('backend/api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Clean up the mangled broken lines 359-367 from previous regex
content = re.sub(r'class = TenantSerializer[\s\S]*?class = CloudUserSerializer\s*', '', content)

# 2. Remove TenantFromRequestMixin from all ViewSet definitions
# e.g., class BranchViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
content = content.replace('(TenantFromRequestMixin, SoftDeleteModelViewSet)', '(SoftDeleteModelViewSet)')
content = content.replace('(TenantFromRequestMixin, viewsets.ModelViewSet)', '(viewsets.ModelViewSet)')
content = content.replace('(TenantFromRequestMixin, ', '(')

# 3. Remove .select_related("tenant") and .prefetch_related("tenant")
content = content.replace('.select_related("tenant")', '')
content = content.replace('.prefetch_related("tenant")', '')

# 4. Remove occurrences of `tenant=tenant` or similar left behind in querysets or dicts
content = re.sub(r',\s*tenant=tenant', '', content)
content = re.sub(r'tenant=tenant,\s*', '', content)

with open('backend/api/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Views cleaned again.")
