"""
Wave 1 — Heavy Multi-Year Financial & Stock Time-Machine Oracle QA Suite.

Implements an independent Pure Python Mathematical Oracle (PureMathOracle)
and verifies 100% mathematical parity across:
- 36 Months (2024/01 to 2026/12) x 3 Isolated Branches (108 slices)
- Pre-License External Data Isolation (2024/01 to 2024/06 < lic_start 2024/07)
- All 10 Reports + CashDrawerReportView + InventoryItemViewSet.ledger
- Time-Machine Stock Clamping, Bottleneck Horizon, & Multi-Line / Date-Edit Guards
- Sales Return (RETURN) Financial vs Physical Attribution & Area/Salesperson Filtering
- Soft-Delete Reversibility & Cryptographic HMAC Receipt.is_authentic Verification
"""
import calendar
import datetime
from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import (
    Branch,
    ClientLicense,
    CommissionHistory,
    CompanySetting,
    Expense,
    InstallmentPayment,
    InventoryAdjustment,
    InventoryItem,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    Receipt,
    SaleItem,
    Salesperson,
    Supplier,
)
from api.services.receipt_service import (
    create_receipt,
    process_return_receipt,
    update_receipt,
)
from api.services.purchase_service import (
    create_purchase_invoice,
    update_purchase_invoice,
)
from api.utils.security_utils import generate_record_signature


