import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { ShieldAlert, Globe, Activity, Code, Box } from 'lucide-react';

export default function Layout() {
  return (
    <div className="min-h-screen relative overflow-hidden cyber-grid flex flex-col">
      {/* Visual Effects */}
      <div className="scanline pointer-events-none" />
      <div className="fixed inset-0 bg-gradient-to-b from-transparent via-cyber-bg/50 to-cyber-bg pointer-events-none" />

      <div className="relative z-20 max-w-[1600px] mx-auto p-4 lg:p-8 w-full flex-1 flex flex-col space-y-6">
        
        {/* Header Section */}
        <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 pb-6 border-b border-cyber-border">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="absolute inset-0 bg-cyber-green/20 blur-xl rounded-full" />
              <div className="relative p-3 bg-cyber-surface border border-cyber-green/30 rounded-xl">
                <ShieldAlert className="w-8 h-8 text-cyber-green" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-3xl font-bold uppercase tracking-tighter">القيادة والسيطرة</h1>
                <span className="px-2 py-0.5 bg-cyber-green/10 border border-cyber-green/30 rounded text-[10px] font-bold text-cyber-green tracking-widest uppercase">وحدة الهجوم</span>
              </div>
              <p className="text-slate-500 text-sm font-medium flex items-center gap-2">
                <Globe className="w-3 h-3" /> Autonomous Genetic SQLi Evolution System
              </p>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row items-center gap-4 w-full lg:w-auto">
            {/* Tab Navigation */}
            <div className="flex bg-black/40 rounded-lg p-1 border border-cyber-border w-full sm:w-auto">
              <NavLink 
                to="/" 
                className={({isActive}) => `flex-1 sm:flex-none px-4 py-2 rounded-md text-xs font-bold transition-all flex items-center justify-center gap-2 ${isActive ? 'bg-cyber-green/20 text-cyber-green' : 'text-slate-500 hover:text-slate-300'}`}
              >
                <Activity className="w-3.5 h-3.5" /> القيادة
              </NavLink>
              <NavLink 
                to="/sandbox" 
                className={({isActive}) => `flex-1 sm:flex-none px-4 py-2 rounded-md text-xs font-bold transition-all flex items-center justify-center gap-2 ${isActive ? 'bg-cyber-blue/20 text-cyber-blue' : 'text-slate-500 hover:text-slate-300'}`}
              >
                <Code className="w-3.5 h-3.5" /> المختبر
              </NavLink>
              <NavLink 
                to="/builder" 
                className={({isActive}) => `flex-1 sm:flex-none px-4 py-2 rounded-md text-xs font-bold transition-all flex items-center justify-center gap-2 ${isActive ? 'bg-cyber-amber/20 text-cyber-amber' : 'text-slate-500 hover:text-slate-300'}`}
              >
                <Box className="w-3.5 h-3.5" /> منشئ الهجمات
              </NavLink>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col">
          <Outlet />
        </main>

        {/* Footer Info */}
        <footer className="flex justify-between items-center text-[10px] text-slate-600 font-bold uppercase tracking-[0.2em] pt-4 border-t border-cyber-border mt-auto">
          <div className="flex gap-6">
            <span>النظام: Linux x86_64</span>
            <span>النواة: 6.5.0-kali-amd64</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-cyber-green animate-pulse" />
            <span>اتصال مشفر نشط</span>
          </div>
        </footer>

      </div>
    </div>
  );
}
