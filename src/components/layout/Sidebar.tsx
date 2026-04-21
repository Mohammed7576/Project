import React from 'react';
import { NavLink } from 'react-router-dom';
import { Terminal, Activity, Database, ShieldAlert, Settings, Cpu } from 'lucide-react';

const navItems = [
  { name: 'لوحة القيادة الموحدة', path: '/', icon: Activity },
  { name: 'مختبر المحاكاة', path: '/sandbox', icon: Terminal },
  { name: 'بيئات الأهداف', path: '/targets', icon: Database },
  { name: 'التحليل السلوكي WAF', path: '/waf', icon: ShieldAlert },
  { name: 'إعدادات النظام البحثي', path: '/settings', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-64 h-screen bg-[#0a0a0a] border-l border-[#10b981]/20 flex flex-col">
      {/* Logo Area */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-[#10b981]/20">
        <Cpu className="w-6 h-6 text-[#10b981]" />
        <span className="text-[#10b981] font-bold tracking-widest uppercase text-sm">
          NEURAL-DB-EXFRAME
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
                `flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-200 group ${
                  isActive
                    ? 'bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/30 shadow-[0_0_10px_rgba(16,185,129,0.1)]'
                    : 'text-slate-400 hover:text-[#10b981] hover:bg-[#10b981]/5'
                }`
              }
            >
              <Icon className="w-5 h-5 shrink-0" />
              <span className="font-mono text-sm">{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* System Status */}
      <div className="p-4 border-t border-[#10b981]/10 space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[9px] font-mono tracking-widest leading-none">
            <span className="text-slate-500 uppercase">System Uptime</span>
            <span className="text-[#10b981]">14:02:11</span>
          </div>
          <div className="flex items-center justify-between text-[9px] font-mono tracking-widest leading-none">
            <span className="text-slate-500 uppercase">Core Load</span>
            <span className="text-blue-400">12.4%</span>
          </div>
        </div>
        
        <div className="pt-2">
          <div className="flex items-center justify-between text-xs font-mono mb-2">
            <span className="text-slate-400">حالة النظام</span>
            <span className="text-[#10b981] flex items-center gap-1.5 uppercase font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse"></span>
              ONLINE
            </span>
          </div>
          <div className="w-full bg-[#10b981]/10 rounded-full h-1 overflow-hidden">
            <div className="bg-[#10b981] h-full rounded-full w-4/5 shadow-[0_0_8px_#10b981]"></div>
          </div>
        </div>
      </div>
    </aside>
  );
}
