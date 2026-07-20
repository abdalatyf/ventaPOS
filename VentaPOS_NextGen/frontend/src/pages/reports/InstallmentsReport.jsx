import useSmartScroll from '../../hooks/useSmartScroll';
import React, { useState, useEffect, useContext, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import { IconFilter, IconReceipt, IconPrinter, IconSortAscending, IconPlus, IconTrash } from '@tabler/icons-react';

const fmtNum = (val) => {
  const num = Number(val) || 0;
  return Math.round(num).toLocaleString('en-US');
};

const toArabic = (str) => {
  if (str === null || str === undefined) return '';
  return String(str).replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[d]);
};

// --- Installment Row Component ---
const InstallmentRow = React.memo(({ payment, index, isSelected, toggleSelect, navigate }) => {
  return (
    <tr>
      <td className="text-center align-middle border-secondary-subtle">
        <input 
          type="checkbox" 
          className="form-check-input border-secondary-subtle" 
          checked={isSelected}
          onChange={() => toggleSelect(payment.payment_id)}
        />
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold">{toArabic(index + 1)}</td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">
        {(() => {
          const d = new Date(payment.date);
          return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
        })()}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle fw-bold text-primary">
        {payment.customer_name}
      </td>
      <td className="text-center align-middle border-secondary-subtle text-muted" dir="ltr">{toArabic(payment.phone)}</td>
      <td className="text-center align-middle border-secondary-subtle">{payment.area}</td>
      <td className="text-center align-middle border-secondary-subtle fw-bold">{payment.salesperson_name}</td>
      <td className="text-center align-middle border-secondary-subtle">
        <a href="#" onClick={(e) => { e.preventDefault(); navigate(`/pos?edit=${payment.receipt_id}`); }} className="drilldown-link text-decoration-none fw-bold text-primary" dir="ltr">
          {toArabic(payment.receipt_num)}
        </a>
      </td>
      <td className="text-center align-middle border-secondary-subtle text-muted" dir="ltr">{toArabic(payment.sale_date)}</td>
      <td className="text-end px-2 align-middle border-secondary-subtle fw-bold text-success">
        {toArabic(fmtNum(payment.amount))}
      </td>
    </tr>
  );
});

// Columns available for sorting
const SORTABLE_COLUMNS = [
  { id: 'salesperson_name', label: 'المندوب' },
  { id: 'area', label: 'المنطقة' },
  { id: 'phone', label: 'رقم الموبايل' },
  { id: 'customer_name', label: 'العميل' },
  { id: 'date', label: 'تاريخ القسط' },
  { id: 'sale_date', label: 'تاريخ البيع' },
  { id: 'amount', label: 'قيمة التحصيل' },
  { id: 'receipt_num', label: 'رقم الفاتورة' }
];

