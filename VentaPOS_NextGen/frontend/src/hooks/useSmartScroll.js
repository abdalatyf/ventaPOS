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
    
    const navbar = document.querySelector('header.navbar');
    const navbarBottom = navbar ? navbar.getBoundingClientRect().bottom : 56;
    const card = tableContainerRef.current.closest('.card');
    const toolbar = card?.querySelector('.sticky-toolbar') || document.querySelector('.sticky-toolbar');
    const triggerEl = toolbar || tableContainerRef.current;
    const triggerTop = triggerEl.getBoundingClientRect().top;

    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = document.documentElement.clientHeight || window.innerHeight;
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const currentZoom = parseFloat(document.body.style.zoom) || 1.0;
    const tolerance = Math.max(6, 10 / currentZoom);
    const distanceToBottom = scrollHeight - clientHeight - scrollTop;

    // Activate Scroll #2 (internal table scroll) when the table's sticky-toolbar touches the Navbar OR window hits bottom
    if (triggerTop <= navbarBottom + 4 || distanceToBottom <= tolerance) {
      if (tableContainerRef.current.style.overflowY !== 'auto') {
        tableContainerRef.current.style.overflowY = 'auto';
      }
    } else {
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

    const navbar = document.querySelector('header.navbar');
    const navbarHeight = navbar ? navbar.offsetHeight : 56;
    const card = tableContainerRef.current.closest('.card');
    const toolbar = card?.querySelector('.sticky-toolbar') || document.querySelector('.sticky-toolbar');
    const toolbarHeight = toolbar ? toolbar.offsetHeight : 0;
    
    // 8px pb-2 + 2px card borders = 10px exact bottom space
    const offset = navbarHeight + toolbarHeight + 10;
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

      const card = node.closest('.card');
      const toolbar = card?.querySelector('.sticky-toolbar') || document.querySelector('.sticky-toolbar');
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
