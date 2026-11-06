import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { IconPackage } from '@tabler/icons-react';
import toast from 'react-hot-toast';
import api from '../api';
import { useDefaultDate } from '../hooks/useDefaultDate';
import { parseNumber } from '../utils/formatUtils';

import LedgerHeader from '../components/ledger/LedgerHeader';
import LedgerMetricsCards from '../components/ledger/LedgerMetricsCards';
import LedgerCommissionForm from '../components/ledger/LedgerCommissionForm';
import LedgerDeficitForm from '../components/ledger/LedgerDeficitForm';
import LedgerTimelineTable from '../components/ledger/LedgerTimelineTable';

export default function ProductLedger() {
  const { id: paramId } = useParams();
  const navigate = useNavigate();

  const [allProducts, setAllProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState(paramId || '');
  const [productSearchQuery, setProductSearchQuery] = useState('');
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const currentBranchId = localStorage.getItem('branchId') || 1;
  const { defaultYear, defaultMonth } = useDefaultDate(currentBranchId);

  // Commission Change Form State
  const [showCommissionForm, setShowCommissionForm] = useState(false);
  const [commSubmitting, setCommSubmitting] = useState(false);
  const [commForm, setCommForm] = useState({
    amount: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
  });

  // Deficit Registration Form State
  const [showDeficitForm, setShowDeficitForm] = useState(false);
  const [deficitSubmitting, setDeficitSubmitting] = useState(false);
  const [deficitForm, setDeficitForm] = useState({
    quantity: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
    reason: '',
  });

  // Keep form dates in sync when defaultDate is loaded
  useEffect(() => {
    if (defaultMonth && defaultYear) {
      setCommForm(prev => ({ ...prev, month: defaultMonth, year: defaultYear }));
      setDeficitForm(prev => ({ ...prev, month: defaultMonth, year: defaultYear }));
    }
  }, [defaultMonth, defaultYear]);

  // Filter state for timeline
  const [eventFilter, setEventFilter] = useState('ALL');

  // Load all products for the autocomplete selector
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const res = await api.get('/inventory-items/', { params: { branch_id: currentBranchId } });
        const list = res.data.results || res.data || [];
        setAllProducts(list);
        
        if (paramId) {
          const found = list.find(p => String(p.id) === String(paramId));
          if (found) {
            setProductSearchQuery(found.name);
          }
        }
      } catch (err) {
        console.error('Error fetching products list:', err);
      }
    };
    fetchProducts();
  }, [paramId, currentBranchId]);

  // Sync state if URL param changes
  useEffect(() => {
    if (paramId && paramId !== selectedProductId) {
      setSelectedProductId(paramId);
    }
  }, [paramId]);

  // Fetch product ledger when selectedProductId changes
  const fetchLedger = async (targetId) => {
    const idToFetch = targetId || selectedProductId;
    if (!idToFetch) {
      setData(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/inventory-items/${idToFetch}/ledger/`);
      setData(res.data);
      if (res.data?.item) {
        setProductSearchQuery(res.data.item.name);
      }
    } catch (err) {
      console.error('Error fetching ledger:', err);
      setError('حدث خطأ أثناء تحميل سجل حياة الصنف. يرجى التأكد من اختيار صنف صالح.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProductId) {
      fetchLedger(selectedProductId);
    } else {
      setData(null);
    }
  }, [selectedProductId]);

  // Product selector handler
  const handleSelectProduct = (prod) => {
    if (prod && prod.id) {
      setSelectedProductId(prod.id);
      setProductSearchQuery(prod.name);
      navigate(`/product-ledger/${prod.id}`, { replace: true });
    } else {
      setSelectedProductId('');
      setProductSearchQuery('');
      setData(null);
      navigate(`/product-ledger`, { replace: true });
    }
  };

  // Commission update submit
  const handleCommissionSubmit = async (e) => {
    e.preventDefault();
    if (!commForm.amount || !commForm.month || !commForm.year) {
      toast.error('يرجى إدخال قيمة المندبة والشهر والسنة.');
      return;
    }

    const cleanAmount = parseNumber(commForm.amount);
    if (cleanAmount < 0) {
      toast.error('قيمة المندبة لا يمكن أن تكون سالبة.');
      return;
    }

    try {
      setCommSubmitting(true);
      await api.post('/commission-histories/', {
        item: selectedProductId,
        commission_amount: cleanAmount,
        activation_month: Math.round(parseNumber(commForm.month)),
        activation_year: Math.round(parseNumber(commForm.year)),
      });

      toast.success('تم تسجيل المندبة الجديدة بنجاح');
      setShowCommissionForm(false);
      setCommForm(prev => ({ ...prev, amount: '' }));
      fetchLedger(selectedProductId);
    } catch (err) {
      console.error('Error saving commission:', err);
      const msg = err.response?.data?.detail || err.response?.data?.error || 'فشل في حفظ المندبة الجديدة.';
      toast.error(msg);
    } finally {
      setCommSubmitting(false);
    }
  };

  // Deficit update submit
  const handleDeficitSubmit = async (e) => {
    e.preventDefault();
    if (!deficitForm.quantity || !deficitForm.month || !deficitForm.year) {
      toast.error('يرجى إدخال كمية العجز والشهر والسنة.');
      return;
    }

    const cleanQty = Math.round(parseNumber(deficitForm.quantity));
    if (cleanQty <= 0) {
      toast.error('الكمية يجب أن تكون أكبر من صفر.');
      return;
    }

    try {
      setDeficitSubmitting(true);
      await api.post('/inventory-adjustments/', {
        item: selectedProductId,
        adjustment_type: 'DEFICIT',
        quantity: cleanQty,
        month: Math.round(parseNumber(deficitForm.month)),
        year: Math.round(parseNumber(deficitForm.year)),
        reason: deficitForm.reason.trim() || 'عجز مخزن',
      });

      toast.success('تم تسجيل العجز بنجاح وتحديث كارت الصنف');
      setShowDeficitForm(false);
      setDeficitForm(prev => ({ ...prev, quantity: '', reason: '' }));
      fetchLedger(selectedProductId);
    } catch (err) {
      console.error('Error recording deficit:', err);
      const msg = err.response?.data?.detail || err.response?.data?.error || 'فشل في تسجيل العجز.';
      toast.error(msg);
    } finally {
      setDeficitSubmitting(false);
    }
  };

  const itemInfo = data?.item || null;
  const metrics = data?.dashboard_metrics || {};
  const timeline = data?.timeline || [];
  const monthlySummary = data?.monthly_summary || [];

  // Filtered timeline
  const filteredTimeline = useMemo(() => {
    if (eventFilter === 'ALL') return timeline;
    return timeline.filter(ev => {
      if (eventFilter === 'PURCHASES') return ev.type === 'PURCHASE' || ev.type === 'RETURN';
      if (eventFilter === 'SALES') return ev.type === 'SALE' || ev.type === 'SALE_RETURN';
      if (eventFilter === 'DEFICITS') return ev.type === 'DEFICIT';
      if (eventFilter === 'COMMISSIONS') return ev.type === 'COMMISSION_CHANGE';
      return true;
    });
  }, [timeline, eventFilter]);

  return (
    <div className="container-fluid py-3" dir="rtl">
      {/* Top Header & Product Selector */}
      <LedgerHeader
        allProducts={allProducts}
        productSearchQuery={productSearchQuery}
        setProductSearchQuery={setProductSearchQuery}
        handleSelectProduct={handleSelectProduct}
      />

      {error && <div className="alert alert-danger shadow-sm mb-3">{error}</div>}

      {loading && (
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status"></div>
          <div className="text-muted mt-2 fw-semibold">جاري جلب سجل العمليات وأسعار الشراء...</div>
        </div>
      )}

      {!loading && !selectedProductId && (
        <div className="card shadow-sm text-center py-5 border-0">
          <div className="card-body">
            <IconPackage size={64} className="text-muted mb-3 opacity-50" />
            <h3 className="fw-bold text-secondary">اختر صنفاً من الشريط العلوي</h3>
            <p className="text-muted">لعرض كارت الصنف وسجل الحركات وأسعار الشراء التاريخية وتعديلات المندبة.</p>
          </div>
        </div>
      )}

      {!loading && selectedProductId && itemInfo && (
        <>
          {/* Top 6 KPI Summary Cards */}
          <LedgerMetricsCards itemInfo={itemInfo} metrics={metrics} />

          {/* Action Panels: Change Commission & Record Deficit */}
          <div className="row g-2 mb-3">
            <div className="col-lg-6">
              <LedgerCommissionForm
                showCommissionForm={showCommissionForm}
                setShowCommissionForm={setShowCommissionForm}
                commForm={commForm}
                setCommForm={setCommForm}
                handleCommissionSubmit={handleCommissionSubmit}
                commSubmitting={commSubmitting}
              />
            </div>
            <div className="col-lg-6">
              <LedgerDeficitForm
                showDeficitForm={showDeficitForm}
                setShowDeficitForm={setShowDeficitForm}
                deficitForm={deficitForm}
                setDeficitForm={setDeficitForm}
                handleDeficitSubmit={handleDeficitSubmit}
                deficitSubmitting={deficitSubmitting}
              />
            </div>
          </div>

          {/* Full Chronological Timeline Table & Monthly Summary */}
          <LedgerTimelineTable
            filteredTimeline={filteredTimeline}
            eventFilter={eventFilter}
            setEventFilter={setEventFilter}
            monthlySummary={monthlySummary}
          />
        </>
      )}
    </div>
  );
}
