import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, Database, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface EvolutionData {
  time: string;
  avgScore: number;
  attempts: number;
}

interface Exploit {
  payload: string;
  type: string;
  timestamp: string;
}

export default function Dashboard() {
  const [evolutionData, setEvolutionData] = useState<EvolutionData[]>([]);
  const [exploits, setExploits] = useState<Exploit[]>([]);
  const [stats, setStats] = useState({
    targets: '0',
    payloads: '0',
    blocks: '0',
    successRate: '0%'
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [evoRes, exploitRes, targetRes, lootRes] = await Promise.all([
          fetch('/api/evolution-stats'),
          fetch('/api/exploits'),
          fetch('/api/targets'), // Assuming this exists or returns empty
          fetch('/api/loot')
        ]);

        if (evoRes.ok) setEvolutionData(await evoRes.json());
        if (exploitRes.ok) setExploits(await exploitRes.json());
        
        // Mocking some stats based on real data counts
        const exploitData = exploitRes.ok ? await exploitRes.clone().json() : [];
        const lootData = lootRes.ok ? await lootRes.json() : [];
        
        setStats({
          targets: lootData.length.toString(),
          payloads: (evolutionData.length * 12).toString(), // Rough estimate
          blocks: (evolutionData.reduce((acc, curr) => acc + (curr.attempts * (1 - curr.avgScore)), 0)).toFixed(0),
          successRate: evolutionData.length > 0 
            ? (evolutionData[evolutionData.length - 1].avgScore * 100).toFixed(1) + '%'
            : '0%'
        });
      } catch (e) {
        console.error("Failed to fetch dashboard data", e);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [evolutionData.length]);

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
        <StatCard title="الأهداف النشطة" value={stats.targets} icon={Database} trend="+1" />
        <StatCard title="الحمولات المولدة" value={stats.payloads} icon={Zap} trend="+142/ساعة" />
        <StatCard title="حظر WAF" value={stats.blocks} icon={ShieldAlert} trend="-12%" />
        <StatCard title="معدل النجاح" value={stats.successRate} icon={Activity} trend="+2.4%" />
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6 min-h-[400px] flex flex-col">
          <h2 className="text-lg font-mono text-white mb-4 border-b border-[#10b981]/20 pb-2">رسم بياني للتطور</h2>
          <div className="flex-1 w-full min-h-[300px]">
            {evolutionData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={evolutionData}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis 
                    dataKey="time" 
                    stroke="#64748b" 
                    fontSize={10} 
                    tickFormatter={(str) => str.split(' ')[1]} 
                  />
                  <YAxis stroke="#64748b" fontSize={10} domain={[0, 1]} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #10b98133', borderRadius: '8px' }}
                    itemStyle={{ color: '#10b981' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="avgScore" 
                    stroke="#10b981" 
                    fillOpacity={1} 
                    fill="url(#colorScore)" 
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-600 font-mono text-sm">
                [ في انتظار بيانات التطور... ]
              </div>
            )}
          </div>
        </div>
        
        <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6 min-h-[400px]">
          <h2 className="text-lg font-mono text-white mb-4 border-b border-[#10b981]/20 pb-2">أحدث الثغرات</h2>
          <div className="space-y-4 max-h-[350px] overflow-y-auto custom-scrollbar pr-2">
            {exploits.length > 0 ? exploits.slice(0, 10).map((exploit, i) => (
              <div key={i} className="bg-black/50 p-3 rounded border border-[#10b981]/10">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-[#10b981] font-mono">{exploit.type}</span>
                  <span className="text-slate-500">{new Date(exploit.timestamp).toLocaleTimeString('ar-EG')}</span>
                </div>
                <code className="text-[10px] text-slate-300 break-all">
                  {exploit.payload}
                </code>
              </div>
            )) : (
              <div className="text-center text-slate-600 font-mono text-xs py-10">
                لا توجد ثغرات مكتشفة بعد
              </div>
            )}
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
