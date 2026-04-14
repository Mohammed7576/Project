console.log("[MAIN] Script starting...");
if ((window as any).updateStatus) (window as any).updateStatus("JavaScript starting...");

import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import './index.css';

console.log("[MAIN] Imports completed.");
if ((window as any).updateStatus) (window as any).updateStatus("Imports completed, rendering...");

const rootElement = document.getElementById('root');
if (!rootElement) {
  console.error("[MAIN] Root element not found!");
} else {
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
    console.log("[MAIN] Render call completed.");
    // We don't clear updateStatus, it will be replaced by React content
  } catch (err) {
    console.error("[MAIN] Render failed:", err);
    if ((window as any).updateStatus) (window as any).updateStatus("RENDER ERROR: " + err);
    rootElement.innerHTML = `<div style="color: #ff4444; padding: 40px; background: #1a0000; font-family: monospace; min-height: 100vh; border: 4px solid #ff0000;"><h1>Render Error</h1><pre>${err}</pre></div>`;
  }
}
