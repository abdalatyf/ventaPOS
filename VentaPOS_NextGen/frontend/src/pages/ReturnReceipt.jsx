import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '../api';
import { useActiveBranch } from '../hooks/useActiveBranch';
import { parseStrictInt, parseWholeMoney, parseValidMonthYear, formatMMYYYY } from '../utils/formatUtils';
import { IconArrowLeft, IconReceiptRefund, IconCheck } from '@tabler/icons-react';

export default function ReturnReceipt() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { branchId } = useActiveBranch();

  const [receipt, setReceipt] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Object mapping sale_item index (or id) to return quantity
  const [returnedItems, setReturnedItems] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const submittingRef = useRef(false);
  const prevBranchIdRef = useRef(branchId);

  const [returnMonth, setReturnMonth] = useState(new Date().getMonth() + 1);
  const [returnYear, setReturnYear] = useState(new Date().getFullYear());

  // Installment groups for new debt
  const [groups, setGroups] = useState([
    { amount: '', count: '' },
    { amount: '', count: '' },
    { amount: '', count: '' }
  ]);
  const [schedule, setSchedule] = useState([]);

  // Redirect if branch switches mid-return
  useEffect(() => {
    const prevBranch = prevBranchIdRef.current;
    if (prevBranch === branchId) return;
    prevBranchIdRef.current = branchId;
    if (prevBranch !== null) {
      toast.error('تم تغيير الفرع — تم الخروج من شاشة المرتجع.');
      navigate('/receipts', { replace: true });
    }
  }, [branchId, navigate]);

  // Fetch receipt
  useEffect(() => {
    let cancelled = false;
    const fetchReceipt = async () => {
      try {
        const res = await api.get(`/receipts/${id}/`);
        if (cancelled) return;
        const fetchedReceipt = res.data;
        const activeBranch = branchId || localStorage.getItem('branchId');
        if (fetchedReceipt.branch && activeBranch && String(fetchedReceipt.branch) !== String(activeBranch)) {
          toast.error('الفاتورة تنتمي لفرع آخر.');
          navigate('/receipts', { replace: true });
          return;
        }
        setReceipt(fetchedReceipt);
        
        let minM = fetchedReceipt.sale_month + 1;
        let minY = fetchedReceipt.sale_year;
        if (minM > 12) {
          minM = 1;
          minY++;
        }
        
        const today = new Date();
        const curM = today.getMonth() + 1;
        const curY = today.getFullYear();
        
        // Default to min allowed date if current date is before it
        if (curY < minY || (curY === minY && curM < minM)) {
          setReturnMonth(minM);
          setReturnYear(minY);
        }
      } catch (err) {
        if (!cancelled) {
          console.error(err);
          toast.error('حدث خطأ أثناء جلب تفاصيل الفاتورة');
          navigate(-1);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchReceipt();
    return () => { cancelled = true; };
  }, [id, navigate, branchId]);

  const toEnglish = (str) => {
    if (str === undefined || str === null) return '';
    return String(str)
      .replace(/[٠-٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
      .replace(/×/g, '*')
      .replace(/،/g, ',');
  };

  const fmt = (val) => {
    if (val === undefined || val === null) return 0;
    const clean = toEnglish(String(val)).replace(/,/g, '');
    const p = parseFloat(clean);
    return isNaN(p) ? 0 : p;
  };

  const formatCurrency = val => {
    if (val === undefined || val === null || val === '') return '0 ج.م';
    const num = parseFloat(val);
    return isNaN(num) ? '0 ج.م' : `${Math.round(num).toLocaleString('en-US')} ج.م`;
  };

  // Generate Schedule based on groups
  useEffect(() => {
    const validDate = parseValidMonthYear(returnMonth, returnYear, { minYear: 2000, maxYear: 2100 });
    if (!validDate) {
      setSchedule([]);
      return;
    }

    const newSchedule = [];
    let cMonth = validDate.month + 1;
    let cYear = validDate.year;
    if (cMonth > 12) {
      cMonth = 1;
      cYear++;
    }

    groups.forEach(g => {
      const amt = parseWholeMoney(g.amount, { min: 1 });
      const cnt = parseStrictInt(g.count, { min: 1, max: 360 });
      if (amt !== null && cnt !== null) {
        for (let i = 0; i < cnt; i++) {
          newSchedule.push({ month: cMonth, year: cYear, amount: amt });
          cMonth++;
          if (cMonth > 12) {
            cMonth = 1;
            cYear++;
          }
        }
      }
    });
    setSchedule(newSchedule);
  }, [groups, returnMonth, returnYear]);

  const handleGroupChange = (index, field, value) => {
    setGroups(prev => prev.map((g, idx) => (idx === index ? { ...g, [field]: value } : g)));
  };

  const handleIncrement = (idx, maxQty) => {
    setReturnedItems(prev => {
      const current = prev[idx] || 0;
      if (current >= maxQty) return prev;
      return { ...prev, [idx]: current + 1 };
    });
  };

  const handleDecrement = (idx) => {
    setReturnedItems(prev => {
      const current = prev[idx] || 0;
      if (current <= 0) return prev;
      return { ...prev, [idx]: current - 1 };
    });
  };

  if (loading) {
    return (
      <div className="container-fluid py-5 text-center">
        <div className="spinner-border text-primary mb-3"></div>
        <h4>جاري تحميل بيانات الفاتورة...</h4>
      </div>
    );
  }

  if (!receipt) return null;

  // Calculations
  let totalReturnValue = 0;
  const itemsToReturn = [];
  receipt.sale_items?.forEach((item, idx) => {
    const retQty = returnedItems[idx] || 0;
    if (retQty > 0) {
      const price = fmt(item.unit_price || item.sell_price || item.purchase_price);
      totalReturnValue += retQty * price;
      itemsToReturn.push({
        inventory_item_id: item.inventory_item || item.inventory_item_id,
        quantity: retQty,
        unit_price: price
      });
    }
  });

  const parsedRetDate = parseValidMonthYear(returnMonth, returnYear, { minYear: 2000, maxYear: 2100 });
  const cmpMonth = parsedRetDate ? parsedRetDate.month : 0;
  const cmpYear = parsedRetDate ? parsedRetDate.year : 0;

  // Calculate Paid So Far (Downpayment + Past Installments)
  const isPastInstallment = (inst) => {
    if (!parsedRetDate) return false;
    if (!inst.payment_date) {
      if (inst.payment_year < cmpYear) return true;
      if (inst.payment_year === cmpYear && inst.payment_month < cmpMonth) return true;
      return false;
    }
    const d = new Date(inst.payment_date);
    if (d.getFullYear() < cmpYear) return true;
    if (d.getFullYear() === cmpYear && (d.getMonth() + 1) < cmpMonth) return true;
    return false;
  };

  const pastInstallments = (receipt.installment_payments || []).filter(isPastInstallment);
  const paidInstallmentsSum = pastInstallments.reduce((sum, inst) => sum + fmt(inst.amount), 0);
  const paidSoFar = fmt(receipt.down_payment) + paidInstallmentsSum;
  
  const originalTotal = fmt(receipt.total_amount);
  const newInvoiceTotal = originalTotal - totalReturnValue;
  const newDebt = newInvoiceTotal - paidSoFar;
  
  const totalNewInstallments = schedule.reduce((sum, item) => sum + item.amount, 0);
  
  const handleSubmit = async () => {
    if (submittingRef.current) return;
    submittingRef.current = true;

    try {
      if (itemsToReturn.length === 0) {
        toast.error('لم يتم تحديد أي أصناف للإرجاع!');
        return;
      }

      const validDate = parseValidMonthYear(returnMonth, returnYear, { minYear: 2000, maxYear: 2100 });
      if (!validDate) {
        toast.error('أدخل شهر وسنة مرتجع صحيحين.');
        return;
      }

      let minM = receipt.sale_month + 1;
      let minY = receipt.sale_year;
      if (minM > 12) {
        minM = 1;
        minY++;
      }

      if (validDate.year < minY || (validDate.year === minY && validDate.month < minM)) {
        toast.error(`تاريخ المرتجع لا يمكن أن يكون قبل الشهر التالي لتاريخ البيع (${formatMMYYYY(minM, minY)})`);
        return;
      }

      if (!receipt.is_cash_sale && newDebt > 0) {
        for (const g of groups) {
          const hasAmt = String(g.amount ?? '').trim() !== '';
          const hasCnt = String(g.count ?? '').trim() !== '';
          if ((hasAmt || hasCnt) && (parseWholeMoney(g.amount, { min: 1 }) === null || parseStrictInt(g.count, { min: 1, max: 360 }) === null)) {
            toast.error('أدخل قيمة قسط وعدد شهور صحيحين (أكبر من صفر).');
            return;
          }
        }
        if (Math.abs(totalNewInstallments - newDebt) > 0.01) {
          toast.error(`يجب أن يتطابق إجمالي الأقساط الجديدة (${Math.round(totalNewInstallments).toLocaleString('en-US')}) مع المديونية المتبقية (${Math.round(newDebt).toLocaleString('en-US')}).`);
          return;
        }
      }

      const activeGroups = groups
        .map(g => ({ amount: parseWholeMoney(g.amount, { min: 1 }), count: parseStrictInt(g.count, { min: 1, max: 360 }) }))
        .filter(g => g.amount !== null && g.count !== null);
      const installmentSystemStr = activeGroups.map(g => `${g.amount}*${g.count}`).join(" + ");

      const payload = {
        returned_items: itemsToReturn,
        return_value: Math.round(totalReturnValue),
        return_month: validDate.month,
        return_year: validDate.year,
        new_installments: newDebt > 0 ? schedule.map(s => ({
          payment_month: s.month,
          payment_year: s.year,
          amount: Math.round(s.amount)
        })) : [],
        new_installment_system: newDebt > 0 ? installmentSystemStr : ""
      };

      setSubmitting(true);
      try {
        await api.post(`/receipts/${id}/return_receipt/`, payload);
        toast.success('تم تسجيل المرتجع بنجاح!');
        navigate('/receipts');
      } catch (err) {
        console.error(err);
        toast.error('حدث خطأ: ' + (err.response?.data?.error || err.message));
      }
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  };

  return (
    <div className="container-fluid pb-3 px-3 fs-3 pt-3" dir="rtl" style={{ fontSize: '1.02rem' }}>
      <div className="page-header d-print-none mb-4">
        <div className="row align-items-center">
          <div className="col">
            <h2 className="page-title text-primary d-flex align-items-center gap-2">
              <IconReceiptRefund size={28} />
              استرجاع بضاعة من الفاتورة #{receipt.receipt_number || receipt.id}
            </h2>
            <div className="text-secondary mt-1">
              العميل: {receipt.customer_name || 'عميل نقدي'} | إجمالي الفاتورة: {formatCurrency(receipt.total_amount)}
            </div>
          </div>
          <div className="col-auto ms-auto">
            <Link to="/receipts" className="btn btn-outline-secondary d-flex align-items-center gap-2">
              <IconArrowLeft size={18} /> رجوع للدفتر
            </Link>
          </div>
        </div>
      </div>

      <div className="row">
        {/* Cart selection */}
        <div className="col-lg-7">
          <div className="card shadow-sm border-secondary-subtle mb-2" style={{ position: 'relative', zIndex: 30 }}>
            <div className="card-header bg-light">
              <h3 className="card-title m-0">تحديد الأصناف المسترجعة</h3>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive" style={{ minHeight: 200, maxHeight: 'calc(100vh - 380px)', overflowY: 'auto' }}>
                <table className="table table-vcenter table-hover table-sm text-nowrap tabular-nums mb-0 table-sticky-header" style={{ fontSize: '0.95rem' }}>
                  <thead className="bg-light">
                    <tr>
                      <th>الصنف</th>
                      <th className="text-center">السعر</th>
                      <th className="text-center">المباع</th>
                      <th className="text-center">كمية الاسترجاع</th>
                      <th className="text-end px-3">إجمالي الخصم</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(receipt.sale_items || []).map((item, idx) => {
                      const pName = item.productName || item.product_name || item.inventory_item_name || `صنف #${item.inventory_item}`;
                      const qty = fmt(item.quantity) || 1;
                      const price = fmt(item.unit_price || item.sell_price || item.purchase_price);
                      const retQty = returnedItems[idx] || 0;
                      
                      return (
                        <tr key={idx} className={retQty > 0 ? 'bg-danger-lt' : ''}>
                          <td className="fw-bold">{pName}</td>
                          <td className="text-center">{formatCurrency(price)}</td>
                          <td className="text-center">{qty}</td>
                          <td className="text-center">
                            <div className="input-group input-group-sm justify-content-center" style={{ width: '120px', margin: '0 auto' }}>
                              <button className="btn btn-outline-secondary" type="button" onClick={() => handleDecrement(idx)}>-</button>
                              <input type="text" className="form-control py-1 fs-4 text-center fw-bold border-secondary-subtle" value={retQty} readOnly style={{ borderColor: '#adb5bd' }} />
                              <button className="btn btn-outline-secondary" type="button" onClick={() => handleIncrement(idx, qty)}>+</button>
                            </div>
                          </td>
                          <td className="text-end px-3 fw-bold text-danger">
                            {retQty > 0 ? formatCurrency(retQty * price) : '0 ج.م'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="card-footer bg-light d-flex justify-content-between align-items-center">
              <span className="fw-bold">إجمالي المرتجع:</span>
              <span className="fs-3 fw-bolder text-danger">{formatCurrency(totalReturnValue)}</span>
            </div>
          </div>
        </div>

        {/* Financials & Reschedule */}
        <div className="col-lg-5">
          <div className="card shadow-sm border-secondary-subtle mb-2" style={{ position: 'relative', zIndex: 30 }}>
            <div className="card-header bg-primary text-white">
              <h3 className="card-title m-0 text-white">الخلاصة المالية وإعادة الجدولة</h3>
            </div>
            <div className="card-body p-4">
              <div className="row mb-4">
                <div className="col-6">
                  <label className="form-label fw-bold">شهر المرتجع</label>
                  <input 
                    type="text"
                    inputMode="numeric"
                    dir="ltr"
                    className="form-control text-center fw-bold" 
                    value={returnMonth} 
                    placeholder="شهر" 
                    onChange={(e) => setReturnMonth(e.target.value)} 
                    required 
                  />
                </div>
                <div className="col-6">
                  <label className="form-label fw-bold">سنة المرتجع</label>
                  <input 
                    type="text"
                    inputMode="numeric"
                    dir="ltr"
                    className="form-control text-center fw-bold" 
                    value={returnYear} 
                    placeholder="سنة" 
                    onChange={(e) => setReturnYear(e.target.value)} 
                    required 
                  />
                </div>
              </div>
              
              <div className="d-flex justify-content-between mb-3 border-bottom pb-2">
                <span className="text-secondary">إجمالي الفاتورة الأصلية:</span>
                <span className="fw-bold">{formatCurrency(originalTotal)}</span>
              </div>
              <div className="d-flex justify-content-between mb-3 border-bottom pb-2">
                <span className="text-danger fw-bold">قيمة المرتجع:</span>
                <span className="fw-bold text-danger">- {formatCurrency(totalReturnValue)}</span>
              </div>
              <div className="d-flex justify-content-between mb-3 border-bottom pb-2">
                <span className="text-secondary">ما سدده العميل (مقدم + أقساط قديمة):</span>
                <span className="fw-bold text-success">{formatCurrency(paidSoFar)}</span>
              </div>
              <div className="d-flex justify-content-between mb-4 bg-light p-2 rounded">
                <span className="fw-bold fs-4">المديونية المتبقية / الرصيد الجديد:</span>
                <span className={`fw-bolder fs-3 ${newDebt > 0 ? 'text-danger' : 'text-success'}`}>
                  {newDebt > 0 ? formatCurrency(newDebt) : formatCurrency(0)}
                </span>
              </div>

              {receipt.is_cash_sale && (
                <div className="alert alert-info fw-bold">
                  هذه فاتورة نقدية. سيتم سحب {formatCurrency(totalReturnValue)} من نقدية اليوم وإرجاعها للعميل.
                </div>
              )}

              {!receipt.is_cash_sale && newDebt <= 0 && totalReturnValue > 0 && (
                <div className="alert alert-success fw-bold d-flex align-items-center gap-2">
                  <IconCheck size={24} />
                  العميل يستحق استرداد مبلغ {formatCurrency(Math.abs(newDebt))} نقداً!
                  <br />
                  تم سداد الفاتورة بالكامل وسيتم إلغاء جميع الأقساط القادمة.
                </div>
              )}

              {!receipt.is_cash_sale && newDebt > 0 && totalReturnValue > 0 && (
                <div className="mt-4">
                  <h4 className="fw-bold text-primary mb-3">حدد نظام التقسيط للمبلغ المتبقي ({formatCurrency(newDebt)})</h4>
                  {groups.map((group, idx) => (
                    <div className="row g-2 mb-2 align-items-center" key={idx}>
                      <div className="col">
                        <input type="text" className="form-control py-1 fs-3 border-secondary-subtle text-center fw-bold" placeholder={`قسط ${idx + 1}`} 
                          value={group.amount} onChange={e => handleGroupChange(idx, 'amount', e.target.value)} style={{ borderColor: '#adb5bd' }} />
                      </div>
                      <div className="col-auto text-center px-1 fw-bold fs-4">×</div>
                      <div className="col">
                        <input type="text" className="form-control py-1 fs-3 border-secondary-subtle text-center fw-bold" placeholder={`عدد الشهور`}
                          value={group.count} onChange={e => handleGroupChange(idx, 'count', e.target.value)} style={{ borderColor: '#adb5bd' }} />
                      </div>
                    </div>
                  ))}
                  <div className={`mt-3 text-end fw-bold ${Math.abs(totalNewInstallments - newDebt) < 0.01 ? 'text-success' : 'text-danger'}`}>
                    مجموع الأقساط الجديدة: {formatCurrency(totalNewInstallments)}
                  </div>
                </div>
              )}

              <button 
                className="btn btn-primary w-100 mt-4 py-2 fs-4 fw-bold" 
                disabled={submitting || totalReturnValue === 0}
                onClick={handleSubmit}
              >
                {submitting ? 'جاري الحفظ...' : 'تأكيد المرتجع'}
              </button>

            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
