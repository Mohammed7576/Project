import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Sandbox from './pages/Sandbox';
import PlaceholderPage from './pages/PlaceholderPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="sandbox" element={<Sandbox />} />
          <Route path="targets" element={<PlaceholderPage title="Target Management" />} />
          <Route path="waf" element={<PlaceholderPage title="WAF Analysis" />} />
          <Route path="settings" element={<PlaceholderPage title="System Settings" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

