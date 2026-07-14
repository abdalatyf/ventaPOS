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

When a table has too many columns, it requires horizontal scrolling (`overflow-x: auto`). However, placing `overflow-x: auto` on a container breaks the Native Window Sticky behavior for the table headers (`position: sticky` relative to the window). Furthermore, allowing a wide table to grow infinitely tall pushes its horizontal scrollbar to the very bottom of the page, rendering it invisible to the user until they scroll all the way down.

To solve this UX Paradox, use the **Hybrid Scroll Merging Architecture**:

### 1. Visual Merge (CSS)
Restrict the table container's height to the exact remaining viewport space and hide its vertical scrollbar. This ensures the horizontal scrollbar is *always* visible at the bottom of the screen, while visually tricking the user into seeing only one continuous vertical scrollbar (the window's).

```jsx
<div 
  ref={setTableRef}
  className="table-responsive hide-vertical-scroll" 
  style={{ maxHeight: 'calc(100vh - 110px)', overflowY: 'auto', overflowX: 'auto' }}
>
  <style>
    {`
      /* Hide vertical scrollbar but keep horizontal */
      .hide-vertical-scroll::-webkit-scrollbar { width: 0px; height: 8px; }
      .hide-vertical-scroll::-webkit-scrollbar-track { background: #f1f1f1; }
      .hide-vertical-scroll::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 4px; }
      .hide-vertical-scroll { scrollbar-width: thin; }
    `}
  </style>
  <table className="table text-nowrap">
    {/* Table Content */}
  </table>
</div>
```

### 2. Smart Scroll Interceptor (JS)
Because the table container now has a restricted height, it intercepts vertical scrolling (Scroll Bubbling). If the user hovers over the table and scrolls down, the table will scroll internally *before* the window scrolls, leaving the page filters stuck on the screen.
To enforce "Window-First" scroll priority, attach this `useCallback` to the table wrapper to intercept downward scrolls until the window has scrolled past the sticky threshold.

```jsx
const handleWheel = useCallback((e) => {
  if (!tableContainerRef.current) return;
  
  if (e.deltaY > 0) { // Scrolling DOWN
    const rect = tableContainerRef.current.getBoundingClientRect();
    // 111px is the threshold (Navbar 64px + Toolbar 46px + 1px buffer)
    if (rect.top > 111) {
      e.preventDefault(); // Stop table from scrolling
      // Force window (or root container) to scroll instead
      const root = document.getElementById('root');
      if (root && root.scrollHeight > root.clientHeight) {
        root.scrollBy({ top: e.deltaY, behavior: 'auto' });
      } else {
        window.scrollBy({ top: e.deltaY, behavior: 'auto' });
      }
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
```


### 3. Solving the Zoom & Dynamic Wrapping Paradox (JS)
A common pitfall with maxHeight: calc(100vh - Xpx) is that it assumes X is constant.
However, if the user zooms the browser (or uses an internal document.body.style.zoom), or if the filters wrap to a new line on smaller screens, the height of the sticky elements above the table will change.
Additionally, zoom scaling introduces fractional pixels which breaks exact scrollTop === scrollHeight - clientHeight calculations.

**The Solution:**
1. **Dynamic Max Height**: Use ResizeObserver to measure the exact height of the Navbar + sticky-toolbar dynamically, and inject 	able.style.maxHeight directly.
2. **Zoom-Tolerant Bottom Detection**: Use a 15px buffer to absorb any sub-pixel fractional rounding errors introduced by zooming.


### 4. The 40px Overlap Paradox
Even with dynamic zoom handling, you might notice that when scrolling to the absolute bottom of the page, the table header disappears under the sticky toolbar.
**Why?** Because the scrollHeight of the page includes bottom margins/paddings (e.g. mb-3 on the card or p-3 on the page-body). This extra height allows the page to scroll *further up* than the exact height of the table container, pushing the top of the container (and its sticky header) UNDERneath the .sticky-toolbar.
**The Solution:** Subtract these margins (e.g. 40px) from the maxHeight calculation. This makes the container slightly shorter to absorb the margin scroll gap, preventing it from ever overlapping the sticky elements above it.
