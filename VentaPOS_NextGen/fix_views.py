import re

with open('backend/api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove specific ViewSets
content = re.sub(r'class TenantViewSet[\s\S]*?(?=class )', '', content)
content = re.sub(r'class CloudUserViewSet[\s\S]*?(?=class )', '', content)
content = re.sub(r'class ActionLogViewSet[\s\S]*?(?=class )', '', content)
content = re.sub(r'class SyncLogViewSet[\s\S]*?(?=class )', '', content)

# 2. Remove TenantFromRequestMixin entirely
content = re.sub(r'class TenantFromRequestMixin:[\s\S]*?(?=class )', '', content)

# 3. Clean SoftDeleteModelViewSet
# Remove ", TenantFromRequestMixin" from class definition
content = re.sub(r'class SoftDeleteModelViewSet\(viewsets\.ModelViewSet, TenantFromRequestMixin\):', 'class SoftDeleteModelViewSet(viewsets.ModelViewSet):', content)

# In get_queryset, remove the tenant filtering block
# We'll just replace the whole get_queryset method inside SoftDeleteModelViewSet to be simple:
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         if not self.request.query_params.get('include_deleted'):
#             queryset = queryset.filter(is_deleted=False)
#         return queryset
old_get_queryset = r'    def get_queryset\(self\):[\s\S]*?return queryset\n'
new_get_queryset = '''    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.query_params.get('include_deleted'):
            queryset = queryset.filter(is_deleted=False)
        return queryset
'''
# Only replace the first occurrence (which is inside SoftDeleteModelViewSet)
content = re.sub(old_get_queryset, new_get_queryset, content, count=1)

# In perform_create, remove tenant injection
# Replace:
#     def perform_create(self, serializer):
#         # Inject tenant if the serializer has it, and it's not already provided
#         if hasattr(self.request, 'tenant') and self.request.tenant:
#             serializer.save(tenant=self.request.tenant)
#         else:
#             serializer.save()
old_perform_create = r'    def perform_create\(self, serializer\):[\s\S]*?serializer\.save\(\)\n'
new_perform_create = '''    def perform_create(self, serializer):
        serializer.save()
'''
content = re.sub(old_perform_create, new_perform_create, content, count=1)

# 4. Remove all remaining occurrences of 'tenant=self.request.tenant'
content = content.replace('tenant=self.request.tenant, ', '')
content = content.replace(', tenant=self.request.tenant', '')
content = content.replace('tenant=self.request.tenant', '')

# 5. Remove 'tenant = Tenant.objects.filter(is_deleted=False).first()' and similar blocks in custom views
content = re.sub(r'[ \t]*tenant = Tenant\.objects\.filter\(is_deleted=False\)\.first\(\)\n', '', content)
content = re.sub(r'[ \t]*tenant = Tenant\.objects\.using\("default"\)\.first\(\)\n', '', content)

# Remove 'if Tenant.objects.filter(is_deleted=False).exists() and...'
# We'll let `python manage.py check` or tests tell us where the manual syntax errors are left over.

with open('backend/api/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Views updated.")
