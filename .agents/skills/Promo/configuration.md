# Promo App - Configuration & Environment

## Overview
The `Promo` application is entirely static and requires no complex configuration, build steps, or environment setup. It consists of a single `index.html` file and an `imgs` directory.

## Boot Sequence & Execution
- **Boot Sequence**: None. The browser parses the HTML document top-to-bottom.
- **Local Execution**: The application is executed by simply opening `index.html` in any modern web browser. No local development server (like Node.js, Python, or Nginx) is strictly required, although it can be served via any standard static file server.

## Environment Variables & Constants
- **Environment Variables**: None required.
- **Constants**: Defined natively within the `<style>` block in `index.html` as CSS Variables (e.g., `--gold`, `--dark`, `--text`) scoped to `:root`.

## External Dependencies
There are no package managers (e.g., `npm`, `pip`, `pub`) used in this module. The application relies on the following external CDNs:
- **Google Fonts**: Fetches the 'Cairo' font family via `<link href="https://fonts.googleapis.com/css2?family=Cairo..." rel="stylesheet">`.

## Build Process
- **Build/Compilation**: None. The HTML, CSS, and JS are written directly into the source file. There is no minification, bundling, or compilation step.
