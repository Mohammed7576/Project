import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { AttackProvider } from './context/AttackContext.tsx';

const rootElement = document.getElementById('root');
if (rootElement) {
  console.log("[MAIN] Rendering root with AttackProvider...");
  createRoot(rootElement).render(
    <StrictMode>
      <AttackProvider>
        <App />
      </AttackProvider>
    </StrictMode>,
  );
}
