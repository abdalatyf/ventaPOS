import re

with open('backend/api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove specific ViewSets safely
# Use ^class to only match class at the start of a line.
content = re.sub(r'^class TenantViewSet[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)
content = re.sub(r'^class CloudUserViewSet[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)
content = re.sub(r'^class ActionLogViewSet[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)
content = re.sub(r'^class SyncLogViewSet[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)

# 2. Remove TenantFromRequestMixin entirely
content = re.sub(r'^class TenantFromRequestMixin:[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)

# 3. Clean SoftDeleteModelViewSet
content = content.replace('class SoftDeleteModelViewSet(viewsets.ModelViewSet, TenantFromRequestMixin):', 'class SoftDeleteModelViewSet(viewsets.ModelViewSet):')

old_get_queryset = r'    def get_queryset\(self\):[\s\S]*?return queryset\n'
new_get_queryset = '''    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.query_params.get('include_deleted'):
            queryset = queryset.filter(is_deleted=False)
        return queryset
'''
content = re.sub(old_get_queryset, new_get_queryset, content, count=1)

old_perform_create = r'    def perform_create\(self, serializer\):[\s\S]*?serializer\.save\(\)\n'
new_perform_create = '''    def perform_create(self, serializer):
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError
        try:
            serializer.save()
        except IntegrityError as e:
            print(f"IntegrityError in perform_create: {e}")
            if "UNIQUE constraint failed" in str(e):
                raise ValidationError({"name": ["الاسم ده متسجل قبل كده، أو موجود في سلة المهملات."]})
            raise ValidationError({"error": [f"حدث خطأ في قاعدة البيانات: {e}"]})
'''
content = re.sub(old_perform_create, new_perform_create, content, count=1)

old_create = r'    def create\(self, request, \*args, \*\*kwargs\):[\s\S]*?return Response\(serializer\.data, status=status\.HTTP_201_CREATED, headers=headers\)'
new_create = '''    def create(self, request, *args, **kwargs):
        """Auto-fill branch if missing."""
        from api.models import Branch
        if isinstance(request.data, dict) or hasattr(request.data, 'copy'):
            data = request.data.copy()
            if 'branch' not in data:
                branch = None
                if request.headers.get("X-Branch-ID"):
                    branch = Branch.objects.filter(id=request.headers.get("X-Branch-ID"), is_deleted=False).first()
                if not branch:
                    branch = Branch.objects.filter(is_deleted=False).first()
                if branch:
                    data['branch'] = branch.id
        else:
            data = request.data
            
        from rest_framework.response import Response
        from rest_framework import status
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)'''
content = re.sub(old_create, new_create, content, count=1)

# Remove `_fill_local_data` entirely
content = re.sub(r'    def _fill_local_data[\s\S]*?(?=    def perform_create)', '', content)

# 4. Clean up the rest of the file
# Remove TenantFromRequestMixin inheritance
content = content.replace('(TenantFromRequestMixin, SoftDeleteModelViewSet)', '(SoftDeleteModelViewSet)')
content = content.replace('(TenantFromRequestMixin, viewsets.ModelViewSet)', '(viewsets.ModelViewSet)')
content = content.replace('(TenantFromRequestMixin, ', '(')

# Remove select_related("tenant") and prefetch_related("tenant")
content = content.replace('.select_related("tenant")', '')
content = content.replace('.prefetch_related("tenant")', '')
content = content.replace('.select_related("tenant", "branch")', '.select_related("branch")')
content = content.replace(', "tenant"', '')
content = content.replace('"tenant", ', '')

# Remove manual tenant passing in views
content = re.sub(r',\s*tenant=tenant', '', content)
content = re.sub(r'tenant=tenant,\s*', '', content)
content = content.replace('tenant=self.request.tenant, ', '')
content = content.replace(', tenant=self.request.tenant', '')
content = content.replace('tenant=self.request.tenant', '')
content = re.sub(r'[ \t]*tenant = Tenant\.objects\.filter\(is_deleted=False\)\.first\(\)\n', '', content)
content = re.sub(r'[ \t]*tenant = Tenant\.objects\.using\("default"\)\.first\(\)\n', '', content)
content = re.sub(r'[ \t]*tenant = Tenant\.objects\.first\(\)\n', '', content)
content = re.sub(r'[ \t]*tenant = Tenant\.objects\.using\("default"\)\.create\(company_code="TEST", name="Test Tenant"\)\n', '', content)

with open('backend/api/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Views rewritten safely.")
