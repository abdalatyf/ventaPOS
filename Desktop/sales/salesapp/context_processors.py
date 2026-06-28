from .models import ClientLicense

def license_plan_context(request):
    is_pro_plan = False
    
    if request.user.is_authenticated:
        active_license = ClientLicense.get_active_license()
        if active_license:
            # 1: Trial, 4: Pro 1Y, 5: Pro 3Y, 6: Pro 5Y, 7: Lifetime Pro
            if active_license.product_id in [1, 4, 5, 6, 7]:
                is_pro_plan = True
                
    return {
        'is_pro_plan': is_pro_plan
    }


# W9GG-3V8Q-XMB3-99DG
# 7DFA-ZTC4-MLU8-8TL8