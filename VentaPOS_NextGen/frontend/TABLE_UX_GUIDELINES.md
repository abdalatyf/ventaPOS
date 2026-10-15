# Unified Table Scroll Architecture (Native Sticky Layout)

This document defines the standard architecture for all data tables in the VentaPOS NextGen frontend. We use a **Native Window Scroll** approach instead of nested scroll containers. This ensures a consistent, mobile-friendly, and accessible scrolling experience across the entire application.

## Core Principles

1. **Single Scrollbar**: The entire page scrolls natively using the browser's window scrollbar. There should be NO internal scrolling divs (`overflow-auto` or `overflow-hidden` on wrappers).
2. **Sticky Hierarchy**: As the user scrolls down:
   - The **Navbar** remains fixed at the top of the viewport (`top: 0`).
   - The **Toolbar** (the row containing filters, search inputs, or action buttons immediately above the table) sticks directly underneath the Navbar.
   - The **Table Headers (`thead th`)** stick directly underneath the Toolbar.

## CSS Architecture

The global offsets must be defined in `src/index.css` via CSS variables to allow for easy global adjustments.

```css
:root {
  --navbar-height: 64px; /* Tabler Default */
  --toolbar-height: 46px; /* Card Header Default */
}

/* 1. Page Wrapper */
/* Must NOT have overflow: hidden or fixed heights that block native scroll */
.native-page-scroll {
  height: auto !important;
  min-height: 100vh;
  overflow: visible !important;
}

/* 2. Sticky Toolbar (The row above the table) */
.sticky-toolbar {
  position: sticky;
  top: var(--navbar-height);
  z-index: 1020;
  background-color: #f8f9fa; /* Ensure it's not transparent */
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* 3. Sticky Table Header */
.table-sticky-header th {
  position: sticky !important;
  top: calc(var(--navbar-height) + var(--toolbar-height)) !important;
  z-index: 1010;
  background-color: #f8f9fa !important;
  box-shadow: inset 0 -1px 0 var(--tblr-border-color);
}
```

## Critical CSS Overrides for Tabler UI

To ensure native window scrolling works flawlessly, the following global rules MUST be enforced in `index.css`:
- `html, body` must have `overflow: auto` (not `hidden`).
- `.page` must have `min-height: 100vh` (not `height`). If `height: 100vh` is used, the sticky Navbar will disappear when the page scrolls past the initial 100vh.
- The global `<Navbar />` component must explicitly have the `sticky-top` Bootstrap class.
- The `.table-responsive` class MUST NOT be used as a wrapper around `.table-sticky-header`, because its default `overflow-x: auto` breaks window-level sticky positioning.

## Implementation Steps for React Components

When refactoring any page to use this architecture, follow these exact steps:

### 1. Remove Layout Constraints
Strip `flex-grow-1`, `overflow-auto`, `overflow-hidden`, and `h-100` from the outermost wrappers (e.g., the main `div`, the `.card` wrapping the table, and the `.table-responsive` div). The table should expand naturally to its full height in the DOM. Add the `.native-page-scroll` class if necessary.

### 2. Apply Sticky Classes
- Identify the row immediately above the table (e.g., `<div className="card-header">`). Add `className="sticky-toolbar"`.
- On the table itself, add `className="table table-sticky-header"`.

### 3. Refactor Infinite Scroll (Intersection Observer)
Since the internal `.table-responsive` div no longer scrolls, internal `onScroll` handlers attached to it will fail. Replace them with an `IntersectionObserver` attached to the last row of the table. This is much more performant and robust than tracking global window scroll events.

**Example Infinite Scroll Implementation:**

