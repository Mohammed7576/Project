import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import './index.css';

console.log("[APP] Initializing React application...");

const rootElement = document.getElementById('root');
if (!rootElement) {
  console.error("[APP] Root element not found!");
} else {
  console.log("[APP] Root element found, rendering...");
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
    console.log("[APP] Render call completed.");
  } catch (err) {
    console.error("[APP] Render failed:", err);
    rootElement.innerHTML = `<div style="color: white; padding: 20px; background: #900;"><h1>Critical Error</h1><pre>${err}</pre></div>`;
  }
}
