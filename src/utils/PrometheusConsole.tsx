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
  AlertTriangle,
  GitGraph
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { GoogleGenAI, Type } from "@google/genai";
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

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

interface LogEntry {
  id: number;
  message: string;
  type: 'info' | 'success' | 'error' | 'warning' | 'critical' | 'refinement';
  timestamp: string;
}

export default function PrometheusConsole() {
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
  
  const logEndRef = useRef<HTMLDivElement>(null);

  const addLog = (message: string, type: 'info' | 'success' | 'error' | 'warning' | 'critical' | 'refinement' = 'info') => {
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

  useEffect(() => {
    fetchExploits();
  }, []);

  const fetchExploits = async () => {
    try {
      const res = await fetch('/api/exploits');
      const data = await res.json();
      setSavedExploits(data);
    } catch (e) {
      console.error("Failed to fetch exploits", e);
    }
  };

  const analyzeAndHint = async (payload: string, context: string) => {
    addLog("[AI] Analyzing stagnation. Consulting Gemini...", "warning");
    try {
      const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: `The SQL injection tool is stuck. 
        Current Best Payload: ${payload}
        Context: ${context}
        Suggest a mutation strategy (logical_alts, inline_comments, union_balance, junk_fill, context_aware, directed_bypass) 
        and a target keyword to bypass.`,
        config: {
          responseMimeType: "application/json",
          responseSchema: {
            type: Type.OBJECT,
            properties: {
              strategy: { type: Type.STRING },
              target_keyword: { type: Type.STRING },
              suggestion: { type: Type.STRING }
            },
            required: ["strategy", "target_keyword", "suggestion"]
          }
        }
      });

      const hint = JSON.parse(response.text || "{}");
      addLog(`[AI Insight] ${hint.suggestion}`, "success");
      
      // Send hint to backend
      await fetch('/api/hint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(hint)
      });
      addLog("[AI] Hint injected into next generation.", "info");
    } catch (e) {
      console.error("AI Analysis failed", e);
      addLog("[AI] Analysis failed. Continuing with standard evolution.", "error");
    }
  };

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
            let type: 'info' | 'success' | 'error' | 'warning' | 'critical' | 'refinement' = 'info';
            if (line.includes('[!!!]') || line.includes('CRITICAL')) type = 'critical';
            else if (line.includes('[+]') || line.includes('SUCCESSFUL')) type = 'success';
            else if (line.includes('[REFINEMENT]')) type = 'refinement';
            else if (line.includes('[!]')) type = 'error';
            else if (line.includes('[*]') || line.includes('[SKIPPED]')) type = 'warning';
            
            addLog(line, type);
            
            if (line.includes('[ANALYSIS_REQUIRED]')) {
              const payloadMatch = line.match(/Payload: (.*?) \|/);
              if (payloadMatch) {
                analyzeAndHint(payloadMatch[1], "Stagnation detected in evolution");
              }
            }
            
            if (line.includes('[*] Stealth Mode Active')) {
              setIsStealthMode(true);
            } else if (line.includes('[!] Stagnation detected') || line.includes('Injecting chaos')) {
              setIsChaosMode(true);
            } else if (line.includes('Score:') && parseFloat(line.match(/Score: ([\d.]+)/)?.[1] || "0") > 0.1) {
              setIsStealthMode(false);
              setIsChaosMode(false);
            }
            
            if (line.includes('[*] WAF DETECTED:')) {
              const wafMatch = line.match(/WAF DETECTED: (.*)/);
              if (wafMatch) setWafInfo(wafMatch[1]);
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
              fetchExploits(); // Refresh from DB
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

  const fetchLineage = async () => {
    try {
      const res = await fetch('/api/lineage');
      const data = await res.json();
      setLineage(data);
    } catch (err) {
      console.error("Error fetching lineage:", err);
    }
  };

  useEffect(() => {
    if (isRunning) {
      const interval = setInterval(fetchLineage, 5000);
      return () => clearInterval(interval);
    }
  }, [isRunning]);

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
                {wafInfo && (
                  <div className="flex items-center justify-between text-xs pt-2 border-t border-cyber-border/30">
                    <span className="text-cyber-blue font-bold">WAF المكتشف</span>
                    <span className="text-cyber-blue font-mono animate-pulse">{wafInfo}</span>
                  </div>
                )}
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
                <div className="flex-1 overflow-y-auto p-4 font-mono text-[13px] space-y-1 selection:bg-cyber-green/30">
                  {logs.length === 0 && (
                    <div className="text-slate-700 italic">في انتظار البدء...</div>
                  )}
                  {logs.map((log) => (
                    <div 
                      key={log.id}
                      className="flex gap-3 group border-b border-white/5 pb-1"
                    >
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
                  ))}
                  <div ref={logEndRef} />
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
                    <Activity className="w-8 h-8 animate-pulse" />
                    <p className="text-[10px] uppercase font-bold tracking-widest">في انتظار بدء التطور...</p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    {lineage.map((node, idx) => (
                      <div key={idx} className="group relative pl-4 border-l border-cyber-border/30 py-1 hover:border-cyber-amber/50 transition-colors">
                        <div className="absolute -left-[5px] top-3 w-2 h-2 rounded-full bg-cyber-border group-hover:bg-cyber-amber transition-colors" />
                        <div className="flex flex-col gap-0.5">
                          <div className="flex items-center gap-2">
                            <span className="text-[9px] text-slate-500 font-mono truncate max-w-[150px] opacity-60">
                              {node.parent.substring(0, 20)}...
                            </span>
                            <ChevronRight className="w-2 h-2 text-slate-700" />
                            <span className={cn(
                              "text-[10px] font-mono font-bold truncate max-w-[200px]",
                              node.score > 0.8 ? "text-cyber-green" : "text-slate-300"
                            )}>
                              {node.payload}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-[8px] uppercase tracking-tighter">
                            <span className="text-cyber-amber">Score: {(node.score * 100).toFixed(0)}%</span>
                            <span className="text-slate-600">{node.status}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>

            {/* Exploit Repository (Long-term Memory) */}
            <section className="cyber-card p-5 flex flex-col h-[400px]">
              <div className="flex items-center justify-between border-b border-cyber-border pb-3 mb-4">
                <h3 className="text-xs font-bold text-cyber-green uppercase tracking-widest flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5" /> مستودع الثغرات المكتشفة
                </h3>
                <span className="px-2 py-0.5 bg-cyber-green/10 rounded text-[10px] font-bold text-cyber-green">
                  {savedExploits.length} إجمالي
                </span>
              </div>
              
              <div className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar">
                {savedExploits.length === 0 && (
                  <div className="text-center py-10">
                    <Database className="w-8 h-8 text-slate-800 mx-auto mb-2 opacity-20" />
                    <p className="text-[10px] text-slate-600 uppercase font-bold">لا توجد بيانات محفوظة</p>
                  </div>
                )}
                {savedExploits.map((exploit, idx) => (
                  <div key={idx} className="p-3 bg-black/40 border border-cyber-border rounded-lg group hover:border-cyber-green/50 transition-colors">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-[9px] font-bold text-cyber-green bg-cyber-green/10 px-1.5 py-0.5 rounded uppercase">
                        {exploit.type}
                      </span>
                      <span className="text-[8px] text-slate-600 font-mono">
                        {new Date(exploit.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    <code className="text-[11px] text-slate-300 break-all font-mono block leading-relaxed">
                      {exploit.payload}
                    </code>
                  </div>
                ))}
              </div>
            </section>

            {/* Optimal Exploits (Current Session) */}
            <section className="cyber-card p-5 space-y-4 border-cyber-amber/20 bg-cyber-amber/5">
              <h3 className="text-xs font-bold text-cyber-amber uppercase tracking-widest flex items-center gap-2 border-b border-cyber-amber/20 pb-3">
                <Zap className="w-3.5 h-3.5" /> حمولات الجلسة الحالية ({winningPayloads.length})
              </h3>
              {winningPayloads.length > 0 ? (
                <div className="space-y-3 max-h-[200px] overflow-y-auto pr-2">
                  {winningPayloads.map((payload, idx) => (
                    <div key={idx} className="space-y-2">
                      <div className="p-2 bg-black/60 rounded border border-cyber-amber/30 font-mono text-[10px] text-cyber-amber break-all leading-relaxed">
                        {payload}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-24 flex flex-col items-center justify-center text-slate-600 space-y-2">
                  <Cpu className="w-6 h-6 opacity-20" />
                  <p className="text-[10px] font-bold uppercase tracking-widest">جاري البحث عن ثغرات...</p>
                </div>
              )}
            </section>

            {/* Harvested Data */}
            <section className="cyber-card p-5 flex flex-col h-[300px]">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2 border-b border-cyber-border pb-3 mb-4">
                <Database className="w-3.5 h-3.5 text-cyber-blue" /> البيانات المستخرجة
              </h3>
              
              <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                {loot ? (
                  <div className="space-y-4">
                    <div className="p-3 bg-cyber-blue/5 border border-cyber-blue/20 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <ShieldCheck className="w-3.5 h-3.5 text-cyber-blue" />
                        <span className="text-[10px] font-bold text-cyber-blue uppercase">تم اكتشاف الهيكل</span>
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
                      لا توجد بيانات مستخرجة بعد. <br/> في انتظار نجاح سلسلة الاستغلال.
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

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}
