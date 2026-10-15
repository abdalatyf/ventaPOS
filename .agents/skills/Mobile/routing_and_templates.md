# Mobile App Routing & UI Architecture

## Navigation Flow & Routing Strategy
The VentaPOS Mobile application does not use named routes (`/path`). Instead, it relies strictly on imperative Flutter navigation using `Navigator.push` and `Navigator.pushReplacement` with `MaterialPageRoute`.

### Route Map
1.  **Entry Point (Implicit `/`): `SplashScreen`**
    *   **Component:** `SplashScreen` (`main.dart`)
    *   **Action:** Displays a loading indicator while `_checkIdentity()` polls the local database.
    *   **Transitions:**
        *   If `salesperson_id == 0` -> `Navigator.pushReplacement` -> **`SetupScreen`**
        *   If `salesperson_id > 0` -> `Navigator.pushReplacement` -> **`DashboardScreen`**

2.  **Setup Node: `SetupScreen`**
    *   **Component:** `SetupScreen` (`screens/setup_screen.dart`)
    *   **Transitions:**
        *   Upon successful processing of the setup JSON file -> `Navigator.pushReplacement` -> **`DashboardScreen`**

3.  **Hub Node: `DashboardScreen`**
    *   **Component:** `DashboardScreen` (`screens/dashboard_screen.dart`)
    *   **Transitions:**
        *   "إنشاء فاتورة جديدة" button -> `Navigator.push` -> **`PosScreen`**
            *   *Callback:* Awaits `bool? saved`. If `true`, refreshes the dashboard counter.
        *   "أرشيف الفواتير والتصدير" button -> `Navigator.push` -> **`ReceiptsArchiveScreen`**
            *   *Callback:* Awaits pop. Automatically refreshes dashboard upon return.

4.  **Creation/Edit Node: `PosScreen`**
    *   **Component:** `PosScreen` (`screens/pos_screen.dart`)
    *   **Transitions:**
        *   Upon successful save -> `Navigator.pop(context, true)` (Returns to caller: Dashboard or Archive).
        *   "إضافة منتج" button -> Opens `AlertDialog` overlay (Search products).

5.  **Archive Node: `ReceiptsArchiveScreen`**
    *   **Component:** `ReceiptsArchiveScreen` (`screens/receipts_archive_screen.dart`)
    *   **Transitions:**
        *   "تعديل" (Edit) icon on a specific receipt -> `Navigator.push` -> **`PosScreen(existingReceiptJson, receiptId)`**.
            *   *Callback:* Awaits return `true` to refresh the archive list.
        *   "حذف" or "مسح الفواتير المُصدرة" -> Opens `AlertDialog` overlays for confirmation.

## UI Component Hierarchy & Layout Inheritance

### Global Layout Wrapper
All screens inherit a foundational layout configuration injected at the root level in `main.dart`:
```dart
MaterialApp(
  theme: ThemeData(primarySwatch: Colors.teal, fontFamily: 'Arial'),
  builder: (context, child) {
    // Forces Right-to-Left (RTL) globally for Arabic UI
    return Directionality(textDirection: TextDirection.rtl, child: child!);
  },
)
```

### Screen Templates
There is no generic BaseScaffold class. Each screen manually implements its own `Scaffold`:
*   **Standard Layout:** All functional screens (`DashboardScreen`, `PosScreen`, `ReceiptsArchiveScreen`, `SetupScreen`) implement:
    *   `Scaffold`
    *   `AppBar` (often containing action icons like refresh or filters)
    *   `body`: Utilizing scrolling layouts like `ListView` (in POS), `Column` with `Expanded` (in Archive), or `Padding > Column` (in Dashboard).
*   **Bottom Sheet (Persistent):** The `PosScreen` utilizes the `bottomSheet` property of the `Scaffold` to anchor the financial totals and the "Save" button permanently at the bottom of the screen above the keyboard.
*   **Cards:** Extensive use of the `Card` widget for modular visual grouping (e.g., individual cart items, metric displays, setup box).
