# Promo App - Routing & UI Architecture

## Routing and Navigation Flow
The `Promo` application is a single-page static website (`index.html`). There is no client-side router (like React Router) or server-side URL routing. Navigation is handled strictly via native HTML anchor links.

**URL Patterns / Anchor Links:**
- `#features` -> Scrolls to the Features section (المميزات).
- `#guide` -> Scrolls to the Quick Start Guide section (دليل البدء).
- `#pricing` -> Scrolls to the Pricing section (الأسعار).
- `#security` -> Scrolls to the Security section (الأمان).

## Frontend Component Tree & Template Hierarchy
The UI is a single contiguous HTML document. There are no templating engines (like Jinja or Blade) or reusable component frameworks.

**Layout Hierarchy (Top to Bottom):**
1. **`<nav>` (Navigation Bar):** Fixed at the top, contains the logo, anchor links, and a CTA button to WhatsApp.
2. **`<section class="hero">`:** The main banner with a headline, description, primary CTA buttons, and summary statistics.
3. **`<section class="features-section" id="features">`:** A CSS Grid layout (`.features-grid`) containing multiple feature cards (`.feature-card`) highlighting application capabilities.
4. **`<section>` (Receipt Sample):** Displays an image (`imgs/invoice.png`) of a printed receipt.
5. **`<section class="steps-section">`:** Displays the four core steps to start using the software.
6. **`<section class="guide-section" id="guide">`:** A comprehensive step-by-step visual guide containing text descriptions and corresponding application screenshots.
7. **`<section class="pricing-section" id="pricing">`:** Displays pricing tiers in a grid (`.price-card`), including a highlighted popular plan.
8. **`<section class="compare-section">`:** Displays a comparison table (`.compare-table`) of features across different pricing plans.
9. **`<section class="security-section" id="security">`:** Details the security features of the VentaPOS software.
10. **`<section>` (Download):** Contains the direct download link for the setup executable (`Venta_Offline_Setup_v1.0.exe`).
11. **`<section class="cta-section">`:** A final Call-To-Action banner with a WhatsApp contact button.
12. **`<footer>`:** Contains the copyright information and logo.
