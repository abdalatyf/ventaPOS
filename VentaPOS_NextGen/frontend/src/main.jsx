import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@tabler/core/dist/css/tabler.rtl.min.css'
import '@tabler/core/dist/js/tabler.min.js'
import './index.css'
import setupFileLogger from './utils/fileLogger'
import App from './App.jsx'

setupFileLogger();

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
