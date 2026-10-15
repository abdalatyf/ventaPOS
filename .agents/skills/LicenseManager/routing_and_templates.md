# LicenseManager - Routing & UI Architecture

This document maps every URL pattern to its corresponding view and template, detailing the navigation flow and the frontend layout inheritance hierarchy.

## 1. Layout Inheritance Hierarchy (Templates)
The frontend architecture utilizes Django's template engine.

### Root Template: `base.html`
*   **Purpose**: Acts as the master layout for the entire application.
*   **Structure**: 
    *   Includes HTML5 boilerplate with `dir="rtl"` for Arabic layout.
    *   Loads Bootstrap 5 via CDN.
    *   Loads Google Fonts (`Cairo`).
    *   Defines inline CSS styles for layout, cards, and sidebar.
*   **Conditional Sidebar**: The sidebar navigation menu is wrapped in a `{% if request.session.is_logged_in %}` block, meaning it is completely hidden on the login page.
*   **Dynamic Active States**: The sidebar uses `request.resolver_match.url_name` to dynamically highlight the currently active page.
*   **Content Block**: Provides `{% block content %}{% endblock %}` for child templates to inject their specific UI.

### Child Templates
All other functional HTML pages inherit from `base.html` using the `{% extends 'base.html' %}` tag and inject their UI into the `{% block content %}`.
*   `login.html`
*   `dashboard.html`
*   `clients_list.html`
*   `add_client.html`
*   `licenses_list.html`
*   `add_license.html`
*   `license_success.html`

## 2. Route Map & Navigation Flow

### Authentication Routes
*   **URL Pattern**: `/`
    *   **Name**: `login`
    *   **View**: `licenses.views.login_view`
    *   **Template**: `login.html`
    *   **Flow**: Renders the login form. Upon successful password verification via POST, the user is redirected to `/dashboard/`.
*   **URL Pattern**: `/logout/`
    *   **Name**: `logout`
    *   **View**: `licenses.views.logout_view`
    *   **Template**: *None* (Action endpoint)
    *   **Flow**: Clears the session (`is_logged_in = False`) and redirects to `/`.

### Dashboard Route
*   **URL Pattern**: `/dashboard/`
    *   **Name**: `dashboard`
    *   **View**: `licenses.views.dashboard_view`
    *   **Template**: `dashboard.html`
    *   **Flow**: The central hub. Displays aggregate statistics, revenue, and alerts for licenses expiring within 30 days. Provides sidebar navigation to all other screens.

### Client Management Routes
*   **URL Pattern**: `/clients/`
    *   **Name**: `clients_list`
    *   **View**: `licenses.views.clients_list_view`
    *   **Template**: `clients_list.html`
    *   **Flow**: Displays a table of all clients. Includes a search form. Includes a delete button for each client.
*   **URL Pattern**: `/clients/add/`
    *   **Name**: `add_client`
    *   **View**: `licenses.views.add_client_view`
    *   **Template**: `add_client.html`
    *   **Flow**: Renders the new client form. **Crucial Flow**: Upon successful form submission, the view automatically redirects to `/licenses/add/` to streamline the workflow of adding a client and immediately issuing them a license.
*   **URL Pattern**: `/clients/delete/<int:client_id>/`
    *   **Name**: `delete_client`
    *   **View**: `licenses.views.delete_client_view`
    *   **Template**: *None* (Action endpoint)
    *   **Flow**: Accepts POST requests to delete a client, then redirects back to `/clients/`.

### License Management Routes
*   **URL Pattern**: `/licenses/`
    *   **Name**: `licenses_list`
    *   **View**: `licenses.views.licenses_list_view`
    *   **Template**: `licenses_list.html`
    *   **Flow**: Displays a table of all generated licenses. Includes text search and a status dropdown filter (`active` / `inactive`). Includes delete buttons.
*   **URL Pattern**: `/licenses/add/`
    *   **Name**: `add_license`
    *   **View**: `licenses.views.add_license_view`
    *   **Template**: `add_license.html`
    *   **Flow**: Renders the new license form. Defaults the price to `2000`. Upon successful submission, redirects to `/licenses/success/<license_id>/`.
*   **URL Pattern**: `/licenses/success/<int:license_id>/`
    *   **Name**: `license_success`
    *   **View**: `licenses.views.license_success_view`
    *   **Template**: `license_success.html`
    *   **Flow**: A dedicated success screen showing the newly generated `generated_code` in large font. Contains JavaScript `copyCode()` to copy the code to the clipboard. Contains a dynamically generated URL link to open WhatsApp with a pre-filled message containing the license details for the client.
*   **URL Pattern**: `/licenses/delete/<int:license_id>/`
    *   **Name**: `delete_license`
    *   **View**: `licenses.views.delete_license_view`
    *   **Template**: *None* (Action endpoint)
    *   **Flow**: Accepts POST requests to delete a license, then redirects back to `/licenses/`.
