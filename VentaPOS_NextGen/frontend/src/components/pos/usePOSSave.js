import { useState, useRef } from 'react';
import toast from 'react-hot-toast';
import api from '../../api';
import { toEnglish } from './posUtils';
import { parseStrictInt, parseWholeMoney, parseValidMonthYear } from '../../utils/formatUtils';
import { scheduleTransitionFocus } from '../../utils/focusUtils';

export default function usePOSSave({
  branchId,
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
  systems = [],
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
  const submittingRef = useRef(false);

  const handleSave = async () => {
    if (submittingRef.current) return;
    submittingRef.current = true;

    try {
      setError('');
      const activeBranchId = parseStrictInt(branchId ?? localStorage.getItem('branchId'), { min: 1 });
      if (activeBranchId === null) {
        const msg = 'اختر الفرع أولاً.';
        setError(msg);
        toast.error(msg);
        return;
      }

      const validDate = parseValidMonthYear(saleMonth, saleYear, { minYear: 2000, maxYear: 2100 });
      if (!validDate) {
        const msg = 'أدخل شهر وسنة صحيحين.';
        setError(msg);
        toast.error(msg);
        return;
      }

      if (isFreeTextMode) {
        if (!productsText || !productsText.trim()) {
          const msg = 'أدخل وصف البضاعة للأصناف.';
          setError(msg);
          toast.error(msg);
          return;
        }
        if (parseWholeMoney(manualTotalAmount, { min: 1 }) === null) {
          const msg = 'أدخل إجمالي الفاتورة بشكل صحيح.';
          setError(msg);
          toast.error(msg);
          return;
        }
      } else {
        if (items.length === 0) { const msg = 'لا توجد أصناف في الفاتورة.'; setError(msg); toast.error(msg); return; }
      }

      const validSalesperson = parseStrictInt(salespersonId, { min: 1 });
      if (validSalesperson === null) { const msg = 'اختر المندوب.'; setError(msg); toast.error(msg); return; }

      let downVal = Math.round(totalAmount);
      if (!isCashSale) {
        if (!customerName || !customerName.trim()) {
          const msg = 'أدخل اسم العميل.';
          setError(msg);
          toast.error(msg);
          return;
        }
        const trimmedDown = String(downPayment ?? '').trim();
        downVal = trimmedDown === '' ? 0 : parseWholeMoney(trimmedDown, { min: 0 });
        if (downVal === null) {
          const msg = 'أدخل قيمة مقدم صحيحة (0 أو أكثر).';
          setError(msg);
          toast.error(msg);
          return;
        }
        if (downVal > totalAmount) {
          const msg = 'المقدم لا يمكن أن يتجاوز إجمالي الفاتورة.';
          setError(msg);
          toast.error(msg);
          return;
        }
        for (const sys of systems) {
          const hasCount = String(sys?.count ?? '').trim() !== '';
          const hasAmt = String(sys?.amount ?? '').trim() !== '';
          if (hasCount || hasAmt) {
            const c = parseStrictInt(sys?.count, { min: 1, max: 360 });
            const a = parseWholeMoney(sys?.amount, { min: 1 });
            if (c === null || a === null) {
              const msg = 'أدخل عدد أشهر وقسط صحيحين (أكبر من صفر).';
              setError(msg);
              toast.error(msg);
              return;
            }
          }
        }
        if (isUnbalanced) {
          const msg = 'إجمالي الأقساط والمقدم لا يتطابق مع إجمالي الفاتورة!';
          setError(msg);
          toast.error(msg);
          return;
        }
      }

      setSaving(true);
      const roundedTotal = Math.round(isCashSale ? totalAmount : totalPayments);
      const payload = {
        branch: activeBranchId,
        customer_name: isCashSale ? 'عميل نقدي' : toEnglish(customerName).trim(),
        phone_number: isCashSale ? '' : toEnglish(phoneNumber).trim(),
        address: isCashSale ? '' : toEnglish(address).trim(),
        area: toEnglish(area).trim(),
        salesperson: validSalesperson,
        sale_month: validDate.month,
        sale_year: validDate.year,
        is_cash_sale: isCashSale,
        total_amount: roundedTotal,
        down_payment: isCashSale ? roundedTotal : downVal,
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
          scheduleTransitionFocus(prodQueryRef, 100);
        } else {
          if (!keepSalesperson) {
            scheduleTransitionFocus(salespersonRef, 100);
          } else {
            scheduleTransitionFocus(custNameRef, 100);
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
      }
    } finally {
      submittingRef.current = false;
      setSaving(false);
    }
  };

  return { handleSave, saving, error, setError };
}