export default function InstallmentsReport() {
  const { setTableRef } = useSmartScroll();
  const { year, month, branchId } = useContext(ReportsContext);
  const navigate = useNavigate();
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });
  const tableContainerRef = useRef(null);

  const [selectedIds, setSelectedIds] = useState([]);
  
  const [saleFromYear, setSaleFromYear] = useState('');
  const [saleFromMonth, setSaleFromMonth] = useState('');
  const [saleToYear, setSaleToYear] = useState('');
  const [saleToMonth, setSaleToMonth] = useState('');
  const [salespersonId, setSalespersonId] = useState('');
  
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [area, setArea] = useState('');

  // Default Sort Order requested by User
  const [sortRules, setSortRules] = useState([
    { id: 1, column: 'salesperson_name', dir: 'asc' },
    { id: 2, column: 'area', dir: 'asc' },
    { id: 3, column: 'phone', dir: 'asc' },
    { id: 4, column: 'customer_name', dir: 'asc' }
  ]);
  const [showSortMenu, setShowSortMenu] = useState(false);
  
  const [salespersonsList, setSalespersonsList] = useState([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState({
    total_installments_amount: 0,
    installments_count: 0,
    installments: []
  });

  const handleSelectAll = useCallback((e) => {
    if (e.target.checked && data.installments) {
      setSelectedIds(data.installments.map(item => item.payment_id));
    } else {
      setSelectedIds([]);
    }
  }, [data.installments]);

  const toggleSelect = useCallback((id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }, []);

  const years = Array.from({ length: 11 }, (_, i) => new Date().getFullYear() - 5 + i);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

  useEffect(() => {
    // Fetch salespersons for filter dropdown
    const fetchSalespersons = async () => {
      try {
        const res = await api.get('/salespersons/', { params: { branch_id: branchId } });
        setSalespersonsList(res.data.results || res.data);
      } catch (err) {
        console.error("Failed to load salespersons", err);
      }
    };
    if (branchId) {
      fetchSalespersons();
    }
  }, [branchId]);

  useEffect(() => {
    if (year && month && branchId) {
      fetchData();
    }
  }, [year, month, saleFromYear, saleFromMonth, saleToYear, saleToMonth, salespersonId, branchId]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/reports/installments/', {
        params: {
          branch_id: branchId,
          year: year || undefined,
          month: month || undefined,
          salesperson_id: salespersonId || undefined,
          sale_from_year: saleFromYear || undefined,
          sale_from_month: saleFromMonth || undefined,
          sale_to_year: saleToYear || undefined,
          sale_to_month: saleToMonth || undefined,
          customer_name: customerName || undefined,
          phone: phone || undefined,
          area: area || undefined,
        }
      });
      setData(res.data);
      setSelectedIds([]);
    } catch (err) {
      setError(err.response?.data?.detail || 'حدث خطأ أثناء تحميل بيانات التقرير');
    } finally {
      setLoading(false);
    }
  };

  // --- Sorting Engine ---
  const addSortRule = () => {
    setSortRules([...sortRules, { id: Date.now(), column: 'amount', dir: 'desc' }]);
  };

  const removeSortRule = (id) => {
    setSortRules(sortRules.filter(r => r.id !== id));
  };

  const updateSortRule = (id, field, value) => {
    setSortRules(sortRules.map(r => r.id === id ? { ...r, [field]: value } : r));
  };

  const processedInstallments = useMemo(() => {
    if (!data.installments || data.installments.length === 0) return [];
    let list = [...data.installments];
    
    if (sortRules.length > 0) {
      list.sort((a, b) => {
        for (let rule of sortRules) {
          let valA = a[rule.column] || '';
          let valB = b[rule.column] || '';
          
          if (rule.column === 'amount') {
            valA = Number(valA);
            valB = Number(valB);
          } else if (typeof valA === 'string') {
            valA = valA.toLowerCase();
            valB = valB.toLowerCase();
          }
          
          if (valA < valB) return rule.dir === 'asc' ? -1 : 1;
          if (valA > valB) return rule.dir === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return list;
  }, [data.installments, sortRules]);

  return (
    <div className="p-3 fs-3" dir="rtl" style={{ fontSize: '1.02rem' }}>
      {/* Extra Filters */}
      <div className="card mb-3 border-0 bg-light-lt">
        <div className="card-body p-2">
          <div className="row g-2 align-items-center">
            <div className="col-auto">
              <span className="text-muted small fw-bold"><IconFilter size={14} className="me-1"/> فلاتر:</span>
            </div>
            
            <div className="col-auto">
              <input type="text" className="form-control form-control-sm" placeholder="اسم العميل" value={customerName} onChange={e => setCustomerName(e.target.value)} />
            </div>
            <div className="col-auto">
              <input type="text" className="form-control form-control-sm" placeholder="رقم الموبايل" value={phone} onChange={e => setPhone(e.target.value)} />
            </div>
            <div className="col-auto">
              <input type="text" className="form-control form-control-sm" placeholder="المنطقة" value={area} onChange={e => setArea(e.target.value)} />
            </div>

            <div className="col-auto">
              <select className="form-select form-select-sm" value={salespersonId} onChange={e => setSalespersonId(e.target.value)}>
                <option value="">كل المناديب</option>
                {salespersonsList.map(sp => (
                  <option key={sp.id} value={sp.id}>{sp.name}</option>
                ))}
              </select>
            </div>
            
            <div className="col-auto border-start ps-2">
              <span className="text-muted small fw-bold">تاريخ البيع (من)</span>
            </div>
            <div className="col-auto">
              <div className="d-flex gap-1">
                <select className="form-select form-select-sm" value={saleFromMonth} onChange={e => setSaleFromMonth(e.target.value)}>
                  <option value="">الشهر</option>
                  {months.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
                <select className="form-select form-select-sm" value={saleFromYear} onChange={e => setSaleFromYear(e.target.value)}>
                  <option value="">السنة</option>
                  {years.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
            </div>

            <div className="col-auto border-start ps-2">
              <span className="text-muted small fw-bold">(إلى)</span>
            </div>
            <div className="col-auto">
              <div className="d-flex gap-1">
                <select className="form-select form-select-sm" value={saleToMonth} onChange={e => setSaleToMonth(e.target.value)}>
                  <option value="">الشهر</option>
                  {months.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
                <select className="form-select form-select-sm" value={saleToYear} onChange={e => setSaleToYear(e.target.value)}>
                  <option value="">السنة</option>
                  {years.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
            </div>

            <div className="col-auto ms-auto">
              <button className="btn btn-sm btn-primary px-4 fw-bold" onClick={fetchData}>
                بحث
              </button>
            </div>

          </div>
        </div>
      </div>

      {error && <div className="alert alert-danger mb-3 border-secondary-subtle">{error}</div>}

      <div className="card shadow-sm" style={{ border: '1px solid #dee2e6' }}>
        <div className="card-header sticky-toolbar bg-light d-flex flex-wrap justify-content-between align-items-center py-2 gap-2" style={{ borderColor: '#dee2e6 !important' }}>
          <div className="d-flex align-items-center gap-3">
            <div className="text-dark fw-bold fs-3 d-flex align-items-center gap-2">
              نتائج التحصيل
              <span className="badge bg-primary text-white rounded-pill px-2 py-1">{toArabic(data.installments_count)} قسط</span>
            </div>
            
            {/* Sort Button Dropdown */}
            <div className="dropdown">
              <button 
                className="btn btn-sm btn-outline-secondary fw-bold px-3 py-1 d-flex align-items-center gap-1"
                type="button"
                onClick={() => setShowSortMenu(!showSortMenu)}
              >
                <IconSortAscending size={16} /> ترتيب حسب
              </button>
              
              {showSortMenu && (
                <div className="dropdown-menu show p-3 shadow-lg" style={{ minWidth: '350px', position: 'absolute', top: '100%', right: 0, zIndex: 1050 }}>
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <h6 className="m-0 fw-bold">إعدادات الفرز المتعدد</h6>
                    <button className="btn-close" onClick={() => setShowSortMenu(false)}></button>
                  </div>
                  
                  {sortRules.length === 0 ? (
                    <div className="text-muted small text-center my-3">الجدول بدون ترتيب (حسب السيرفر)</div>
                  ) : (
                    <div className="d-flex flex-column gap-2 mb-3">
                      {sortRules.map((rule, index) => (
                        <div key={rule.id} className="d-flex align-items-center gap-2 bg-light p-2 rounded border">
                          <span className="badge bg-secondary">{index + 1}</span>
                          <select className="form-select form-select-sm flex-grow-1" value={rule.column} onChange={e => updateSortRule(rule.id, 'column', e.target.value)}>
                            {SORTABLE_COLUMNS.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
                          </select>
                          <select className="form-select form-select-sm" style={{ width: '100px' }} value={rule.dir} onChange={e => updateSortRule(rule.id, 'dir', e.target.value)}>
                            <option value="asc">تصاعدي</option>
                            <option value="desc">تنازلي</option>
                          </select>
                          <button className="btn btn-sm btn-icon btn-outline-danger border-0" onClick={() => removeSortRule(rule.id)}>
                            <IconTrash size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  <div className="d-flex justify-content-between">
                    <button className="btn btn-sm btn-primary d-flex align-items-center gap-1" onClick={addSortRule}>
                      <IconPlus size={14} /> إضافة شرط
                    </button>
                    <button className="btn btn-sm btn-outline-secondary" onClick={() => setSortRules([])}>
                      مسح الكل
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            {selectedIds.length > 0 && (
              <div className="d-flex align-items-center gap-2 slide-in-right">
                <span className="badge bg-secondary px-2 py-1 fs-5 rounded-pill shadow-sm">
                  محدد: {toArabic(selectedIds.length)}
                </span>
                <button className="btn btn-sm btn-outline-primary fw-bold px-3 py-1 d-flex align-items-center gap-1">
                  <IconPrinter size={16} /> طباعة المحدد
                </button>
              </div>
            )}
          </div>
          
          <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm" style={{ borderColor: '#adb5bd !important' }}>
            إجمالي التحصيلات:{' '}
            <span className="text-success fw-bolder fs-4">{toArabic(fmtNum(data.total_installments_amount))}</span>
          </div>
        </div>

        {loading ? (
          <div className="card-body text-center py-5">
            <div className="spinner-border text-primary mb-3"></div>
            <div className="text-secondary fw-bold fs-3">جاري تحميل التحصيلات...</div>
          </div>
        ) : (
          <div
            ref={setTableRef}
            className="table-responsive hide-vertical-scroll" 
            style={{ 
              border: '1px solid #dee2e6',
              overflowY: 'auto',
              overflowX: 'auto'
            }}
          >
            <style>
              {`
                .hide-vertical-scroll::-webkit-scrollbar { width: 0px; height: 8px; }
                .hide-vertical-scroll::-webkit-scrollbar-track { background: #f1f1f1; }
                .hide-vertical-scroll::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 4px; }
                .hide-vertical-scroll::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }
                .hide-vertical-scroll { scrollbar-width: thin; }
                
                .hybrid-sticky-header th {
                  position: sticky !important;
                  top: 0 !important;
                  z-index: 1010;
                  background-color: #f8f9fa !important;
                  box-shadow: inset 0 -1px 0 var(--tblr-border-color);
                }
              `}
            </style>
            <table className="table hybrid-sticky-header table-bordered table-vcenter table-hover mb-0 text-nowrap">
              <thead className="bg-light">
                <tr>
                  <th className="text-center w-1">
                    <input 
                      type="checkbox" 
                      className="form-check-input border-secondary-subtle" 
                      checked={data.installments.length > 0 && selectedIds.length === data.installments.length}
                      onChange={handleSelectAll}
                    />
                  </th>
                  <th className="text-center w-1">#</th>
                  <th className="text-center">تاريخ القسط</th>
                  <th className="text-start px-2">العميل</th>
                  <th className="text-center">رقم الموبايل</th>
                  <th className="text-center">المنطقة</th>
                  <th className="text-center">المندوب</th>
                  <th className="text-center">رقم الفاتورة</th>
                  <th className="text-center">تاريخ البيع</th>
                  <th className="text-end px-2">قيمة التحصيل</th>
                </tr>
              </thead>
              <tbody>
                {processedInstallments.length > 0 ? processedInstallments.map((payment, index) => (
                  <InstallmentRow 
                    key={payment.payment_id}
                    payment={payment}
                    index={index}
                    isSelected={selectedIds.includes(payment.payment_id)}
                    toggleSelect={toggleSelect}
                    navigate={navigate}
                  />
                )) : (
                  <tr>
                    <td colSpan="10" className="text-center py-5">
                      <IconReceipt size={48} className="text-muted mb-2 opacity-50" />
                      <h4 className="text-muted fw-bold">لا توجد تحصيلات مطابقة لمعايير البحث</h4>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
