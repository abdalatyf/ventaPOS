import React, { useState, useEffect, useContext, useMemo } from 'react';
import { IconReceipt, IconSearch, IconFilter, IconRefresh } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import DebouncedInput from '../../components/DebouncedInput';
import { fmtNum, toEnglish, parseNumber, formatMMYYYY } from '../../utils/formatUtils';

const CATEGORY_PRESETS = ['مصروفات عامة', 'إيجار', 'كهرباء ومياه', 'نقل ومشال', 'صيانة', 'نثريات'];

export default function ExpensesReport() {
  const { year, month, branchId } = useContext(ReportsContext);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [descriptionQuery, setDescriptionQuery] = useState('');
  const [categoryQuery, setCategoryQuery] = useState('');
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
      if (categoryQuery) {
        const cat = item.category || 'مصروفات عامة';
        if (cat !== categoryQuery) return false;
      }
      if (cleanQuery) {
        const desc = String(item.description || '').toLowerCase();
        if (!desc.includes(cleanQuery)) return false;
      }
      const amt = Number(item.amount) || 0;
      if (cleanMin !== null && amt < cleanMin) return false;
      if (cleanMax !== null && amt > cleanMax) return false;
      return true;
    });
  }, [rawList, descriptionQuery, categoryQuery, minAmount, maxAmount]);

  const totalAmount = useMemo(() => {
    return processedItems.reduce((acc, item) => acc + (Number(item.amount) || 0), 0);
  }, [processedItems]);

  const handleResetFilters = () => {
    setDescriptionQuery('');
    setCategoryQuery('');
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
      key: 'category', 
      label: 'التصنيف', 
      align: 'center', 
      className: 'fw-bold text-nowrap', 
      render: (item) => (
        <span className="badge bg-blue-lt text-primary fw-bold px-2 py-1">
          {item.category || 'مصروفات عامة'}
        </span>
      )
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

  const renderFilters = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Description */}
      <div className="flex-grow-1" style={{ minWidth: '150px' }}>
        <DebouncedInput 
          type="text" 
          className="form-control form-control-sm fw-bold border-secondary-subtle" 
          placeholder="بحث في البيان..." 
          value={descriptionQuery}
          onChange={(e) => setDescriptionQuery(e.target.value)}
        />
      </div>

      {/* Category */}
      <div style={{ width: '130px' }} className="flex-shrink-0">
        <select
          className="form-select form-select-sm fw-bold border-secondary-subtle"
          value={categoryQuery}
          onChange={(e) => setCategoryQuery(e.target.value)}
        >
          <option value="">كل التصنيفات</option>
          {CATEGORY_PRESETS.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {/* Min Amount */}
      <div style={{ width: '90px' }} className="flex-shrink-0">
        <DebouncedInput 
          type="text" 
          inputMode="numeric"
          className="form-control form-control-sm fw-bold border-secondary-subtle text-center px-1" 
          placeholder="من مبلغ" 
          value={minAmount}
          onChange={(e) => setMinAmount(toEnglish(e.target.value))}
        />
      </div>

      {/* Max Amount */}
      <div style={{ width: '90px' }} className="flex-shrink-0">
        <DebouncedInput 
          type="text" 
          inputMode="numeric"
          className="form-control form-control-sm fw-bold border-secondary-subtle text-center px-1" 
          placeholder="إلى مبلغ" 
          value={maxAmount}
          onChange={(e) => setMaxAmount(toEnglish(e.target.value))}
        />
      </div>

      {/* Reset */}
      <button 
        type="button" 
        className="btn btn-outline-secondary btn-sm fw-bold px-2 py-1 flex-shrink-0 border-secondary-subtle d-flex align-items-center gap-1" 
        onClick={handleResetFilters}
        title="إعادة ضبط الفلاتر"
      >
        <IconRefresh size={14} />
        <span>إعادة ضبط</span>
      </button>
    </div>
  );

  return (
    <div className="w-100 p-0">
      {error && <div className="alert alert-danger mb-2 py-1">{error}</div>}

      <ReportTable
        columns={columns}
        data={processedItems}
        loading={loading}
        sortableColumns={[
          { id: 'id', label: 'رقم المصروف' },
          { id: 'description', label: 'البيان' },
          { id: 'category', label: 'التصنيف' },
          { id: 'amount', label: 'المبلغ' }
        ]}
        defaultSortRules={[
          { id: 1, column: 'id', dir: 'desc' }
        ]}
        summaryCards={summaryCards}
        renderFilters={renderFilters}
        emptyMessage="لا توجد مصروفات مسجلة في هذه الفترة"
        emptyIcon={IconReceipt}
      />
    </div>
  );
}
