"""
Expense Views for VentaPOS NextGen:
ExpenseViewSet.
"""
from api.models import Expense
from api.serializers import ExpenseSerializer
from .base import SoftDeleteModelViewSet, to_english_numerals, get_request_branch_id


class ExpenseViewSet(SoftDeleteModelViewSet):
    queryset = Expense.objects.select_related("branch").all()
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if branch_id := get_request_branch_id(self.request):
            qs = qs.filter(branch_id=branch_id)
        if year := params.get("year"):
            clean_year = to_english_numerals(str(year).strip())
            try:
                qs = qs.filter(expense_year=int(clean_year))
            except ValueError:
                pass
        if month := params.get("month"):
            clean_month = to_english_numerals(str(month).strip())
            try:
                qs = qs.filter(expense_month=int(clean_month))
            except ValueError:
                pass
        if desc := params.get("description"):
            if str(desc).strip():
                qs = qs.filter(description__icontains=str(desc).strip())
        if category := params.get("category"):
            if str(category).strip():
                qs = qs.filter(category__icontains=str(category).strip())
        if amount_min := (params.get("amount_min") or params.get("amount_from")):
            if str(amount_min).strip():
                clean_min = to_english_numerals(str(amount_min).strip())
                try:
                    qs = qs.filter(amount__gte=float(clean_min))
                except ValueError:
                    pass
        if amount_max := (params.get("amount_max") or params.get("amount_to")):
            if str(amount_max).strip():
                clean_max = to_english_numerals(str(amount_max).strip())
                try:
                    qs = qs.filter(amount__lte=float(clean_max))
                except ValueError:
                    pass
        return qs
