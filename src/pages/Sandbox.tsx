import React, { useState } from 'react';
import { Play, Square, Globe, Shield, Zap, Target, Terminal as TerminalIcon } from 'lucide-react';

export default function Sandbox() {
  const [url, setUrl] = useState('');
  const [isAttacking, setIsAttacking] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  const startAttack = async () => {
    if (!url) return;
    setIsAttacking(true);
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Initializing Prometheus Engine...`]);
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Target set to: ${url}`]);
    
    try {
      // In a real scenario, this would call /api/run-prometheus
      // For now, we simulate the connection
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Phase 1: Context Discovery active...`]);
    } catch (error) {
      setLogs(prev => [...prev, `[ERROR] Failed to connect to engine.`]);
      setIsAttacking(false);
    }
  };

  const stopAttack = () => {
    setIsAttacking(false);
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Attack terminated by user.`]);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
      {/* Configuration Panel */}
      <div className="lg:col-span-1 space-y-6">
        <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6">
          <h2 className="text-lg font-mono text-white mb-4 flex items-center">
            <Target className="w-5 h-5 mr-2 text-[#10b981]" />
            Attack Configuration
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Target URL</label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input 
                  type="text" 
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/search.php?id=1"
                  className="w-full bg-black/40 border border-[#10b981]/20 rounded-lg pl-10 pr-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-[#10b981]/50 transition-all font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Population</label>
                <input type="number" defaultValue={12} className="w-full bg-black/40 border border-[#10b981]/20 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none font-mono" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Generations</label>
                <input type="number" defaultValue={50} className="w-full bg-black/40 border border-[#10b981]/20 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none font-mono" />
              </div>
            </div>

            <div className="pt-4">
              {!isAttacking ? (
                <button 
                  onClick={startAttack}
                  disabled={!url}
                  className="w-full bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/30 py-3 rounded-lg font-mono font-bold flex items-center justify-center gap-2 hover:bg-[#10b981]/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed group shadow-[0_0_15px_rgba(16,185,129,0.1)]"
                >
                  <Play className="w-4 h-4 fill-current group-hover:scale-110 transition-transform" />
                  LAUNCH ATTACK
                </button>
              ) : (
                <button 
                  onClick={stopAttack}
                  className="w-full bg-red-500/10 text-red-500 border border-red-500/30 py-3 rounded-lg font-mono font-bold flex items-center justify-center gap-2 hover:bg-red-500/20 transition-all group"
                >
                  <Square className="w-4 h-4 fill-current" />
                  TERMINATE
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6">
          <h2 className="text-sm font-mono text-white mb-4 flex items-center">
            <Shield className="w-4 h-4 mr-2 text-[#10b981]" />
            Bypass Strategies
          </h2>
          <div className="space-y-2">
            {['AST Mutation', 'Genetic Crossover', 'WAF Fingerprinting', 'Context Awareness'].map(s => (
              <div key={s} className="flex items-center justify-between text-xs font-mono py-1 border-b border-[#10b981]/5">
                <span className="text-slate-400">{s}</span>
                <span className="text-[#10b981]">ENABLED</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Terminal / Logs Panel */}
      <div className="lg:col-span-2 flex flex-col bg-black border border-[#10b981]/20 rounded-lg overflow-hidden">
        <div className="bg-[#0a0a0a] border-b border-[#10b981]/20 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TerminalIcon className="w-4 h-4 text-[#10b981]" />
            <span className="text-xs font-mono text-slate-400">Prometheus_Console v1.0.4</span>
          </div>
          <div className="flex space-x-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/40"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/40"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/40"></div>
          </div>
        </div>
        
        <div className="flex-1 p-4 font-mono text-xs overflow-y-auto space-y-1 custom-scrollbar bg-[#050505]">
          {logs.length === 0 && (
            <div className="text-slate-600 italic">Waiting for system launch...</div>
          )}
          {logs.map((log, i) => (
            <div key={i} className={log.includes('[ERROR]') ? 'text-red-400' : 'text-[#10b981]/80'}>
              <span className="text-slate-600 mr-2">&gt;</span>
              {log}
            </div>
          ))}
          {isAttacking && (
            <div className="text-[#10b981] animate-pulse">
              <span className="text-slate-600 mr-2">&gt;</span>
              Executing evolution cycles...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
