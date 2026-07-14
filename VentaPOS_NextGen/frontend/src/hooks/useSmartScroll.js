import { useRef, useCallback, useEffect } from 'react';

/**
 * Custom hook to implement the "Hybrid Scroll Merging Architecture".
 * It dynamically calculates the exact maxHeight required so the table seamlessly hits the ceiling,
 * and intercepts wheel events to prioritize window scrolling.
 * Fully Zoom-Tolerant (handles document.body.style.zoom scaling).
 */
export default function useSmartScroll() {
  const tableContainerRef = useRef(null);

  useEffect(() => {
    const adjustHeight = () => {
      if (!tableContainerRef.current) return;
      
      const currentZoom = parseFloat(document.body.style.zoom) || 1.0;
      
      // Calculate total sticky height above the table in CSS pixels
      let stickyHeightCSS = 64; 
      
      const stickyToolbar = document.querySelector('.sticky-toolbar');
      if (stickyToolbar && document.body.contains(stickyToolbar)) {
        const rect = stickyToolbar.getBoundingClientRect();
        // getBoundingClientRect returns scaled pixels, we must un-scale them for CSS
        stickyHeightCSS = 64 + (rect.height / currentZoom);
      }

      // (100vh / zoom) ensures the vh unit covers the entire screen despite CSS zooming.
      // We subtract an additional 40px to account for the bottom margin of the card and padding of the page-body,
      // so the table container doesn't slide underneath the sticky toolbar when scrolled to absolute bottom.
      tableContainerRef.current.style.maxHeight = `calc((100vh / ${currentZoom}) - ${stickyHeightCSS + 40}px)`;
    };

    // Run initially
    adjustHeight();

    // Re-run on resize (or zoom)
    window.addEventListener('resize', adjustHeight);
    
    // Re-run if DOM mutations happen (e.g. filters wrapping changes)
    const observer = new MutationObserver(adjustHeight);
    observer.observe(document.body, { childList: true, subtree: true, attributes: true });
    
    return () => {
      window.removeEventListener('resize', adjustHeight);
      observer.disconnect();
    };
  }, []);

  const handleWheel = useCallback((e) => {
    if (!tableContainerRef.current) return;

    if (e.deltaY > 0) {
      const root = document.getElementById('root');
      const isRootScrollable = root && root.scrollHeight > root.clientHeight;
      const scrollContainer = isRootScrollable ? root : (document.scrollingElement || document.documentElement);

      const distanceToBottom = scrollContainer.scrollHeight - scrollContainer.clientHeight - scrollContainer.scrollTop;
      const isAtBottom = distanceToBottom < 15;

      if (!isAtBottom) {
        e.preventDefault();
        scrollContainer.scrollBy({ top: e.deltaY, behavior: 'auto' });
      }
    }
  }, []);

  const setTableRef = useCallback((node) => {
    if (tableContainerRef.current) {
      tableContainerRef.current.removeEventListener('wheel', handleWheel);
    }
    tableContainerRef.current = node;
    if (node) {
      node.addEventListener('wheel', handleWheel, { passive: false });
    }
  }, [handleWheel]);

  return { setTableRef };
}
