import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout() {
  return (
    <div className="flex h-screen bg-[#050505] text-slate-300 overflow-hidden font-sans selection:bg-[#10b981]/30" dir="rtl">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden relative">
        {/* Cyberpunk Grid Background */}
        <div className="absolute inset-0 pointer-events-none" 
             style={{
               backgroundImage: 'linear-gradient(rgba(16, 185, 129, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(16, 185, 129, 0.03) 1px, transparent 1px)',
               backgroundSize: '30px 30px'
             }}>
        </div>
        
        <Header />
        
        <main className="flex-1 overflow-y-auto p-6 relative z-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
