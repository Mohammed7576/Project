import React, { useState, useEffect, useRef } from 'react';
import { 
  Terminal as TerminalIcon, 
  ShieldAlert, 
  ShieldCheck, 
  Activity, 
  Database, 
  Search, 
  Play, 
  Square, 
  Cpu, 
  Zap, 
  Lock, 
  Globe, 
  BarChart3,
  ChevronRight,
  AlertTriangle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

interface LogEntry {
  id: number;
  message: string;
  type: 'info' | 'success' | 'error' | 'warning' | 'critical';
  timestamp: string;
}

export default function PrometheusConsole() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentGen, setCurrentGen] = useState(0);
  const [winningPayloads, setWinningPayloads] = useState<string[]>([]);
  const [isStealthMode, setIsStealthMode] = useState(false);
  const [isChaosMode, setIsChaosMode] = useState(false);
  const [loot, setLoot] = useState<string | null>(null);
  const [targetConfig, setTargetConfig] = useState({
    url: 'http://localhost/',
    username: 'admin',
    password: 'password',
    security: 'medium',
    populationSize: '12',
    maxGenerations: '30'
  });
  const [stats, setStats] = useState<{gen: number, score: number}[]>([]);
  
  const logEndRef = useRef<HTMLDivElement>(null);

  const addLog = (message: string, type: 'info' | 'success' | 'error' | 'warning' | 'critical' = 'info') => {
    setLogs(prev => [...prev, { 
      id: Date.now() + Math.random(), 
      message, 
      timestamp: new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      type 
    }].slice(-100));
  };

  const scrollToBottom = () => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  const runPrometheus = async () => {
    setIsRunning(true);
    setLogs([]);
    setWinningPayloads([]);
    setLoot(null);
    setCurrentGen(0);
    setStats([]);

    addLog("Initializing Attack Unit...", "warning");
    addLog("Establishing secure tunnel to target...", "info");

    try {
      const params = new URLSearchParams({
        ...targetConfig,
        population: targetConfig.populationSize,
        generations: targetConfig.maxGenerations
      });
      const response = await fetch(`/api/run-prometheus?${params.toString()}`);
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader available");

      let lastScore = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');
        
        lines.forEach(line => {
          if (line.trim()) {
            let type: 'info' | 'success' | 'error' | 'warning' | 'critical' = 'info';
            if (line.includes('[!!!]') || line.includes('CRITICAL')) type = 'critical';
            else if (line.includes('[+]') || line.includes('SUCCESSFUL')) type = 'success';
            else if (line.includes('[!]')) type = 'error';
            else if (line.includes('[*]')) type = 'warning';
            
            addLog(line, type);
            
            if (line.includes('[*] Stealth Mode Active')) {
              setIsStealthMode(true);
            } else if (line.includes('[!] Stagnation detected') || line.includes('Injecting chaos')) {
              setIsChaosMode(true);
            } else if (line.includes('Score:') && parseFloat(line.match(/Score: ([\d.]+)/)?.[1] || "0") > 0.1) {
              setIsStealthMode(false);
              setIsChaosMode(false);
            }
            
            // Extract generation and score for stats
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
                  setStats(prev => [...prev, { gen: currentGen, score }]);
                }
              }
            }

            if (line.includes('[!!!] NEW EXPLOIT DISCOVERED:') || line.includes('[!] Winning Payload:')) {
              const payload = line.split(': ')[1];
              setWinningPayloads(prev => [...new Set([...prev, payload])]);
              setStats(prev => [...prev, { gen: currentGen + 1, score: 1.0 }]);
            }

            if (line.includes('--- [ Loot ] ---')) {
              // Simple heuristic to start capturing loot
              // In a real app, we might have a specific JSON marker
            }
          }
        });
      }
    } catch (err) {
      addLog(`[!] Connection Error: ${err}`, 'error');
    }

    setIsRunning(false);
  };

  return (
    <div className="min-h-screen relative overflow-hidden cyber-grid">
      {/* Visual Effects */}
      <div className="scanline pointer-events-none" />
      <div className="fixed inset-0 bg-gradient-to-b from-transparent via-cyber-bg/50 to-cyber-bg pointer-events-none" />

      <div className="relative z-20 max-w-[1600px] mx-auto p-4 lg:p-8 space-y-6">
        
        {/* Header Section */}
        <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 pb-6 border-b border-cyber-border">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="absolute inset-0 bg-cyber-green/20 blur-xl rounded-full" />
              <div className="relative p-3 bg-cyber-surface border border-cyber-green/30 rounded-xl">
                <ShieldAlert className={`w-8 h-8 text-cyber-green ${isRunning ? 'animate-pulse' : ''}`} />
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
          
          <div className="flex items-center gap-3 w-full lg:w-auto">
            {!isRunning ? (
              <button 
                onClick={runPrometheus}
                className="cyber-button cyber-button-primary w-full lg:w-auto"
              >
                <Play className="w-4 h-4 fill-current" /> تشغيل الوحدة
              </button>
            ) : (
              <button 
                onClick={() => setIsRunning(false)}
                className="cyber-button cyber-button-danger w-full lg:w-auto"
              >
                <Square className="w-4 h-4 fill-current" /> إيقاف التنفيذ
              </button>
            )}
          </div>
        </header>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          
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
                  <span className="text-slate-500">عمق الطفرة</span>
                  <span className="text-slate-300 font-mono">ديناميكي</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">حجم السكان</span>
                  <span className="text-slate-300 font-mono">{targetConfig.populationSize} وحدة</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">معدل النجاح</span>
                  <span className="text-slate-300 font-mono">{(stats.length > 0 ? (stats[stats.length-1].score * 100).toFixed(1) : 0)}%</span>
                </div>
              </div>
            </section>

            {/* Knowledge Base */}
            <section className="cyber-card p-5 bg-cyber-blue/5 border-cyber-blue/20">
              <h3 className="text-xs font-bold text-cyber-blue uppercase tracking-widest flex items-center gap-2 mb-3">
                <Database className="w-3.5 h-3.5" /> الحكمة التاريخية
              </h3>
              <p className="text-[11px] text-slate-400 leading-relaxed font-medium">
                Memory.db نشط. مدير الخبرة يتتبع <span className="text-cyber-blue">9 حمولات ذهبية</span>. 
                تطبيق التعلم المعزز من الطفرات الناجحة السابقة.
              </p>
            </section>
          </div>

          {/* Center Column: Terminal & Charts */}
          <div className="xl:col-span-6 space-y-6">
            
            {/* Terminal Console */}
            <section className="cyber-card flex flex-col h-[500px] shadow-cyber-green/5">
              <div className="bg-cyber-surface/80 px-4 py-3 border-b border-cyber-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TerminalIcon className="w-4 h-4 text-cyber-green" />
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">c2@kali:~/attack_unit</span>
                </div>
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-800" />
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-800" />
                  <div className="w-2.5 h-2.5 rounded-full bg-cyber-green/50" />
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 font-mono text-[13px] space-y-1.5 selection:bg-cyber-green/30">
                <AnimatePresence initial={false}>
                  {logs.length === 0 && (
                    <div className="text-slate-700 italic">Waiting for initialization...</div>
                  )}
                  {logs.map((log) => (
                    <motion.div 
                      key={log.id}
                      initial={{ opacity: 0, x: -4 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex gap-3 group"
                    >
                      <span className="text-slate-700 shrink-0 select-none opacity-50 group-hover:opacity-100 transition-opacity">[{log.timestamp}]</span>
                      <div className={cn(
                        "whitespace-pre-wrap break-all leading-relaxed",
                        log.type === 'success' && "text-cyber-green",
                        log.type === 'error' && "text-cyber-red",
                        log.type === 'warning' && "text-cyber-amber",
                        log.type === 'critical' && "text-white bg-cyber-red/30 px-2 py-0.5 rounded border border-cyber-red/20",
                        log.type === 'info' && "text-slate-300"
                      )}>
                        {log.message}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                <div ref={logEndRef} />
              </div>
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
                <ResponsiveContainer width="100%" height="100%">
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
                    <Tooltip 
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

          {/* Right Column: Loot & Analysis */}
          <div className="xl:col-span-3 space-y-6">
            
            {/* Winning Payloads */}
            <section className="cyber-card p-5 space-y-4 border-cyber-green/20 bg-cyber-green/5">
              <h3 className="text-xs font-bold text-cyber-green uppercase tracking-widest flex items-center gap-2 border-b border-cyber-green/20 pb-3">
                <Zap className="w-3.5 h-3.5" /> Optimal Exploits ({winningPayloads.length})
              </h3>
              {winningPayloads.length > 0 ? (
                <div className="space-y-3 max-h-[200px] overflow-y-auto pr-2">
                  {winningPayloads.map((payload, idx) => (
                    <div key={idx} className="space-y-2">
                      <div className="p-2 bg-black/60 rounded border border-cyber-green/30 font-mono text-[10px] text-cyber-green break-all leading-relaxed">
                        {payload}
                      </div>
                    </div>
                  ))}
                  <button className="w-full py-2 bg-cyber-green/10 hover:bg-cyber-green/20 text-cyber-green text-[10px] font-bold uppercase tracking-widest rounded border border-cyber-green/30 transition-colors">
                    Export All Payloads
                  </button>
                </div>
              ) : (
                <div className="h-24 flex flex-col items-center justify-center text-slate-600 space-y-2">
                  <Cpu className="w-6 h-6 opacity-20" />
                  <p className="text-[10px] font-bold uppercase tracking-widest">Searching for entry points...</p>
                </div>
              )}
            </section>

            {/* Harvested Data */}
            <section className="cyber-card p-5 flex flex-col h-[500px]">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2 border-b border-cyber-border pb-3 mb-4">
                <Database className="w-3.5 h-3.5 text-cyber-blue" /> Harvested Loot
              </h3>
              
              <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                {loot ? (
                  <div className="space-y-4">
                    <div className="p-3 bg-cyber-blue/5 border border-cyber-blue/20 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <ShieldCheck className="w-3.5 h-3.5 text-cyber-blue" />
                        <span className="text-[10px] font-bold text-cyber-blue uppercase">Schema Detected</span>
                      </div>
                      <pre className="text-[11px] text-slate-300 font-mono whitespace-pre-wrap">
                        {loot}
                      </pre>
                    </div>
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-slate-700 space-y-3 text-center px-4">
                    <AlertTriangle className="w-8 h-8 opacity-10" />
                    <p className="text-[10px] font-bold uppercase tracking-widest leading-relaxed">
                      No data exfiltrated yet. <br/> Awaiting successful exploit chain.
                    </p>
                  </div>
                )}
              </div>
            </section>
          </div>

        </div>

        {/* Footer Info */}
        <footer className="flex justify-between items-center text-[10px] text-slate-600 font-bold uppercase tracking-[0.2em] pt-4 border-t border-cyber-border">
          <div className="flex gap-6">
            <span>System: Linux x86_64</span>
            <span>Kernel: 6.5.0-kali-amd64</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-cyber-green animate-pulse" />
            <span>Encrypted Connection Active</span>
          </div>
        </footer>

      </div>
    </div>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}