```jsx
import React, { useRef, useCallback } from 'react';

export default function MyTableComponent() {
  const [data, setData] = useState([]);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMoreUrl, setHasMoreUrl] = useState(null);

  const observer = useRef();
  
  const lastRowElementRef = useCallback(node => {
    if (loadingMore) return;
    if (observer.current) observer.current.disconnect();
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMoreUrl) {
        // Trigger your load more function here
        loadMoreData();
      }
    });
    
    if (node) observer.current.observe(node);
  }, [loadingMore, hasMoreUrl]);

  return (
    <div className="native-page-scroll">
      
      {/* Sticky Toolbar */}
      <div className="card-header sticky-toolbar">
        <h3>Filters & Actions</h3>
      </div>
      
      {/* Table */}
      <div className="table-responsive">
        <table className="table table-sticky-header">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => {
              if (data.length === index + 1) {
                // Attach observer to the very last row
                return (
                  <tr ref={lastRowElementRef} key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.name}</td>
                  </tr>
                );
              }
              return (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.name}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

## Advanced: Hybrid Scroll Architecture (For Wide Tables)

When a table has too many columns, it requires horizontal scrolling (`overflow-x: auto`). However, placing `overflow-x: auto` on a container creates a nested scroll context, which breaks the Native Window Sticky behavior for the table headers (`position: sticky` relative to the window). Furthermore, allowing a wide table to grow infinitely tall pushes its horizontal scrollbar to the very bottom of the page, rendering it invisible to the user until they scroll all the way down.

To solve this UX Paradox without sacrificing native scroll performance, use the **Native CSS Toggling Architecture**:

### 1. Visual Setup (CSS)
Restrict the table container's height to the exact remaining viewport space. Add `scrollbarGutter: 'stable'` to permanently reserve space for the vertical scrollbar, preventing jarring layout shifts when the scrollbar appears. Use the `.hybrid-scroll-container` class so the global `index.css` knows to force the internal sticky headers to `top: 0`.

```jsx
<div 
  ref={setTableRef}
  className="table-responsive hybrid-scroll-container rounded" 
  style={{ overflowY: 'auto', overflowX: 'auto', scrollbarGutter: 'stable' }}
>
  <table className="table table-sticky-header text-nowrap">
    {/* Table Content */}
  </table>
</div>
```

### 2. Smart Scroll CSS Toggler (JS)
Instead of intercepting mouse wheel events via JavaScript (which kills native scroll smoothing and trackpad acceleration), we dynamically toggle the table's CSS `overflow-y` property based on the window's exact scroll position.

By carefully calculating the `maxHeight` of the table to equal exactly `100vh - [Total Sticky Heights] - [Bottom Margins]`, we guarantee that the absolute bottom of the window is reached at the exact millisecond the `.sticky-toolbar` touches the Navbar. When the window hits the bottom, we switch the table to `overflowY: 'auto'`.

```jsx
import { useRef, useCallback, useEffect } from 'react';

export default function useSmartScroll() {
  const tableContainerRef = useRef(null);

  useEffect(() => {
    const adjustHeight = () => {
      if (!tableContainerRef.current) return;
      
      const currentZoom = parseFloat(document.body.style.zoom) || 1.0;
      
      // Navbar is 56px, Toolbar is 56px. Total sticky elements = 112px.
      // The card has a bottom margin (mb-3) of 16px.
      // Total offset = 128px.
      // Restricting the table to exactly 100vh - 128px guarantees that the absolute
      // bottom of the window is reached EXACTLY when the Toolbar touches the Navbar.
      tableContainerRef.current.style.maxHeight = `calc((100vh / ${currentZoom}) - 128px)`;
    };

    const handleScroll = () => {
      if (!tableContainerRef.current) return;
      
      const scrollHeight = document.documentElement.scrollHeight;
      const clientHeight = window.innerHeight;
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      
      // Check absolute distance to bottom (within 5 pixels for sub-pixel rounding)
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

    adjustHeight();
    handleScroll();

    window.addEventListener('resize', adjustHeight);
    window.addEventListener('scroll', handleScroll, { passive: true });
    
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
```

### 3. Solving the Layout Shift Paradox
Because the table container flips between `overflowY: hidden` and `overflowY: auto`, the vertical scrollbar will pop in and out of existence. Normally, this causes the table width to shrink by ~15px and jump left/right dynamically.
**The Solution:** The inline style `scrollbarGutter: 'stable'` fixes this completely. It instructs the browser to always reserve a blank 15px gutter track on the right side of the element, even when `overflowY: hidden` is applied. When `auto` kicks in, the scrollbar paints itself beautifully inside the pre-reserved gutter without shifting a single pixel of the table.
