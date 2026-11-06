import { useEffect } from 'react';
import api from '../../api';
import { parseInstallmentTextToBoxes } from './posUtils';

export default function usePOSDataLoader({
  editId,
  setSalespersons,
  setProducts,
  setSaleMonth,
  setSaleYear,
  setSalespersonId,
  setIsCashSale,
  setCustomerName,
  setPhoneNumber,
  setAddress,
  setArea,
  setDownPayment,
  setInstallmentDesc,
  setSystems,
  setItems,
  setProductsText,
  setManualTotalAmount,
  setLoadingInitial,
  setError,
  salespersonRef,
  isEditingRef
}) {
  useEffect(() => {
    const branchId = localStorage.getItem('branchId');
    setLoadingInitial(true);
    Promise.all([
      api.get(`/salespersons/?branch_id=${branchId}`).catch(() => ({ data: [] })),
      api.get(`/inventory-items/?branch_id=${branchId}`).catch(() => ({ data: [] })),
      editId ? api.get(`/receipts/${editId}/`).catch(() => null) : Promise.resolve(null),
    ]).then(([sRes, pRes, editRes]) => {
      const sps = Array.isArray(sRes.data?.results || sRes.data) ? (sRes.data?.results || sRes.data) : [];
      setSalespersons(sps);
      const itemsList = Array.isArray(pRes.data?.results || pRes.data) ? (pRes.data?.results || pRes.data) : [];
      setProducts(itemsList);

      if (editRes && editRes.data) {
        const r = editRes.data;
        setSaleMonth(r.sale_month);
        setSaleYear(r.sale_year);
        setSalespersonId(r.salesperson?.id || r.salesperson || '');
        setIsCashSale(r.is_cash_sale);
        setCustomerName(r.customer_name);
        setPhoneNumber(r.phone_number);
        setAddress(r.address);
        setArea(r.area);
        setDownPayment(r.down_payment);
        setInstallmentDesc(r.installment_system);

        if (r.installment_system) {
          setSystems(parseInstallmentTextToBoxes(r.installment_system));
        }

        if (r.products_text && setProductsText) {
          setProductsText(r.products_text);
        }
        if (r.total_amount && setManualTotalAmount) {
          setManualTotalAmount(String(r.total_amount));
        }

        if (r.sale_items && r.sale_items.length > 0) {
          setItems(r.sale_items.map((si, idx) => {
            const matchingInv = itemsList.find(inv => inv.id === si.inventory_item);
            return {
              id: si.id || Date.now() + idx,
              inventory_item: si.inventory_item,
              productName: matchingInv ? matchingInv.name : `صنف #${si.inventory_item}`,
              quantity: si.quantity,
              sell_price: parseFloat(si.unit_price || si.sell_price || 0),
            };
          }));
        }
      }
    }).catch(() => setError('فشل في جلب البيانات.')).finally(() => {
      setLoadingInitial(false);
      setTimeout(() => {
        if (!editId) salespersonRef.current?.focus();
      }, 150);
    });
    if (editId) {
      isEditingRef.current = true;
    } else {
      isEditingRef.current = false;
    }
  }, [editId]);
}
