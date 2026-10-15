const fs = require('fs');

let content = fs.readFileSync('TABLE_UX_GUIDELINES.md', 'utf8');

// We append to the Advanced section
const addition = \

### 3. Solving the Zoom & Dynamic Wrapping Paradox (JS)
A common pitfall with \maxHeight: calc(100vh - Xpx)\ is that it assumes \X\ is constant. 
However, if the user zooms the browser (or uses an internal \document.body.style.zoom\), or if the filters wrap to a new line on smaller screens, the height of the sticky elements above the table will change. This leads to visual gaps or overlap.
Additionally, zoom scaling introduces fractional pixels which breaks exact \scrollTop === scrollHeight - clientHeight\ calculations.

**The Solution:**
1. **Dynamic Max Height**: Use a custom React hook (\useSmartScroll\) with a \ResizeObserver\ to measure the exact height of the \Navbar\ + \sticky-toolbar\ dynamically, and inject \	able.style.maxHeight\ directly.
2. **Zoom-Tolerant Bottom Detection**: When checking if the page has hit the bottom to release the scroll interceptor, use a generous buffer (e.g. \15px\) to absorb any sub-pixel fractional rounding errors introduced by zooming.

\\\javascript
// Simplified logic for useSmartScroll.js
export default function useSmartScroll() {
  const tableContainerRef = useRef(null);

  useEffect(() => {
    const adjustHeight = () => {
      if (!tableContainerRef.current) return;
      let stickyHeight = 64; // Default Navbar height
      const stickyToolbar = document.querySelector('.sticky-toolbar');
      if (stickyToolbar && document.body.contains(stickyToolbar)) {
        stickyHeight = 64 + stickyToolbar.getBoundingClientRect().height;
      }
      tableContainerRef.current.style.maxHeight = \\\calc(100vh - \\\px)\\\;
    };
    adjustHeight();
    window.addEventListener('resize', adjustHeight);
    const observer = new MutationObserver(adjustHeight);
    observer.observe(document.body, { childList: true, subtree: true, attributes: true });
    return () => { window.removeEventListener('resize', adjustHeight); observer.disconnect(); };
  }, []);

  const handleWheel = useCallback((e) => {
    if (!tableContainerRef.current) return;
    if (e.deltaY > 0) {
      const root = document.getElementById('root');
      const scrollContainer = (root && root.scrollHeight > root.clientHeight) ? root : (document.scrollingElement || document.documentElement);
      
      // 15px buffer handles fractional zoom pixels
      const distanceToBottom = scrollContainer.scrollHeight - scrollContainer.clientHeight - scrollContainer.scrollTop;
      const isAtBottom = distanceToBottom < 15;
      
      if (!isAtBottom) {
        e.preventDefault();
        scrollContainer.scrollBy({ top: e.deltaY, behavior: 'auto' });
      }
    }
  }, []);
  
  // ... setTableRef logic ...
}
\\\
\;

if (!content.includes('Solving the Zoom & Dynamic Wrapping Paradox')) {
    content += addition;
    fs.writeFileSync('TABLE_UX_GUIDELINES.md', content, 'utf8');
}
