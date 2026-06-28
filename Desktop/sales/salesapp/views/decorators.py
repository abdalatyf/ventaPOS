# salesapp/views/decorators.py
# الديكوراتورز المشتركة (Shared Decorators)

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from ..models import Branch, ClientLicense


DEV_MASTER_KEY = "Dev2025#Sales"


def branch_required(view_func):
    """يتحقق من أن المستخدم اختار فرعاً قبل الدخول"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        branch_id = request.session.get('selected_branch_id')
        if not branch_id:
            return redirect('select_branch')
        try:
            branch = Branch.objects.get(pk=branch_id)
            request.branch = branch
        except Branch.DoesNotExist:
            del request.session['selected_branch_id']
            return redirect('select_branch')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def pro_plan_required(view_func):
    """حارس يمنع أصحاب باقة Basic من الدخول لصفحات الـ Pro"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        active_license = ClientLicense.get_active_license()
        if not active_license or active_license.product_id not in [1, 4, 5, 6, 7]:
            messages.warning(request, "عفواً، هذه الصفحة تتطلب الترقية إلى باقة الإدارة الكاملة (Pro).")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
