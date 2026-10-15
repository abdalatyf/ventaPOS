# LicenseManager - API & Security

This document outlines the API definitions (URL endpoints), data exchange flows, middleware, security configurations, and cryptographic functions utilized in the LicenseManager application.

## 1. API Definitions (URL Endpoints)
The LicenseManager is a server-side rendered Django application. It does not currently expose a RESTful JSON API. Instead, it exposes standard HTTP endpoints that return HTML views or process form submissions.

### Exposed Endpoints
*   `GET /` & `POST /` (`login_view`): Handles user login. Accepts a `password` in the POST body.
*   `GET /dashboard/` (`dashboard_view`): Returns the main statistics dashboard.
*   `GET /clients/` (`clients_list_view`): Returns the list of clients. Accepts an optional `q` query parameter for searching.
*   `POST /clients/delete/<int:client_id>/` (`delete_client_view`): Deletes a specific client.
*   `GET /clients/add/` & `POST /clients/add/` (`add_client_view`): Renders the add client form and processes the creation.
*   `GET /licenses/` (`licenses_list_view`): Returns the list of licenses. Accepts `q` (search) and `status` (`active` or `inactive`) query parameters.
*   `POST /licenses/delete/<int:license_id>/` (`delete_license_view`): Deletes a specific license.
*   `GET /licenses/add/` & `POST /licenses/add/` (`add_license_view`): Renders the add license form and processes the creation.
*   `GET /licenses/success/<int:license_id>/` (`license_success_view`): Displays the generated license code and a formatted WhatsApp message.
*   `GET /logout/` (`logout_view`): Logs the user out.
*   `GET /admin/`: Default Django admin interface (fallback/unused).

## 2. Authentication Flow
The application implements a custom, single-password session-based authentication system rather than using Django's default `User` model.

### Process:
1.  **Login Attempt**: The user submits a POST request to `/` containing a `password` field.
2.  **Validation**: The view compares `request.POST.get('password')` against `settings.MASTER_PASSWORD` (which is hardcoded to `"123"` in `settings.py`).
3.  **Session Creation**: If matched, the application sets a session variable: `request.session['is_logged_in'] = True`.
4.  **Authorization (Middleware/Decorators)**: There are no decorators like `@login_required` used. Instead, a manual check is performed at the top of every protected view:
    ```python
    def is_authenticated(request):
        return request.session.get('is_logged_in', False)
    
    # Inside views:
    if not is_authenticated(request):
        return redirect('login')
    ```
5.  **Logout**: The `/logout/` endpoint sets `request.session['is_logged_in'] = False`.

## 3. Middleware & Security Configurations
The application relies on standard Django security middleware:
*   **`SecurityMiddleware`**: General security enhancements.
*   **`SessionMiddleware`**: Manages the session data required for the custom authentication flow.
*   **`CsrfViewMiddleware`**: Enforces CSRF token presence on all POST requests (critical for form submissions like adding/deleting clients and licenses).
*   **`XFrameOptionsMiddleware`**: Prevents clickjacking by controlling whether the site can be rendered in a `<frame>`, `<iframe>`, etc.

## 4. Cryptographic Functions
Security relies heavily on cryptography to prevent license forgery.

### Algorithms Used:
*   **Hash Algorithm**: `SHA256` (via Python's built-in `hashlib`). Used exclusively to hash the `machine_id` string into a fixed-length byte array, from which the first 4 bytes are extracted to create a 32-bit integer signature of the machine.
*   **Message Authentication Code**: `HMAC-SHA256` (via Python's built-in `hmac`). Used to sign the license payload (Machine Int, Product Int, Date Int) to ensure it cannot be tampered with.
*   **Data Masking**: Bitwise `XOR` is used to mask the license data block using bits derived from the HMAC signature.

### Keys Used:
1.  **Django Application Secret**: 
    *   Stored in `settings.SECRET_KEY` (`django-insecure-pmwa6)4dmwtcdykry@qts9ebq@huw1wzu-^#9o!wei809!b!gk`).
    *   Used by Django for session signing and cryptographic signing. Currently insecure (development mode).
2.  **License Generator Secret**:
    *   Hardcoded in `licenses/utils/crypto.py`.
    *   Value: `b"JqxQQAKo0BbI76tknaKlhd0rC9hDcam_bqJywXmaXHqAKkVPRZhzgRjHX-zME11enx2oB8o_ivJCn2pXBX-Pow"`.
    *   Used specifically for HMAC-SHA256 signatures of the offline license codes.

## 5. Flow of Data Exchange
*   **Input**: User enters data into HTML forms. The data is URL-encoded and sent via POST requests (protected by `{% csrf_token %}`).
*   **Processing**: Django views receive `request.POST`, pass it to Django Forms (`ClientForm`, `LicenseForm`) for validation, and then invoke model `save()` methods (which in turn invoke the `LicenseGenerator`).
*   **Output**: HTML templates are rendered with context dictionaries and returned to the client. Queries are executed via the Django ORM.
