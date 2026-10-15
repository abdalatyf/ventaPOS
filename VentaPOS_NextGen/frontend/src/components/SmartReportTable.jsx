import React from 'react';
import { IconAlertTriangle, IconFileOff } from '@tabler/icons-react';
import useSmartScroll from '../hooks/useSmartScroll';

export default function SmartReportTable({
  columns,
  data,
  loading,
  error,
  sortColumn,
  sortDirection,
  onSort,
  emptyMessage = "لا توجد بيانات مطابقة للبحث",
  renderRow
}) {
  const { setTableRef } = useSmartScroll();

  if (error) {
    return (
      <div className="alert alert-danger d-flex align-items-center" role="alert">
        <IconAlertTriangle className="me-2" />
        <div>{error}</div>
      </div>
    );
  }

  return (
    <div className="card shadow-sm mb-3">
      <div 
        className="table-responsive hide-vertical-scroll" 
        ref={setTableRef}
        style={{ scrollbarGutter: 'stable' }}
      >
        <table className="table table-vcenter card-table table-hover table-striped">
          <thead className="hybrid-sticky-header">
            <tr>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className={col.sortable ? "cursor-pointer" : ""}
                  onClick={() => {
                    if (col.sortable && onSort) onSort(col.key);
                  }}
                  aria-sort={sortColumn === col.key ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}
                >
                  <div className="d-flex align-items-center">
                    {col.label}
                    {col.sortable && sortColumn === col.key && (
                      <span className="ms-1">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              // Skeleton Loader
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={`skel-${i}`}>
                  {columns.map((_, j) => (
                    <td key={`skel-td-${j}`}>
                      <div className="placeholder placeholder-xs col-12"></div>
                    </td>
                  ))}
                </tr>
              ))
            ) : data && data.length > 0 ? (
              data.map((row, i) => renderRow(row, i))
            ) : (
              // Empty State
              <tr>
                <td colSpan={columns.length} className="text-center py-5">
                  <IconFileOff size={48} className="text-muted mb-2 opacity-50" />
                  <h4 className="text-muted fw-bold">{emptyMessage}</h4>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {/* We inject the CSS for the hybrid sticky header once here to avoid duplication */}
      <style dangerouslySetInnerHTML={{__html: `
        .hide-vertical-scroll::-webkit-scrollbar { width: 0px; background: transparent; }
        .hide-vertical-scroll:hover::-webkit-scrollbar { width: 6px; }
        .hide-vertical-scroll::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.2); border-radius: 4px; }
        .hybrid-sticky-header th { 
          position: sticky !important; 
          top: 0 !important; 
          z-index: 10 !important; 
          background-color: #f8f9fa !important; 
          border-bottom: 2px solid #dee2e6 !important;
          box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
      `}} />
    </div>
  );
}
