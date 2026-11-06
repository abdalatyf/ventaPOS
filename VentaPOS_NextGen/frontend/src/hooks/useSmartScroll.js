import { useRef, useCallback, useEffect } from 'react';

/**
 * Custom hook to implement the "2-Scroll Architecture" (Window Scroll -> Internal Table Y & X Scroll).
 * It uses native CSS overflow-y toggling based on absolute distance to bottom.
 * By perfectly calculating the table's maxHeight, the window naturally stops scrolling
 * at the exact millisecond the table container touches the navbar, at which point the table's
 * scrollbar appears (without layout shifts thanks to scrollbar-gutter).
 *
 * Horizontal scroll (overflow-x: auto) is ALWAYS enabled so wide tables can be scrolled horizontally
 * at any time.
 *
 * Uses lightweight ResizeObserver on the sticky-toolbar, table container, and the inner <table>
 * to ensure that asynchronous data loading or resizing immediately recalculates maxHeight and
 * re-evaluates overflowY.
 */
export default function useSmartScroll() {
  const tableContainerRef = useRef(null);
  const resizeObserverRef = useRef(null);

  const handleScroll = useCallback(() => {
    if (!tableContainerRef.current) return;
    
    // Absolute distance to bottom to toggle the scrollbar
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = window.innerHeight;
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    
    const currentZoom = parseFloat(document.body.style.zoom) || 1.0;
    const tolerance = Math.max(8, 12 / currentZoom);
    const distanceToBottom = scrollHeight - clientHeight - scrollTop;
    
    if (distanceToBottom <= tolerance) {
      // Window hit bottom: top of tableContainer is touching Navbar. Enable table internal Y scroll!
      if (tableContainerRef.current.style.overflowY !== 'auto') {
        tableContainerRef.current.style.overflowY = 'auto';
      }
    } else {
      // Window is not at bottom. Disable table internal Y scroll so window natively scrolls!
      if (tableContainerRef.current.style.overflowY !== 'hidden') {
        tableContainerRef.current.style.overflowY = 'hidden';
      }
    }
  }, []);

  const adjustHeight = useCallback(() => {
    if (!tableContainerRef.current) return;
    
    const currentZoom = parseFloat(document.body.style.zoom) || 1.0;
    
    // Always ensure horizontal scroll is enabled
    tableContainerRef.current.style.overflowX = 'auto';

    // Measure toolbar if present (legacy or inside page)
    const toolbar = document.querySelector('.sticky-toolbar');
    const toolbarHeight = toolbar ? toolbar.offsetHeight : 0;
    
    const offset = 56 + toolbarHeight + 20;
    tableContainerRef.current.style.maxHeight = `calc((100vh / ${currentZoom}) - ${offset}px)`;

    // Measure row 1 of multi-level headers dynamically
    const headerRow1 = tableContainerRef.current.querySelector('thead > tr:first-child');
    if (headerRow1) {
      tableContainerRef.current.style.setProperty('--header-row-1-height', `${headerRow1.offsetHeight}px`);
    }

    handleScroll();
  }, [handleScroll]);

  const setupObservers = useCallback((node) => {
    if (resizeObserverRef.current) {
      resizeObserverRef.current.disconnect();
    }

    if (typeof ResizeObserver !== 'undefined' && node) {
      resizeObserverRef.current = new ResizeObserver(() => {
        adjustHeight();
      });

      const toolbar = document.querySelector('.sticky-toolbar');
      if (toolbar) resizeObserverRef.current.observe(toolbar);
      resizeObserverRef.current.observe(node);

      const tableEl = node.querySelector('table');
      if (tableEl) resizeObserverRef.current.observe(tableEl);
    }
  }, [adjustHeight]);

  const setTableRef = useCallback((node) => {
    tableContainerRef.current = node;
    if (node) {
      adjustHeight();
      handleScroll();
      setupObservers(node);
    }
  }, [adjustHeight, handleScroll, setupObservers]);

  useEffect(() => {
    adjustHeight();
    handleScroll();

    window.addEventListener('resize', adjustHeight);
    window.addEventListener('app-zoom-changed', adjustHeight);
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('resize', adjustHeight);
      window.removeEventListener('app-zoom-changed', adjustHeight);
      window.removeEventListener('scroll', handleScroll);
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
    };
  }, [adjustHeight, handleScroll]);

  return { setTableRef };
}
