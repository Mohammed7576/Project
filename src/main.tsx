console.log("[MAIN] Script starting...");
const debugInfo = document.getElementById('debug-info');
if (debugInfo) debugInfo.innerText = "JavaScript starting...";

import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import './index.css';

console.log("[MAIN] Imports completed.");
if (debugInfo) debugInfo.innerText = "Imports completed, rendering...";

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
  } catch (err) {
    console.error("[MAIN] Render failed:", err);
    rootElement.innerHTML = `<div style="color: #ff4444; padding: 40px; background: #1a0000; font-family: monospace; height: 100vh; border: 4px solid #ff0000;"><h1>Render Error</h1><pre>${err}</pre></div>`;
  }
}
