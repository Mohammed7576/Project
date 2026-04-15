import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import PlaceholderPage from './pages/PlaceholderPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="sandbox" element={<PlaceholderPage title="Sandbox Environment" />} />
        <Route path="targets" element={<PlaceholderPage title="Target Management" />} />
        <Route path="waf" element={<PlaceholderPage title="WAF Analysis" />} />
        <Route path="settings" element={<PlaceholderPage title="System Settings" />} />
      </Route>
    </Routes>
  );
}

