# Implementation Plan: UI & Performance Optimization

## Phase 1: Stabilization (Completed)
- `[x]` Strip out `react-virtuoso`.
- `[x]` Re-implement manual native HTML table headers with `position: sticky`.
- `[x]` Debug layout bounding boxes and implement `min-height: 0` holy grail flex cascade.
- `[x]` Implement `onScroll` intersection loading.

## Phase 2: Performance (Completed)
- `[x]` Define `ReceiptRow` component.
- `[x]` Wrap `ReceiptRow` in `React.memo` using strict comparison on `isSelected` and data reference.
- `[x]` Validate instant O(1) row toggles.

## Phase 3: True Bulk Selection (Completed)
- `[x]` Override Django's `get_paginated_response` in `views.py` to calculate `all_ids` for the active filter.
- `[x]` Inject `all_ids` into frontend state (`globalAllIds`).
- `[x]` Hook "Select All" checkbox to toggle selection based on `globalAllIds` vs loaded records.