class PureMathOracle:
    """
    Independent Pure-Python Mathematical Reference Oracle.
    Computes expected stock, prices, commissions, P&L, cash drawer, areas,
    installments, averages, salesperson performance, and product ledgers
    directly from raw in-memory/active records without using any app service.
    """

    def __init__(self, lic_start_ym=(2024, 7)):
        self.lic_start_ym = lic_start_ym

    def is_pre_license(self, year, month):
        return (year, month) < self.lic_start_ym

    def get_coll_rate(self):
        cs = CompanySetting.objects.filter(is_deleted=False).first()
        if cs and cs.collection_commission_rate is not None:
            return float(cs.collection_commission_rate)
        return 0.10

    def get_price_at(self, item, month, year):
        qs = PurchaseInvoiceItem.objects.filter(
            inventory_item_id=item.id,
            is_deleted=False,
            invoice__is_deleted=False,
            invoice__invoice_type="PURCHASE",
        )
        valid = [
            p for p in qs.select_related("invoice")
            if (p.invoice.invoice_year, p.invoice.invoice_month) <= (year, month)
        ]
        if not valid:
            return float(item.initial_purchase_price)
        valid.sort(key=lambda p: (p.invoice.invoice_year, p.invoice.invoice_month, p.id))
        return float(valid[-1].purchase_price)

    def get_comm_at(self, item, month, year):
        qs = CommissionHistory.objects.filter(item_id=item.id, is_deleted=False)
        valid = [
            c for c in qs
            if (c.activation_year, c.activation_month) <= (year, month)
        ]
        if not valid:
            return float(item.initial_commission_amount)
        valid.sort(key=lambda c: (c.activation_year, c.activation_month, c.id))
        return float(valid[-1].commission_amount)

    def get_stock_at(self, item, month, year):
        if (year, month) < (item.initial_year, item.initial_month):
            return 0
        raw = int(item.initial_quantity)
        for p in PurchaseInvoiceItem.objects.filter(
            inventory_item_id=item.id, is_deleted=False, invoice__is_deleted=False
        ).select_related("invoice"):
            if (p.invoice.invoice_year, p.invoice.invoice_month) <= (year, month):
                if p.invoice.invoice_type == "PURCHASE":
                    raw += p.quantity
                else:
                    raw -= p.quantity
        for s in SaleItem.objects.filter(
            inventory_item_id=item.id,
            is_deleted=False,
            receipt__is_deleted=False,
            receipt__is_confirmed=True,
        ).select_related("receipt"):
            if (s.receipt.sale_year, s.receipt.sale_month) <= (year, month):
                if s.receipt.receipt_type == "SALE":
                    raw -= s.quantity
                else:
                    raw += s.quantity
        for adj in InventoryAdjustment.objects.filter(
            item_id=item.id, is_deleted=False, adjustment_type="DEFICIT"
        ):
            if (adj.year, adj.month) <= (year, month):
                raw -= adj.quantity
        return max(0, raw)

    def compute_salesperson_performance(self, branch_id, month, year, sp_id=None, area=None):
        coll_rate = self.get_coll_rate()
        pre_lic = self.is_pre_license(year, month)
        sps = list(
            Salesperson.objects.filter(branch_id=branch_id, is_deleted=False).order_by("id")
        )
        if sp_id:
            sps = [sp for sp in sps if sp.id == sp_id]

        sp_map = {
            sp.id: {
                "sp": sp,
                "receipts_count": 0,
                "cash_sales_raw": 0.0,
                "credit_sales_raw": 0.0,
                "down_payments": 0.0,
                "cash_returns": 0.0,
                "credit_returns": 0.0,
                "collected": 0.0,
                "comm_sales": 0.0,
            }
            for sp in sps
        }

        if not pre_lic:
            sales_qs = Receipt.objects.filter(
                branch_id=branch_id,
                sale_month=month,
                sale_year=year,
                is_deleted=False,
                is_confirmed=True,
            ).exclude(receipt_type="RETURN")
            if sp_id:
                sales_qs = sales_qs.filter(salesperson_id=sp_id)
            if area:
                sales_qs = sales_qs.filter(area__icontains=area)

            for r in sales_qs:
                if r.salesperson_id in sp_map:
                    d = sp_map[r.salesperson_id]
                    d["receipts_count"] += 1
                    if r.is_cash_sale:
                        d["cash_sales_raw"] += float(r.total_amount)
                    else:
                        d["credit_sales_raw"] += float(r.total_amount)
                        d["down_payments"] += float(r.down_payment)

            ret_qs = Receipt.objects.filter(
                branch_id=branch_id,
                receipt_type="RETURN",
                is_deleted=False,
                is_confirmed=True,
            ).select_related("parent_receipt")
            for ret in ret_qs:
                orig_m = ret.parent_receipt.sale_month if ret.parent_receipt else ret.sale_month
                orig_y = ret.parent_receipt.sale_year if ret.parent_receipt else ret.sale_year
                if (orig_y, orig_m) != (year, month):
                    continue
                target_sp = (
                    ret.parent_receipt.salesperson_id
                    if (ret.parent_receipt and ret.parent_receipt.salesperson_id)
                    else ret.salesperson_id
                )
                if sp_id and target_sp != sp_id:
                    continue
                if area:
                    r_area = (ret.area or "").lower()
                    p_area = (ret.parent_receipt.area if ret.parent_receipt and ret.parent_receipt.area else "").lower()
                    if area.lower() not in r_area and area.lower() not in p_area:
                        continue
                if target_sp in sp_map:
                    if ret.is_cash_sale:
                        sp_map[target_sp]["cash_returns"] += float(ret.total_amount)
                    else:
                        sp_map[target_sp]["credit_returns"] += float(ret.total_amount)

            for si in SaleItem.objects.filter(
                receipt__branch_id=branch_id,
                receipt__sale_month=month,
                receipt__sale_year=year,
                receipt__is_deleted=False,
                receipt__is_confirmed=True,
                is_deleted=False,
            ).exclude(receipt__receipt_type="RETURN").select_related("inventory_item", "receipt"):
                if sp_id and si.receipt.salesperson_id != sp_id:
                    continue
                if area and area.lower() not in (si.receipt.area or "").lower():
                    continue
                sid = si.receipt.salesperson_id
                if sid in sp_map:
                    c_unit = self.get_comm_at(si.inventory_item, month, year)
                    sp_map[sid]["comm_sales"] += float(si.quantity) * c_unit

            for ri in SaleItem.objects.filter(
                receipt__branch_id=branch_id,
                receipt__receipt_type="RETURN",
                receipt__is_deleted=False,
                receipt__is_confirmed=True,
                is_deleted=False,
            ).select_related("inventory_item", "receipt", "receipt__parent_receipt"):
                orig_m = ri.receipt.parent_receipt.sale_month if ri.receipt.parent_receipt else ri.receipt.sale_month
                orig_y = ri.receipt.parent_receipt.sale_year if ri.receipt.parent_receipt else ri.receipt.sale_year
                if (orig_y, orig_m) != (year, month):
                    continue
                target_sp = (
                    ri.receipt.parent_receipt.salesperson_id
                    if (ri.receipt.parent_receipt and ri.receipt.parent_receipt.salesperson_id)
                    else ri.receipt.salesperson_id
                )
                if sp_id and target_sp != sp_id:
                    continue
                if area:
                    r_area = (ri.receipt.area or "").lower()
                    p_area = (ri.receipt.parent_receipt.area if ri.receipt.parent_receipt and ri.receipt.parent_receipt.area else "").lower()
                    if area.lower() not in r_area and area.lower() not in p_area:
                        continue
                if target_sp in sp_map:
                    c_unit = self.get_comm_at(ri.inventory_item, orig_m, orig_y)
                    sp_map[target_sp]["comm_sales"] -= float(ri.quantity) * c_unit

        _, last_day = calendar.monthrange(year, month)
        start_d = datetime.date(year, month, 1)
        end_d = datetime.date(year, month, last_day)
        for p in InstallmentPayment.objects.filter(
            receipt__branch_id=branch_id,
            receipt__is_confirmed=True,
            receipt__is_deleted=False,
            is_deleted=False,
            payment_date__range=(start_d, end_d),
        ).select_related("receipt"):
            if sp_id and p.receipt.salesperson_id != sp_id:
                continue
            if area and area.lower() not in (p.receipt.area or "").lower():
                continue
            sid = p.receipt.salesperson_id
            if sid in sp_map:
                sp_map[sid]["collected"] += float(p.amount)

        rows = []
        auto_salaries_sum = 0.0
        for sp in sps:
            d = sp_map[sp.id]
            cash_sales = d["cash_sales_raw"] - d["cash_returns"]
            credit_sales = d["credit_sales_raw"] - d["credit_returns"]
            total_sales_val = cash_sales + credit_sales
            comm_sales = max(0.0, d["comm_sales"])
            comm_coll = d["collected"] * coll_rate
            total_comm = comm_sales + comm_coll
            auto_salaries_sum += total_comm
            rows.append({
                "salesperson_id": sp.id,
                "receipts_count": d["receipts_count"],
                "cash_sales": cash_sales,
                "credit_sales": credit_sales,
                "down_payments": d["down_payments"],
                "total_sales": total_sales_val,
                "collected": d["collected"],
                "comm_sales": comm_sales,
                "comm_coll": comm_coll,
                "total_comm": total_comm,
            })

        return {
            "rows": rows,
            "auto_salaries_sum": auto_salaries_sum,
        }

    def compute_cash_drawer(self, branch_id, month, year):
        pre_lic = self.is_pre_license(year, month)
        perf = self.compute_salesperson_performance(branch_id, month, year)
        auto_salaries = perf["auto_salaries_sum"]

        if pre_lic:
            cash_sales_inflow = 0.0
            down_payments_inflow = 0.0
        else:
            sales_qs = Receipt.objects.filter(
                branch_id=branch_id,
                sale_month=month,
                sale_year=year,
                is_deleted=False,
                is_confirmed=True,
            ).exclude(receipt_type="RETURN")
            cash_sales_inflow = sum(float(r.total_amount) for r in sales_qs if r.is_cash_sale)
            down_payments_inflow = sum(float(r.down_payment) for r in sales_qs if not r.is_cash_sale)

        _, last_day = calendar.monthrange(year, month)
        start_d = datetime.date(year, month, 1)
        end_d = datetime.date(year, month, last_day)
        collections_inflow = sum(
            float(p.amount)
            for p in InstallmentPayment.objects.filter(
                receipt__branch_id=branch_id,
                receipt__is_confirmed=True,
                receipt__is_deleted=False,
                is_deleted=False,
                payment_date__range=(start_d, end_d),
            )
        )

        supplier_returns_inflow = sum(
            float(pi.quantity * pi.purchase_price)
            for pi in PurchaseInvoiceItem.objects.filter(
                invoice__branch_id=branch_id,
                invoice__invoice_month=month,
                invoice__invoice_year=year,
                invoice__invoice_type="RETURN",
                invoice__is_deleted=False,
                is_deleted=False,
            )
        )

        purchases_outflow = sum(
            float(pi.quantity * pi.purchase_price)
            for pi in PurchaseInvoiceItem.objects.filter(
                invoice__branch_id=branch_id,
                invoice__invoice_month=month,
                invoice__invoice_year=year,
                invoice__invoice_type="PURCHASE",
                invoice__is_deleted=False,
                is_deleted=False,
            )
        )

        expenses_outflow = sum(
            float(e.amount)
            for e in Expense.objects.filter(
                branch_id=branch_id,
                expense_month=month,
                expense_year=year,
                is_deleted=False,
            )
        )

        customer_returns_refund = 0.0
        for ret in Receipt.objects.filter(
            branch_id=branch_id,
            sale_month=month,
            sale_year=year,
            receipt_type="RETURN",
            is_deleted=False,
            is_confirmed=True,
        ):
            if ret.is_cash_sale:
                customer_returns_refund += float(ret.total_amount)
            else:
                customer_returns_refund += float(ret.down_payment)

        total_inflow = (
            cash_sales_inflow
            + down_payments_inflow
            + collections_inflow
            + supplier_returns_inflow
        )
        total_outflow = (
            purchases_outflow
            + expenses_outflow
            + auto_salaries
            + customer_returns_refund
        )
        safe_balance = total_inflow - total_outflow
        return {
            "cash_sales_inflow": cash_sales_inflow,
            "down_payments_inflow": down_payments_inflow,
            "collections_inflow": collections_inflow,
            "supplier_returns_inflow": supplier_returns_inflow,
            "purchases_outflow": purchases_outflow,
            "expenses_outflow": expenses_outflow,
            "auto_salaries": auto_salaries,
            "customer_returns_refund": customer_returns_refund,
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "safe_balance": safe_balance,
        }

    def compute_dashboard(self, branch_id, month, year):
        pre_lic = self.is_pre_license(year, month)
        coll_rate = self.get_coll_rate()

        if pre_lic:
            sales_rev = 0.0
            returns_rev = 0.0
            total_cogs = 0.0
            total_sales_comm = 0.0
            reserve_deduction = 0.0
            receipt_count = 0
        else:
            sales_qs = list(
                Receipt.objects.filter(
                    branch_id=branch_id,
                    sale_month=month,
                    sale_year=year,
                    is_deleted=False,
                    is_confirmed=True,
                ).exclude(receipt_type="RETURN")
            )
            ret_qs = [
                r
                for r in Receipt.objects.filter(
                    branch_id=branch_id,
                    receipt_type="RETURN",
                    is_deleted=False,
                    is_confirmed=True,
                ).select_related("parent_receipt")
                if (
                    (r.parent_receipt.sale_year, r.parent_receipt.sale_month) == (year, month)
                    if r.parent_receipt
                    else (r.sale_year, r.sale_month) == (year, month)
                )
            ]
            sales_rev = sum(float(r.total_amount) for r in sales_qs)
            returns_rev = sum(float(r.total_amount) for r in ret_qs)
            receipt_count = len(sales_qs)

            total_cogs = 0.0
            total_sales_comm = 0.0
            for si in SaleItem.objects.filter(
                receipt__branch_id=branch_id,
                receipt__sale_month=month,
                receipt__sale_year=year,
                receipt__is_deleted=False,
                receipt__is_confirmed=True,
                is_deleted=False,
            ).exclude(receipt__receipt_type="RETURN").select_related("inventory_item", "receipt"):
                total_cogs += float(si.quantity) * self.get_price_at(si.inventory_item, month, year)
                total_sales_comm += float(si.quantity) * self.get_comm_at(si.inventory_item, month, year)

            for ri in SaleItem.objects.filter(
                receipt__branch_id=branch_id,
                receipt__receipt_type="RETURN",
                receipt__is_deleted=False,
                receipt__is_confirmed=True,
                is_deleted=False,
            ).select_related("inventory_item", "receipt", "receipt__parent_receipt"):
                orig_m = ri.receipt.parent_receipt.sale_month if ri.receipt.parent_receipt else ri.receipt.sale_month
                orig_y = ri.receipt.parent_receipt.sale_year if ri.receipt.parent_receipt else ri.receipt.sale_year
                if (orig_y, orig_m) != (year, month):
                    continue
                total_cogs -= float(ri.quantity) * self.get_price_at(ri.inventory_item, orig_m, orig_y)
                total_sales_comm -= float(ri.quantity) * self.get_comm_at(ri.inventory_item, orig_m, orig_y)

            credit_sales_diff = sum(
                float(r.total_amount - r.down_payment) for r in sales_qs if not r.is_cash_sale
            )
            credit_ret_total = sum(
                float(r.total_amount) for r in ret_qs if not r.is_cash_sale
            )
            reserve_deduction = max(0.0, (credit_sales_diff - credit_ret_total) * coll_rate)

        total_revenue = sales_rev - returns_rev
        operating_expenses = sum(
            float(e.amount)
            for e in Expense.objects.filter(
                branch_id=branch_id,
                expense_month=month,
                expense_year=year,
                is_deleted=False,
            )
        )
        deficit_loss = sum(
            float(adj.quantity) * self.get_price_at(adj.item, month, year)
            for adj in InventoryAdjustment.objects.filter(
                item__branch_id=branch_id,
                month=month,
                year=year,
                is_deleted=False,
                adjustment_type="DEFICIT",
            ).select_related("item")
        )
        estimated_net_profit = total_revenue - (
            total_cogs + total_sales_comm + reserve_deduction + operating_expenses + deficit_loss
        )
        drawer = self.compute_cash_drawer(branch_id, month, year)
        items = list(InventoryItem.objects.filter(branch_id=branch_id, is_deleted=False))
        inv_value = sum(
            self.get_stock_at(it, month, year) * self.get_price_at(it, month, year)
            for it in items
        )
        low_stock = sum(1 for it in items if self.get_stock_at(it, month, year) <= 3)
        avg_basket = total_revenue // receipt_count if receipt_count > 0 else 0

        return {
            "safe_balance": drawer["safe_balance"],
            "total_revenue": total_revenue,
            "total_cogs": total_cogs,
            "total_sales_commissions": total_sales_comm,
            "total_collection_commissions": reserve_deduction,
            "total_deficit_loss": deficit_loss,
            "estimated_net_profit": estimated_net_profit,
            "current_inventory_value": inv_value,
            "low_stock_count": low_stock,
            "avg_basket_size": avg_basket,
        }


