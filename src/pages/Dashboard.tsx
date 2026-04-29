import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, Database, Zap, Copy, Check, Search, Trash2, LayoutGrid, BarChart3, ListFilter, Radar, MessageSquareWarning, History, EyeOff } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, Legend } from 'recharts';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { cn, copyToClipboard } from '../lib/utils';

// Types remain the same...
interface EvolutionData {
  generation: number;
  avgScore: number;
  attempts: number;
}

interface StrategicMetric {
  generation: number;
  label?: string;
  codes: { '200': number, '403': number, '500': number };
  islands: { island1: number, island2: number, island3: number };
  avgFitness?: number;
  counts?: { '200': number, '403': number, '500': number, 'predictive': number };
}

interface Exploit {
  payload: string;
  type: string;
  timestamp: string;
}

type DashboardSection = 'OVERVIEW' | 'EVOLUTION' | 'EXPLOITS' | 'SWARM' | 'STRATEGIC' | 'DIAGNOSTIC';

export default function Dashboard() {
  const [searchParams] = useSearchParams();
  const targetName = searchParams.get('target');
  
  const [activeSections, setActiveSections] = useState<DashboardSection[]>([]);
  
  const [evolutionData, setEvolutionData] = useState<EvolutionData[]>([]);
  const [strategicMetrics, setStrategicMetrics] = useState<StrategicMetric[]>([]);
  const [exploits, setExploits] = useState<Exploit[]>([]);
  const [reputationTrends, setReputationTrends] = useState<any[]>([]);
  const [selectedLineage, setSelectedLineage] = useState<any[]>([]);
  const [radarPoints, setRadarPoints] = useState<any[]>([]);
  const [sqlErrors, setSqlErrors] = useState<any[]>([]);
  const [convergenceStats, setConvergenceStats] = useState({
    predictiveBlocked: 0,
    convergence: { seconds: 0, formatted: '0:00' }
  });
  const [summaryStats, setSummaryStats] = useState({
    totalGenerations: 0,
    totalPayloads: 0,
    smartAgentBlocked: 0,
    wafBlocked: 0,
    successfulPayloads: 0,
    sqlErrorPayloads: 0,
    attackDuration: { seconds: 0, formatted: '0:00' },
    convergence: { seconds: 0, formatted: '0:00' }
  });
  const [stats, setStats] = useState({
    targets: '0',
    payloads: '0',
    blocks: '0',
    successRate: '0%',
    wafPatterns: '0'
  });
  const [copiedPayload, setCopiedPayload] = useState<string | null>(null);

  const toggleSection = (section: DashboardSection) => {
    setActiveSections(prev => 
      prev.includes(section) 
        ? prev.filter(s => s !== section) 
        : [...prev, section]
    );
  };

  const handleCopy = async (text: string) => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopiedPayload(text);
      setTimeout(() => setCopiedPayload(null), 2000);
    }
  };

  const fetchData = async () => {
    try {
      const q = targetName ? `?targetName=${encodeURIComponent(targetName)}` : '';
      
      const [evoRes, metricRes, exploitRes, targetRes, lootRes, summaryRes, radarRes, repRes, sqlRes, wafRes] = await Promise.all([
        fetch(`/api/evolution-stats${q}`),
        fetch(`/api/strategic-metrics${q}`),
        fetch(`/api/exploits${q}`),
        fetch('/api/targets'),
        fetch('/api/loot'),
        fetch(`/api/stats-summary${q}`),
        fetch(`/api/swarm-radar${q}`),
        fetch(`/api/reputation-trends${q}`),
        fetch(`/api/sql-errors${q}`),
        fetch(`/api/waf-intelligence`)
      ]);

      if (evoRes.ok) {
        const evoVal = await evoRes.json();
        // If specific target has no data, try fetching global data to see if it exists
        if (evoVal.length === 0 && targetName) {
           const fallbackRes = await fetch('/api/evolution-stats');
           if (fallbackRes.ok) {
             const fallbackVal = await fallbackRes.json();
             setEvolutionData(fallbackVal);
           }
        } else {
          setEvolutionData(evoVal);
        }
      }
      
      if (summaryRes.ok) {
        const summary = await summaryRes.json();
        setSummaryStats(summary);
        // Sync older stats state for backward compatibility if needed
        setStats(prev => ({
          ...prev,
          payloads: summary.totalPayloads.toString(),
          blocks: (summary.smartAgentBlocked + summary.wafBlocked).toString(),
          successRate: summary.totalPayloads > 0 ? ((summary.successfulPayloads / summary.totalPayloads) * 100).toFixed(1) + '%' : '0%'
        }));
      }

      if (wafRes.ok) {
        const wafVal = await wafRes.json();
        setStats(prev => ({ ...prev, wafPatterns: wafVal.patterns ? wafVal.patterns.length.toString() : '0' }));
      }

      if (radarRes.ok) setRadarPoints(await radarRes.json());
      if (sqlRes.ok) setSqlErrors(await sqlRes.json());
      if (repRes.ok) setReputationTrends(await repRes.json());
      if (metricRes.ok) setStrategicMetrics(await metricRes.json());
      if (exploitRes.ok) setExploits(await exploitRes.json());
      
      if (targetRes.ok) {
        const targets = await targetRes.json();
        setStats(prev => ({ ...prev, targets: targets.length.toString() }));
      }

    } catch (e) {
      console.error("Failed to fetch dashboard data", e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    
    // Auto-select sections if target is provided
    if (targetName && activeSections.length === 0) {
      setActiveSections(['OVERVIEW', 'EVOLUTION', 'EXPLOITS', 'SWARM']);
    }
    
    return () => clearInterval(interval);
  }, [targetName]);

  const handleTraceLineage = async (payload: string) => {
    try {
      const res = await fetch(`/api/payload-lineage?payload=${encodeURIComponent(payload)}`);
      if (res.ok) {
        setSelectedLineage(await res.json());
      }
    } catch (e) {
      console.error("Lineage trace failed", e);
    }
  };

  const sections = [
    { id: 'OVERVIEW' as const, label: 'الإحصائيات الكلية', icon: LayoutGrid },
    { id: 'EVOLUTION' as const, label: 'مسار الكفاءة التطورية', icon: BarChart3 },
    { id: 'EXPLOITS' as const, label: 'أرشيف سلالات الاختراق', icon: ListFilter },
    { id: 'SWARM' as const, label: 'ديناميكيات السرب الذكي', icon: Radar },
    { id: 'STRATEGIC' as const, label: 'مصفوفة الطفرات الجينية', icon: History },
    { id: 'DIAGNOSTIC' as const, label: 'استثناءات قواعد البيانات', icon: MessageSquareWarning },
  ];

  return (
    <div className="space-y-6 max-w-[1800px] mx-auto pb-12 font-mono">
      {/* Header & Section Selector */}
      <div className="bg-[#0a0a0a]/80 backdrop-blur-md border border-[#10b981]/20 rounded-xl p-4 sticky top-0 z-50 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <Zap className="w-5 h-5 text-[#10b981]" />
                {targetName ? (
                  <span dir="ltr" className="text-blue-400">TARGET: {targetName}</span>
                ) : (
                  <span>عقدة القيادة والتحكم الرئيسية</span>
                )}
              </h1>
              <span className="text-[9px] text-slate-500 uppercase tracking-widest mt-1">
                القياس المباشر لتطور الحمولات الجينية بالوقت الفعلي (Telemetry)
              </span>
            </div>
            <div className="h-8 w-[1px] bg-[#10b981]/20 hidden lg:block"></div>
            <div className="flex items-center gap-2 overflow-x-auto pb-2 lg:pb-0 scrollbar-hide">
              {sections.map(s => (
                <Button
                  key={s.id}
                  variant="outline"
                  size="sm"
                  onClick={() => toggleSection(s.id)}
                  className={cn(
                    "h-8 text-[10px] font-bold gap-2 transition-all border whitespace-nowrap px-3",
                    activeSections.includes(s.id)
                      ? "bg-[#10b981] text-black border-[#10b981] hover:bg-[#10b981]/90 hover:text-black"
                      : "bg-[#10b981]/5 text-slate-400 border-[#10b981]/10 hover:border-[#10b981]/40 hover:bg-[#10b981]/10"
                  )}
                >
                  <s.icon className="w-3.5 h-3.5" />
                  {s.label}
                </Button>
              ))}
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-[10px]">
            <div className="bg-[#10b981]/5 text-[#10b981] px-3 py-1 rounded border border-[#10b981]/20 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse"></span>
              التدفق النشط: {targetName ? 'TARGET_SYNC' : 'GLOBAL_AGGREGATE'}
            </div>
            {activeSections.length > 0 && (
              <button 
                onClick={() => setActiveSections([])}
                className="text-slate-500 hover:text-white flex items-center gap-1 transition-colors"
                title="تفريغ العرض"
              >
                <EyeOff className="w-3.5 h-3.5" />
                تفريغ العرض
              </button>
            )}
          </div>
        </div>
      </div>

      {activeSections.length === 0 ? (
        <Card className="h-[60vh] flex flex-col items-center justify-center text-slate-700 border-2 border-dashed border-[#10b981]/20 bg-[#0a0a0a]">
          <CardContent className="flex flex-col items-center justify-center p-6">
            <LayoutGrid className="w-16 h-16 opacity-5 mb-6 text-[#10b981]" />
            <p className="text-sm font-mono tracking-widest uppercase opacity-40">الشاشة خاملة - يرجى تحديد المقاييس من الأعلى للبدء</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          {/* Overview Cards Section */}
          {activeSections.includes('OVERVIEW') && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              <StatCard title="إجمالي الأجيال المحققة" value={summaryStats.totalGenerations.toString()} icon={History} trend="Evolution Progress" />
              <StatCard title="الحمولات الملغاة (الوكيل الذكي)" value={summaryStats.smartAgentBlocked.toString()} icon={ShieldAlert} trend="Predictive Blocks" />
              <StatCard title="محظورات جدار الحماية (WAF)" value={summaryStats.wafBlocked.toString()} icon={ShieldAlert} trend="Total WAF Blocks" />
              <StatCard title="البصمات التي تم تخطيها (Exploits)" value={summaryStats.successfulPayloads.toString()} icon={Check} trend="Confirmed Bypasses" />
              <StatCard title="أخطاء SQL المستخرجة" value={summaryStats.sqlErrorPayloads.toString()} icon={MessageSquareWarning} trend="Data Leaks/Errors" />
              <StatCard title="الوقت الفعلي المستغرق" value={summaryStats.attackDuration.formatted} icon={Activity} trend="Attack Duration" />
              <StatCard title="إجمالي المحاولات (Full Log)" value={summaryStats.totalPayloads.toString()} icon={Zap} trend="Total Throughput" />
              <StatCard title="قواعد WAF المكتشفة" value={stats.wafPatterns} icon={Radar} trend="Pattern Database" />
            </div>
          )}

          {/* Evolution Chart Section */}
          {activeSections.includes('EVOLUTION') && (
            <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6 min-h-[400px] flex flex-col group relative overflow-hidden">
               <div className="flex justify-between items-end mb-6 border-b border-[#10b981]/10 pb-4">
                <h2 className="text-lg font-mono text-white flex items-center gap-2">
                  <Zap className="w-4 h-4 text-[#10b981]" />
                  مسار الكفاءة التطورية (متوسط الفاعلية لكل جيل)
                </h2>
                <span className="text-[10px] text-slate-500 font-mono w-1/2 text-right">
                  يعرض متوسط التطور المستمر لمجموعات الحمولات بمرور الوقت، مما يوضح منحنى التعلم والتخطي للخوارزمية الجينية.
                </span>
              </div>
              <div className="flex-1 w-full min-h-[300px]">
                {evolutionData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={evolutionData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                      <defs>
                        <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} opacity={0.3} />
                      <XAxis 
                        dataKey="generation" 
                        stroke="#475569" 
                        fontSize={10} 
                        tickFormatter={(val) => `Gen ${val}`} 
                        label={{ value: 'رقم الجيل (Generation)', position: 'insideBottom', offset: -15, fill: '#64748b', fontSize: 10 }}
                      />
                      <YAxis 
                        stroke="#475569" 
                        fontSize={10} 
                        domain={[0, 1]} 
                        tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
                        label={{ value: 'Fitness Score (%)', angle: -90, position: 'insideLeft', offset: 15, fill: '#64748b', fontSize: 10 }}
                      />
                      <Tooltip contentStyle={{ backgroundColor: '#050505', border: '1px solid #10b98133', borderRadius: '4px', fontSize: '10px' }} />
                      <Area type="monotone" dataKey="avgScore" name="Avg Fitness" stroke="#10b981" fillOpacity={1} fill="url(#colorScore)" strokeWidth={3} dot={{ r: 2, fill: '#10b981' }} />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-full text-slate-600 font-mono text-xs italic">بانتظار خط تدفق البيانات التطورية...</div>
                )}
              </div>
            </div>
          )}

          {/* Exploits Section */}
          {activeSections.includes('EXPLOITS') && (
            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
               <div className="xl:col-span-3 bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6 min-h-[400px] flex flex-col relative">
                <div className="flex flex-col gap-1 mb-4 border-b border-[#10b981]/20 pb-4">
                  <h2 className="text-sm font-mono text-white flex items-center gap-2 uppercase tracking-widest">
                    تتبع شجرة سلالات الحمولات الجينية
                  </h2>
                  <p className="text-[10px] text-slate-500 font-mono">عرض هرمي لمسارات الطفرات التي أدت إلى تجاوزات أمنية ناجحة للأنظمة.</p>
                </div>
                <div className="flex gap-2 mb-4 overflow-x-auto pb-2 custom-scrollbar">
                  {exploits.slice(0, 10).map((exp, i) => (
                    <button key={i} onClick={() => handleTraceLineage(exp.payload)} className="px-3 py-1 bg-[#10b981]/5 border border-[#10b981]/20 rounded text-[9px] font-mono text-slate-400 hover:text-white transition-all whitespace-nowrap">EXTRACT-L:{i+1}</button>
                  ))}
                </div>
                <div className="flex-1 space-y-4 overflow-y-auto pr-4 custom-scrollbar rtl">
                   {selectedLineage.length > 0 ? selectedLineage.map((step, i) => (
                    <div key={i} className="relative pr-6 border-r border-[#10b981]/20 pb-6 last:pb-0">
                      <div className="absolute right-[-4px] top-0 w-2 h-2 rounded-full bg-[#10b981]"></div>
                      <div className="bg-black/50 p-3 rounded-lg border border-white/5 hover:border-[#10b981]/30 transition-colors">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-[9px] text-slate-500 font-mono italic uppercase">المرحلة {i + 1} • {step.status}</span>
                          <span className="text-xs font-mono text-[#10b981] font-bold">{(step.score * 100).toFixed(0)}% كفاءة</span>
                        </div>
                        <code className="text-[10px] text-slate-300 break-all bg-black p-3 block rounded font-mono leading-relaxed">
                          {step.payload}
                        </code>
                      </div>
                    </div>
                  )) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-700 italic gap-4">
                      <History className="w-12 h-12 opacity-5" />
                      <span className="text-xs opacity-50">حدد ثغرة من القائمة العلوية لتتبع تاريخ تطورها</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="xl:col-span-1 bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6 flex flex-col max-h-[500px]">
                <h2 className="text-sm font-mono text-white mb-4 border-b border-[#10b981]/20 pb-4 flex items-center justify-center gap-2 uppercase tracking-widest text-center">
                  أرشيف الثغرات المؤكدة
                </h2>
                <div className="flex-1 space-y-4 overflow-y-auto custom-scrollbar pr-2 h-0">
                  {exploits.length > 0 ? exploits.map((exploit, i) => (
                    <div key={i} className="bg-black/50 p-3 rounded border border-[#10b981]/10 hover:border-[#10b981]/30 transition-colors group relative">
                       <div className="flex justify-between text-[10px] mb-2 font-mono">
                        <span className="text-[#10b981] font-bold">{exploit.type}</span>
                        <div className="flex items-center gap-2">
                           <span className="text-slate-600">{new Date(exploit.timestamp).toLocaleTimeString('ar-EG')}</span>
                           <button onClick={() => handleCopy(exploit.payload)} className={cn("p-1 rounded transition-all", copiedPayload === exploit.payload ? "bg-[#10b981]/20 text-[#10b981]" : "hover:bg-white/10 text-slate-500")}>
                             {copiedPayload === exploit.payload ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                           </button>
                        </div>
                      </div>
                      <code className="text-[9px] text-slate-400 break-all bg-black/40 p-2 block rounded font-mono border border-white/5">{exploit.payload}</code>
                    </div>
                  )) : (
                    <div className="text-center text-slate-700 font-mono text-xs py-20 italic">لا توجد ثغرات مسجلة</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Swarm & Strategic Analytics */}
          {(activeSections.includes('SWARM') || activeSections.includes('STRATEGIC')) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
              {activeSections.includes('SWARM') && (
                <>
                  <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-5">
                    <h2 className="text-xs font-mono text-white mb-1 flex items-center gap-2 uppercase">
                      <Activity className="w-3.5 h-3.5 text-blue-500" /> كفاءة تحسين الأنظمة الفرعية (للجزر)
                    </h2>
                    <p className="text-[9px] text-slate-500 font-mono mb-4 border-b border-[#10b981]/10 pb-3">يقارن معدلات الكفاءة عبر استراتيجيات الطفرات المعزولة (نظام الجزر التحليلية).</p>
                    <div className="h-[200px]">
                       <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={strategicMetrics} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} opacity={0.2} />
                          <XAxis dataKey="label" stroke="#475569" fontSize={8} label={{ value: 'Generation ID', position: 'insideBottom', offset: -10, fill: '#64748b', fontSize: 9 }} />
                          <YAxis stroke="#475569" fontSize={8} unit="%" domain={[0, 100]} />
                          <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #10b98133', fontSize: '10px' }} />
                          <Line type="monotone" dataKey="islands.island1" stroke="#10b981" strokeWidth={2} dot={{ r: 2 }} name="1. Inference" />
                          <Line type="monotone" dataKey="islands.island2" stroke="#3b82f6" strokeWidth={2} dot={{ r: 2 }} name="2. WAF Bypass" />
                          <Line type="monotone" dataKey="islands.island3" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 2 }} name="3. Data Extraction" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-5">
                    <h2 className="text-xs font-mono text-white mb-1 flex items-center gap-2 uppercase">
                      <Radar className="w-3.5 h-3.5 text-emerald-500" /> رادار الوكلاء الدقيق (Micro-Agents)
                    </h2>
                    <p className="text-[9px] text-slate-500 font-mono mb-4 border-b border-[#10b981]/10 pb-3">الأداء الفعلي المباشر للوكلاء الفرديين عبر الشبكة الخوارزمية.</p>
                    <div className="h-[200px] overflow-y-auto custom-scrollbar pr-2">
                       {radarPoints.length > 0 ? radarPoints.slice(0, 15).map((p, i) => (
                         <div key={i} className="flex justify-between text-[8px] font-mono p-1.5 bg-black/40 rounded-sm border-r-2 border-emerald-500/30 mb-1">
                           <span className="text-blue-500 opacity-60">جزيرة {p.island_id}</span>
                           <code className="text-slate-400 truncate max-w-[100px]">{p.payload}</code>
                           <span className="text-[#10b981]">{(p.score * 100).toFixed(0)}%</span>
                         </div>
                       )) : <div className="h-full flex items-center justify-center text-slate-700 text-[10px]">No active radar data</div>}
                    </div>
                  </div>
                </>
              )}
              {activeSections.includes('STRATEGIC') && (
                <div className="xl:col-span-2 bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-5 flex flex-col h-[280px]">
                   <h2 className="text-xs font-mono text-white mb-1 flex items-center gap-2 uppercase">
                    <Activity className="w-3.5 h-3.5 text-amber-500" /> مصفوفة الطفرات الجيلية
                  </h2>
                  <p className="text-[9px] text-slate-500 font-mono mb-4 border-b border-[#10b981]/10 pb-3">تحليل استجابات HTTP المرتبطة بخوارزمية التوليد النشطة لكل جيل.</p>
                  <div className="flex-1 overflow-y-auto custom-scrollbar border border-white/5 bg-black/30 rounded">
                    <table className="w-full text-right font-mono text-[9px] border-collapse">
                      <thead className="sticky top-0 bg-[#111]">
                        <tr className="text-slate-400 border-b border-white/10 uppercase tracking-wider text-[8px]">
                          <th className="py-2.5 px-3 text-center border-r border-white/5">رقم الجيل</th>
                          <th className="py-2.5 px-3 text-center border-r border-white/5">متوسط الكفاءة</th>
                          <th className="py-2.5 px-3 text-center text-red-400 border-r border-white/5" title="HTTP 403 Forbidden - WAF Block">403 (حظر)</th>
                          <th className="py-2.5 px-3 text-center text-amber-400 border-r border-white/5" title="HTTP 500 - Internal Server Error / SQL Exception">500 (حقن وخطأ)</th>
                          <th className="py-2.5 px-3 text-center text-[#10b981] border-r border-white/5" title="HTTP 200 - Successful Bypass">200 (تجاوز)</th>
                          <th className="py-2.5 px-3 text-center text-blue-400" title="Predictive AI Blocks generated by the system WAF">استنتاج وتوقف</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {strategicMetrics.slice().reverse().map((gen, i) => (
                          <tr key={i} className="hover:bg-white/5 transition-colors">
                            <td className="py-1.5 px-2 text-white text-center">#{gen.generation.toString().padStart(2, '0')}</td>
                            <td className="py-1.5 px-2 text-center">{( (gen.avgFitness || 0) * 100).toFixed(0)}%</td>
                            <td className="py-1.5 px-2 text-center opacity-70">{gen.counts?.['403'] || 0}</td>
                            <td className="py-1.5 px-2 text-center opacity-70">{gen.counts?.['500'] || 0}</td>
                            <td className="py-1.5 px-2 text-center opacity-70">{gen.counts?.['200'] || 0}</td>
                            <td className="py-1.5 px-2 text-center opacity-70">{gen.counts?.['predictive'] || 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Diagnostic Audit Section */}
          {activeSections.includes('DIAGNOSTIC') && (
            <div className="bg-[#0a0a0a] border border-red-500/20 rounded-lg p-6 relative overflow-hidden">
               <div className="flex items-center justify-between mb-6 border-b border-red-500/10 pb-4">
                <div className="flex flex-col gap-1">
                  <h2 className="text-sm font-mono text-white flex items-center gap-3 uppercase tracking-widest">
                    <ShieldAlert className="w-5 h-5 text-red-500" /> السجل التشخيصي لأخطاء قواعد البيانات (استثناءات SQL)
                  </h2>
                  <p className="text-[10px] text-slate-500 font-mono">استجابات قواعد البيانات المجمعة المستخدمة لرسم الهيكلية الداخلية والتحقق من ثغرات الحقن الأمنية.</p>
                </div>
                <div className="bg-red-500/5 px-2 py-1 rounded border border-red-500/20 text-[9px] text-red-400 font-mono">
                  AST_ERROR_TRACE: ACTIVE
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                {sqlErrors.length > 0 ? sqlErrors.map((err, i) => (
                  <div key={i} className="bg-black/60 border border-red-500/5 p-4 rounded-lg hover:border-red-500/40 transition-all group relative">
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => handleCopy(err.payload)} className={cn("p-1.5 rounded bg-black border border-red-500/20 transition-all", copiedPayload === err.payload ? "text-[#10b981]" : "text-slate-500 hover:text-red-500")}>
                        {copiedPayload === err.payload ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                    <div className="flex justify-between items-center mb-3 text-[8px] font-mono">
                      <span className="text-slate-600">{new Date(err.timestamp).toLocaleTimeString()}</span>
                      <span className="text-red-500/60 uppercase">Critical_Level: 3</span>
                    </div>
                    <code className="text-[10px] text-blue-400/90 break-all block bg-black/40 p-2 rounded border border-white/5 mb-3">{err.payload}</code>
                    <div className="p-3 bg-red-500/5 border-r border-red-500/40 text-[9px] text-red-400/80 leading-relaxed font-mono italic">
                      {err.error_msg}
                    </div>
                  </div>
                )) : (
                  <div className="col-span-full py-20 text-center text-slate-800 font-mono text-sm uppercase opacity-30 italic">لا توجد أخطاء مرصودة في بنية قاعدة البيانات حالياً</div>
                )}
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}

function StatCard({ title, value, icon: Icon, trend }: { title: string, value: string, icon: any, trend: string }) {
  return (
    <Card className="bg-[#0a0a0a] border-[#10b981]/20 relative overflow-hidden group hover:border-[#10b981]/50 transition-all duration-300">
      <div className="absolute top-0 left-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
        <Icon className="w-12 h-12 text-[#10b981]" />
      </div>
      <CardContent className="p-5 relative z-10 font-mono">
        <h3 className="text-slate-500 text-[11px] mb-1 uppercase tracking-tighter">{title}</h3>
        <div className="text-2xl font-bold text-white mb-2">{value}</div>
        <div className="text-[9px] text-[#10b981] opacity-70 tracking-widest">{trend}</div>
      </CardContent>
    </Card>
  );
}
