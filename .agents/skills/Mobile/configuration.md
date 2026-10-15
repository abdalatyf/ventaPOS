# Mobile App Configuration & Environment

## Boot Sequence (`main.dart`)
1.  **Application Launch:** The Dart entry point `void main() async` is called.
2.  **Binding Initialization:** `WidgetsFlutterBinding.ensureInitialized();` ensures Flutter framework engine is ready before any async operations or database calls.
3.  **Root Injection:** `runApp(const MyApp());` mounts the root widget.
4.  **Global UI Config:** `MyApp` builds the `MaterialApp` widget, specifically wrapping all child screens in a `Directionality` widget forcing `TextDirection.rtl` (Right-to-Left) to support the Arabic UI.
5.  **Splash & Boot Evaluation:** The app defaults to `SplashScreen`.
    *   `initState()` triggers asynchronous `_checkIdentity()`.
    *   Calls `DatabaseHelper().getIdentity()` to query the SQLite `config` table.
    *   Wait for 500ms (UX buffer).
    *   **Fork:**
        *   If `salesperson_id == 0`: Routes to `SetupScreen`.
        *   If `salesperson_id > 0`: Routes to `DashboardScreen`.

## Environment Variables & Secrets
**None.** 
The application requires absolutely no `.env` files or environment variables. All "environment" or configuration data (branch ID, salesperson ID) is injected manually by the user via a physical `setup.json` file selected through `file_picker` at runtime.

## External Dependencies (`pubspec.yaml`)
*   **Dart SDK:** `>=3.10.4`
*   **Flutter SDK:** Managed by `flutter` tool.
*   **Packages:**
    *   `sqflite: ^2.4.2`: The core persistence engine for all models and state.
    *   `path_provider: ^2.1.5`: Used to locate the `getDatabasesPath()` for SQLite and `getApplicationDocumentsDirectory()` for JSON exports.
    *   `path: ^1.9.1`: Utilities for constructing file paths (e.g., joining database strings).
    *   `share_plus: ^12.0.1`: Invokes the native OS share sheet (Android/iOS) to dispatch the exported JSON files.
    *   `intl: ^0.20.2`: Included for formatting (though localized string manipulation is heavily used directly in code).
    *   `file_picker: ^10.3.10`: Used purely in the `SetupScreen` to allow the user to browse their local device files for the initialization JSON.

## Build & Execution Instructions
The app relies on standard Flutter build pipelines.
*   **Run Local Development:**
    ```bash
    cd D:\Projects\VentaPOS\Mobile\sales_app_offline
    flutter pub get
    flutter run
    ```
*   **Build Production APK (Android):**
    ```bash
    flutter build apk --release
    ```
*   **Linting:** Uses `flutter_lints: ^6.0.0` configured via `analysis_options.yaml`.

*Note: The app is purely offline and does not require a running backend server to boot, test, or operate.*
