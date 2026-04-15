import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Sandbox from './pages/Sandbox';
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
            <Route path="targets" element={<PlaceholderPage title="إدارة الأهداف" />} />
            <Route path="waf" element={<PlaceholderPage title="تحليل WAF" />} />
            <Route path="settings" element={<PlaceholderPage title="إعدادات النظام" />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AttackProvider>
  );
}