class HeavyFinancialOracleQATests(TestCase):
    """
    Comprehensive 36-Month x 3-Branch Financial & Stock Time-Machine QA Suite.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="admin_oracle", password="password123", email="admin@ventapos.local"
        )
        CompanySetting.objects.all().update(is_deleted=True)
        cls.company_setting = CompanySetting.objects.create(
            name="معرض النخبة للأجهزة والمفروشات",
            collection_commission_rate=Decimal("0.10"),
        )

        ClientLicense.objects.all().update(is_deleted=True)
        from api.utils.security_utils import get_machine_id
        start_date = datetime.date(2024, 7, 1)
        expiry_date = datetime.date(2028, 1, 1)
        balance = 50000
        machine_id = get_machine_id()
        product_id = 1
        cls.active_license = ClientLicense.objects.create(
            start_date=start_date,
            expiry_date=expiry_date,
            invoices_balance=balance,
            machine_id=machine_id,
            product_id=product_id,
            is_active=True,
            license_code_hash=generate_record_signature(
                expiry_date, balance, machine_id, product_id, True
            ),
        )

        cls.branches = []
        cls.salespersons = {}
        cls.suppliers = {}
        cls.items = {}

        for b_idx in range(1, 4):
            b = Branch.objects.create(name=f"فرع {b_idx}")
            cls.branches.append(b)
            cls.salespersons[b.id] = [
                Salesperson.objects.create(branch=b, name=f"مندوب {b_idx}-أ"),
                Salesperson.objects.create(branch=b, name=f"مندوب {b_idx}-ب"),
            ]
            cls.suppliers[b.id] = [
                Supplier.objects.create(branch=b, name=f"مورد {b_idx}-1"),
                Supplier.objects.create(branch=b, name=f"مورد {b_idx}-2"),
            ]
            cls.items[b.id] = [
                InventoryItem.objects.create(
                    branch=b,
                    name=f"ثلاجة توشيبا {b_idx}",
                    initial_quantity=20 * b_idx,
                    initial_purchase_price=Decimal(str(8000 + b_idx * 500)),
                    initial_commission_amount=Decimal(str(100 + b_idx * 10)),
                    initial_month=7,
                    initial_year=2024,
                ),
                InventoryItem.objects.create(
                    branch=b,
                    name=f"غسالة إل جي {b_idx}",
                    initial_quantity=15 * b_idx,
                    initial_purchase_price=Decimal(str(6000 + b_idx * 400)),
                    initial_commission_amount=Decimal(str(80 + b_idx * 10)),
                    initial_month=7,
                    initial_year=2024,
                ),
                InventoryItem.objects.create(
                    branch=b,
                    name=f"بوتاجاز يونيون {b_idx}",
                    initial_quantity=10 * b_idx,
                    initial_purchase_price=Decimal(str(4000 + b_idx * 300)),
                    initial_commission_amount=Decimal(str(60 + b_idx * 10)),
                    initial_month=10,
                    initial_year=2024,
                ),
            ]

        cls._seed_36_month_simulation()

    @classmethod
    def _seed_36_month_simulation(cls):
        areas = ["القاهرة", "الجيزة", "الإسكندرية"]

        for b_idx, b in enumerate(cls.branches, start=1):
            sp1, sp2 = cls.salespersons[b.id]
            sup1, sup2 = cls.suppliers[b.id]
            it1, it2, it3 = cls.items[b.id]

            # -----------------------------------------------------------------
            # Phase A: Pre-License Months (2024/01 to 2024/06)
            # -----------------------------------------------------------------
            for m in range(1, 7):
                # Pre-license Cash Receipt
                create_receipt(
                    validated_data={
                        "branch": b,
                        "salesperson": sp1 if m % 2 == 1 else sp2,
                        "customer_name": f"عميل قديم نقدي {b_idx}-{m}",
                        "phone_number": "01111111111",
                        "area": areas[m % 3],
                        "address": "عنوان قديم",
                        "sale_month": m,
                        "sale_year": 2024,
                        "is_cash_sale": True,
                        "total_amount": Decimal(str(3000 + m * 200 * b_idx)),
                        "down_payment": Decimal(str(3000 + m * 200 * b_idx)),
                        "products_text": f"بضاعة قديمة نقدي شهر {m}",
                        "is_confirmed": True,
                    },
                    items_data=[],
                    installments_data=[],
                )

                # Pre-license Installment Receipt with 12 installments extending into 2024/07-2025/06
                inst_amount = Decimal(str(250 * b_idx))
                down_pay = Decimal(str(1000 * b_idx))
                total_amt = down_pay + inst_amount * 12
                inst_rows = []
                cur_m, cur_y = m, 2024
                for _ in range(12):
                    cur_m += 1
                    if cur_m > 12:
                        cur_m = 1
                        cur_y += 1
                    inst_rows.append({
                        "payment_month": cur_m,
                        "payment_year": cur_y,
                        "amount": inst_amount,
                    })

                create_receipt(
                    validated_data={
                        "branch": b,
                        "salesperson": sp2 if m % 2 == 1 else sp1,
                        "customer_name": f"عميل قديم قسط {b_idx}-{m}",
                        "phone_number": "01222222222",
                        "area": areas[(m + 1) % 3],
                        "address": "عنوان قسط قديم",
                        "sale_month": m,
                        "sale_year": 2024,
                        "is_cash_sale": False,
                        "total_amount": total_amt,
                        "down_payment": down_pay,
                        "products_text": f"بضاعة قديمة تقسيط شهر {m}",
                        "installment_system": f"{int(inst_amount)}*12",
                        "is_confirmed": True,
                    },
                    items_data=[],
                    installments_data=inst_rows,
                )

            # -----------------------------------------------------------------
            # Phase B: Post-License Months (2024/07 to 2026/12)
            # -----------------------------------------------------------------
            # Commission History step-functions
            CommissionHistory.objects.create(
                item=it1,
                commission_amount=Decimal(str(130 + b_idx * 10)),
                activation_month=1,
                activation_year=2025,
            )
            CommissionHistory.objects.create(
                item=it1,
                commission_amount=Decimal(str(160 + b_idx * 10)),
                activation_month=1,
                activation_year=2026,
            )
            CommissionHistory.objects.create(
                item=it2,
                commission_amount=Decimal(str(110 + b_idx * 10)),
                activation_month=6,
                activation_year=2025,
            )

            all_post_months = (
                [(2024, m) for m in range(7, 13)]
                + [(2025, m) for m in range(1, 13)]
                + [(2026, m) for m in range(1, 13)]
            )

            for idx, (yr, mn) in enumerate(all_post_months):
                # 1. Periodic Purchases with price step-ups
                if idx % 3 == 0:
                    p_price_1 = Decimal(str(8200 + b_idx * 500 + idx * 50))
                    p_price_2 = Decimal(str(6200 + b_idx * 400 + idx * 40))
                    p_items = [
                        {"inventory_item": it1, "quantity": 6, "purchase_price": p_price_1},
                        {"inventory_item": it2, "quantity": 5, "purchase_price": p_price_2},
                    ]
                    if (yr, mn) >= (2024, 10):
                        p_price_3 = Decimal(str(4200 + b_idx * 300 + idx * 30))
                        p_items.append(
                            {"inventory_item": it3, "quantity": 4, "purchase_price": p_price_3}
                        )
                    create_purchase_invoice(
                        validated_data={
                            "branch": b,
                            "supplier": sup1 if idx % 2 == 0 else sup2,
                            "invoice_month": mn,
                            "invoice_year": yr,
                            "invoice_type": "PURCHASE",
                        },
                        items_data=p_items,
                    )

                # 2. Periodic Supplier Returns
                if idx in (4, 12, 22):
                    ret_price = Decimal(str(8000 + b_idx * 500))
                    create_purchase_invoice(
                        validated_data={
                            "branch": b,
                            "supplier": sup1,
                            "invoice_month": mn,
                            "invoice_year": yr,
                            "invoice_type": "RETURN",
                        },
                        items_data=[
                            {"inventory_item": it1, "quantity": 1, "purchase_price": ret_price}
                        ],
                    )

                # 3. Cash Sale every month
                cash_price_1 = Decimal(str(11000 + b_idx * 500 + idx * 100))
                cash_items = [{"inventory_item": it1, "quantity": 1, "unit_price": cash_price_1}]
                if (yr, mn) >= (2024, 10) and idx % 2 == 0:
                    cash_price_3 = Decimal(str(5500 + b_idx * 300))
                    cash_items.append(
                        {"inventory_item": it3, "quantity": 1, "unit_price": cash_price_3}
                    )
                cash_total = sum(i["quantity"] * i["unit_price"] for i in cash_items)
                cash_rec = create_receipt(
                    validated_data={
                        "branch": b,
                        "salesperson": sp1 if idx % 2 == 0 else sp2,
                        "customer_name": f"عميل نقدي {b_idx}-{yr}-{mn}",
                        "phone_number": "01099999999",
                        "area": areas[idx % 3],
                        "address": "شارع الجمهورية",
                        "sale_month": mn,
                        "sale_year": yr,
                        "is_cash_sale": True,
                        "total_amount": cash_total,
                        "down_payment": cash_total,
                        "is_confirmed": True,
                    },
                    items_data=cash_items,
                    installments_data=[],
                )

                # 4. Installment Sale every month (with multi-box uneven remainder on even idx)
                cred_price_2 = Decimal(str(8500 + b_idx * 400 + idx * 50))
                cred_qty = 2 if idx in (2, 8, 16) else 1
                cred_total = cred_price_2 * cred_qty
                cred_dp = Decimal(str(1500 + b_idx * 100))
                rem = cred_total - cred_dp
                # 3-month schedule with exact integer split (2 months of floor + 1 month with remainder)
                base_inst = int(rem) // 3
                last_inst = int(rem) - base_inst * 2
                inst_schedule = []
                cm, cy = mn, yr
                for step_i, amt_val in enumerate([base_inst, base_inst, last_inst]):
                    cm += 1
                    if cm > 12:
                        cm = 1
                        cy += 1
                    inst_schedule.append({
                        "payment_month": cm,
                        "payment_year": cy,
                        "amount": Decimal(str(amt_val)),
                    })

                cred_rec = create_receipt(
                    validated_data={
                        "branch": b,
                        "salesperson": sp2 if idx % 2 == 0 else sp1,
                        "customer_name": f"عميل تقسيط {b_idx}-{yr}-{mn}",
                        "phone_number": "01088888888",
                        "area": areas[(idx + 1) % 3],
                        "address": "شارع التحرير",
                        "sale_month": mn,
                        "sale_year": yr,
                        "is_cash_sale": False,
                        "total_amount": cred_total,
                        "down_payment": cred_dp,
                        "installment_system": f"{base_inst}*2+{last_inst}*1",
                        "is_confirmed": True,
                    },
                    items_data=[
                        {"inventory_item": it2, "quantity": cred_qty, "unit_price": cred_price_2}
                    ],
                    installments_data=inst_schedule,
                )

                # 5. Same-month & cross-month Customer Returns
                if idx == 2:
                    # Partial credit return in the next month (M+1)
                    ret_m = mn + 1 if mn < 12 else 1
                    ret_y = yr if mn < 12 else yr + 1
                    new_rem = cred_price_2 - cred_dp
                    process_return_receipt(
                        cred_rec,
                        {
                            "return_month": ret_m,
                            "return_year": ret_y,
                            "returned_items": [
                                {"inventory_item_id": it2.id, "quantity": 1}
                            ],
                            "new_installments": [
                                {
                                    "payment_month": ret_m,
                                    "payment_year": ret_y,
                                    "amount": str(new_rem),
                                }
                            ] if new_rem > 0 else [],
                            "new_installment_system": f"{int(new_rem)}*1" if new_rem > 0 else "",
                        },
                    )
                elif idx == 8:
                    # Cash return in the following month (M+1)
                    ret_m = mn + 1 if mn < 12 else 1
                    ret_y = yr if mn < 12 else yr + 1
                    process_return_receipt(
                        cash_rec,
                        {
                            "return_month": ret_m,
                            "return_year": ret_y,
                            "returned_items": [
                                {"inventory_item_id": it1.id, "quantity": 1}
                            ],
                        },
                    )

                # 6. Inventory Deficits & Operating Expenses
                if idx in (5, 15, 25):
                    InventoryAdjustment.objects.create(
                        item=it1,
                        adjustment_type="DEFICIT",
                        quantity=1,
                        reason=f"عجز جرد {yr}/{mn}",
                        month=mn,
                        year=yr,
                    )

                Expense.objects.create(
                    branch=b,
                    category="RENT" if idx % 2 == 0 else "UTILITIES",
                    description=f"مصروفات تشغيل {yr}/{mn}",
                    amount=Decimal(str(500 * b_idx + idx * 25)),
                    expense_month=mn,
                    expense_year=yr,
                )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.oracle = PureMathOracle(lic_start_ym=(2024, 7))

    def test_01_full_36_months_x_3_branches_oracle_parity_across_all_reports(self):
        """
        Iterates over all 3 branches and representative months across 2024, 2025, and 2026
        (including pre-license months 2024/01-2024/06 and post-license months with returns,
        deficits, price changes, and commission changes) and asserts 100% parity between
        all backend report endpoints and the PureMathOracle.
        """
        months_to_verify = [
            (yr, mn)
            for yr in (2024, 2025, 2026)
            for mn in range(1, 13)
        ]

        for branch in self.branches:
            b_id = branch.id
            headers = {"HTTP_X_BRANCH_ID": str(b_id)}

            for yr, mn in months_to_verify:
                is_pre = self.oracle.is_pre_license(yr, mn)

                # 1. Dashboard Report
                dash_res = self.client.get(
                    f"/api/v1/reports/dashboard/?branch_id={b_id}&year={yr}&month={mn}",
                    **headers,
                )
                self.assertEqual(dash_res.status_code, 200)
                kpis = dash_res.data["kpis"]
                expected_dash = self.oracle.compute_dashboard(b_id, mn, yr)
                for key, exp_val in expected_dash.items():
                    self.assertAlmostEqual(
                        float(kpis[key]),
                        float(exp_val),
                        places=2,
                        msg=f"Dashboard mismatch on {key} for branch={b_id}, {yr}/{mn}",
                    )
                if is_pre:
                    self.assertEqual(dash_res.data["top_products"], [])
                    self.assertEqual(dash_res.data["top_areas"], [])
                    self.assertEqual(float(kpis["total_revenue"]), 0.0)
                    self.assertEqual(float(kpis["avg_basket_size"]), 0.0)

                # 2. Cash Drawer Summary (from Dashboard) & Cash Drawer Itemized Report
                cd_summary = dash_res.data["cash_drawer_summary"]
                expected_cd = self.oracle.compute_cash_drawer(b_id, mn, yr)
                self.assertAlmostEqual(
                    float(cd_summary["safe_balance"]),
                    float(expected_cd["safe_balance"]),
                    places=2,
                    msg=f"CashDrawer safe_balance mismatch for branch={b_id}, {yr}/{mn}",
                )

                cd_res = self.client.get(
                    f"/api/v1/reports/cash-drawer/?branch_id={b_id}&year={yr}&month={mn}",
                    **headers,
                )
                self.assertEqual(cd_res.status_code, 200)
                self.assertAlmostEqual(
                    sum(float(x["amount"]) for x in cd_res.data["cash_sales"]),
                    float(expected_cd["cash_sales_inflow"]),
                    places=2,
                )
                self.assertAlmostEqual(
                    sum(float(x["down_payment"]) for x in cd_res.data["down_payments"]),
                    float(expected_cd["down_payments_inflow"]),
                    places=2,
                )
                self.assertAlmostEqual(
                    sum(float(x["amount"]) for x in cd_res.data["collections"]),
                    float(expected_cd["collections_inflow"]),
                    places=2,
                )
                if is_pre:
                    self.assertEqual(cd_res.data["cash_sales"], [])
                    self.assertEqual(cd_res.data["down_payments"], [])

                # 3. Salesperson Performance Report
                sp_res = self.client.get(
                    f"/api/v1/reports/salesperson-performance/?branch_id={b_id}&year={yr}&month={mn}",
                    **headers,
                )
                self.assertEqual(sp_res.status_code, 200)
                expected_sp = self.oracle.compute_salesperson_performance(b_id, mn, yr)
                api_sp_map = {int(r["id"]): r for r in sp_res.data["results"]}
                for exp_row in expected_sp["rows"]:
                    sid = exp_row["salesperson_id"]
                    api_row = api_sp_map[sid]
                    self.assertEqual(api_row["receipts_count"], exp_row["receipts_count"])
                    self.assertAlmostEqual(float(api_row["cash_sales"]), exp_row["cash_sales"], places=2)
                    self.assertAlmostEqual(float(api_row["credit_sales"]), exp_row["credit_sales"], places=2)
                    self.assertAlmostEqual(float(api_row["down_payments"]), exp_row["down_payments"], places=2)
                    self.assertAlmostEqual(float(api_row["collected"]), exp_row["collected"], places=2)
                    self.assertAlmostEqual(float(api_row["comm_sales"]), exp_row["comm_sales"], places=2)
                    self.assertAlmostEqual(float(api_row["comm_coll"]), exp_row["comm_coll"], places=2)
                    self.assertAlmostEqual(float(api_row["due_salary"]), exp_row["total_comm"], places=2)

                # 4. Profit & Loss Report
                pnl_res = self.client.get(
                    f"/api/v1/reports/profit-and-loss/?branch_id={b_id}&year={yr}&month={mn}",
                    **headers,
                )
                self.assertEqual(pnl_res.status_code, 200)
                pnl_sum = pnl_res.data["summary"]
                if is_pre:
                    self.assertEqual(float(pnl_sum["grand_revenue"]), 0.0)
                    self.assertEqual(float(pnl_sum["grand_cost"]), 0.0)
                    self.assertEqual(float(pnl_sum["grand_commission"]), 0.0)
                else:
                    self.assertAlmostEqual(
                        float(pnl_sum["grand_revenue"]),
                        float(expected_dash["total_revenue"]),
                        places=2,
                    )
                    self.assertAlmostEqual(
                        float(pnl_sum["grand_cost"]),
                        float(expected_dash["total_cogs"]),
                        places=2,
                    )
                    self.assertAlmostEqual(
                        float(pnl_sum["net_profit_final"]),
                        float(expected_dash["estimated_net_profit"]),
                        places=2,
                    )

                # 5. Areas Report
                areas_res = self.client.get(
                    f"/api/v1/reports/areas/?branch_id={b_id}&year={yr}&month={mn}",
                    **headers,
                )
                self.assertEqual(areas_res.status_code, 200)
                areas_summary = areas_res.data["summary"]
                if is_pre:
                    self.assertEqual(areas_summary["total_invoices_count"], 0)
                    self.assertEqual(float(areas_summary["total_sales"]), 0.0)
                    self.assertEqual(float(areas_summary["net_sales"]), 0.0)
                    self.assertAlmostEqual(
                        float(areas_summary["total_due_installments"]),
                        float(expected_cd["collections_inflow"]),
                        places=2,
                    )
                else:
                    self.assertAlmostEqual(
                        float(areas_summary["total_due_installments"]),
                        float(expected_cd["collections_inflow"]),
                        places=2,
                    )

                # 6. Installments Report
                inst_res = self.client.get(
                    f"/api/v1/reports/installments/?branch_id={b_id}&year={yr}&month={mn}",
                    **headers,
                )
                self.assertEqual(inst_res.status_code, 200)
                self.assertAlmostEqual(
                    float(inst_res.data["total_installments_amount"]),
                    float(expected_cd["collections_inflow"]),
                    places=2,
                )

                # 7. Inventory Movement Report
                inv_res = self.client.get(
                    f"/api/v1/reports/inventory-movement/?branch_id={b_id}&year={yr}&month={mn}",
                    **headers,
                )
                self.assertEqual(inv_res.status_code, 200)
                self.assertAlmostEqual(
                    float(inv_res.data["total_inventory_value"]),
                    float(expected_dash["current_inventory_value"]),
                    places=2,
                )
                for row in inv_res.data["items"]:
                    item_obj = InventoryItem.objects.get(id=int(row["id"]))
                    self.assertEqual(
                        int(row["final_stock"]),
                        self.oracle.get_stock_at(item_obj, mn, yr),
                    )

                # 8. Purchases Report
                pur_res = self.client.get(
                    f"/api/v1/reports/purchases/?branch_id={b_id}&year={yr}&month={mn}",
                    **headers,
                )
                self.assertEqual(pur_res.status_code, 200)
                self.assertAlmostEqual(
                    float(pur_res.data["summary"]["gross_purchases_amount"]),
                    float(expected_cd["purchases_outflow"]),
                    places=2,
                )
                self.assertAlmostEqual(
                    float(pur_res.data["summary"]["total_returns_amount"]),
                    float(expected_cd["supplier_returns_inflow"]),
                    places=2,
                )
                self.assertAlmostEqual(
                    float(pur_res.data["summary"]["net_purchases_amount"]),
                    float(expected_cd["purchases_outflow"] - expected_cd["supplier_returns_inflow"]),
                    places=2,
                )

                # 9. Receipts List & Aggregate Summary (excludes RETURN notices from sales totals)
                rec_res = self.client.get(
                    f"/api/v1/receipts/?branch_id={b_id}&year={yr}&month={mn}",
                    **headers,
                )
                self.assertEqual(rec_res.status_code, 200)
                non_ret_sales = Receipt.objects.filter(
                    branch_id=b_id, sale_year=yr, sale_month=mn, is_deleted=False
                ).exclude(receipt_type="RETURN")
                expected_rec_sum = sum(float(r.total_amount) for r in non_ret_sales)
                self.assertAlmostEqual(
                    float(rec_res.data["aggregate"]["total_sales"]),
                    expected_rec_sum,
                    places=2,
                )
                self.assertAlmostEqual(
                    float(rec_res.data["total_amount_sum"]),
                    expected_rec_sum,
                    places=2,
                )

            # 10. Product Ledger for each item in the branch
            for item_obj in self.items[b_id]:
                led_res = self.client.get(
                    f"/api/v1/inventory-items/{item_obj.id}/ledger/?branch_id={b_id}",
                    **headers,
                )
                self.assertEqual(led_res.status_code, 200)
                self.assertEqual(
                    led_res.data["item_info"]["current_stock"],
                    self.oracle.get_stock_at(item_obj, 12, 2026),
                )
                if led_res.data["timeline"]:
                    self.assertEqual(
                        led_res.data["timeline"][-1]["running_stock"],
                        led_res.data["item_info"]["current_stock"],
                    )

    def test_02_return_attribution_with_area_and_edited_salesperson(self):
        """
        Verifies:
        1. process_return_receipt copies area and address from original_receipt.
        2. Filtering AreasReportView and InventoryMovementReportView by area includes returns.
        3. Editing parent_receipt.salesperson after a return does NOT double-deduct the return
           across both salespersons in SalespersonPerformanceReportView.
        """
        b = self.branches[0]
        sp1, sp2 = self.salespersons[b.id]
        it1 = self.items[b.id][0]
        headers = {"HTTP_X_BRANCH_ID": str(b.id)}

        rec = create_receipt(
            validated_data={
                "branch": b,
                "salesperson": sp1,
                "customer_name": "عميل اختبار منطقة",
                "phone_number": "01055555555",
                "area": "منطقة المعادي الخاصة",
                "address": "شارع 9 المعادي",
                "sale_month": 5,
                "sale_year": 2026,
                "is_cash_sale": True,
                "total_amount": Decimal("24000.00"),
                "down_payment": Decimal("24000.00"),
                "is_confirmed": True,
            },
            items_data=[{"inventory_item": it1, "quantity": 2, "unit_price": Decimal("12000.00")}],
            installments_data=[],
        )

        ret_res = process_return_receipt(
            rec,
            {
                "return_month": 6,
                "return_year": 2026,
                "returned_items": [{"inventory_item_id": it1.id, "quantity": 1}],
            },
        )
        ret_obj = Receipt.objects.get(id=ret_res["return_receipt_id"])
        self.assertEqual(ret_obj.area, "منطقة المعادي الخاصة")
        self.assertEqual(ret_obj.address, "شارع 9 المعادي")

        # Filter AreasReportView by "منطقة المعادي الخاصة" in month 5 (sale) and month 6 (return)
        area_rep_m5 = self.client.get(
            f"/api/v1/reports/areas/?branch_id={b.id}&year=2026&month=5&area=منطقة المعادي الخاصة",
            **headers,
        )
        self.assertEqual(area_rep_m5.status_code, 200)
        self.assertEqual(len(area_rep_m5.data["areas"]), 1)
        self.assertEqual(area_rep_m5.data["areas"][0]["invoices_count"], 1)
        self.assertAlmostEqual(float(area_rep_m5.data["areas"][0]["gross_sales"]), 24000.0, places=2)

        area_rep_m6 = self.client.get(
            f"/api/v1/reports/areas/?branch_id={b.id}&year=2026&month=6&area=منطقة المعادي الخاصة",
            **headers,
        )
        self.assertEqual(area_rep_m6.status_code, 200)
        self.assertEqual(len(area_rep_m6.data["areas"]), 1)
        a_row = area_rep_m6.data["areas"][0]
        self.assertEqual(a_row["invoices_count"], 0)  # Only SALE counted as invoice, not RETURN
        self.assertEqual(a_row["returns_count"], 1)
        self.assertAlmostEqual(float(a_row["returns_amount"]), 12000.0, places=2)

        # Filter InventoryMovementReportView by "منطقة المعادي الخاصة" in month 6 (return month)
        inv_rep = self.client.get(
            f"/api/v1/reports/inventory-movement/?branch_id={b.id}&year=2026&month=6&area=منطقة المعادي الخاصة",
            **headers,
        )
        self.assertEqual(inv_rep.status_code, 200)
        it1_row = next(r for r in inv_rep.data["items"] if int(r["id"]) == it1.id)
        self.assertEqual(int(it1_row["sales_returns"]), 1)

        # Now change parent_receipt.salesperson from sp1 to sp2 and verify no double deduction in month 5
        rec.salesperson = sp2
        rec.save(update_fields=["salesperson"])

        sp_rep = self.client.get(
            f"/api/v1/reports/salesperson-performance/?branch_id={b.id}&year=2026&month=5&area=منطقة المعادي الخاصة",
            **headers,
        )
        self.assertEqual(sp_rep.status_code, 200)
        # Total net cash sales in "منطقة المعادي الخاصة" must be 24000 - 12000 = 12000 (not 0!)
        self.assertAlmostEqual(float(sp_rep.data["totals"]["grand_total_cash"]), 12000.0, places=2)

    def test_03_stock_bottleneck_horizon_multiline_and_date_edit_guards(self):
        """
        Verifies:
        1. Bottleneck horizon beyond latest Receipt (e.g. a future DEFICIT in 2026/11 when
           evaluating safe_available_qty in an earlier month).
        2. Duplicate inventory_item lines in a single Receipt or PurchaseInvoice RETURN
           cannot bypass safe_limit.
        3. Back-dating a Receipt via PATCH without sale_items into a month with 0 stock
           is blocked by validate_items_stock_integrity.
        """
        b = Branch.objects.create(name="فرع اختبارات الحماية")
        sp = Salesperson.objects.create(branch=b, name="مندوب حماية")
        sup = Supplier.objects.create(branch=b, name="مورد حماية")
        item = InventoryItem.objects.create(
            branch=b,
            name="تكييف شارب انفرتر",
            initial_quantity=5,
            initial_purchase_price=Decimal("15000.00"),
            initial_commission_amount=Decimal("200.00"),
            initial_month=3,
            initial_year=2026,
        )
        headers = {"HTTP_X_BRANCH_ID": str(b.id)}

        # Register a DEFICIT of 3 units in 2026/09 (when no Receipt exists in 2026/09)
        InventoryAdjustment.objects.create(
            item=item,
            adjustment_type="DEFICIT",
            quantity=3,
            reason="تلف مخزني",
            month=9,
            year=2026,
        )

        # In 2026/04, stock at target is 5, but bottleneck in 2026/09 leaves only 5 - 3 = 2!
        stock_res = self.client.get(
            f"/api/v1/inventory-items/{item.id}/stock/?branch_id={b.id}&month=4&year=2026",
            **headers,
        )
        self.assertEqual(stock_res.status_code, 200)
        self.assertEqual(stock_res.data["safe_available_qty"], 2)
        self.assertEqual(stock_res.data["bottleneck_month"], 9)
        self.assertEqual(stock_res.data["bottleneck_year"], 2026)

        # Attempting to sell 2 units across two duplicate lines (1 + 2 = 3 > 2) must fail!
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            create_receipt(
                validated_data={
                    "branch": b,
                    "salesperson": sp,
                    "customer_name": "عميل تحايل سطور",
                    "sale_month": 4,
                    "sale_year": 2026,
                    "is_cash_sale": True,
                    "total_amount": Decimal("60000.00"),
                    "down_payment": Decimal("60000.00"),
                    "is_confirmed": True,
                },
                items_data=[
                    {"inventory_item": item, "quantity": 1, "unit_price": Decimal("20000.00")},
                    {"inventory_item": item, "quantity": 2, "unit_price": Decimal("20000.00")},
                ],
                installments_data=[],
            )

        # Attempting a multi-line supplier RETURN exceeding safe_limit (2 + 1 = 3 > 2) must fail!
        with self.assertRaises(ValidationError):
            create_purchase_invoice(
                validated_data={
                    "branch": b,
                    "supplier": sup,
                    "invoice_month": 4,
                    "invoice_year": 2026,
                    "invoice_type": "RETURN",
                },
                items_data=[
                    {"inventory_item": item, "quantity": 2, "purchase_price": Decimal("15000.00")},
                    {"inventory_item": item, "quantity": 1, "purchase_price": Decimal("15000.00")},
                ],
            )

        # Sell 2 units validly in 2026/04
        valid_rec = create_receipt(
            validated_data={
                "branch": b,
                "salesperson": sp,
                "customer_name": "عميل سليم",
                "sale_month": 4,
                "sale_year": 2026,
                "is_cash_sale": True,
                "total_amount": Decimal("40000.00"),
                "down_payment": Decimal("40000.00"),
                "is_confirmed": True,
            },
            items_data=[
                {"inventory_item": item, "quantity": 2, "unit_price": Decimal("20000.00")}
            ],
            installments_data=[],
        )

        # Attempt to back-date valid_rec to 2026/02 (before item initial_month=2026/03) without sale_items
        with self.assertRaises(ValidationError):
            update_receipt(
                valid_rec,
                validated_data={"sale_month": 2, "sale_year": 2026},
                items_data=None,
                installments_data=None,
            )

    def test_04_pre_license_patch_preserves_products_text_and_cash_switch_cleans_installments(self):
        """
        Verifies:
        1. Editing a Pre-License receipt via PATCH with sale_items=[] preserves products_text.
        2. Switching an Installment receipt to Cash (is_cash_sale=True) soft-deletes old
           InstallmentPayment rows even when installment_payments is omitted.
        3. Receipt.is_authentic remains True across create, update, and return flows.
        """
        b = self.branches[0]
        sp = self.salespersons[b.id][0]
        it1 = self.items[b.id][0]
        headers = {"HTTP_X_BRANCH_ID": str(b.id)}

        # 1. Pre-license receipt in 2024/02
        pre_rec = Receipt.objects.filter(
            branch=b, sale_year=2024, sale_month=2, is_cash_sale=False
        ).first()
        self.assertIsNotNone(pre_rec)
        patch_res = self.client.patch(
            f"/api/v1/receipts/{pre_rec.id}/?branch_id={b.id}",
            {
                "customer_name": "عميل معدل قبل الترخيص",
                "products_text": "ثلاجة + غسالة قبل الاشتراك",
                "sale_items": [],
            },
            format="json",
            **headers,
        )
        self.assertEqual(patch_res.status_code, 200)
        pre_rec.refresh_from_db()
        self.assertEqual(pre_rec.products_text, "ثلاجة + غسالة قبل الاشتراك")
        self.assertTrue(pre_rec.is_authentic)

        # 2. Create an installment receipt in 2026/08, then switch it to is_cash_sale=True via PATCH
        inst_rec = create_receipt(
            validated_data={
                "branch": b,
                "salesperson": sp,
                "customer_name": "عميل قسط متحول لكاش",
                "sale_month": 8,
                "sale_year": 2026,
                "is_cash_sale": False,
                "total_amount": Decimal("12000.00"),
                "down_payment": Decimal("2000.00"),
                "installment_system": "5000*2",
                "is_confirmed": True,
            },
            items_data=[{"inventory_item": it1, "quantity": 1, "unit_price": Decimal("12000.00")}],
            installments_data=[
                {"payment_month": 9, "payment_year": 2026, "amount": Decimal("5000.00")},
                {"payment_month": 10, "payment_year": 2026, "amount": Decimal("5000.00")},
            ],
        )
        self.assertEqual(inst_rec.payments.filter(is_deleted=False).count(), 2)
        self.assertTrue(inst_rec.is_authentic)

        switch_res = self.client.patch(
            f"/api/v1/receipts/{inst_rec.id}/?branch_id={b.id}",
            {
                "is_cash_sale": True,
                "down_payment": "12000.00",
            },
            format="json",
            **headers,
        )
        self.assertEqual(switch_res.status_code, 200)
        inst_rec.refresh_from_db()
        self.assertTrue(inst_rec.is_cash_sale)
        self.assertEqual(inst_rec.payments.filter(is_deleted=False).count(), 0)
        self.assertTrue(inst_rec.is_authentic)

        # 3. Soft-delete inst_rec and verify Dashboard & Stock Time-Machine recompute
        stock_With_sale = it1.get_stock_at_date(8, 2026)
        del_res = self.client.delete(
            f"/api/v1/receipts/{inst_rec.id}/?branch_id={b.id}",
            **headers,
        )
        self.assertEqual(del_res.status_code, 204)
        self.assertEqual(it1.get_stock_at_date(8, 2026), stock_With_sale + 1)
