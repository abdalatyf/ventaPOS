import { useRef, useCallback, useEffect } from 'react';

/**
 * Custom hook to implement the "Hybrid Scroll Merging Architecture".
 * It uses native CSS overflow-y toggling based on absolute distance to bottom.
 * By perfectly calculating the table's maxHeight, the window naturally stops scrolling
 * at the exact millisecond the toolbar touches the navbar, at which point the table's
 * scrollbar appears (without layout shifts thanks to scrollbar-gutter).
 *
 * Uses lightweight ResizeObserver on the toolbar and table container (never a body-wide MutationObserver)
 * and dynamically calculates --header-row-1-height for pixel-perfect 2-row sticky headers.
 */
export default function useSmartScroll() {
  const tableContainerRef = useRef(null);

  useEffect(() => {
    const adjustHeight = () => {
      if (!tableContainerRef.current) return;
      
      const currentZoom = parseFloat(document.body.style.zoom) || 1.0;
      
      // Navbar is 56px.
      // We dynamically measure the height of the sticky-toolbar.
      const toolbar = document.querySelector('.sticky-toolbar');
      const toolbarHeight = toolbar ? toolbar.offsetHeight : 0;
      
      // The card has a bottom margin (mb-3) of 16px.
      // Total offset ensures the table's absolute bottom touches the screen bottom exactly when the toolbar touches the navbar.
      const offset = 56 + toolbarHeight + 16;
      
      tableContainerRef.current.style.maxHeight = `calc((100vh / ${currentZoom}) - ${offset}px)`;

      // Measure row 1 of multi-level headers dynamically
      const headerRow1 = tableContainerRef.current.querySelector('thead > tr:first-child');
      if (headerRow1) {
        tableContainerRef.current.style.setProperty('--header-row-1-height', `${headerRow1.offsetHeight}px`);
      }
    };

    const handleScroll = () => {
      if (!tableContainerRef.current) return;
      
      // We use absolute distance to bottom to toggle the scrollbar.
      const scrollHeight = document.documentElement.scrollHeight;
      const clientHeight = window.innerHeight;
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      
      const currentZoom = parseFloat(document.body.style.zoom) || 1.0;
      const tolerance = Math.max(8, 12 / currentZoom);
      const distanceToBottom = scrollHeight - clientHeight - scrollTop;
      
      if (distanceToBottom <= tolerance) {
        // Window hit the bottom (Toolbar is touching Navbar). Enable table scrolling!
        if (tableContainerRef.current.style.overflowY !== 'auto') {
          tableContainerRef.current.style.overflowY = 'auto';
        }
      } else {
        // Window is not at bottom. Disable table scrolling so window natively scrolls!
        if (tableContainerRef.current.style.overflowY !== 'hidden') {
          tableContainerRef.current.style.overflowY = 'hidden';
        }
      }
    };

    // Run initially
    adjustHeight();
    handleScroll();

    window.addEventListener('resize', adjustHeight);
    window.addEventListener('app-zoom-changed', adjustHeight);
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    // High-performance ResizeObserver observing only relevant elements
    let resizeObserver = null;
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => {
        adjustHeight();
      });
      const toolbar = document.querySelector('.sticky-toolbar');
      if (toolbar) resizeObserver.observe(toolbar);
      if (tableContainerRef.current) resizeObserver.observe(tableContainerRef.current);
    }
    
    return () => {
      window.removeEventListener('resize', adjustHeight);
      window.removeEventListener('app-zoom-changed', adjustHeight);
      window.removeEventListener('scroll', handleScroll);
      if (resizeObserver) resizeObserver.disconnect();
    };
  }, []);

  const setTableRef = useCallback((node) => {
    tableContainerRef.current = node;
  }, []);

  return { setTableRef };
}
