import React from 'react';
import { NavLink } from 'react-router-dom';
import { Terminal, Activity, Database, ShieldAlert, Settings, Cpu } from 'lucide-react';

const navItems = [
  { name: 'Dashboard', path: '/', icon: Activity },
  { name: 'Sandbox', path: '/sandbox', icon: Terminal },
  { name: 'Targets', path: '/targets', icon: Database },
  { name: 'WAF Analysis', path: '/waf', icon: ShieldAlert },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-64 h-screen bg-[#0a0a0a] border-r border-[#10b981]/20 flex flex-col">
      {/* Logo Area */}
      <div className="h-16 flex items-center px-6 border-b border-[#10b981]/20">
        <Cpu className="w-6 h-6 text-[#10b981] mr-3" />
        <span className="text-[#10b981] font-bold tracking-widest uppercase text-sm">
          Prometheus
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 px-3 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 rounded-md transition-all duration-200 group ${
                  isActive
                    ? 'bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/30 shadow-[0_0_10px_rgba(16,185,129,0.1)]'
                    : 'text-slate-400 hover:text-[#10b981] hover:bg-[#10b981]/5'
                }`
              }
            >
              <Icon className="w-5 h-5 mr-3" />
              <span className="font-mono text-sm">{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* System Status */}
      <div className="p-4 border-t border-[#10b981]/20">
        <div className="flex items-center justify-between text-xs font-mono mb-2">
          <span className="text-slate-400">System Status</span>
          <span className="text-[#10b981] animate-pulse">ONLINE</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1.5">
          <div className="bg-[#10b981] h-1.5 rounded-full w-full"></div>
        </div>
      </div>
    </aside>
  );
}
