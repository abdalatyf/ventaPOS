# UI & Performance Optimization

## Problem
1. **UI Jitter / "Dancing Tables"**: Using `react-virtuoso` for virtualized tables caused severe jittering when scrolling because standard HTML table cells (`<td>`) varied in size dynamically depending on their content (e.g., text wrapping), confusing the virtualizer's height calculations.
2. **Sticky Header Failure & Zoom Collapse**: CSS Flexbox columns containing tables blew out the viewport on zoom-out because of missing `min-height: 0` constraints, which broke `position: sticky` and caused gray gaps.
3. **Checkbox Lag**: Toggling checkboxes in large tables caused the entire component tree to re-render, creating a severe 1-3 second input lag.
4. **False "Select All"**: Selecting all checkboxes only selected the visible page, not the entire matching search subset in the backend.

## Solution
1. **Native Scrolling**: Removed `react-virtuoso` entirely. Resorted to native `overflow-auto` with infinite scroll triggers (`onScroll`).
2. **Holy Grail Flexbox**: Applied `min-height: 0` recursively from the `AppShell` down to the innermost `.table-responsive` card, strictly preventing any flex item from forcing native body scrolling.
3. **React.memo**: Extracted rows into `ReceiptRow` wrapped with `React.memo` using strict `prevProps.isSelected === nextProps.isSelected` comparator, reducing render times from O(N) to O(1) during selection.
4. **True Bulk Selection**: Patched Django REST Framework's `PageNumberPagination` to inject an array of all matched `id`s (`all_ids`) alongside the results. The UI uses this array for "Select All".
5. **Pagination Batching**: Raised `page_size` to 200 items to give the user a larger initial data batch.
