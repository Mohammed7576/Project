import React, { useState, useEffect } from 'react';
import { Database, Plus, Trash2, ExternalLink, Shield, AlertTriangle } from 'lucide-react';

interface Target {
  url: string;
  waf_name: string;
  db_type: string;
  lastAttack: string;
}

export default function Targets() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [newUrl, setNewUrl] = useState('');

  useEffect(() => {
    const fetchTargets = async () => {
      try {
        const response = await fetch('/api/targets');
        if (response.ok) {
          const data = await response.json();
          setTargets(data.map((d: any) => ({
            url: d.target_url,
            waf_name: d.waf_name,
            db_type: d.db_type,
            lastAttack: d.last_updated
          })));
        }
      } catch (e) {
        console.error("Failed to fetch targets", e);
      }
    };
    fetchTargets();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white font-mono">إدارة <span className="text-[#10b981]">الأهداف</span></h1>
        <div className="flex gap-2">
          <input 
            type="text" 
            placeholder="أضف رابط هدف جديد..."
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            className="bg-black/40 border border-[#10b981]/20 rounded-lg px-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-[#10b981]/50 font-mono w-64"
          />
          <button className="bg-[#10b981] text-black px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 hover:bg-[#10b981]/80 transition-all">
            <Plus className="w-4 h-4" />
            إضافة
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {targets.length > 0 ? targets.map((target, i) => (
          <div key={i} className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-4 flex items-center justify-between hover:border-[#10b981]/40 transition-all group">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-[#10b981]/10 flex items-center justify-center">
                <Shield className="w-5 h-5 text-[#10b981]" />
              </div>
              <div>
                <h3 className="text-sm font-mono text-white flex items-center gap-2">
                  {target.url}
                  <ExternalLink className="w-3 h-3 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer" />
                </h3>
                <div className="flex gap-3 mt-1">
                  <span className="text-[10px] font-mono text-slate-500">آخر هجوم: {new Date(target.lastAttack).toLocaleString('ar-EG')}</span>
                  <span className="text-[10px] font-mono text-[#10b981]">DB: {target.db_type}</span>
                  <span className="text-[10px] font-mono text-blue-400">WAF: {target.waf_name}</span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-left">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/20">
                  نشط
                </span>
              </div>
              <button className="p-2 text-slate-500 hover:text-red-500 transition-colors">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        )) : (
          <div className="bg-[#0a0a0a] border border-dashed border-slate-800 rounded-lg p-12 text-center">
            <Database className="w-12 h-12 text-slate-700 mx-auto mb-4" />
            <p className="text-slate-500 font-mono text-sm">لا توجد أهداف مسجلة حالياً. ابدأ هجوماً من المختبر لتسجيل الأهداف.</p>
          </div>
        )}
      </div>
    </div>
  );
}
