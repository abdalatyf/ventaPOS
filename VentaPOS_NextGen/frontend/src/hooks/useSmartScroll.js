import { useRef, useCallback, useEffect } from 'react';

/**
 * Custom hook to implement the "Hybrid Scroll Merging Architecture".
 * It uses native CSS overflow-y toggling based on absolute distance to bottom.
 * By perfectly calculating the table's maxHeight, the window naturally stops scrolling
 * at the exact millisecond the toolbar touches the navbar, at which point the table's
 * scrollbar appears (without layout shifts thanks to scrollbar-gutter).
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
    };

    const handleScroll = () => {
      if (!tableContainerRef.current) return;
      
      // We use absolute distance to bottom to toggle the scrollbar.
      // This is mathematically flawless regardless of zoom or screen size.
      const scrollHeight = document.documentElement.scrollHeight;
      const clientHeight = window.innerHeight;
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      
      // If we are at the absolute bottom of the page (within 5 pixels for rounding)
      const distanceToBottom = scrollHeight - clientHeight - scrollTop;
      
      if (distanceToBottom <= 5) {
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
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    // Re-run if DOM mutations happen
    const observer = new MutationObserver(() => {
      adjustHeight();
      handleScroll();
    });
    observer.observe(document.body, { childList: true, subtree: true, attributes: true });
    
    return () => {
      window.removeEventListener('resize', adjustHeight);
      window.removeEventListener('scroll', handleScroll);
      observer.disconnect();
    };
  }, []);

  const setTableRef = useCallback((node) => {
    tableContainerRef.current = node;
  }, []);

  return { setTableRef };
}
