from django import forms
from django.contrib.auth.forms import AuthenticationForm

# 1. فورم تسجيل الدخول العادي (معدل ليقبل تنسيق البوتستراب)
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'اسم المستخدم', 'autofocus': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'كلمة المرور'
    }))

# 2. فورم الطوارئ (المفتاح الماستر)
class EmergencyResetForm(forms.Form):
    master_key = forms.CharField(
        label="كود الطوارئ لمرة واحدة",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'أدخل كود الطوارئ'})
    )
    new_username = forms.CharField(
        label="اسم المستخدم الجديد",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'admin'})
    )
    new_password = forms.CharField(
        label="كلمة المرور الجديدة",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'كلمة المرور الجديدة'})
    )

from .models import CompanySetting # تأكد من استدعاء الموديل

class CompanyProtectedForm(forms.ModelForm):
    class Meta:
        model = CompanySetting
        fields = ['name', 'phone1', 'phone2']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone1': forms.TextInput(attrs={'class': 'form-control'}),
            'phone2': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CompanyFreeForm(forms.ModelForm):
    class Meta:
        model = CompanySetting
        fields = ['description', 'footer_text']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: تجارة الأدوات الكهربائية'}),
            'footer_text': forms.TextInput(attrs={'class': 'form-control'}),
        }

# في forms.py

class SetupCombinedForm(forms.ModelForm):
    # حقول إضافية للمدير (غير موجودة في موديل الشركة)
    username = forms.CharField(label="اسم المستخدم (للمدير)", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'admin'}))
    password = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(label="تأكيد كلمة المرور", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    branch_name = forms.CharField(label="اسم الفرع الرئيسي", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الفرع الرئيسي'}))

    class Meta:
        model = CompanySetting
        # لاحظ أننا حذفنا الشعار logo
        fields = ['name', 'phone1', 'phone2']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),     
            'phone1': forms.TextInput(attrs={'class': 'form-control'}),
            'phone2': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("كلمتا المرور غير متطابقتين!")
        return cleaned_data