import { useState } from 'react';
import toast from 'react-hot-toast';
import api from '../../api';
import { toEnglish } from './posUtils';

export default function usePOSSave({
  items,
  setItems,
  salespersonId,
  setSalespersonId,
  setSalespersonQuery,
  keepSalesperson,
  isCashSale,
  customerName,
  setCustomerName,
  phoneNumber,
  setPhoneNumber,
  address,
  setAddress,
  area,
  setArea,
  saleMonth,
  saleYear,
  downPayment,
  setDownPayment,
  installmentDesc,
  setInstallmentDesc,
  setSystems,
  totalAmount,
  totalPayments,
  isUnbalanced,
  allInstallments,
  editId,
  isEditingRef,
  navigate,
  fetchNextNumber,
  salespersonRef,
  custNameRef,
  prodQueryRef,
  isFreeTextMode,
  productsText,
  setProductsText,
  manualTotalAmount,
  setManualTotalAmount
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSave = async () => {
    setError('');
    if (isFreeTextMode) {
      if (!productsText || !productsText.trim()) {
        const msg = 'أدخل وصف البضاعة للأصناف.';
        setError(msg);
        toast.error(msg);
        return;
      }
      if (Number(totalAmount) <= 0) {
        const msg = 'أدخل إجمالي الفاتورة بشكل صحيح.';
        setError(msg);
        toast.error(msg);
        return;
      }
    } else {
      if (items.length === 0) { const msg = 'لا توجد أصناف في الفاتورة.'; setError(msg); toast.error(msg); return; }
    }
    if (!salespersonId) { const msg = 'اختر المندوب.'; setError(msg); toast.error(msg); return; }
    if (!isCashSale && !customerName.trim()) { const msg = 'أدخل اسم العميل.'; setError(msg); toast.error(msg); return; }
    if (!isCashSale && isUnbalanced) { const msg = 'إجمالي الأقساط والمقدم لا يتطابق مع إجمالي الفاتورة!'; setError(msg); toast.error(msg); return; }

    setSaving(true);
    const payload = {
      customer_name: isCashSale ? 'عميل نقدي' : toEnglish(customerName).trim(),
      phone_number: isCashSale ? '' : toEnglish(phoneNumber),
      address: isCashSale ? '' : toEnglish(address),
      area: toEnglish(area),
      salesperson: parseInt(salespersonId),
      sale_month: parseInt(saleMonth),
      sale_year: parseInt(saleYear),
      is_cash_sale: isCashSale,
      total_amount: isCashSale ? totalAmount : totalPayments,
      down_payment: isCashSale ? totalAmount : (parseFloat(toEnglish(downPayment)) || 0),
      installment_system: isCashSale ? '' : toEnglish(installmentDesc),
      products_text: isFreeTextMode ? productsText.trim() : undefined,
      sale_items: isFreeTextMode ? [] : items.map(i => ({ inventory_item: i.inventory_item, quantity: i.quantity, sell_price: i.sell_price })),
      installment_payments: isCashSale ? [] : allInstallments,
    };

    try {
      if (isEditingRef.current && editId) {
        await api.patch(`/receipts/${editId}/`, payload);
        isEditingRef.current = false;
        toast.success('تم تعديل الفاتورة بنجاح');
        navigate('/receipts');
        return;
      } else {
        await api.post('/receipts/', payload);
        toast.success('تم حفظ الفاتورة بنجاح');
      }
      
      setItems([]);
      if (isFreeTextMode) {
        if (setProductsText) setProductsText('');
        if (setManualTotalAmount) setManualTotalAmount('');
      }
      setCustomerName('');
      setPhoneNumber('');
      setAddress('');
      setArea('');
      setDownPayment('');
      setInstallmentDesc('');
      setSystems([{ count: '', amount: '' }, { count: '', amount: '' }, { count: '', amount: '' }]);
      
      if (!keepSalesperson) {
        setSalespersonId('');
        setSalespersonQuery('');
      }

      fetchNextNumber();

      if (isCashSale) {
        setTimeout(() => prodQueryRef.current?.focus(), 100);
      } else {
        if (!keepSalesperson) {
          setTimeout(() => salespersonRef.current?.focus(), 100);
        } else {
          setTimeout(() => custNameRef.current?.focus(), 100);
        }
      }
    } catch (err) {
      console.error(err);
      let errorMsg = 'حدث خطأ غير متوقع أثناء الحفظ.';
      if (err.response?.data) {
        const d = err.response.data;
        if (typeof d === 'string') {
          errorMsg = d;
        } else {
          let extracted = d.license || d.detail || d.error || d.non_field_errors;
          if (!extracted) {
            const firstKey = Object.keys(d)[0];
            if (firstKey && Array.isArray(d[firstKey])) {
              extracted = d[firstKey][0];
            } else if (firstKey && typeof d[firstKey] === 'string') {
              extracted = d[firstKey];
            }
          }
          if (Array.isArray(extracted)) extracted = extracted[0];
          if (extracted) errorMsg = extracted;
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error(errorMsg);
    } finally { 
      setSaving(false); 
    }
  };

  return { handleSave, saving, error, setError };
}
