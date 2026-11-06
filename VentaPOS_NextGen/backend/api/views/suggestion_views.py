"""
Suggestion and Autocomplete Views for VentaPOS NextGen:
CustomerSuggestionsView, ProductSuggestionsView.
"""
from django.db.models import Case, When, IntegerField, Q
from rest_framework import views
from rest_framework.response import Response

from api.models import Receipt, InventoryItem
from api.services.stock_service import calculate_bulk_stock_timeline
from .base import to_english_numerals, resolve_salesperson_id, get_default_date, get_request_branch_id


class CustomerSuggestionsView(views.APIView):
    def get(self, request):
        term = to_english_numerals(request.query_params.get("term", "").strip())
        field = request.query_params.get("field", "").strip()
        salesperson_id = to_english_numerals(request.query_params.get("salesperson_id", "").strip())
        current_area = to_english_numerals(request.query_params.get("current_area", "").strip())
        current_name = to_english_numerals(request.query_params.get("current_name", "").strip())
        branch_id = get_request_branch_id(request)

        if field not in ['name', 'phone', 'address', 'area']:
            return Response([])

        receipts_qs = Receipt.objects.filter(is_deleted=False)
        if branch_id:
            receipts_qs = receipts_qs.filter(branch_id=branch_id)

        if field == 'area':
            receipts_qs = receipts_qs.filter(area__icontains=term).exclude(area='').exclude(area__isnull=True)
        elif field == 'name':
            receipts_qs = receipts_qs.filter(customer_name__icontains=term)
        elif field == 'address':
            receipts_qs = receipts_qs.filter(address__icontains=term).exclude(address='').exclude(address__isnull=True)
        elif field == 'phone':
            receipts_qs = receipts_qs.filter(phone_number__icontains=term).exclude(phone_number='').exclude(phone_number__isnull=True)

        sp_id = resolve_salesperson_id(salesperson_id)

        if len(term) < 1:
            receipts_qs = receipts_qs.order_by('-id')
        else:
            when_conditions = []
            if field in ['phone', 'address']:
                if sp_id and current_area and current_name:
                    when_conditions.append(When(Q(salesperson_id=sp_id) & Q(area=current_area) & Q(customer_name=current_name), then=0))
                if current_area and current_name:
                    when_conditions.append(When(Q(area=current_area) & Q(customer_name=current_name), then=1))
                if current_name:
                    when_conditions.append(When(customer_name=current_name, then=2))
                if current_area:
                    when_conditions.append(When(area=current_area, then=3))
                if sp_id:
                    when_conditions.append(When(salesperson_id=sp_id, then=4))
            elif field == 'name':
                if sp_id and current_area:
                    when_conditions.append(When(Q(salesperson_id=sp_id) & Q(area=current_area), then=0))
                if sp_id:
                    when_conditions.append(When(salesperson_id=sp_id, then=1))
                if current_area:
                    when_conditions.append(When(area=current_area, then=2))
            elif field == 'area':
                if sp_id:
                    when_conditions.append(When(salesperson_id=sp_id, then=0))

            if when_conditions:
                receipts_qs = receipts_qs.order_by(
                    Case(*when_conditions, default=10, output_field=IntegerField()),
                    '-id'
                )
            else:
                receipts_qs = receipts_qs.order_by('-id')

        receipt_rows = list(
            receipts_qs.values(
                'customer_name', 'phone_number', 'address', 'area', 'salesperson_id'
            )[:500]
        )

        suggestions_map = {}
        for r in receipt_rows:
            if field == 'area':
                val = r.get('area')
            elif field == 'name':
                val = r.get('customer_name')
            elif field == 'address':
                val = r.get('address')
            elif field == 'phone':
                val = r.get('phone_number')
            else:
                continue

            if not val:
                continue
            val = str(val).strip()
            if not val:
                continue

            relevance = 0
            if val.lower().startswith(term.lower()):
                relevance += 50

            r_sp_id = r.get('salesperson_id')
            r_area = r.get('area') or ''
            r_name = r.get('customer_name') or ''

            if field == 'area':
                if sp_id and r_sp_id == sp_id:
                    relevance += 20
            elif field == 'name':
                if sp_id and r_sp_id == sp_id:
                    relevance += 20
                if current_area and r_area.strip().lower() == current_area.lower():
                    relevance += 10
            elif field == 'address':
                if current_area and r_area.strip().lower() == current_area.lower():
                    relevance += 30
                if sp_id and r_sp_id == sp_id:
                    relevance += 10
                if current_name and r_name.strip().lower() == current_name.lower():
                    relevance += 5
            elif field == 'phone':
                if current_area and r_area.strip().lower() == current_area.lower():
                    relevance += 30
                if sp_id and r_sp_id == sp_id:
                    relevance += 10
                if current_name and r_name.strip().lower() == current_name.lower():
                    relevance += 5

            if val not in suggestions_map:
                suggestions_map[val] = {
                    "value": val,
                    "relevance": relevance,
                    "use_count": 1
                }
            else:
                suggestions_map[val]["use_count"] += 1
                if relevance > suggestions_map[val]["relevance"]:
                    suggestions_map[val]["relevance"] = relevance

        suggestions_list = list(suggestions_map.values())
        if field == 'area':
            suggestions_list.sort(key=lambda x: (-x["relevance"], -x["use_count"]))
        else:
            suggestions_list.sort(key=lambda x: (-x["relevance"], x["value"].lower()))

        results = []
        for item in suggestions_list[:15]:
            results.append({"value": item["value"]})

        return Response(results)


class ProductSuggestionsView(views.APIView):
    def get(self, request):
        term = to_english_numerals(request.query_params.get("term", "").strip())
        month_str = to_english_numerals(request.query_params.get("month", "").strip())
        year_str = to_english_numerals(request.query_params.get("year", "").strip())
        branch_id = get_request_branch_id(request)

        default_year, default_month = get_default_date(branch_id=branch_id)

        try:
            target_month = int(month_str) if month_str else default_month
            target_year = int(year_str) if year_str else default_year
        except ValueError:
            target_month = default_month
            target_year = default_year

        items_qs = InventoryItem.objects.filter(is_deleted=False)
        if term:
            items_qs = items_qs.filter(name__icontains=term)

        if branch_id:
            items_qs = items_qs.filter(branch_id=branch_id)

        items = list(items_qs[:50])
        stock_map = calculate_bulk_stock_timeline(items, target_month, target_year, default_month, default_year)

        results = []
        for item in items:
            item_data = stock_map.get(item.id, {})
            max_qty = item_data.get('safe_available_qty', 0)
            results.append({
                "id": str(item.id),
                "value": item.name,
                "max": max_qty
            })

        return Response(results)
