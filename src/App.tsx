import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Sandbox from './pages/Sandbox';
import Targets from './pages/Targets';
import WAFAnalysis from './pages/WAFAnalysis';
import PlaceholderPage from './pages/PlaceholderPage';
import { AttackProvider } from './context/AttackContext';

export default function App() {
  return (
    <AttackProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="sandbox" element={<Sandbox />} />
            <Route path="targets" element={<Targets />} />
            <Route path="waf" element={<WAFAnalysis />} />
            <Route path="settings" element={<PlaceholderPage title="إعدادات النظام" />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AttackProvider>
  );
}

