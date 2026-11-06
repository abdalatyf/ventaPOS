import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import useSmartScroll from '../hooks/useSmartScroll';
import { IconSortAscending, IconPlus, IconTrash, IconPrinter } from '@tabler/icons-react';
import PrintModal from './common/PrintModal';
import api from '../api';
import './ReportTable.css';
import { useStandardTableSlots } from './common/StandardTablePageLayout';

const SortDropdown = ({ sortRules, setSortRules, sortableColumns }) => {
  const [showSortMenu, setShowSortMenu] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on outside click or Escape key
  useEffect(() => {
    if (!showSortMenu) return;
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowSortMenu(false);
      }
    };
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setShowSortMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showSortMenu]);

  const addSortRule = () => {
    if (sortableColumns.length > 0) {
      setSortRules([...sortRules, { id: Date.now(), column: sortableColumns[0].id, dir: 'asc' }]);
    }
  };

  const removeSortRule = (id) => {
    setSortRules(sortRules.filter(r => r.id !== id));
  };

  const updateSortRule = (id, field, value) => {
    setSortRules(sortRules.map(r => r.id === id ? { ...r, [field]: value } : r));
  };

  if (sortableColumns.length === 0) return null;

  return (
    <div className="dropdown" ref={dropdownRef}>
      <button 
        type="button"
        className={`btn btn-sm btn-outline-secondary fw-bold px-3 py-1 d-flex align-items-center gap-1 border-secondary-subtle ${showSortMenu ? 'active' : ''}`}
        onClick={() => setShowSortMenu(!showSortMenu)}
        title="ترتيب متعدد الأعمدة"
      >
        <IconSortAscending size={14} />
        <span>ترتيب حسب</span>
        {sortRules.length > 0 && (
          <span className="badge bg-secondary ms-1 rounded-pill">{sortRules.length}</span>
        )}
      </button>

      {showSortMenu && (
        <div className="dropdown-menu show p-3 shadow-lg" style={{ minWidth: '400px', zIndex: 1050, left: 0, right: 'auto' }}>
          <div className="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom">
            <h6 className="mb-0 fw-bold">قواعد الترتيب</h6>
            <button type="button" className="btn btn-sm btn-outline-primary py-0 px-2" onClick={addSortRule}>
              <IconPlus size={14} className="me-1"/> إضافة قاعدة
            </button>
          </div>

          {sortRules.length === 0 ? (
            <div className="text-center text-muted small py-3">لا توجد قواعد ترتيب محددة</div>
          ) : (
            <div className="d-flex flex-column gap-2 mb-2">
              {sortRules.map((rule, idx) => (
                <div key={rule.id} className="d-flex gap-2 align-items-center p-2 bg-light rounded border">
                  <span className="badge bg-secondary rounded-pill">{idx + 1}</span>
                  <select 
                    className="form-select form-select-sm" 
                    value={rule.column} 
                    onChange={(e) => updateSortRule(rule.id, 'column', e.target.value)}
                  >
                    {sortableColumns.map(col => (
                      <option key={col.id} value={col.id}>{col.label}</option>
                    ))}
                  </select>
                  <select 
                    className="form-select form-select-sm" 
                    style={{ width: '100px' }}
                    value={rule.dir} 
                    onChange={(e) => updateSortRule(rule.id, 'dir', e.target.value)}
                  >
                    <option value="asc">تصاعدي</option>
                    <option value="desc">تنازلي</option>
                  </select>
                  <button type="button" className="btn btn-sm btn-icon btn-outline-danger border-0" onClick={() => removeSortRule(rule.id)}>
                    <IconTrash size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="d-flex justify-content-end mt-3 pt-2 border-top">
            <button type="button" className="btn btn-sm btn-primary px-4" onClick={() => setShowSortMenu(false)}>تم</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default function ReportTable({
  columns = [],
  data = [],
  loading = false,
  summaryCards = [],
  renderFilters = null,
  renderRow = null,
  renderHeader = null,
  emptyMessage = "لا توجد بيانات للفترة المحددة",
  emptyIcon: EmptyIcon,
  checkboxSelection = false,
  selectedIds = [],
  onSelectionChange = null,
  idField = 'id',
  sortableColumns = [],
  defaultSortRules = [],
  headerToolbarExtra = null, // for buttons like Print
  reportTitle = null,
  periodLabel = null,
  filtersSummary = [],
  footerRow = null,
  onPrintReport = null,
  children = null,
}) {
  const { setTableRef } = useSmartScroll();
  const [sortRules, setSortRules] = useState(defaultSortRules);
  const [focusedRowIndex, setFocusedRowIndex] = useState(-1);
  const [printModalOpen, setPrintModalOpen] = useState(false);
  const tableContainerElemRef = useRef(null);

  // Combine ref for useSmartScroll and internal keyboard focus
  const handleSetTableRef = useCallback((node) => {
    tableContainerElemRef.current = node;
    setTableRef(node);
  }, [setTableRef]);

  // Direct Column Header Click-to-Sort
  const toggleSort = useCallback((colKey) => {
    setSortRules(prevRules => {
      const existingIdx = prevRules.findIndex(r => r.column === colKey);
      if (existingIdx === -1) {
        return [{ id: Date.now(), column: colKey, dir: 'asc' }];
      }
      const existing = prevRules[existingIdx];
      if (existing.dir === 'asc') {
        return [{ ...existing, dir: 'desc' }];
      }
      return [];
    });
  }, []);

  const isColSortable = useCallback((colKey) => {
    if (!sortableColumns || sortableColumns.length === 0) return true;
    return sortableColumns.some(c => c.id === colKey);
  }, [sortableColumns]);

  const getColSortDir = useCallback((colKey) => {
    const rule = sortRules.find(r => r.column === colKey);
    return rule ? rule.dir : null;
  }, [sortRules]);

  const processedData = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) return [];
    if (sortRules.length === 0) return data;

    return [...data].sort((a, b) => {
      for (let rule of sortRules) {
        let valA = a[rule.column];
        let valB = b[rule.column];

        // Handle numeric parsing if string looks like a number
        if (typeof valA === 'string' && typeof valB === 'string') {
          const numA = parseFloat(valA.replace(/,/g, ''));
          const numB = parseFloat(valB.replace(/,/g, ''));
          if (!isNaN(numA) && !isNaN(numB)) {
            valA = numA;
            valB = numB;
          }
        }

        if (valA < valB) return rule.dir === 'asc' ? -1 : 1;
        if (valA > valB) return rule.dir === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [data, sortRules]);

  const handleSelectAll = (e) => {
    if (!onSelectionChange) return;
    if (e.target.checked && processedData.length > 0) {
      onSelectionChange(processedData.map(item => item[idField]));
    } else {
      onSelectionChange([]);
    }
  };

  const toggleSelect = (id) => {
    if (!onSelectionChange) return;
    onSelectionChange(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  // Keyboard navigation across table rows
  const handleKeyDown = (e) => {
    if (!processedData || processedData.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocusedRowIndex(prev => {
        const next = Math.min(prev + 1, processedData.length - 1);
        scrollRowIntoView(next);
        return next;
      });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setFocusedRowIndex(prev => {
        const next = Math.max(prev - 1, 0);
        scrollRowIntoView(next);
        return next;
      });
    } else if (e.key === ' ' && checkboxSelection && focusedRowIndex >= 0) {
      e.preventDefault();
      const item = processedData[focusedRowIndex];
      if (item) toggleSelect(item[idField]);
    } else if (e.key === 'Enter' && focusedRowIndex >= 0) {
      const container = tableContainerElemRef.current;
      if (container) {
        const row = container.querySelector(`tbody tr[data-row-index="${focusedRowIndex}"]`);
        if (row) {
          const actionEl = row.querySelector('.drilldown-link, a, button');
          if (actionEl) actionEl.click();
        }
      }
    }
  };

  const scrollRowIntoView = (index) => {
    const container = tableContainerElemRef.current;
    if (container) {
      const row = container.querySelector(`tbody tr[data-row-index="${index}"]`);
      if (row) {
        row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  };

  const effectiveReportTitle = useMemo(() => {
    if (reportTitle) return reportTitle;
    const path = typeof window !== 'undefined' ? window.location.pathname : '';
    const titleMap = {
      '/reports/receipts': 'تقرير فواتير البيع',
      '/reports/purchases': 'تقرير فواتير المشتريات',
      '/reports/installments': 'تقرير تحصيلات الأقساط',
      '/reports/inventory-movement': 'تقرير حركة المخزون',
      '/reports/expenses': 'تقرير المصروفات',
      '/reports/profit-and-loss': 'تقرير الأرباح والخسائر',
      '/reports/salesperson-performance': 'تقرير أداء المناديب',
      '/reports/averages': 'تقرير المتوسطات والربحية',
      '/reports/cash-drawer': 'تقرير تفاصيل السيولة والخزنة',
    };
    return titleMap[path] || 'تقرير تحليلي';
  }, [reportTitle]);

  const executePrintReport = async ({ action, targetPrinter }) => {
    const printColumns = columns.map(col => ({
      key: col.key || col.id,
      label: col.label,
      align: col.align || 'center'
    }));

    const printRows = processedData.map((row, index) => {
      const rowObj = {};
      columns.forEach(col => {
        const key = col.key || col.id;
        let val = '';
        if (col.getValue && typeof col.getValue === 'function') {
          val = col.getValue(row, index);
        } else if (col.plainText && typeof col.plainText === 'function') {
          val = col.plainText(row, index);
        } else if (row[key] !== undefined && row[key] !== null) {
          val = row[key];
        }
        if (col.format === 'currency') {
          val = Math.round(Number(val) || 0).toLocaleString('en-US');
        }
        rowObj[key] = val !== undefined && val !== null ? String(val) : '';
      });
      return rowObj;
    });

    const printKpis = (summaryCards || []).map(card => ({
      label: card.label,
      value: card.value,
      color: card.color || 'primary'
    }));

    const currentBranchId = localStorage.getItem('branchId');

    const payload = {
      title: effectiveReportTitle,
      branch_id: currentBranchId ? Number(currentBranchId) : undefined,
      period_label: periodLabel || undefined,
      filters_summary: filtersSummary || [],
      kpis: printKpis,
      columns: printColumns,
      rows: printRows,
      footer_row: footerRow || null,
      action,
      target_printer: targetPrinter || null
    };

    await api.post('/reports/desktop_print/', payload);
  };

  // Inject row1Extra (filters) and row2 (summary pills + print + sort) into StandardTablePageLayout
  const slotPortals = useStandardTableSlots({
    row1Extra: renderFilters ? (
      <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
        {typeof renderFilters === 'function' ? renderFilters() : renderFilters}
      </div>
    ) : null,
    row2: (
      <div className="d-flex align-items-center justify-content-between w-100 flex-nowrap" style={{ overflow: 'visible' }}>
        {summaryCards && summaryCards.length > 0 ? (
          <div className="d-flex align-items-center gap-2 flex-nowrap overflow-auto hide-vertical-scroll" style={{ minWidth: 0 }}>
            {summaryCards.map((card, i) => {
              const IconComp = card.icon;
              return (
                <div key={i} className="flex-shrink-0">
                  <div className="text-dark fw-bold border px-3 py-1 bg-white rounded shadow-sm d-flex align-items-center gap-2 report-summary-card" style={{ borderColor: '#adb5bd' }}>
                    {IconComp && <IconComp size={14} className={`text-${card.color || 'primary'}`} />}
                    <span className="text-muted small">{card.label}:</span>
                    <span className={`text-${card.color || 'primary'} fw-bolder fs-4 tabular-nums`}>{card.value}</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="d-flex align-items-center gap-2">
            <span className="badge bg-secondary text-white rounded-pill px-2 py-1 tabular-nums">
              {processedData.length || (data ? data.length : 0)} سجل
            </span>
          </div>
        )}

        <div className="ms-auto d-flex gap-2 align-items-center flex-shrink-0">
          {headerToolbarExtra}

          <button
            type="button"
            className="btn btn-sm btn-outline-primary fw-bold px-3 py-1 d-flex align-items-center gap-1 border-secondary-subtle"
            onClick={onPrintReport || (() => setPrintModalOpen(true))}
            disabled={loading || (processedData.length === 0 && (!data || data.length === 0))}
            title="طباعة التقرير"
          >
            <IconPrinter size={14} />
            <span>طباعة</span>
          </button>

          {/* Multi-Rule Sort Dropdown */}
          <SortDropdown 
            sortableColumns={sortableColumns}
            sortRules={sortRules}
            setSortRules={setSortRules}
          />
        </div>
      </div>
    )
  });

  return (
    <>
      {slotPortals}
      <div className="card shadow-sm border-secondary-subtle flex-grow-1 d-flex flex-column mb-3" style={{ minHeight: 0 }}>
      {/* Table Container */}
      <div 
        ref={handleSetTableRef} 
        tabIndex={0}
        onKeyDown={handleKeyDown}
        className="table-responsive hide-vertical-scroll report-table-container flex-grow-1 rounded-bottom focus-ring-none" 
        style={{ outline: 'none', overflow: 'visible' }}
      >
        <table className="table table-bordered table-vcenter table-hover mb-0 text-nowrap table-sticky-header">
          {children ? (
            children
          ) : (
            <>
              <thead className="bg-light report-sticky-header">
                {renderHeader ? (
                  typeof renderHeader === 'function' ? renderHeader({ toggleSort, sortRules, getColSortDir }) : renderHeader
                ) : (
                  <tr>
                    {checkboxSelection && (
                      <th className="text-center w-1">
                        <input 
                          type="checkbox" 
                          className="form-check-input border-secondary-subtle" 
                          checked={processedData.length > 0 && selectedIds.length === processedData.length}
                          onChange={handleSelectAll} 
                        />
                      </th>
                    )}
                    {columns.map((col, i) => {
                      const colKey = col.key || col.id;
                      const sortable = col.sortable !== false && isColSortable(colKey);
                      const sortDir = getColSortDir(colKey);
                      return (
                        <th 
                          key={colKey || i} 
                          className={`text-${col.align || 'center'} ${col.className || ''} ${sortable ? 'sortable-th' : ''}`} 
                          style={col.style}
                          onClick={sortable ? () => toggleSort(colKey) : undefined}
                          title={sortable ? 'انقر للترتيب' : undefined}
                        >
                          <div className="d-flex align-items-center justify-content-center gap-1">
                            <span>{col.label}</span>
                            {sortable && (
                              <span className="small text-muted" style={{ minWidth: '12px' }}>
                                {sortDir === 'asc' ? '↑' : sortDir === 'desc' ? '↓' : ''}
                              </span>
                            )}
                          </div>
                        </th>
                      );
                    })}
                  </tr>
                )}
              </thead>
              <tbody>
                {loading ? (
                  [...Array(10)].map((_, i) => (
                    <tr key={i}>
                      {checkboxSelection && <td><div className="placeholder w-100"></div></td>}
                      {columns.map((col, j) => (
                        <td key={j}><div className="placeholder w-100"></div></td>
                      ))}
                    </tr>
                  ))
                ) : processedData.length > 0 ? (
                  processedData.map((item, index) => {
                    const isFocused = focusedRowIndex === index;
                    if (renderRow) {
                      return renderRow({
                        item, 
                        index, 
                        isSelected: selectedIds.includes(item[idField]),
                        toggleSelect: () => toggleSelect(item[idField]),
                        isFocused
                      });
                    }
                    
                    return (
                      <tr 
                        key={item[idField] || index}
                        data-row-index={index}
                        className={isFocused ? 'table-row-focused' : ''}
                        onClick={() => setFocusedRowIndex(index)}
                      >
                        {checkboxSelection && (
                          <td className="text-center align-middle border-secondary-subtle">
                            <input 
                              type="checkbox" 
                              className="form-check-input border-secondary-subtle" 
                              checked={selectedIds.includes(item[idField])}
                              onChange={() => toggleSelect(item[idField])}
                            />
                          </td>
                        )}
                        {columns.map((col, j) => {
                          let val = col.render ? col.render(item, index) : item[col.key];
                          if (col.format === 'currency') val = (Number(val) || 0).toLocaleString('en-US');
                          if (col.format === 'number') val = val;
                          return (
                            <td key={j} className={`text-${col.align || 'center'} align-middle border-secondary-subtle ${col.className || ''}`} style={col.style} dir={col.dir}>
                              {val}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={checkboxSelection ? columns.length + 1 : (columns.length || 1)} className="text-center py-5">
                      {EmptyIcon && <EmptyIcon size={48} className="text-muted mb-2 opacity-50" />}
                      <h4 className="text-muted fw-bold">{emptyMessage}</h4>
                    </td>
                  </tr>
                )}
              </tbody>
            </>
          )}
        </table>
      </div>

      {!onPrintReport && (
        <PrintModal
          isOpen={printModalOpen}
          onClose={() => setPrintModalOpen(false)}
          title={`طباعة ${effectiveReportTitle}`}
          itemCount={processedData.length}
          itemLabel="سجل"
          onExecute={executePrintReport}
        />
      )}
      </div>
    </>
  );
}
