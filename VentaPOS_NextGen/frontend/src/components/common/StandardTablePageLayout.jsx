import React, { createContext, useContext, useState, useLayoutEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';

/**
 * StandardTableLayoutContext — Context allowing composite child views
 * (such as InventoryTab, SalespersonsTab, SuppliersTab, and ReportTable)
 * to portal their live search, count badges, and action bars directly into
 * the unified 2-row top card of StandardTablePageLayout without triggering
 * parent state re-render loops or losing input focus.
 */
export const StandardTableLayoutContext = createContext(null);

/**
 * useStandardTableSlots hook
 * Portals row1Extra and row2 elements into the parent StandardTablePageLayout
 * (or renders them inline as a fallback card if mounted outside StandardTablePageLayout).
 */
export function useStandardTableSlots(slots) {
  const context = useContext(StandardTableLayoutContext);
  const row1Extra = slots?.row1Extra;
  const row2 = slots?.row2;
  const hasRow2 = Boolean(row2);
  const setHasChildRow2 = context?.setHasChildRow2;

  useLayoutEffect(() => {
    if (setHasChildRow2 && hasRow2) {
      setHasChildRow2(true);
      return () => {
        setHasChildRow2(false);
      };
    }
  }, [setHasChildRow2, hasRow2]);

  if (!context) {
    if (!row1Extra && !row2) return null;
    return (
      <div className="card shadow-sm standard-top-card border-secondary-subtle d-print-none">
        {row1Extra && (
          <div className="standard-top-row standard-top-row-1 d-flex align-items-center gap-2 px-3">
            {row1Extra}
          </div>
        )}
        {row2 && (
          <div className="standard-top-row standard-top-row-2 d-flex align-items-center gap-2 px-3 border-top bg-light-subtle">
            {row2}
          </div>
        )}
      </div>
    );
  }

  return (
    <>
      {context.row1SlotEl && row1Extra ? createPortal(row1Extra, context.row1SlotEl) : null}
      {context.row2SlotEl && row2 ? createPortal(row2, context.row2SlotEl) : null}
    </>
  );
}

/**
 * StandardTablePageLayout — Unified Page Layout for Table & Listing Views
 * 
 * Standardizes:
 * - Fixed Top Section Height ("Title + 2 Rows") across all 5 table pages:
 *   - Header Banner (.standard-page-header): Fixed 48px height with Icon + Title on right, headerActions on left.
 *   - Unified 2-Row Top Controls Card (.standard-top-card): Single border-secondary-subtle card containing:
 *     - Row 1 (.standard-top-row.standard-top-row-1): Fixed 48px height for filter & search controls.
 *     - Row 2 (.standard-top-row.standard-top-row-2): Fixed 48px height for actions, status badges, & totals.
 * - Table Area (.standard-page-table-area): Starts immediately below the 2-row card at the exact same Y position (231px).
 * - Window-Level Sticky Table Header: The top section scrolls away naturally, leaving only <thead> sticky under the 56px Navbar.
 */
export default function StandardTablePageLayout({
  title,
  icon: Icon,
  headerActions = null,
  row1 = null,
  row2 = null,
  toolbar = null,
  children,
  modals = null,
  containerClassName = 'container-fluid px-3 pt-2 pb-4 native-page-scroll',
}) {
  const [row1SlotEl, setRow1SlotEl] = useState(null);
  const [row2SlotEl, setRow2SlotEl] = useState(null);
  const [hasChildRow2, setHasChildRow2] = useState(false);

  const contextValue = useMemo(() => ({
    row1SlotEl,
    row2SlotEl,
    setHasChildRow2,
    hasContext: true,
  }), [row1SlotEl, row2SlotEl]);

  return (
    <StandardTableLayoutContext.Provider value={contextValue}>
      <div className={containerClassName} dir="rtl">
        {/* ── Fixed Height Top Section (Title + Row 1 + Row 2) ── */}
        <div className="standard-page-top-section d-print-none">
          {(title || headerActions) && (
            <div className="standard-page-header d-flex justify-content-between align-items-center border-bottom border-secondary-subtle">
              <div className="d-flex align-items-center gap-2">
                {Icon && <Icon className="text-primary flex-shrink-0" size={24} />}
                {title && (
                  <h2 className="page-title m-0 fw-bold text-dark fs-2 d-flex align-items-center gap-2">
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

          <div className="card shadow-sm standard-top-card border-secondary-subtle">
            <div className="standard-top-row standard-top-row-1 d-flex align-items-center gap-2 px-3">
              {row1}
              <div ref={setRow1SlotEl} className="d-flex align-items-center gap-2 flex-grow-1" style={{ minWidth: 0, overflow: 'visible' }} />
            </div>
            <div className="standard-top-row standard-top-row-2 d-flex align-items-center gap-2 px-3 border-top bg-light-subtle">
              {!hasChildRow2 && (row2 || toolbar)}
              <div ref={setRow2SlotEl} className={hasChildRow2 ? 'd-flex align-items-center gap-2 w-100' : 'd-none'} style={{ minWidth: 0, overflow: 'visible' }} />
            </div>
          </div>
        </div>

        {/* ── Table Area (Starts directly with <table> at Y=231px) ── */}
        <div className="standard-page-table-area">
          {children}
        </div>

        {/* ── Modals & Context Menus Slot ── */}
        {modals}
      </div>
    </StandardTableLayoutContext.Provider>
  );
}

