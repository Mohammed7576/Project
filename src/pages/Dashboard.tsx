import React, { useState, useEffect, useRef } from 'react';
import { 
  Terminal as TerminalIcon, 
  ShieldCheck, 
  Activity, 
  Database, 
  Search, 
  Play, 
  Square, 
  Zap, 
  Lock, 
  Globe, 
  BarChart3,
  ChevronRight,
  AlertTriangle,
  GitGraph,
  Network
} from 'lucide-react';
import { 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  ZAxis
} from 'recharts';
import { Virtuoso } from 'react-virtuoso';
import { cn } from '../lib/utils';

interface LogEntry {
  id: number;
  message: string;
  type: 'info' | 'success' | 'error' | 'warning' | 'critical' | 'refinement';
  timestamp: string;
}

export default function Dashboard() {
  console.log("[DASHBOARD] Rendering component...");
  
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentGen, setCurrentGen] = useState(0);
  const [winningPayloads, setWinningPayloads] = useState<string[]>([]);
  const [isStealthMode, setIsStealthMode] = useState(false);
  const [isChaosMode, setIsChaosMode] = useState(false);
  const [showTerminal, setShowTerminal] = useState(true);
  const [loot, setLoot] = useState<string | null>(null);
  const [wafInfo, setWafInfo] = useState<string | null>(null);
  const [lineage, setLineage] = useState<{payload: string, parent: string, score: number, status: string}[]>([]);
  const [savedExploits, setSavedExploits] = useState<{payload: string, type: string, timestamp: string}[]>([]);
  const [targetConfig, setTargetConfig] = useState({
    url: 'http://localhost/',
    username: 'admin',
    password: 'password',
    security: 'medium',
    populationSize: '12',
    maxGenerations: '30'
  });
  const [stats, setStats] = useState<{gen: number, score: number}[]>([]);
  const [lootData, setLootData] = useState<any[]>([]);
  const [aiStats, setAiStats] = useState<{totalStates: number, stepsDone?: number, recentStates: any[]}>({totalStates: 0, stepsDone: 0, recentStates: []});

  const addLog = (message: string, type: LogEntry['type'] = 'info') => {
    console.log(`[LOG] ${type.toUpperCase()}: ${message}`);
    setLogs(prev => {
      const newLogs = [...prev, { 
        id: Date.now() + Math.random(), 
        message, 
        timestamp: new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        type 
      }];
      // Keep only last 500 logs to prevent memory issues
      return newLogs.slice(-500);
    });
  };

  const [swarmData, setSwarmData] = useState<any[]>([]);
  const [brainLogs, setBrainLogs] = useState<any[]>([]);

  const isMounted = useRef(true);
  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const fetchEvolutionStats = async () => {
    try {
      const res = await fetch('/api/ai-stats');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      if (isMounted.current) setAiStats(data);
    } catch (e) {
      console.error("Failed to fetch evolution stats", e);
    }
  };

  const fetchExploits = async () => {
    try {
      const res = await fetch('/api/exploits');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      if (isMounted.current) setSavedExploits(data);
    } catch (e) {
      console.error("Failed to fetch exploits", e);
    }
  };

  const fetchLoot = async () => {
    try {
      const res = await fetch('/api/loot');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      if (isMounted.current) setLootData(data);
    } catch (e) {
      console.error("Failed to fetch loot", e);
    }
  };

  const fetchSwarmData = async () => {
    try {
      const res = await fetch('/api/swarm-radar');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      if (isMounted.current) setSwarmData(data);
    } catch (e) {
      console.error("Failed to fetch swarm data", e);
    }
  };

  const fetchBrainLogs = async () => {
    try {
      const res = await fetch('/api/brain-logs');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      if (isMounted.current) setBrainLogs(data);
    } catch (e) {
      console.error("Failed to fetch brain logs", e);
    }
  };

  const fetchLineage = async () => {
    try {
      const res = await fetch('/api/lineage');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      if (isMounted.current) setLineage(data);
    } catch (err) {
      console.error("Error fetching lineage:", err);
    }
  };

  useEffect(() => {
    fetchExploits();
    fetchLoot();
    fetchEvolutionStats();
    fetchSwarmData();
    fetchBrainLogs();

    const interval = setInterval(() => {
      fetchSwarmData();
      fetchBrainLogs();
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const runPrometheus = async () => {
    setIsRunning(true);
    setLogs([]);
    setStats([]);
    setWinningPayloads([]);
    setLoot(null);
    setWafInfo(null);
    setCurrentGen(0);
    
    addLog("Initializing Prometheus Attack Unit...", "info");
    addLog(`Target: ${targetConfig.url}`, "info");
    
    try {
      const queryParams = new URLSearchParams(targetConfig).toString();
      const response = await fetch(`/api/run-prometheus?${queryParams}`);
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader available");

      let lastScore = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        lines.forEach(line => {
          if (line.trim()) {
            let type: LogEntry['type'] = 'info';
            if (line.includes('[+]') || line.includes('SUCCESS')) type = 'success';
            if (line.includes('[-]')) type = 'warning';
            if (line.includes('[!]')) type = 'error';
            if (line.includes('CRITICAL') || line.includes('NEW EXPLOIT')) type = 'critical';
            if (line.includes('REFINEMENT')) type = 'refinement';
            
            addLog(line, type);

            if (line.includes('[ANALYSIS_REQUIRED]')) {
              addLog("[SYSTEM] Stagnation detected. Evolution strategy adjustment required.", "warning");
            }

            if (line.includes('[*] WAF DETECTED:')) {
              const wafMatch = line.match(/WAF DETECTED: (.*)/);
              if (wafMatch) setWafInfo(wafMatch[1]);
            }
            
            if (line.includes('[+] Generation')) {
              const genMatch = line.match(/Generation (\d+)/);
              if (genMatch) {
                const gen = parseInt(genMatch[1]);
                setCurrentGen(gen);
              }
            }

            if (line.includes('Score:')) {
              const scoreMatch = line.match(/Score: ([\d.]+)/);
              if (scoreMatch) {
                const score = parseFloat(scoreMatch[1]);
                if (score > lastScore) {
                  lastScore = score;
                  setStats(prev => {
                    const newStats = [...prev, { gen: currentGen, score }];
                    // Decimation: Keep max 60 points to avoid SVG overload
                    if (newStats.length > 60) {
                      return newStats.filter((_, i) => i % 2 === 0 || i === newStats.length - 1);
                    }
                    return newStats;
                  });
                }
              }
            }

            if (line.includes('[!!!] NEW EXPLOIT DISCOVERED:') || line.includes('[!] Winning Payload:')) {
              const payload = line.split(': ')[1];
              setWinningPayloads(prev => [...new Set([...prev, payload])]);
              setStats(prev => [...prev, { gen: currentGen + 1, score: 1.0 }]);
              fetchExploits();
            }

            if (line.includes('[Loot] Automated extraction successful')) {
              fetchLoot();
            }
          }
        });
      }
    } catch (err) {
      addLog(`[!] Connection Error: ${err}`, 'error');
    }

    setIsRunning(false);
  };

  useEffect(() => {
    if (isRunning) {
      const interval = setInterval(() => {
        fetchLineage();
        fetchLoot();
        fetchEvolutionStats();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [isRunning]);

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 flex-1">
      
      {/* Left Column: Config & Stats */}
      <div className="xl:col-span-3 space-y-6">
        
        {/* Target Configuration */}
        <section className="cyber-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-cyber-border pb-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <Search className="w-3.5 h-3.5 text-cyber-blue" /> معايير الهدف
            </h3>
            <Lock className="w-3 h-3 text-slate-600" />
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="cyber-label">رابط الهدف</label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                <input 
                  type="text" 
                  value={targetConfig.url}
                  onChange={(e) => setTargetConfig({...targetConfig, url: e.target.value})}
                  className="cyber-input pl-9"
                  placeholder="http://target.local/"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="cyber-label">اسم المستخدم</label>
                <input 
                  type="text" 
                  value={targetConfig.username}
                  onChange={(e) => setTargetConfig({...targetConfig, username: e.target.value})}
                  className="cyber-input"
                />
              </div>
              <div>
                <label className="cyber-label">كلمة المرور</label>
                <input 
                  type="password" 
                  value={targetConfig.password}
                  onChange={(e) => setTargetConfig({...targetConfig, password: e.target.value})}
                  className="cyber-input"
                />
              </div>
            </div>

            <div>
              <label className="cyber-label">مستوى الحماية</label>
              <select 
                value={targetConfig.security}
                onChange={(e) => setTargetConfig({...targetConfig, security: e.target.value})}
                className="cyber-input appearance-none"
              >
                <option value="low">منخفض (LOW)</option>
                <option value="medium">متوسط (MEDIUM)</option>
                <option value="high">عالي (HIGH)</option>
                <option value="impossible">مستحيل (IMPOSSIBLE)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="cyber-label">عدد السكان</label>
                <input 
                  type="number" 
                  value={targetConfig.populationSize}
                  onChange={(e) => setTargetConfig({...targetConfig, populationSize: e.target.value})}
                  className="cyber-input"
                  min="1"
                  max="100"
                />
              </div>
              <div>
                <label className="cyber-label">عدد الأجيال</label>
                <input 
                  type="number" 
                  value={targetConfig.maxGenerations}
                  onChange={(e) => setTargetConfig({...targetConfig, maxGenerations: e.target.value})}
                  className="cyber-input"
                  min="1"
                  max="200"
                />
              </div>
            </div>
            
            {!isRunning ? (
              <button 
                onClick={runPrometheus}
                className="cyber-button cyber-button-primary w-full justify-center mt-2"
              >
                <Play className="w-4 h-4 fill-current" /> بدء الهجوم
              </button>
            ) : (
              <button 
                onClick={() => setIsRunning(false)}
                className="cyber-button cyber-button-danger w-full justify-center mt-2"
              >
                <Square className="w-4 h-4 fill-current" /> إيقاف
              </button>
            )}
          </div>
        </section>

        {/* Loot Section (New) */}
        <section className="cyber-card p-5 flex flex-col h-[400px]">
          <div className="flex items-center justify-between border-b border-cyber-border pb-3 mb-4">
            <h3 className="text-xs font-bold text-cyber-blue uppercase tracking-widest flex items-center gap-2">
              <Database className="w-3.5 h-3.5" /> البيانات المستخرجة (Loot)
            </h3>
            <span className="text-[10px] text-slate-500 font-mono">تلقائي</span>
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-4 pr-1 custom-scrollbar">
            {lootData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 space-y-3 opacity-50">
                <Lock className="w-8 h-8" />
                <p className="text-[10px] uppercase tracking-widest font-bold">بانتظار استخراج البيانات...</p>
              </div>
            ) : (
              lootData.map((item, idx) => (
                <div key={idx} className="bg-black/40 border border-cyber-blue/20 rounded-lg p-3 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold text-cyber-blue uppercase">قاعدة البيانات:</span>
                    <span className="text-[10px] font-mono text-slate-300">{item.database_name || 'غير معروف'}</span>
                  </div>
                  
                  <div>
                    <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">الجداول المكتشفة:</span>
                    <div className="flex flex-wrap gap-1">
                      {item.tables?.map((t: string, i: number) => (
                        <span key={i} className="text-[9px] bg-cyber-blue/10 text-cyber-blue px-1.5 py-0.5 rounded border border-cyber-blue/20">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>

                  {item.columns && Object.keys(item.columns).length > 0 && (
                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">أعمدة حيوية:</span>
                      {Object.entries(item.columns).map(([table, cols]: [string, any], i) => (
                        <div key={i} className="text-[9px] text-slate-400">
                          <span className="text-cyber-amber">{table}:</span> {(cols as string[]).join(', ')}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </section>

        {/* System Metrics */}
        <section className="cyber-card p-5 space-y-4">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2 border-b border-cyber-border pb-3">
            <Activity className="w-3.5 h-3.5 text-cyber-amber" /> مقاييس الوقت الفعلي
          </h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-black/40 rounded-lg border border-cyber-border">
              <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">الجيل</p>
              <p className="text-2xl font-display font-bold text-white tracking-tight">{currentGen}</p>
            </div>
            <div className="p-3 bg-black/40 rounded-lg border border-cyber-border">
              <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">الحالة</p>
              <p className={`text-xs font-bold uppercase tracking-wider ${isRunning ? 'text-cyber-amber animate-pulse' : 'text-cyber-green'}`}>
                {isRunning ? 'قيد التطور' : 'في الانتظار'}
              </p>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500">وضع التخفي</span>
              <span className={cn("font-mono font-bold", isStealthMode ? "text-cyber-amber animate-pulse" : "text-slate-700")}>
                {isStealthMode ? "نشط" : "غير نشط"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500">وضع الفوضى</span>
              <span className={cn("font-mono font-bold", isChaosMode ? "text-cyber-red animate-pulse" : "text-slate-700")}>
                {isChaosMode ? "نشط" : "غير نشط"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500">معدل النجاح</span>
              <span className="text-slate-300 font-mono">{(stats.length > 0 ? (stats[stats.length-1].score * 100).toFixed(1) : 0)}%</span>
            </div>
            {wafInfo && (
              <div className="flex items-center justify-between text-xs pt-2 border-t border-cyber-border/30">
                <span className="text-cyber-blue font-bold">WAF المكتشف</span>
                <span className="text-cyber-blue font-mono animate-pulse">{wafInfo}</span>
              </div>
            )}
          </div>
        </section>

        {/* Swarm Radar (New) */}
        <section className="cyber-card p-5 lg:col-span-2">
          <div className="flex items-center justify-between border-b border-cyber-border pb-3 mb-4">
            <h3 className="text-xs font-bold text-cyber-amber uppercase tracking-widest flex items-center gap-2">
              <Network className="w-4 h-4" /> رادار الأسراب الحي (Live Swarm Radar)
            </h3>
            <div className="flex gap-3 text-[10px] font-bold uppercase">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyber-blue"></span> Island 1</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyber-green"></span> Island 2</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyber-amber"></span> Island 3</span>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" dataKey="x" name="Complexity" stroke="#475569" tick={{fontSize: 10}} />
                <YAxis type="number" dataKey="y" name="Success Rate" stroke="#475569" tick={{fontSize: 10}} />
                <ZAxis type="number" dataKey="z" range={[20, 200]} name="Payload Size" />
                <RechartsTooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ backgroundColor: 'rgba(0,0,0,0.9)', border: '1px solid #0ea5e9', borderRadius: '4px' }}
                  itemStyle={{ color: '#0ea5e9', fontSize: '12px' }}
                />
                <Scatter name="Island 1" data={swarmData.filter(d => d.island === 1)} fill="#0ea5e9" opacity={0.7} />
                <Scatter name="Island 2" data={swarmData.filter(d => d.island === 2)} fill="#10b981" opacity={0.7} />
                <Scatter name="Island 3" data={swarmData.filter(d => d.island === 3)} fill="#f59e0b" opacity={0.7} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Evolution Intelligence Level */}
        <section className="cyber-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-cyber-border pb-3">
            <h3 className="text-xs font-bold text-cyber-blue uppercase tracking-widest flex items-center gap-2">
              <Zap className="w-3.5 h-3.5" /> ذكاء التطور التراكمي
            </h3>
            <span className="text-[10px] text-cyber-blue font-mono">Genetic RL</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-cyber-blue/5 border border-cyber-blue/20 rounded-lg text-center">
              <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">الذكريات المخزنة</p>
              <p className="text-2xl font-display font-bold text-cyber-blue tracking-tight">{aiStats.totalStates}</p>
              <p className="text-[9px] text-cyber-blue/60 mt-1 uppercase tracking-tighter">Replay Buffer</p>
            </div>
            <div className="p-3 bg-cyber-blue/5 border border-cyber-blue/20 rounded-lg text-center">
              <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">خطوات التدريب</p>
              <p className="text-2xl font-display font-bold text-cyber-blue tracking-tight">{aiStats.stepsDone || 0}</p>
              <p className="text-[9px] text-cyber-blue/60 mt-1 uppercase tracking-tighter">Steps Done</p>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-[10px] text-slate-500 font-bold uppercase flex items-center gap-2">
              <Activity className="w-3 h-3" /> نشاط الدماغ (Brain Activity):
            </p>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
              {brainLogs.length === 0 ? (
                <p className="text-[10px] text-slate-700 italic">لا توجد نشاطات مسجلة بعد...</p>
              ) : (
                brainLogs.map((log, i) => (
                  <div key={i} className="p-2 bg-black/40 border border-cyber-border/50 rounded text-xs flex flex-col gap-1">
                    <div className="flex justify-between items-center">
                      <span className={cn(
                        "text-[9px] font-bold uppercase px-1.5 py-0.5 rounded",
                        log.type === 'DECISION' ? "bg-cyber-blue/20 text-cyber-blue" :
                        log.type === 'LEARNING' ? "bg-cyber-green/20 text-cyber-green" :
                        log.type === 'CURIOSITY' ? "bg-cyber-amber/20 text-cyber-amber" :
                        log.type === 'SWARM' ? "bg-purple-500/20 text-purple-400" :
                        "bg-slate-800 text-slate-300"
                      )}>
                        {log.type}
                      </span>
                      <span className="text-[9px] text-slate-500 font-mono">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-slate-300 font-mono text-[10px] leading-relaxed">{log.message}</p>
                    {log.confidence && (
                      <div className="flex items-center gap-2 mt-1">
                        <div className="h-1 flex-1 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-cyber-blue" 
                            style={{ width: `${Math.min(100, Math.max(0, log.confidence * 100))}%` }}
                          />
                        </div>
                        <span className="text-[8px] text-cyber-blue font-mono">{(log.confidence * 100).toFixed(0)}%</span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </div>

      {/* Center Column: Terminal & Charts */}
      <div className="xl:col-span-6 space-y-6 flex flex-col">
        
        {/* Terminal Console (Virtualization Applied) */}
        <section className="cyber-card flex flex-col flex-1 min-h-[400px] shadow-cyber-green/5">
          <div className="bg-cyber-surface/80 px-4 py-3 border-b border-cyber-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TerminalIcon className="w-4 h-4 text-cyber-green" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">c2@kali:~/attack_unit</span>
            </div>
            <div className="flex gap-3 items-center">
              <button 
                onClick={() => setShowTerminal(!showTerminal)}
                className="text-[9px] font-bold uppercase tracking-tighter px-2 py-0.5 rounded border border-cyber-border hover:bg-white/5 transition-colors text-slate-500"
              >
                {showTerminal ? "إخفاء الترمنال" : "إظهار الترمنال"}
              </button>
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-slate-800" />
                <div className="w-2.5 h-2.5 rounded-full bg-slate-800" />
                <div className="w-2.5 h-2.5 rounded-full bg-cyber-green/50" />
              </div>
            </div>
          </div>
          
          {showTerminal ? (
            <div className="flex-1 p-4 font-mono text-[13px] bg-black/20">
              {logs.length === 0 ? (
                <div className="text-slate-700 italic h-full flex items-center justify-center">في انتظار البدء...</div>
              ) : (
                <Virtuoso
                  className="custom-scrollbar h-full w-full"
                  data={logs}
                  followOutput="smooth"
                  itemContent={(index, log) => (
                    <div className="flex gap-3 group border-b border-white/5 py-1 items-start">
                      <span className="text-slate-700 shrink-0 select-none opacity-50 group-hover:opacity-100 transition-opacity">[{log.timestamp}]</span>
                      <div className={cn(
                        "whitespace-pre-wrap break-all leading-relaxed",
                        log.type === 'success' && "text-cyber-green",
                        log.type === 'error' && "text-cyber-red",
                        log.type === 'warning' && "text-cyber-amber",
                        log.type === 'refinement' && "text-cyber-blue font-bold border-l-2 border-cyber-blue pl-2",
                        log.type === 'critical' && "text-white bg-cyber-red/30 px-2 py-0.5 rounded border border-cyber-red/20",
                        log.type === 'info' && "text-slate-300"
                      )}>
                        {log.message}
                      </div>
                    </div>
                  )}
                />
              )}
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-4 bg-black/20">
              <div className="w-12 h-12 rounded-full border-2 border-dashed border-cyber-border animate-spin flex items-center justify-center">
                <Activity className="w-6 h-6 text-cyber-green/30" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">الترمنال مخفي لتقليل استهلاك المعالج</p>
                <p className="text-[10px] text-slate-600 mt-1">يتم تسجيل البيانات في الخلفية</p>
              </div>
            </div>
          )}
        </section>

        {/* Evolution Chart */}
        <section className="cyber-card p-5 h-[280px]">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <BarChart3 className="w-3.5 h-3.5 text-cyber-green" /> تقدم التطور
            </h3>
            <div className="flex items-center gap-4 text-[10px] uppercase font-bold tracking-wider">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-cyber-green" />
                <span className="text-slate-500">درجة اللياقة</span>
              </div>
            </div>
          </div>
          
          <div className="h-[180px] w-full">
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <AreaChart data={stats}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis 
                  dataKey="gen" 
                  stroke="#475569" 
                  fontSize={10} 
                  tickLine={false} 
                  axisLine={false}
                  label={{ value: 'Generation', position: 'insideBottom', offset: -5, fontSize: 10, fill: '#475569' }}
                />
                <YAxis 
                  stroke="#475569" 
                  fontSize={10} 
                  tickLine={false} 
                  axisLine={false}
                  domain={[0, 1]}
                />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0f1115', border: '1px solid #1e293b', borderRadius: '8px', fontSize: '10px' }}
                  itemStyle={{ color: '#10b981' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorScore)" 
                  animationDuration={1000}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      {/* Right Column: Exploits & Loot */}
      <div className="xl:col-span-3 space-y-6">
        
        {/* Evolution Tree Visualization */}
        <section className="cyber-card p-5 flex flex-col h-[380px]">
          <div className="flex items-center justify-between border-b border-cyber-border pb-3 mb-4">
            <h3 className="text-xs font-bold text-cyber-amber uppercase tracking-widest flex items-center gap-2">
              <GitGraph className="w-3.5 h-3.5" /> شجرة تطور الحمولات
            </h3>
            <span className="text-[10px] text-slate-500 font-mono">آخر 100 طفرة</span>
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {lineage.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 space-y-2 opacity-50">
                <GitGraph className="w-8 h-8" />
                <p className="text-[10px] uppercase tracking-widest font-bold">لا توجد بيانات تطور بعد</p>
              </div>
            ) : (
              lineage.map((item, idx) => (
                <div key={idx} className="bg-black/40 border border-cyber-border rounded p-2 text-[10px] font-mono">
                  <div className="text-slate-500 truncate mb-1" title={item.parent}>
                    <ChevronRight className="w-3 h-3 inline text-cyber-amber" /> {item.parent}
                  </div>
                  <div className="text-cyber-green truncate pl-3 border-l border-cyber-border" title={item.payload}>
                    {item.payload}
                  </div>
                  <div className="flex justify-between mt-2 pl-3">
                    <span className="text-slate-600">{item.status}</span>
                    <span className="text-cyber-blue font-bold">{(item.score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Successful Exploits */}
        <section className="cyber-card p-5 flex flex-col h-[380px]">
          <div className="flex items-center justify-between border-b border-cyber-border pb-3 mb-4">
            <h3 className="text-xs font-bold text-cyber-green uppercase tracking-widest flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5" /> مستودع الثغرات المكتشفة
            </h3>
            <span className="px-2 py-0.5 bg-cyber-green/10 text-cyber-green rounded text-[10px] font-bold">
              إجمالي {savedExploits.length}
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar">
            {savedExploits.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 space-y-3 opacity-50">
                <Database className="w-8 h-8" />
                <p className="text-[10px] uppercase tracking-widest font-bold">لا توجد بيانات محفوظة</p>
              </div>
            ) : (
              savedExploits.map((exploit, idx) => (
                <div key={idx} className="group relative bg-black/60 border border-cyber-green/20 rounded-lg p-3 hover:border-cyber-green/50 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[9px] font-bold text-cyber-green uppercase tracking-wider bg-cyber-green/10 px-1.5 py-0.5 rounded">
                      {exploit.type}
                    </span>
                    <span className="text-[9px] text-slate-500">{new Date(exploit.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <code className="block text-xs font-mono text-slate-300 break-all">
                    {exploit.payload}
                  </code>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

    </div>
  );
}
