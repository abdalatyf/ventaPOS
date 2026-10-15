import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '../api';
import { IconArrowRight, IconDeviceFloppy, IconTrash } from '@tabler/icons-react';

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmt = (n) => (parseFloat(n) || 0).toLocaleString('en-US', { minimumFractionDigits: 2 });

function genSchedule(count, amount, startMonth, startYear) {
  const rows = [];
  let m = parseInt(startMonth), y = parseInt(startYear);
  let countInt = parseInt(count || 0);
  if (countInt > 360) countInt = 360;
  for (let i = 0; i < countInt; i++) {
    m++; if (m > 12) { m = 1; y++; }
    if (parseFloat(amount) > 0) rows.push({ payment_month: m, payment_year: y, amount: parseFloat(amount) });
  }
  return rows;
}

// ── Arabic Digits Conversion Helpers ──────────────────────────────────────────


const toEnglish = (str) => {
  if (str === undefined || str === null) return '';
  return String(str)
    .replace(/[٠-٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
    .replace(/×/g, '*')
    .replace(/،/g, ',');
};

// ── Suggestion List Component ────────────────────────────────────────────────
const SuggestionList = ({ open, suggestions, activeIndex, onSelect }) => {
  if (!open || !suggestions.length) return null;
    const activeItemRef = useRef(null);
  
  useEffect(() => {
    if (open && activeItemRef.current) {
      activeItemRef.current.scrollIntoView({ block: 'nearest' });
    }
  }, [activeIndex, open]);

  return (
    <ul tabIndex="-1" className="list-group shadow position-absolute w-100 bg-white"
      onMouseDown={(e) => e.preventDefault()}
      style={{ zIndex: 1055, top: '100%', maxHeight: 200, overflowY: 'auto', border: '1px solid #d8dee4' }}>
      {suggestions.map((s, i) => (
        <li
          key={i}
          className={`list-group-item list-group-item-action py-2 cursor-pointer border-bottom ${i === activeIndex ? '' : 'bg-white'}`} style={i === activeIndex ? { backgroundColor: '#f1f5f9', color: '#1e293b' } : {}}
          onMouseDown={() => onSelect(s)}
          ref={i === activeIndex ? activeItemRef : null}
          
        >
          {typeof s === 'string' ? s : (
              <>
                <div className="fw-bold">{s.customer_name || s.name || s.value || ''}</div>
                {s.phone_number && <div className="text-muted small">{s.phone_number} · {s.area}</div>}
              </>
            )}
        </li>
      ))}
    </ul>
  );
};

// ── Inline Label Row ──────────────────────────────────────────────────────────
const Field = ({ label, children, labelCol = 'col-sm-3', inputCol = 'col-sm-9', className = '' }) => (
  <div className={`row mb-2 align-items-center ${className}`}>
    <label className={`${labelCol} col-form-label fw-bold text-dark pe-1`}>{label}</label>
    <div className={inputCol}>{children}</div>
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════════
const POS = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const editId = searchParams.get('edit');

  const [salespersons, setSalespersons]   = useState([]);
  const [products, setProducts]           = useState([]);
  const [loadingInitial, setLoadingInitial] = useState(true);

  // ── Invoice Meta
  const [saleMonth, setSaleMonth]         = useState(new Date().getMonth() + 1);
  const [saleYear, setSaleYear]           = useState(new Date().getFullYear());
  const [salespersonId, setSalespersonId] = useState('');
  const [keepSalesperson, setKeepSalesperson] = useState(false);
  const [salespersonQuery, setSalespersonQuery] = useState('');
  const salespersonRef = useRef(null);
  const [isCashSale, setIsCashSale]       = useState(false);

  // ── Customer Fields (represented in Arabic digits inside React state)
  const [customerName, setCustomerName]   = useState('');
  const [phoneNumber, setPhoneNumber]     = useState('');
  const [area, setArea]                   = useState('');
  const [address, setAddress]             = useState('');

  // ── Cart
  const [items, setItems]                 = useState([]);
  const [productQuery, setProductQuery]   = useState('');
  const [productSuggestions, setProductSuggestions] = useState([]);
  const [productDropOpen, setProductDropOpen]       = useState(false);
  const [selectedProduct, setSelectedProduct]       = useState(null);
  const [quantity, setQuantity]           = useState(1);
  const [sellPrice, setSellPrice]         = useState('');
  const [itemError, setItemError]         = useState('');

  // ── History Tracking ──────────────────────────────────────────────────────────
  const [historyCursors, setHistoryCursors] = useState({ name: null, phone: null, area: null, address: null });
  const [nextReceiptNumber, setNextReceiptNumber] = useState(null);

  const fetchNextNumber = async () => {
    try {
      const res = await api.get('receipts-next-number/');
      setNextReceiptNumber(res.data.next_receipt_number);
    } catch (err) {
      console.error('Failed to fetch next receipt number', err);
    }
  };

  useEffect(() => {
    fetchNextNumber();
  }, []);


  // ── Payment
  const [downPayment, setDownPayment]     = useState('');
  const [installmentDesc, setInstallmentDesc] = useState('');
  const [systems, setSystems]             = useState([
    { count: '', amount: '' },
    { count: '', amount: '' },
    { count: '', amount: '' },
  ]);

  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState('');
  const [debugMsg, setDebugMsg] = useState('Init');

  // ── Autocomplete / Suggestions State
  const [suggestions, setSuggestions] = useState([]);
  const [activeInput, setActiveInput] = useState(''); // 'name', 'phone', 'area', 'address', 'product'
  const [activeIndex, setActiveIndex] = useState(-1);
  const suggestTimerRef = useRef(null);
  const blurTimerRef = useRef(null);
  const activeRequestFieldRef = useRef(null);
  const isEditingRef = useRef(false);

  const qtyRef       = useRef(null);
  const priceRef     = useRef(null);
  const prodQueryRef = useRef(null);
  const custNameRef  = useRef(null);

  // ── Fetch Initial Data ────────────────────────────────────────────────────
  useEffect(() => {
    const branchId = localStorage.getItem('branchId');
    setLoadingInitial(true);
    Promise.all([
      api.get(`/salespersons/?branch_id=${branchId}`).catch(() => ({ data: [] })),
      api.get(`/inventory-items/?branch_id=${branchId}`).catch(() => ({ data: [] })),
      editId ? api.get(`/receipts/${editId}/`).catch(() => null) : Promise.resolve(null),
    ]).then(([sRes, pRes, editRes]) => {
      setSalespersons(Array.isArray(sRes.data?.results || sRes.data) ? (sRes.data?.results || sRes.data) : []);
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
          const cleanText = toEnglish(r.installment_system);
          const parts = cleanText.split('+');
          const newSystems = [
            { count: '', amount: '' },
            { count: '', amount: '' },
            { count: '', amount: '' }
          ];
          parts.forEach((part, index) => {
            if (index >= 3) return;
            let [val1, val2] = part.trim().split('*');
            if (val1 && val2) {
              let v1 = parseInt(val1) || 0;
              let v2 = parseInt(val2) || 0;
              let amount, count;
              if (v2 > 20) {
                amount = v2;
                count = v1;
              } else {
                amount = v1;
                count = v2;
              }
              newSystems[index] = {
                count: count,
                amount: amount
              };
            }
          });
          setSystems(newSystems);
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

  // ── Derived Values ────────────────────────────────────────────────────────
  const totalAmount = useMemo(() => {
    return items.reduce((s, i) => s + i.quantity * i.sell_price, 0);
  }, [items]);

  const totalPayments = useMemo(() => {
    const down = parseFloat(toEnglish(downPayment)) || 0;
    const sysTotal = systems.reduce((s, sys) => {
      const count = parseInt(toEnglish(sys.count)) || 0;
      const amount = parseFloat(toEnglish(sys.amount)) || 0;
      return s + (count * amount);
    }, 0);
    return down + sysTotal;
  }, [downPayment, systems]);

  const diff = useMemo(() => totalAmount - totalPayments, [totalAmount, totalPayments]);
  
  const isBalanced = useMemo(() => {
    return !isCashSale && items.length > 0 && Math.abs(diff) <= 5.01;
  }, [isCashSale, items.length, diff]);

  const isUnbalanced = useMemo(() => {
    return !isCashSale && items.length > 0 && !isBalanced;
  }, [isCashSale, items.length, isBalanced]);
  
  const allInstallments = useMemo(() => {
    return systems.flatMap(sys => 
      genSchedule(toEnglish(sys.count), toEnglish(sys.amount), saleMonth, saleYear)
    );
  }, [systems, saleMonth, saleYear]);

  // ── Sync: Boxes ➔ Text ─────────────────────────────────────────────────────
  const syncBoxesToText = (sysArray) => {
    const parts = sysArray
      .filter(s => s.count && s.amount && parseInt(toEnglish(s.count)) !== 0 && parseFloat(toEnglish(s.amount)) !== 0)
      .map(s => `${toEnglish(s.amount)}*${toEnglish(s.count)}`);
    setInstallmentDesc(parts.join('+'));
  };

  // ── Reverse Sync: Text ➔ Boxes ─────────────────────────────────────────────
  const syncTextToBoxes = (textVal) => {
    const cleanText = toEnglish(textVal);
    const parts = cleanText.split('+');
    const newSystems = [
      { count: '', amount: '' },
      { count: '', amount: '' },
      { count: '', amount: '' }
    ];

    parts.forEach((part, index) => {
      if (index >= 3) return;
      let [val1, val2] = part.trim().split('*');
      if (val1 && val2) {
        let v1 = parseInt(val1) || 0;
        let v2 = parseInt(val2) || 0;
        let amount = Math.max(v1, v2);
        let count = Math.min(v1, v2);
        newSystems[index] = {
          count: count,
          amount: amount
        };
      }
    });

    setSystems(newSystems);
  };

  const handleSystemChange = (idx, field, val) => {
    const arabicVal = val;
    const updated = systems.map((s, i) => i === idx ? { ...s, [field]: arabicVal } : s);
    setSystems(updated);
    syncBoxesToText(updated);
  };

  const handleDescChange = (val) => {
    const arabicVal = val;
    setInstallmentDesc(arabicVal);
    syncTextToBoxes(arabicVal);
  };

  // ── Cash Toggle ────────────────────────────────────────────────────────────
  const handleCashToggle = (val) => {
    setIsCashSale(val);
    if (val) {
      setCustomerName(''); setPhoneNumber(''); setAddress('');
      setDownPayment(''); setInstallmentDesc('');
      setSystems([{ count: '', amount: '' }, { count: '', amount: '' }, { count: '', amount: '' }]);
    }
  };

  // ── Dynamic Suggestions Search (Context-Aware) ──────────────────────────────
  const triggerSuggestions = (val, fieldType) => {
    clearTimeout(suggestTimerRef.current);
    clearTimeout(blurTimerRef.current);
    const term = toEnglish(val).trim();

    if (fieldType === 'salesperson') {
      const q = term.toLowerCase();
      const filtered = salespersons.filter(s => s.name && s.name.toLowerCase().includes(q));
      setSuggestions(filtered);
      setActiveInput(fieldType);
      setActiveIndex(-1);
      return;
    }

    activeRequestFieldRef.current = fieldType;
    suggestTimerRef.current = setTimeout(async () => {
      try {
        let url = '';
        if (fieldType === 'product') {
          url = `/product-suggestions/?term=${encodeURIComponent(term)}&month=${saleMonth}&year=${saleYear}`;
        } else {
          const currentArea = toEnglish(area);
          const currentName = toEnglish(customerName);
          url = `/customer-suggestions/?term=${encodeURIComponent(term)}&field=${fieldType}&salesperson_id=${salespersonId}&current_area=${encodeURIComponent(currentArea)}&current_name=${encodeURIComponent(currentName)}`;
        }

        const res = await api.get(url);
        
        // BUG-F03 Fix: Ignore response if the active field has changed
        if (activeRequestFieldRef.current !== fieldType) return;
        
        const data = res.data?.results || res.data;
        const list = Array.isArray(data) ? data : [];
        
        if (fieldType === 'product') {
          setSuggestions(list.slice(0, 10));
        } else {
          setSuggestions(list.map(item => ({ value: item.value })).slice(0, 10));
        }

        setActiveInput(fieldType);
        setActiveIndex(-1);
      } catch {
        setSuggestions([]);
      }
    }, 300);
  };

  // ── Keyboard Navigation (Arrow Keys + Enter) ───────────────────────────────
  
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if (e.altKey) {
        setDebugMsg(`Alt pressed + ${e.key}`);
      }
      if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
        const activeElem = document.activeElement;
        let fieldType = null;
        setDebugMsg(`Alt+Arrow detected. Active ID: ${activeElem ? activeElem.id : 'none'}`);
        if (activeElem && activeElem.id) {
          if (activeElem.id === 'input_name') fieldType = 'name';
          else if (activeElem.id === 'input_phone') fieldType = 'phone';
          else if (activeElem.id === 'input_area') fieldType = 'area';
          else if (activeElem.id === 'input_address') fieldType = 'address';
        }
        
        if (fieldType) {
          e.preventDefault();
          e.stopPropagation();
          setDebugMsg(`Calling API for ${fieldType} ${e.key === 'ArrowRight' ? 'prev' : 'next'}`);
          if (e.key === 'ArrowRight') handleHistoryCursor(fieldType, 'prev');
          if (e.key === 'ArrowLeft') handleHistoryCursor(fieldType, 'next');
        } else {
          setDebugMsg(`No fieldType matched for ID: ${activeElem ? activeElem.id : 'none'}`);
        }
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown, { capture: true });
    return () => window.removeEventListener('keydown', handleGlobalKeyDown, { capture: true });
  }, [historyCursors]);

  const handleHistoryCursor = async (fieldType, direction) => {
    try {
      const currentCursor = historyCursors[fieldType];
      let url = `/receipts-history-cursor/?direction=${direction}`;
      if (currentCursor !== null && currentCursor !== undefined) {
        url += `&current_receipt_number=${currentCursor}`;
      } else if (direction === 'next') {
        return;
      }
      
      const res = await api.get(url);
      
      if (res.data && res.data.receipt_number) {
        setHistoryCursors(prev => ({ ...prev, [fieldType]: res.data.receipt_number }));
        
        let val = '';
        if (fieldType === 'name') val = res.data.customer_name;
        else if (fieldType === 'phone') val = res.data.phone_number;
        else if (fieldType === 'area') val = res.data.area;
        else if (fieldType === 'address') val = res.data.address;
        
        const arabicVal = val || '';
        if (fieldType === 'name') setCustomerName(arabicVal);
        else if (fieldType === 'phone') setPhoneNumber(arabicVal);
        else if (fieldType === 'area') setArea(arabicVal);
        else if (fieldType === 'address') setAddress(arabicVal);
        
      } else if (direction === 'next' && (!res.data || !res.data.receipt_number)) {
        // Reached newest state -> clear the field
        setHistoryCursors(prev => ({ ...prev, [fieldType]: null }));
        if (fieldType === 'name') setCustomerName('');
        else if (fieldType === 'phone') setPhoneNumber('');
        else if (fieldType === 'area') setArea('');
        else if (fieldType === 'address') setAddress('');
      }
    } catch (err) {
      console.log('No history found');
    }
  };



  const handleKeyDown = (e, fieldType) => {



    if (activeInput !== fieldType || !suggestions.length) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev + 1) % suggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex > -1) {
        handleSuggestionSelect(suggestions[activeIndex], fieldType);
      } else if (suggestions.length > 0) {
        handleSuggestionSelect(suggestions[0], fieldType);
      }
    }
  };

  const handleSuggestionSelect = (item, fieldType) => {
    if (fieldType === 'salesperson') {
      setSalespersonId(item.id);
      setSalespersonQuery(item.name);
    } else if (fieldType === 'product') {
        setSelectedProduct(item);
        setProductQuery(item.value);
        setSellPrice(isCashSale ? (item.cash_price || '') : (item.installment_price || ''));
        setTimeout(() => qtyRef.current?.focus(), 50);
        api.get(`/inventory-items/${item.id}/stock/?month=${saleMonth}&year=${saleYear}`)
           .then(res => {
             if (res.data && res.data.safe_available_qty !== undefined) {
               // Calculate remaining stock by subtracting what's already in the cart
               const existing = items.find(i => i.inventory_item === item.id);
               const remaining = res.data.safe_available_qty - (existing ? existing.quantity : 0);
               setSelectedProduct(prev => prev && prev.id === item.id ? { 
                 ...prev, 
                 safe_qty: remaining,
                 bottleneck_month: res.data.bottleneck_month,
                 bottleneck_year: res.data.bottleneck_year
               } : prev);
             }
           }).catch(() => {});
      } else {
      const arabicVal = item.value;
      if (fieldType === 'name') {
        setCustomerName(arabicVal);
      } else if (fieldType === 'area') {
        setArea(arabicVal);
      } else if (fieldType === 'address') {
        setAddress(arabicVal);
      } else if (fieldType === 'phone') {
        setPhoneNumber(arabicVal);
      }
    }
    setSuggestions([]);
    setActiveInput('');
    setActiveIndex(-1);
  };

  // ── Add Item ──────────────────────────────────────────────────────────────
  const handleAddItem = async () => {
    setItemError('');
    let currentProduct = selectedProduct;
      if (!currentProduct && productQuery.trim() !== '') {
        try {
          const res = await api.get(`/product-suggestions/?term=${encodeURIComponent(productQuery.trim())}&month=${saleMonth}&year=${saleYear}`);
          const exactMatch = res.data.find(p => p.value === productQuery.trim());
          if (exactMatch) {
            currentProduct = exactMatch;
          } else {
            setItemError('يرجى اختيار منتج أولاً أو كتابة اسمه بدقة.');
            return;
          }
        } catch {
          setItemError('خطأ في الاتصال أثناء التحقق من المنتج.');
          return;
        }
      } else if (!currentProduct) {
        setItemError('يرجى اختيار منتج أولاً أو كتابة اسمه بدقة.');
        return;
      }
    if (!quantity || quantity < 1) { setItemError('الكمية يجب أن تكون 1 على الأقل.'); return; }
    if (!sellPrice || parseFloat(sellPrice) <= 0) { setItemError('أدخل سعر صحيح.'); return; }

    const existing = items.find(i => i.inventory_item === currentProduct.id);
    const reqQty   = parseInt(quantity) + (existing ? existing.quantity : 0);
    let safeQty = currentProduct.safe_qty;

    if (safeQty !== undefined) {
      if (reqQty > safeQty) {
        setItemError(`الكمية المطلوبة أكبر من المتاح بأمان: ${safeQty}`);
        return;
      }
    } else {
      let retries = 3;
      while (retries > 0) {
        try {
          const res = await api.get(`/inventory-items/${currentProduct.id}/stock/?month=${saleMonth}&year=${saleYear}`);
          if (res.data && res.data.safe_available_qty !== undefined) {
            safeQty = res.data.safe_available_qty;
            if (reqQty > safeQty) {
              setItemError(`الكمية المطلوبة أكبر من المتاح بأمان: ${safeQty}`);
              return;
            }
          }
          break;
        } catch {
          retries--;
          if (retries > 0) await new Promise(r => setTimeout(r, 50));
        }
      }
    }

      if (existing) {
        setItems(items.map(i => i.inventory_item === currentProduct.id
          ? { ...i, quantity: reqQty, sell_price: parseFloat(sellPrice), safe_qty: safeQty !== undefined ? safeQty : i.safe_qty } : i));
      } else {
        setItems([...items, {
          id: Date.now(), inventory_item: currentProduct.id,
          productName: currentProduct.value,
          quantity: parseInt(quantity), sell_price: parseFloat(sellPrice),
          safe_qty: safeQty,
      }]);
    }
    setProductQuery(''); setSelectedProduct(null); setQuantity(1); setSellPrice('');
    setTimeout(() => prodQueryRef.current?.focus(), 50);
  };

  const handleCartKD = (e, nextRef) => { if (e.key === 'Enter') { e.preventDefault(); nextRef.current?.focus(); } };

  // ── Save الوصل ────────────────────────────────────────────────────────────
  const handleSave = async () => {
    setError('');
    if (items.length === 0)                      { const msg = 'لا توجد أصناف في الفاتورة.'; setError(msg); toast.error(msg); return; }
    if (!salespersonId)                          { const msg = 'اختر المندوب.'; setError(msg); toast.error(msg); return; }
    if (!isCashSale && !customerName.trim())     { const msg = 'أدخل اسم العميل.'; setError(msg); toast.error(msg); return; }
    if (!isCashSale && isUnbalanced)             { const msg = 'إجمالي الأقساط والمقدم لا يتطابق مع إجمالي الفاتورة!'; setError(msg); toast.error(msg); return; }

    setSaving(true);
    const payload = {
      customer_name:        isCashSale ? 'عميل نقدي' : toEnglish(customerName).trim(),
      phone_number:         isCashSale ? '' : toEnglish(phoneNumber),
      address:              isCashSale ? '' : toEnglish(address),
      area:                 toEnglish(area),
      salesperson:          parseInt(salespersonId),
      sale_month:           parseInt(saleMonth),
      sale_year:            parseInt(saleYear),
      is_cash_sale:         isCashSale,
      total_amount:         isCashSale ? totalAmount : totalPayments,
      down_payment:         isCashSale ? totalAmount : (parseFloat(toEnglish(downPayment)) || 0),
      installment_system:   isCashSale ? '' : toEnglish(installmentDesc),
      sale_items:           items.map(i => ({ inventory_item: i.inventory_item, quantity: i.quantity, sell_price: i.sell_price })),
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

      fetchNextNumber(); // Refresh next receipt number

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
          // Extract first available string error from the JSON object
          let extracted = d.license || d.detail || d.error || d.non_field_errors;
          if (!extracted) {
            // Find the first value that is an array and get its first item (DRF default style)
            const firstKey = Object.keys(d)[0];
            if (firstKey && Array.isArray(d[firstKey])) {
              extracted = d[firstKey][0];
            } else if (firstKey && typeof d[firstKey] === 'string') {
              extracted = d[firstKey];
            }
          }
          // If it's still an array, extract the string
          if (Array.isArray(extracted)) extracted = extracted[0];
          if (extracted) errorMsg = extracted;
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error(errorMsg);
    } finally { setSaving(false); }
  };

  if (loadingInitial) return (
    <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '50vh' }}>
      <div className="spinner-border text-primary" />
    </div>
  );

  return (
    <div className="container-fluid pb-3 px-3 fs-3 pt-3" dir="rtl" style={{ fontSize: '1.02rem' }}>
      <div style={{position:"fixed", top:0, left:0, zIndex:9999, background:"red", color:"white", padding:"10px", fontSize:"16px", direction: "ltr"}}>DEBUG: {debugMsg}</div>

      

      {error && <div className="alert alert-danger py-2 mb-2 fw-bold fs-3">{error}</div>}

      <div className="row g-2 align-items-start">

        {/* ══════════════════════════════════════════════════════════════════
            RIGHT — col-lg-7
            ══════════════════════════════════════════════════════════════════ */}
        <div className="col-lg-7">

          {/* ── بيانات الوصل والعميل ── */}
          <div className="card premium-card mb-2" style={{ position: 'relative', zIndex: 30 }}>
            <div className="card-body p-3">

              {/* صف 1: الشهر | السنة | المندوب */}
              <div className="row g-2 mb-2 align-items-center">
                <div className="col-auto">
                  <label className="col-form-label fw-bold text-dark">الشهر</label>
                </div>
                <div className="col-2">
                  <input type="number" className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" value={saleMonth} min="1" max="12" onChange={e => {
                    const v = parseInt(e.target.value);
                    if (v >= 1 && v <= 12) setSaleMonth(v);
                    else if (e.target.value === '') setSaleMonth('');
                  }} style={{ borderColor: '#adb5bd' }} />
                </div>
                <div className="col-auto">
                  <label className="col-form-label fw-bold text-dark">السنة</label>
                </div>
                <div className="col-2">
                  <input type="number" className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" value={saleYear} min="2020" onChange={e => setSaleYear(e.target.value)} style={{ borderColor: '#adb5bd' }} />
                </div>
                <div className="col-auto">
                  <label className="col-form-label fw-bold text-dark">المندوب</label>
                </div>
                <div className="col d-flex align-items-center gap-2">
                  <div className="position-relative flex-grow-1">
                    <input
                      type="text"
                      ref={salespersonRef}
                      className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                      value={salespersonQuery}
                      autoComplete="off"
                      onChange={e => {
                        setSalespersonQuery(e.target.value);
                        setSalespersonId(''); // Clear ID if user types manually
                        triggerSuggestions(e.target.value, 'salesperson');
                      }}
                      onKeyDown={e => handleKeyDown(e, 'salesperson')}
                      onBlur={() => {
                        blurTimerRef.current = setTimeout(() => {
                          if (salespersonQuery.trim() !== '') {
                            const exactMatch = salespersons.find(s => s.name === salespersonQuery.trim());
                            if (exactMatch) {
                              setSalespersonId(exactMatch.id);
                              setSalespersonQuery(exactMatch.name);
                            }
                          }
                          setSuggestions([]);
                          setActiveInput('');
                        }, 200);
                      }}
                      placeholder="ابحث عن مندوب..."
                      onFocus={() => triggerSuggestions(salespersonQuery, 'salesperson')}
                      style={{ borderColor: '#adb5bd' }}
                    />
                    <SuggestionList
                      open={activeInput === 'salesperson'}
                      suggestions={suggestions}
                      activeIndex={activeIndex}
                      onSelect={s => handleSuggestionSelect(s, 'salesperson')}
                    />
                  </div>
                  <div className="form-check m-0 d-flex align-items-center gap-1">
                    <input 
                      className="form-check-input mt-0" 
                      type="checkbox" 
                      id="keepSalespersonCheck" 
                      checked={keepSalesperson}
                      onChange={e => setKeepSalesperson(e.target.checked)}
                    />
                    <label className="form-check-label fw-bold text-nowrap fs-4" htmlFor="keepSalespersonCheck">
                      تثبيت
                    </label>
                  </div>
                </div>
              </div>

              {/* صف 2-4: بيانات العميل — تختفي في الكاش */}
              {!isCashSale && (
                <>
                  {/* اسم العميل */}
                  <Field label="اسم العميل" labelCol="col-sm-2" inputCol="col-sm-10" className="mb-2">
                    <div className="position-relative">
                      <input
                        type="text"
                        id="input_name"
                        ref={custNameRef}
                        className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                        value={customerName}
                        autoComplete="off"
                        onChange={e => { setCustomerName(e.target.value); triggerSuggestions(e.target.value, 'name'); }}
                        onKeyDown={e => handleKeyDown(e, 'name')}
                        onFocus={() => triggerSuggestions(customerName, 'name')}
                        onBlur={() => { blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); }}
                        style={{ borderColor: '#adb5bd' }}
                      />
                      <SuggestionList
                        open={activeInput === 'name'}
                        suggestions={suggestions}
                        activeIndex={activeIndex}
                        onSelect={s => handleSuggestionSelect(s, 'name')}
                      />
                    </div>
                  </Field>

                  {/* التليفون | المنطقة */}
                  <div className="row g-2 mb-2 align-items-center">
                    <div className="col-auto">
                      <label className="col-form-label fw-bold text-dark">هاتف</label>
                    </div>
                    <div className="col-4">
                      <div className="position-relative">
                        <input
                          type="tel"
                          id="input_phone"
                          className="form-control py-1 fs-3 border-secondary-subtle text-center fw-bold"
                          value={phoneNumber}
                          dir="ltr"
                          onChange={e => setPhoneNumber(e.target.value)}
                          onKeyDown={e => handleKeyDown(e, 'phone')}
                          onFocus={() => triggerSuggestions(phoneNumber, 'phone')}
                          onBlur={() => { blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); }}
                          style={{ borderColor: '#adb5bd' }}
                        />
                        <SuggestionList
                          open={activeInput === 'phone'}
                          suggestions={suggestions}
                          activeIndex={activeIndex}
                          onSelect={s => handleSuggestionSelect(s, 'phone')}
                        />
                      </div>
                    </div>
                    <div className="col-auto">
                      <label className="col-form-label fw-bold text-dark">المنطقة</label>
                    </div>
                    <div className="col">
                      <div className="position-relative">
                        <input
                          type="text"
                          className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                          id="input_area"
                          value={area}
                          onChange={e => { setArea(e.target.value); triggerSuggestions(e.target.value, 'area'); }}
                          onKeyDown={e => handleKeyDown(e, 'area')}
                          onFocus={() => triggerSuggestions(area, 'area')}
                          onBlur={() => { blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); }}
                          style={{ borderColor: '#adb5bd' }}
                        />
                        <SuggestionList
                          open={activeInput === 'area'}
                          suggestions={suggestions}
                          activeIndex={activeIndex}
                          onSelect={s => handleSuggestionSelect(s, 'area')}
                        />
                      </div>
                    </div>
                  </div>

                  {/* العنوان */}
                  <Field label="العنوان" labelCol="col-sm-2" inputCol="col-sm-10" className="mb-0">
                    <div className="position-relative">
                      <input
                        id="input_address"
                          type="text"
                        className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                        value={address}
                        onChange={e => { setAddress(e.target.value); triggerSuggestions(e.target.value, 'address'); }}
                        onKeyDown={e => handleKeyDown(e, 'address')}
                        onFocus={() => triggerSuggestions(address, 'address')}
                        onBlur={() => { blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); }}
                        style={{ borderColor: '#adb5bd' }}
                      />
                      <SuggestionList
                        open={activeInput === 'address'}
                        suggestions={suggestions}
                        activeIndex={activeIndex}
                        onSelect={s => handleSuggestionSelect(s, 'address')}
                      />
                    </div>
                  </Field>
                </>
              )}

              {/* المنطقة وحدها في وضع الكاش */}
              {isCashSale && (
                <div className="row g-2 align-items-center">
                  <div className="col-auto">
                    <label className="col-form-label fw-bold text-dark">المنطقة</label>
                  </div>
                  <div className="col-5">
                    <div className="position-relative">
                      <input
                        type="text"
                        className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                          id="input_area"
                          value={area}
                        onChange={e => { setArea(e.target.value); triggerSuggestions(e.target.value, 'area'); }}
                        onKeyDown={e => handleKeyDown(e, 'area')}
                          onFocus={() => triggerSuggestions(area, 'area')}
                        onBlur={() => { blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); }}
                        style={{ borderColor: '#adb5bd' }}
                      />
                      <SuggestionList
                        open={activeInput === 'area'}
                        suggestions={suggestions}
                        activeIndex={activeIndex}
                        onSelect={s => handleSuggestionSelect(s, 'area')}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ── الأصناف ── */}
          <div className="card premium-card mb-2" style={{ position: 'relative', zIndex: 20 }}>

            {/* شريط الإضافة مع عناوين الحقول */}
            <div className="card-body p-2 border-bottom bg-light" style={{ borderColor: '#dee2e6 !important' }}>
              {itemError && <div className="alert alert-danger py-1 mb-2 small fw-bold">{itemError}</div>}
              <div className="row g-2 align-items-center mb-4">
                  <div className="col-auto">
                    <label className="form-label fw-bold text-dark mb-0">الصنف</label>
                </div>
                <div className="col">
                  <div className="position-relative">
                    <input
                      ref={prodQueryRef}
                      type="text"
                      className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                      value={productQuery}
                      autoComplete="off"
                      onChange={e => {
                          const val = e.target.value;
                          setProductQuery(val);
                          if (selectedProduct && selectedProduct.value !== val) {
                            setSelectedProduct(null);
                          }
                          triggerSuggestions(val, 'product');
                        }}
                      onKeyDown={e => handleKeyDown(e, 'product')}
                            onFocus={() => triggerSuggestions(productQuery, 'product')}
                      onBlur={() => { 
                          if (!selectedProduct && productQuery.trim() !== '') {
                            const exactMatch = suggestions.find(p => p.value === productQuery.trim());
                            const fetchStockForMatch = (match) => {
                              api.get(`/inventory-items/${match.id}/stock/?month=${saleMonth}&year=${saleYear}`)
                                 .then(res => {
                                   if (res.data && res.data.safe_available_qty !== undefined) {
                                     const existing = items.find(i => i.inventory_item === match.id);
                                     const remaining = res.data.safe_available_qty - (existing ? existing.quantity : 0);
                                     setSelectedProduct({ 
                                       ...match, 
                                       safe_qty: remaining,
                                       bottleneck_month: res.data.bottleneck_month,
                                       bottleneck_year: res.data.bottleneck_year
                                     });
                                   }
                                 }).catch(() => {});
                            };

                            if (exactMatch) {
                              fetchStockForMatch(exactMatch);
                            } else {
                              // BUG-F05 Fix: Fallback to API if suggestions is empty (Race Condition)
                              api.get(`/product-suggestions/?term=${encodeURIComponent(productQuery.trim())}&month=${saleMonth}&year=${saleYear}`)
                                 .then(res => {
                                   const fallbackMatch = res.data.find(p => p.value === productQuery.trim());
                                   if (fallbackMatch) fetchStockForMatch(fallbackMatch);
                                 }).catch(() => {});
                            }
                          }
                          blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); 
                        }}
                      style={{ borderColor: '#adb5bd' }}
                    />
                    <SuggestionList
                      open={activeInput === 'product'}
                      suggestions={suggestions}
                      activeIndex={activeIndex}
                      onSelect={s => handleSuggestionSelect(s, 'product')}
                    />
                  </div>
                </div>
                <div className="col-auto">
                  <label className="form-label fw-bold text-dark mb-0">الكمية</label>
                </div>
                <div className="col-2 position-relative text-center">
                    <input ref={qtyRef} type="number" className="form-control py-1 fs-3 border-secondary-subtle text-center fw-bold"
                      value={quantity} min="1"
                      onChange={e => setQuantity(e.target.value)}
                      onKeyDown={e => handleCartKD(e, priceRef)}
                      style={{ borderColor: '#adb5bd' }} />
                    {selectedProduct && selectedProduct.safe_qty !== undefined && (
                      <div className="position-absolute text-success fw-bold mt-1" style={{ fontSize: '0.8rem', whiteSpace: 'nowrap', left: '50%', transform: 'translateX(-50%)' }}>
                        متاح: {selectedProduct.safe_qty}
                        {selectedProduct.bottleneck_month && (
                          <span className="text-warning ms-1">
                            (مقيد بسبب كمية شهر {selectedProduct.bottleneck_month}/{selectedProduct.bottleneck_year})
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                <div className="col-auto">
                  <label className="form-label fw-bold text-dark mb-0">السعر</label>
                </div>
                <div className="col-2">
                  <input ref={priceRef} type="number" className="form-control py-1 fs-3 border-secondary-subtle text-danger fw-bold text-center"
                    value={sellPrice}
                    onChange={e => setSellPrice(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddItem(); } }}
                    style={{ borderColor: '#adb5bd' }} />
                </div>
                <div className="col-auto">
                  <button className="btn btn-success d-flex align-items-center justify-content-center fw-bold p-0" 
                          onClick={handleAddItem} 
                          style={{ width: '36px', height: '36px', fontSize: '1.5rem', border: '1px solid #adb5bd' }}>
                    +
                  </button>
                </div>
              </div>
            </div>

            {/* جدول الأصناف */}
            <div className="table-responsive" style={{ minHeight: 200 }}>
              <table className="table table-vcenter table-hover table-sm mb-0">
                <thead className="table-light border-bottom">
                  <tr>
                    <th>#</th>
                    <th>الصنف</th>
                    <th className="text-center">الكمية</th>
                    <th className="text-center">السعر</th>
                    <th className="text-center">الإجمالي</th>
                    <th className="w-1"></th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr><td colSpan="6" className="text-center py-5 text-muted fw-bold">لا توجد أصناف مضافة</td></tr>
                  ) : (
                    items.map((item, idx) => (
                      <tr key={item.id} className="border-bottom">
                        <td className="text-muted small">{idx + 1}</td>
                        <td className="fw-bold text-dark">
                            <div>{item.productName}</div></td>
                        <td className="text-center fw-bold">{item.quantity}</td>
                        <td className="text-center text-success fw-bold">{item.sell_price.toLocaleString()}</td>
                        <td className="text-center text-primary fw-bold">{(item.quantity * item.sell_price).toLocaleString()}</td>
                        <td>
                          <button className="btn btn-outline-danger btn-icon btn-sm"
                            onClick={() => setItems(items.filter(i => i.id !== item.id))}>
                            <IconTrash size={16} />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        {/* END RIGHT */}

        {/* ══════════════════════════════════════════════════════════════════
            LEFT — col-lg-5
            ══════════════════════════════════════════════════════════════════ */}
        <div className="col-lg-5">
          <div className="card premium-card mb-3" style={{ position: 'relative', zIndex: 10 }}>
            <div className="card-body p-3">

              {/* ── وضع التقسيط: المقدم + وصف القسط في سطر واحد ── */}
              {!isCashSale && (
                <>
                  <div className="row g-2 mb-3 align-items-center">
                    <div className="col-auto">
                      <label className="col-form-label fw-bold text-dark">المقدم</label>
                    </div>
                    <div className="col-3">
                      <input type="text" className="form-control py-1 fs-3 border-secondary-subtle text-success fw-bold text-center"
                        value={downPayment}
                        onChange={e => setDownPayment(e.target.value)}
                        style={{ borderColor: '#adb5bd' }} />
                    </div>
                    <div className="col-auto">
                      <label className="col-form-label fw-bold text-dark">نظام القسط</label>
                    </div>
                    <div className="col">
                      <input type="text" className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-muted bg-light"
                        value={installmentDesc}
                        readOnly
                        disabled
                        style={{ borderColor: '#adb5bd' }} />
                    </div>
                  </div>

                  {/* حاسبة الأقساط 3×2 مع Placeholders المطلوبة */}
                  <div className="row g-2 mb-3">
                    {systems.map((sys, idx) => (
                      <div key={idx} className="col-4">
                        <div className="border rounded p-2 text-center bg-light" style={{ borderColor: '#adb5bd' }}>
                          <div className="text-dark small fw-bold mb-1">نظام {idx + 1}</div>
                          <input type="text" className="form-control py-1 fs-3 border-secondary-subtle text-center mb-1 fw-bold"
                            value={sys.count}
                            placeholder={`شهر ${idx + 1}`}
                            onChange={e => handleSystemChange(idx, 'count', e.target.value)}
                            style={{ borderColor: '#adb5bd' }} />
                          <input type="text" className="form-control py-1 fs-3 border-secondary-subtle text-center text-primary fw-bold"
                            value={sys.amount}
                            placeholder={`مبلغ ${idx + 1}`}
                            onChange={e => handleSystemChange(idx, 'amount', e.target.value)}
                            style={{ borderColor: '#adb5bd' }} />
                          {sys.count && sys.amount && (
                            <div className="text-success small mt-1 fw-bold border-top pt-1" style={{ borderColor: '#adb5bd' }}>
                              {fmt((parseInt(toEnglish(sys.count))||0)*(parseFloat(toEnglish(sys.amount))||0))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {/* وضع الكاش */}
              {isCashSale && (
                <div className="alert alert-success py-3 text-center mb-3 fw-bold border border-success">
                  كاش — لا توجد أقساط ومقدم
                </div>
              )}

            </div>

            {/* زر الحفظ */}
            <div className="px-3 pb-3">
              <button
                className={`btn btn-lg w-100 fw-bold py-3 border-secondary-subtle ${(isCashSale && items.length > 0) || isBalanced ? 'btn-success' : 'btn-secondary'}`}
                onClick={handleSave}
                disabled={saving || (!isCashSale && isUnbalanced)}
                style={{ border: '1px solid #adb5bd' }}
              >
                {saving
                  ? <><span className="spinner-border spinner-border-sm me-1"></span>جاري الحفظ...</>
                  : <><IconDeviceFloppy size={20} className="me-1" />تأكيد البيع</>}
              </button>
            </div>

            <div className="card-body p-3 border-top bg-light" style={{ borderColor: '#dee2e6 !important' }}>

              {/* رقم الوصل + نوع البيع في سطر واحد */}
              <div className="row g-2 align-items-center mb-3">
                <div className="col-auto">
                  <label className="col-form-label fw-bold text-dark">رقم الوصل</label>
                </div>
                <div className="col-3">
                  <input type="text" className="form-control py-1 fs-3 border-secondary-subtle bg-white text-muted text-center fw-bold" value={nextReceiptNumber || 'تلقائي'} readOnly style={{ borderColor: '#adb5bd' }} />
                </div>
                <div className="col-auto me-auto">
                  {/* spacer */}
                </div>
                <div className="col-auto">
                  <div className="btn-group border rounded" style={{ borderColor: '#adb5bd' }}>
                    <button className={`btn btn-sm px-3 ${isCashSale ? 'btn-success' : 'btn-outline-success'}`}
                      onClick={() => handleCashToggle(true)}>كاش</button>
                    <button className={`btn btn-sm px-3 ${!isCashSale ? 'btn-primary' : 'btn-outline-primary'}`}
                      onClick={() => handleCashToggle(false)}>قسط</button>
                  </div>
                </div>
              </div>

              {/* إجمالي المبيعات | إجمالي الأقساط والمقدم | الفرق — سطر واحد */}
              <div className={`rounded p-2 border ${isBalanced ? 'bg-success-lt border-success' : isUnbalanced ? 'bg-danger-lt border-danger' : 'bg-white'}`} style={!isBalanced && !isUnbalanced ? { borderColor: '#adb5bd' } : {}}>
                <div className="row g-0 text-center">
                  <div className="col-4 border-end" style={{ borderColor: '#adb5bd !important' }}>
                    <div className="text-dark small fw-bold">المبيعات</div>
                    <div className="fw-bold text-success fs-3">{fmt(totalAmount)}</div>
                  </div>
                  {!isCashSale && (
                    <>
                      <div className="col-4 border-end" style={{ borderColor: '#adb5bd !important' }}>
                        <div className="text-dark small fw-bold">الأقساط والمقدم</div>
                        <div className="fw-bold text-primary fs-3">{fmt(totalPayments)}</div>
                      </div>
                      <div className="col-4">
                        <div className="text-dark small fw-bold">الفرق</div>
                        <div className={`fw-bold fs-3 ${isBalanced ? 'text-success' : 'text-danger'}`}>
                          {isBalanced ? '✓' : fmt(Math.abs(diff))}
                        </div>
                      </div>
                    </>
                  )}
                  {isCashSale && (
                    <div className="col-8 d-flex align-items-center justify-content-center">
                      <span className="badge bg-success py-2 px-3 fw-bold fs-3">متزن</span>
                    </div>
                  )}
                </div>
              </div>

            </div>
          </div>
        </div>
        {/* END LEFT */}

      </div>
    </div>
  );
};

export default POS;

