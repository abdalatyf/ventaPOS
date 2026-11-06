import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../api';

import POSCustomerForm from '../components/pos/POSCustomerForm';
import POSItemsTable from '../components/pos/POSItemsTable';
import POSInstallmentBox from '../components/pos/POSInstallmentBox';
import POSTotalsSummary from '../components/pos/POSTotalsSummary';
import usePOSHistory from '../components/pos/usePOSHistory';
import usePOSDataLoader from '../components/pos/usePOSDataLoader';
import usePOSSuggestions from '../components/pos/usePOSSuggestions';
import usePOSSave from '../components/pos/usePOSSave';
import { 
  fmt, 
  toEnglish, 
  formatBoxesToInstallmentText,
  addItemToCart
} from '../components/pos/posUtils';

const POS = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('edit');

  const [salespersons, setSalespersons] = useState([]);
  const [products, setProducts] = useState([]);
  const [loadingInitial, setLoadingInitial] = useState(true);

  // Invoice Meta
  const [saleMonth, setSaleMonth] = useState(new Date().getMonth() + 1);
  const [saleYear, setSaleYear] = useState(new Date().getFullYear());
  const [salespersonId, setSalespersonId] = useState('');
  const [keepSalesperson, setKeepSalesperson] = useState(false);
  const [salespersonQuery, setSalespersonQuery] = useState('');
  const salespersonRef = useRef(null);
  const [isCashSale, setIsCashSale] = useState(false);

  // Customer Fields
  const [customerName, setCustomerName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [area, setArea] = useState('');
  const [address, setAddress] = useState('');

  // Cart
  const [items, setItems] = useState([]);
  const [productQuery, setProductQuery] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [sellPrice, setSellPrice] = useState('');
  const [itemError, setItemError] = useState('');

  // Free-Text Mode for Print-Only or Pre-License receipts
  const [productsText, setProductsText] = useState('');
  const [manualTotalAmount, setManualTotalAmount] = useState('');
  const [licenseInfo, setLicenseInfo] = useState({ isPrintOnly: false, licStartDate: null });

  useEffect(() => {
    api.get('/license/status/').then(res => {
      setLicenseInfo({
        isPrintOnly: Boolean(res.data?.is_print_only),
        licStartDate: res.data?.lic_start_date || res.data?.start_date || null
      });
    }).catch(err => console.error('Failed to load license status in POS', err));
  }, []);

  const isPreLicenseDate = useMemo(() => {
    if (!licenseInfo.licStartDate || !saleYear || !saleMonth) return false;
    try {
      const [licY, licM] = licenseInfo.licStartDate.split('-').map(Number);
      const sY = Number(saleYear);
      const sM = Number(saleMonth);
      if (sY < licY) return true;
      if (sY === licY && sM < licM) return true;
      return false;
    } catch {
      return false;
    }
  }, [licenseInfo.licStartDate, saleYear, saleMonth]);

  const isFreeTextMode = licenseInfo.isPrintOnly || isPreLicenseDate;

  // History tracking hook
  usePOSHistory({
    setCustomerName,
    setPhoneNumber,
    setArea,
    setAddress
  });

  const currentBranchId = localStorage.getItem('branchId') || 1;
  const [nextReceiptNumber, setNextReceiptNumber] = useState(null);

  const fetchNextNumber = async () => {
    try {
      const res = await api.get('receipts-next-number/', { params: { branch_id: currentBranchId } });
      setNextReceiptNumber(res.data.next_receipt_number);
    } catch (err) {
      console.error('Failed to fetch next receipt number', err);
    }
  };

  useEffect(() => {
    fetchNextNumber();
  }, [currentBranchId]);

  // Payment
  const [downPayment, setDownPayment] = useState('');
  const [installmentDesc, setInstallmentDesc] = useState('');
  const [systems, setSystems] = useState([
    { count: '', amount: '' },
    { count: '', amount: '' },
    { count: '', amount: '' },
  ]);

  const isEditingRef = useRef(false);
  const qtyRef = useRef(null);
  const priceRef = useRef(null);
  const prodQueryRef = useRef(null);
  const custNameRef = useRef(null);

  // Fetch Initial Data via Hook
  usePOSDataLoader({
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
    setError: () => {},
    salespersonRef,
    isEditingRef
  });

  // Autocomplete suggestions hook
  const {
    suggestions,
    setSuggestions,
    activeInput,
    setActiveInput,
    activeIndex,
    triggerSuggestions,
    handleKeyDown,
    handleSuggestionSelect,
    blurTimerRef
  } = usePOSSuggestions({
    salespersons,
    saleMonth,
    saleYear,
    customerName,
    setCustomerName,
    phoneNumber,
    setPhoneNumber,
    area,
    setArea,
    address,
    setAddress,
    salespersonId,
    setSalespersonId,
    setSalespersonQuery,
    isCashSale,
    setSelectedProduct,
    setProductQuery,
    setSellPrice,
    items,
    qtyRef
  });

  // Derived Values
  const totalAmount = useMemo(() => {
    if (isFreeTextMode) {
      return parseFloat(toEnglish(manualTotalAmount)) || 0;
    }
    return items.reduce((s, i) => s + i.quantity * i.sell_price, 0);
  }, [isFreeTextMode, manualTotalAmount, items]);

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
  const hasItems = useMemo(() => {
    if (isFreeTextMode) {
      return Boolean(productsText && productsText.trim()) && totalAmount > 0;
    }
    return items.length > 0;
  }, [isFreeTextMode, productsText, totalAmount, items]);

  const isBalanced = useMemo(() => !isCashSale && hasItems && Math.abs(diff) <= 5.01, [isCashSale, hasItems, diff]);
  const isUnbalanced = useMemo(() => !isCashSale && hasItems && !isBalanced, [isCashSale, hasItems, isBalanced]);
  
  const allInstallments = useMemo(() => {
    const rows = [];
    let m = parseInt(saleMonth);
    let y = parseInt(saleYear);

    systems.forEach(sys => {
      const countInt = Math.min(360, parseInt(toEnglish(sys.count)) || 0);
      const amt = parseFloat(toEnglish(sys.amount)) || 0;
      if (amt > 0 && countInt > 0) {
        for (let i = 0; i < countInt; i++) {
          m++;
          if (m > 12) { m = 1; y++; }
          rows.push({ payment_month: m, payment_year: y, amount: amt });
        }
      }
    });
    return rows;
  }, [systems, saleMonth, saleYear]);

  // Save hook
  const { handleSave, saving, error } = usePOSSave({
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
  });

  const handleSystemChange = (idx, field, val) => {
    const updated = systems.map((s, i) => i === idx ? { ...s, [field]: val } : s);
    setSystems(updated);
    setInstallmentDesc(formatBoxesToInstallmentText(updated));
  };

  const handleCashToggle = (val) => {
    setIsCashSale(val);
    if (val) {
      setCustomerName(''); setPhoneNumber(''); setAddress('');
      setDownPayment(''); setInstallmentDesc('');
      setSystems([{ count: '', amount: '' }, { count: '', amount: '' }, { count: '', amount: '' }]);
    }
  };

  const handleAddItem = () => {
    addItemToCart({
      selectedProduct,
      productQuery,
      saleMonth,
      saleYear,
      quantity,
      sellPrice,
      items,
      setItems,
      setItemError,
      setProductQuery,
      setSelectedProduct,
      setQuantity,
      setSellPrice,
      prodQueryRef
    });
  };

  const handleCartKD = (e, nextRef) => { 
    if (e.key === 'Enter') { 
      e.preventDefault(); 
      nextRef.current?.focus(); 
    } 
  };

  if (loadingInitial) return (
    <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '50vh' }}>
      <div className="spinner-border text-primary" />
    </div>
  );

  return (
    <div className="container-fluid pb-3 px-3 fs-3 pt-3" dir="rtl" style={{ fontSize: '1.02rem' }}>
      {error && <div className="alert alert-danger py-2 mb-2 fw-bold fs-3">{error}</div>}

      <div className="row g-2 align-items-start">
        {/* RIGHT — col-lg-7 */}
        <div className="col-lg-7">
          <POSCustomerForm
            saleMonth={saleMonth}
            setSaleMonth={setSaleMonth}
            saleYear={saleYear}
            setSaleYear={setSaleYear}
            salespersonRef={salespersonRef}
            salespersonQuery={salespersonQuery}
            setSalespersonQuery={setSalespersonQuery}
            setSalespersonId={setSalespersonId}
            triggerSuggestions={triggerSuggestions}
            handleKeyDown={handleKeyDown}
            blurTimerRef={blurTimerRef}
            salespersons={salespersons}
            activeInput={activeInput}
            setActiveInput={setActiveInput}
            suggestions={suggestions}
            setSuggestions={setSuggestions}
            activeIndex={activeIndex}
            handleSuggestionSelect={handleSuggestionSelect}
            keepSalesperson={keepSalesperson}
            setKeepSalesperson={setKeepSalesperson}
            isCashSale={isCashSale}
            custNameRef={custNameRef}
            customerName={customerName}
            setCustomerName={setCustomerName}
            phoneNumber={phoneNumber}
            setPhoneNumber={setPhoneNumber}
            area={area}
            setArea={setArea}
            address={address}
            setAddress={setAddress}
          />

          {isFreeTextMode ? (
            <div className="card shadow-sm mb-2" style={{ position: 'relative', zIndex: 20 }}>
              <div className="card-header bg-light py-2 border-bottom d-flex align-items-center justify-content-between">
                <span className="fw-bold text-dark fs-4">
                  بيان البضاعة والأصناف
                </span>
                {licenseInfo.isPrintOnly ? (
                  <span className="badge bg-purple-lt text-purple fw-bold px-2 py-1">باقة طباعة فقط</span>
                ) : (
                  <span className="badge bg-warning-lt text-warning fw-bold px-2 py-1">
                    فاتورة سابقة للاشتراك ({licenseInfo.licStartDate})
                  </span>
                )}
              </div>
              <div className="card-body p-3">
                <div className="mb-3">
                  <label className="form-label fw-bold text-dark mb-1">
                    بيان الأصناف (نص حر) <span className="text-danger">*</span>
                  </label>
                  <textarea
                    className="form-control fw-bold border-secondary-subtle"
                    rows="3"
                    placeholder="اكتب بيان الأصناف المباعة (مثال: غرفة نوم كاملة + شاشة 43 بوصة + غسالة...)"
                    value={productsText}
                    onChange={(e) => setProductsText(e.target.value)}
                  />
                  <small className="text-muted d-block mt-1">
                    يُسجل هذا البيان على الفاتورة وتتم طباعته على إيصالات الأقساط دون خصم أرصدة مخزنية.
                  </small>
                </div>
                <div className="row g-2 align-items-center">
                  <div className="col-auto">
                    <label className="form-label fw-bold text-dark mb-0">إجمالي الفاتورة (جنيه) <span className="text-danger">*</span></label>
                  </div>
                  <div className="col-4">
                    <input
                      type="number"
                      min="1"
                      step="1"
                      className="form-control py-1 fs-3 border-secondary-subtle text-danger fw-bold text-center"
                      value={manualTotalAmount}
                      onChange={(e) => setManualTotalAmount(e.target.value)}
                      placeholder="0"
                    />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <POSItemsTable
              itemError={itemError}
              prodQueryRef={prodQueryRef}
              productQuery={productQuery}
              setProductQuery={setProductQuery}
              selectedProduct={selectedProduct}
              setSelectedProduct={setSelectedProduct}
              triggerSuggestions={triggerSuggestions}
              handleKeyDown={handleKeyDown}
              activeInput={activeInput}
              setActiveInput={setActiveInput}
              suggestions={suggestions}
              setSuggestions={setSuggestions}
              activeIndex={activeIndex}
              handleSuggestionSelect={handleSuggestionSelect}
              saleMonth={saleMonth}
              saleYear={saleYear}
              items={items}
              setItems={setItems}
              blurTimerRef={blurTimerRef}
              qtyRef={qtyRef}
              quantity={quantity}
              setQuantity={setQuantity}
              handleCartKD={handleCartKD}
              priceRef={priceRef}
              sellPrice={sellPrice}
              setSellPrice={setSellPrice}
              handleAddItem={handleAddItem}
            />
          )}
        </div>

        {/* LEFT — col-lg-5 */}
        <div className="col-lg-5">
          <div className="card shadow-sm mb-3" style={{ position: 'relative', zIndex: 10 }}>
            <POSInstallmentBox
              isCashSale={isCashSale}
              downPayment={downPayment}
              setDownPayment={setDownPayment}
              installmentDesc={installmentDesc}
              systems={systems}
              handleSystemChange={handleSystemChange}
              toEnglish={toEnglish}
              fmt={fmt}
            />

            <POSTotalsSummary
              handleSave={handleSave}
              saving={saving}
              isCashSale={isCashSale}
              items={items}
              hasItems={hasItems}
              isBalanced={isBalanced}
              isUnbalanced={isUnbalanced}
              nextReceiptNumber={nextReceiptNumber}
              handleCashToggle={handleCashToggle}
              totalAmount={totalAmount}
              totalPayments={totalPayments}
              diff={diff}
              fmt={fmt}
            />
          </div>
        </div>

      </div>
    </div>
  );
};

export default POS;
