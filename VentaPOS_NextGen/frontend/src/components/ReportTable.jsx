import React, { useState, useMemo } from 'react';
import useSmartScroll from '../hooks/useSmartScroll';
import { IconSortAscending, IconPlus, IconTrash } from '@tabler/icons-react';
import './ReportTable.css';



const SortDropdown = ({ sortRules, setSortRules, sortableColumns }) => {
  const [showSortMenu, setShowSortMenu] = useState(false);

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
    <div className="dropdown">
      <button 
        className={`btn btn-sm btn-outline-secondary fw-bold px-3 py-1 d-flex align-items-center gap-1 ${showSortMenu ? 'active' : ''}`}
        onClick={() => setShowSortMenu(!showSortMenu)}
      >
        <IconSortAscending size={16} />
        ترتيب حسب
        {sortRules.length > 0 && (
          <span className="badge bg-secondary ms-1 rounded-pill">{sortRules.length}</span>
        )}
      </button>

      {showSortMenu && (
        <div className="dropdown-menu show p-3 shadow-lg" style={{ minWidth: '400px', zIndex: 1050, left: 0, right: 'auto' }}>
          <div className="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom">
            <h6 className="mb-0 fw-bold">قواعد الترتيب</h6>
            <button className="btn btn-sm btn-outline-primary py-0 px-2" onClick={addSortRule}>
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
                  <button className="btn btn-sm btn-icon btn-outline-danger border-0" onClick={() => removeSortRule(rule.id)}>
                    <IconTrash size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="d-flex justify-content-end mt-3 pt-2 border-top">
            <button className="btn btn-sm btn-primary px-4" onClick={() => setShowSortMenu(false)}>تم</button>
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
}) {
  const { setTableRef } = useSmartScroll();
  const [sortRules, setSortRules] = useState(defaultSortRules);

  const processedData = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) return [];
    if (sortRules.length === 0) return data;

    return [...data].sort((a, b) => {
      for (let rule of sortRules) {
        let valA = a[rule.column];
        let valB = b[rule.column];

        // Handle numeric parsing if string looks like a number
        if (typeof valA === 'string' && typeof valB === 'string') {
          const numA = parseFloat(valA);
          const numB = parseFloat(valB);
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

  return (
    <div className="card shadow-sm border-secondary-subtle flex-grow-1 d-flex flex-column mb-3" style={{ minHeight: 0 }}>
      {/* Unified Sticky Toolbar */}
      {(renderFilters || summaryCards.length > 0 || sortableColumns.length > 0 || headerToolbarExtra) && (
        <div className="sticky-toolbar bg-white border-bottom p-2 d-print-none d-flex align-items-center gap-2">
          
          {renderFilters && renderFilters()}

          {summaryCards && summaryCards.length > 0 && (
            <div className="flex-grow-1 overflow-auto hide-vertical-scroll" style={{ minWidth: 0 }}>
              <div className="d-flex flex-nowrap gap-2 pb-1 px-1">
                {summaryCards.map((card, i) => {
                  const IconComp = card.icon;
                  return (
                    <div key={i} className="flex-shrink-0">
                      <div className="text-dark fw-bold border px-3 py-1 bg-white rounded shadow-sm d-flex align-items-center gap-2 report-summary-card">
                        {IconComp && <IconComp size={16} className={`text-${card.color || 'primary'}`} />}
                        <span className="text-muted small">{card.label}:</span>
                        <span className={`text-${card.color || 'primary'} fw-bolder fs-4`}>{card.value}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="ms-auto d-flex gap-2 align-items-center">
            {headerToolbarExtra}

            {/* Sort Dropdown */}
            <SortDropdown 
              sortableColumns={sortableColumns}
              sortRules={sortRules}
              setSortRules={setSortRules}
            />
          </div>
        </div>
      )}

      {/* Table Container */}
      <div 
        ref={setTableRef} 
        className="table-responsive hide-vertical-scroll report-table-container flex-grow-1 rounded-bottom" 
        style={{ maxHeight: 'calc(100vh - 200px)' }}
      >
        <table className="table table-bordered table-vcenter table-hover mb-0 text-nowrap">
          <thead className="bg-light report-sticky-header">
            {renderHeader ? renderHeader() : (
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
                {columns.map((col, i) => (
                  <th key={col.key || i} className={`text-${col.align || 'center'} ${col.className || ''}`} style={col.style}>
                    {col.label}
                  </th>
                ))}
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
                if (renderRow) {
                  return renderRow({
                    item, 
                    index, 
                    isSelected: selectedIds.includes(item[idField]),
                    toggleSelect: () => toggleSelect(item[idField])
                  });
                }
                
                return (
                  <tr key={item[idField] || index}>
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
                <td colSpan={checkboxSelection ? columns.length + 1 : columns.length} className="text-center py-5">
                  {EmptyIcon && <EmptyIcon size={48} className="text-muted mb-2 opacity-50" />}
                  <h4 className="text-muted fw-bold">{emptyMessage}</h4>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
