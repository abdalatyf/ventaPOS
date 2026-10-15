import React, { useState, useEffect, useContext, useMemo } from 'react';
import { IconReceipt, IconSearch, IconFilter, IconRefresh } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import DebouncedInput from '../../components/DebouncedInput';
import { fmtNum, toEnglish, parseNumber, formatMMYYYY } from '../../utils/formatUtils';

export default function ExpensesReport() {
  const { year, month, branchId } = useContext(ReportsContext);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [descriptionQuery, setDescriptionQuery] = useState('');
  const [minAmount, setMinAmount] = useState('');
  const [maxAmount, setMaxAmount] = useState('');

  useEffect(() => {
    const fetchExpenses = async () => {
      if (!year || !month || !branchId) return;

      setLoading(true);
      setError(null);
      try {
        const response = await api.get('/expenses/', {
          params: { year, month, branch_id: branchId }
        });
        setData(response.data.results || response.data || []);
      } catch (err) {
        console.error("Error fetching expenses report:", err);
        setError("حدث خطأ أثناء جلب تقرير المصروفات.");
      } finally {
        setLoading(false);
      }
    };
    fetchExpenses();
  }, [year, month, branchId]);

  const rawList = Array.isArray(data) ? data : [];

  const processedItems = useMemo(() => {
    const cleanMin = minAmount !== '' ? parseNumber(minAmount) : null;
    const cleanMax = maxAmount !== '' ? parseNumber(maxAmount) : null;
    const cleanQuery = descriptionQuery.trim().toLowerCase();

    return rawList.filter((item) => {
      if (cleanQuery) {
        const desc = String(item.description || '').toLowerCase();
        if (!desc.includes(cleanQuery)) return false;
      }
      const amt = Number(item.amount) || 0;
      if (cleanMin !== null && amt < cleanMin) return false;
      if (cleanMax !== null && amt > cleanMax) return false;
      return true;
    });
  }, [rawList, descriptionQuery, minAmount, maxAmount]);

  const totalAmount = useMemo(() => {
    return processedItems.reduce((acc, item) => acc + (Number(item.amount) || 0), 0);
  }, [processedItems]);

  const handleResetFilters = () => {
    setDescriptionQuery('');
    setMinAmount('');
    setMaxAmount('');
  };

  const columns = [
    { 
      key: 'id', 
      label: 'رقم المصروف', 
      align: 'center', 
      className: 'fw-bold text-muted', 
      render: (item, i) => item.id || i + 1 
    },
    { 
      key: 'description', 
      label: 'البيان', 
      align: 'start', 
      className: 'fw-bold text-primary text-wrap px-2', 
      render: (item) => item.description || 'بدون بيان'
    },
    { 
      key: 'amount', 
      label: 'المبلغ', 
      align: 'center', 
      className: 'fw-bold text-danger text-nowrap fs-5', 
      render: (item) => fmtNum(item.amount || 0)
    },
    { 
      key: 'date', 
      label: 'التاريخ', 
      align: 'center', 
      className: 'text-muted text-nowrap', 
      dir: 'ltr', 
      render: (item) => formatMMYYYY(item.expense_month || month, item.expense_year || year) 
    }
  ];

  const summaryCards = [
    { 
      label: 'عدد المصروفات', 
      value: processedItems.length, 
      color: 'dark', 
      icon: IconReceipt 
    },
    { 
      label: 'إجمالي المصروفات', 
      value: fmtNum(totalAmount), 
      color: 'danger', 
      icon: IconReceipt 
    }
  ];

  const renderFiltersGrid = () => (
    <div className="card shadow-sm mb-3" style={{ border: '1px solid #dee2e6' }}>
      <div className="card-body p-3">
        <form onSubmit={(e) => e.preventDefault()}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: '0.75rem', alignItems: 'center' }}>
            
            <div style={{ gridColumn: 'span 4' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">البيان</span>
                <DebouncedInput 
                  type="text" 
                  className="form-control fw-bold border-secondary-subtle" 
                  placeholder="بحث في البيان..." 
                  value={descriptionQuery}
                  onChange={(e) => setDescriptionQuery(e.target.value)}
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 2' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">من مبلغ</span>
                <DebouncedInput 
                  type="text" 
                  inputMode="numeric"
                  className="form-control fw-bold border-secondary-subtle text-center px-1" 
                  placeholder="0" 
                  value={minAmount}
                  onChange={(e) => setMinAmount(toEnglish(e.target.value))}
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 2' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">إلى مبلغ</span>
                <DebouncedInput 
                  type="text" 
                  inputMode="numeric"
                  className="form-control fw-bold border-secondary-subtle text-center px-1" 
                  placeholder="0" 
                  value={maxAmount}
                  onChange={(e) => setMaxAmount(toEnglish(e.target.value))}
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 2' }} className="d-flex align-items-center gap-2 justify-content-end">
              <button 
                type="button" 
                className="btn btn-outline-secondary w-100 fw-bold fs-4 py-1" 
                onClick={handleResetFilters}
                title="إعادة ضبط الفلاتر"
                style={{ border: '1px solid #adb5bd' }}
              >
                <IconRefresh size={16} className="me-1" />
                إعادة ضبط
              </button>
            </div>

          </div>
        </form>
      </div>
    </div>
  );

  return (
    <div className="container-fluid p-0 d-flex flex-column" dir="rtl" style={{ minHeight: 'calc(100vh - 100px)' }}>
      {error && <div className="alert alert-danger mb-3">{error}</div>}
      
      {renderFiltersGrid()}

      <ReportTable
        columns={columns}
        data={processedItems}
        loading={loading}
        sortableColumns={[
          { id: 'id', label: 'رقم المصروف' },
          { id: 'description', label: 'البيان' },
          { id: 'amount', label: 'المبلغ' }
        ]}
        defaultSortRules={[
          { id: 1, column: 'id', dir: 'desc' }
        ]}
        summaryCards={summaryCards}
        emptyMessage="لا توجد مصروفات مسجلة في هذه الفترة"
        emptyIcon={IconReceipt}
      />
    </div>
  );
}
