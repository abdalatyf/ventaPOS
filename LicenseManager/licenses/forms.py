from django import forms
from .models import Client, License

# تصميم موحد لكل الحقول
class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control form-control-lg'})

class ClientForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'phone', 'store_name', 'machine_id', 'is_banned']
        widgets = {
            'is_banned': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 25px; height: 25px;'}),
        }

class LicenseForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = License
        fields = ['client', 'product_id', 'price', 'start_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}), # يظهر تقويم لاختيار التاريخ
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    # ترتيب العملاء من الأحدث للأقدم لتسهيل الاختيار
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.order_by('-created_at')