import React from 'react';
import { Bell, Search, User } from 'lucide-react';

export default function Header() {
  return (
    <header className="h-16 bg-[#0a0a0a] border-b border-[#10b981]/20 flex items-center justify-between px-6">
      {/* Search Bar */}
      <div className="flex items-center gap-2 bg-black/50 border border-[#10b981]/20 rounded-md px-3 py-1.5 w-96 focus-within:border-[#10b981]/50 transition-colors">
        <Search className="w-4 h-4 text-slate-500 shrink-0" />
        <input
          type="text"
          placeholder="ابحث عن الحمولات، الأهداف، السجلات..."
          className="bg-transparent border-none outline-none text-sm text-slate-300 font-mono w-full placeholder:text-slate-600"
        />
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4">
        <button className="relative p-2 text-slate-400 hover:text-[#10b981] transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#10b981] rounded-full"></span>
        </button>
        
        <div className="h-8 w-px bg-[#10b981]/20"></div>
        
        <button className="flex items-center gap-2 text-slate-400 hover:text-[#10b981] transition-colors">
          <div className="w-8 h-8 rounded-md bg-[#10b981]/10 border border-[#10b981]/30 flex items-center justify-center">
            <User className="w-4 h-4 text-[#10b981]" />
          </div>
          <span className="font-mono text-sm hidden sm:block">المسؤول</span>
        </button>
      </div>
    </header>
  );
}
