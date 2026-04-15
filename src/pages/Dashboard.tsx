import React from 'react';
import { Activity, ShieldAlert, Database, Zap } from 'lucide-react';

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white font-mono tracking-tight">
          نظرة عامة على <span className="text-[#10b981]">النظام</span>
        </h1>
        <div className="flex items-center space-x-2 space-x-reverse text-sm font-mono bg-[#10b981]/10 text-[#10b981] px-3 py-1 rounded border border-[#10b981]/30">
          <span className="w-2 h-2 rounded-full bg-[#10b981]"></span>
          <span>مراقبة مباشرة</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="الأهداف النشطة" value="3" icon={Database} trend="+1" />
        <StatCard title="الحمولات المولدة" value="1,204" icon={Zap} trend="+142/ساعة" />
        <StatCard title="حظر WAF" value="89" icon={ShieldAlert} trend="-12%" />
        <StatCard title="معدل النجاح" value="94.2%" icon={Activity} trend="+2.4%" />
      </div>

      {/* Main Content Area Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6 min-h-[400px]">
          <h2 className="text-lg font-mono text-white mb-4 border-b border-[#10b981]/20 pb-2">رسم بياني للتطور</h2>
          <div className="flex items-center justify-center h-full text-slate-600 font-mono text-sm">
            [ سيتم تحميل الرسم البياني هنا ]
          </div>
        </div>
        
        <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6 min-h-[400px]">
          <h2 className="text-lg font-mono text-white mb-4 border-b border-[#10b981]/20 pb-2">أحدث الثغرات</h2>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-black/50 p-3 rounded border border-[#10b981]/10">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-[#10b981] font-mono">الهدف_{i}</span>
                  <span className="text-slate-500">منذ دقيقتين</span>
                </div>
                <code className="text-xs text-slate-300 break-all">
                  ' UNION SELECT NULL,database()--
                </code>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, trend }: { title: string, value: string, icon: any, trend: string }) {
  return (
    <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-5 relative overflow-hidden group hover:border-[#10b981]/50 transition-colors">
      <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <Icon className="w-16 h-16 text-[#10b981]" />
      </div>
      <div className="relative z-10">
        <h3 className="text-slate-400 font-mono text-sm mb-1">{title}</h3>
        <div className="text-3xl font-bold text-white mb-2">{value}</div>
        <div className="text-xs font-mono text-[#10b981]">{trend}</div>
      </div>
    </div>
  );
}
