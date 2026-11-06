import React from 'react';

/**
 * StandardTablePageLayout — Unified Page Layout for Table & Listing Views
 * 
 * Standardizes:
 * - Outer fluid container: container-fluid py-3 d-flex flex-column native-page-scroll
 * - Page header banner: Icon + Title on right, header actions on left
 * - Sticky top toolbar slot: container for filters / search bars
 * - Main content area: flex-grow-1 for tables and data cards
 * - Modals / context menus slot: rendered at root level to prevent clipping
 * 
 * Props:
 * - title: string | React.ReactNode
 * - icon: React.ComponentType<{ size?: number, className?: string }>
 * - headerActions: React.ReactNode
 * - toolbar: React.ReactNode
 * - children: React.ReactNode
 * - modals: React.ReactNode
 * - className: string
 * - contentClassName: string
 */
export default function StandardTablePageLayout({
  title,
  icon: Icon,
  headerActions = null,
  toolbar = null,
  children,
  modals = null,
  className = '',
  contentClassName = '',
}) {
  return (
    <div
      className={`container-fluid py-3 d-flex flex-column native-page-scroll flex-grow-1 ${className}`}
      dir="rtl"
      style={{ minHeight: 'calc(100vh - 60px)', fontSize: '1.02rem' }}
    >
      {/* ── Page Header Banner ── */}
      {(title || headerActions) && (
        <div
          className="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-secondary-subtle"
          style={{ borderColor: '#dee2e6' }}
        >
          <div className="d-flex align-items-center gap-2">
            {Icon && <Icon size={28} className="text-primary flex-shrink-0" />}
            {title && (
              <h2 className="fw-bold text-dark m-0 fs-2 d-flex align-items-center gap-2">
                {title}
              </h2>
            )}
          </div>
          {headerActions && (
            <div className="d-flex align-items-center gap-2">
              {headerActions}
            </div>
          )}
        </div>
      )}

      {/* ── Sticky Top Toolbar Slot ── */}
      {toolbar && (
        <div className="mb-2">
          {toolbar}
        </div>
      )}

      {/* ── Main Content Area (Table / Card) ── */}
      <div className={`flex-grow-1 d-flex flex-column ${contentClassName}`}>
        {children}
      </div>

      {/* ── Modals & Context Menus Slot ── */}
      {modals}
    </div>
  );
}
