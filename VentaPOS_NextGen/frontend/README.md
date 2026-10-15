# VentaPOS NextGen - Frontend

Welcome to the **VentaPOS NextGen** frontend repository! This is a modern, offline-first Desktop POS application built with React, Vite, and Tabler UI. It is designed entirely in Arabic (RTL) with a professional and easy-to-use interface tailored for local markets.

## 1. Project Overview
The frontend is designed to be fast, responsive, and robust, providing an offline-first POS experience where the frontend runs locally on the cashier's machine alongside the backend. 
- **Core Framework**: React 19
- **Build Tool**: Vite (Lightning fast HMR and optimized builds)
- **UI Component Library**: Tabler UI (via `@tabler/core` and custom React integration)
- **Language & Direction**: Arabic (RTL) native.

## 2. Setup and Installation

### Prerequisites
Make sure you have [Node.js](https://nodejs.org/) (v18+ recommended) and npm installed on your machine.

### Installation
Clone the repository, navigate to the frontend directory, and install dependencies:

```bash
cd D:/Projects/VentaPOS/VentaPOS_NextGen/frontend
npm install
```

### Environment Variables
You can configure the application by creating a `.env` file in the root of the frontend directory.
- `VITE_API_URL`: The base URL for the backend API. 
  *(Default: `http://127.0.0.1:8000/api/v1` if not provided)*

## 3. Running the Development Server
To start the Vite development server with Hot-Module Replacement (HMR):

```bash
npm run dev
```
The server will typically start at `http://localhost:5173`.

## 4. Folder Structure Overview

- **`src/pages/`**: Contains the main page components corresponding to different routes (e.g., `POS.jsx`, `Dashboard.jsx`, `Inventory.jsx`, `Login.jsx`). It also includes subdirectories for `reports/`, `settings/`, and `tools/`.
- **`src/components/`**: Reusable and shared UI components (e.g., `AppShell.jsx`, `Navbar.jsx`, `ActivationModal.jsx`).
- **`src/hooks/`**: Custom React hooks encapsulating reusable logic (e.g., `useSmartScroll.js`, `useDefaultDate.js`).
- **`src/utils/`**: Helper scripts, parsers, and generic utilities.
- **`src/api.js`**: Axios instance configuration, base URL setup, and request/response interceptors.
- **`src/App.jsx`**: Main application component containing the React Router configuration and route protections.

## 5. Key Architectural Choices

- **Token-based Auth & Multi-Tenant Setup**: 
  Authentication uses standard Token-based Auth. Additionally, multi-tenancy is handled via custom headers. `api.js` automatically intercepts outgoing requests to inject `Authorization`, `X-Company-Code`, `X-Machine-ID`, and `X-Branch-ID` headers retrieved from `LocalStorage`.
- **LocalStorage for Branch Context**: 
  The POS operates under a strict Branch Context. After login, users must select a branch. The `branchId` is persisted in `LocalStorage` and is required to access the main application shell.
- **React Router & Protected Routes**: 
  Routing is managed by `react-router-dom`. The `ProtectedRoute` component acts as a gatekeeper, ensuring the user has both a valid auth `token` and a selected `branchId` before rendering the `AppShell`.
- **Offline-First & Interceptors**: 
  The frontend seamlessly handles subscription and local license validations. Global Axios response interceptors catch `402 Payment Required` to enforce a "Read-Only Mode" when subscriptions expire, broadcasting custom events like `subscription_expired` to trigger UI modals globally.

## 6. Building for Production

To build the application for production deployment:

```bash
npm run build
```
This command bundles the React application in production mode and outputs the optimized static files into the `dist/` directory, ready to be served or packaged with the local desktop shell. You can preview the production build locally by running `npm run preview`.
