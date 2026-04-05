import React, { useState, useEffect, useRef } from 'react';
import { Terminal, ShieldAlert, ShieldCheck, Activity, Database, Search, Terminal as TerminalIcon, Play, Square, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { IslandManager, Individual } from '../core/IslandManager';
import { DataExtractor } from '../utils/DataExtractor';

// Simulated Target (DVWA-like)
const simulateTargetResponse = (payload: string): { body: string, status: number } => {
  const upper = payload.toUpperCase();
  let body = "<html><body><h1>User ID</h1>";
  let status = 200;

  // WAF logic (simulating DVWA Medium)
  if (payload.includes("'") || payload.includes('"')) {
    // DVWA Medium often filters quotes
    body += "<p>WAF Blocked: Potential SQL Injection detected.</p>";
    status = 403;
  } else if (upper.includes("UNION") && upper.includes("SELECT")) {
    if (upper.includes("USERS")) {
      body += "<pre>ID: 1\nFirst name: admin\nSurname: admin\nUser: admin\nPassword: 5f4dcc3b5aa765d61d8327deb882cf99</pre>";
    } else if (upper.includes("INFORMATION_SCHEMA")) {
      body += "<pre>table_name: users\ntable_name: guestbook</pre>";
    } else {
      body += "<pre>ID: 1\nFirst name: admin\nSurname: admin</pre>";
    }
  } else if (upper.includes("OR 1=1") || upper.includes("OR TRUE")) {
    body += "<pre>ID: 1\nFirst name: admin\nSurname: admin\nID: 2\nFirst name: gordonb\nSurname: brown</pre>";
  } else {
    body += "<p>User ID 1 exists.</p>";
  }

  body += "</body></html>";
  return { body, status };
};

export default function PrometheusConsole() {
  const [logs, setLogs] = useState<{ msg: string, type: 'info' | 'success' | 'error' | 'warning' | 'critical' }[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentGen, setCurrentGen] = useState(0);
  const [winningPayload, setWinningPayload] = useState<string | null>(null);
  const [loot, setLoot] = useState<string | null>(null);
  
  const logEndRef = useRef<HTMLDivElement>(null);

  const addLog = (msg: string, type: 'info' | 'success' | 'error' | 'warning' | 'critical' = 'info') => {
    setLogs(prev => [...prev, { msg, type }]);
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
    setWinningPayload(null);
    setLoot(null);

    try {
      const response = await fetch('/api/run-prometheus');
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader available");

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
            
            // Check for winning payload in the stream
            if (line.includes('[!] Winning Payload:')) {
              const payload = line.split(': ')[1];
              setWinningPayload(payload);
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
    <div className="min-h-screen bg-black text-green-500 font-mono p-4 md:p-8 selection:bg-green-900 selection:text-white">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-green-900 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-900/20 rounded border border-green-500/30">
              <ShieldAlert className="w-8 h-8 text-green-400 animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tighter text-green-400">PROMETHEUS PROJECT</h1>
              <p className="text-xs text-green-700 uppercase tracking-widest font-bold">Unit 804 - Autonomous SQLi Evolution</p>
            </div>
          </div>
          
          <div className="flex gap-3">
            {!isRunning ? (
              <button 
                onClick={runPrometheus}
                className="flex items-center gap-2 bg-green-900/40 hover:bg-green-800/60 text-green-400 border border-green-500/50 px-6 py-2 rounded transition-all active:scale-95"
              >
                <Play className="w-4 h-4" /> INITIALIZE UNIT
              </button>
            ) : (
              <button 
                onClick={() => setIsRunning(false)}
                className="flex items-center gap-2 bg-red-900/40 hover:bg-red-800/60 text-red-400 border border-red-500/50 px-6 py-2 rounded transition-all active:scale-95"
              >
                <Square className="w-4 h-4" /> HALT EXECUTION
              </button>
            )}
          </div>
        </div>

        {/* Main Console */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Stats Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-zinc-900/50 border border-green-900/50 rounded p-4 space-y-4">
              <h3 className="text-xs font-bold text-green-700 uppercase border-b border-green-900/30 pb-2 flex items-center gap-2">
                <Activity className="w-3 h-3" /> System Status
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-green-800">Generation:</span>
                  <span className="text-green-400">{currentGen}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-green-800">Population:</span>
                  <span className="text-green-400">12</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-green-800">Target:</span>
                  <span className="text-green-400">DVWA (Medium)</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-green-800">Uptime:</span>
                  <span className="text-green-400">00:04:21</span>
                </div>
              </div>
            </div>

            <div className="bg-zinc-900/50 border border-green-900/50 rounded p-4 space-y-4">
              <h3 className="text-xs font-bold text-green-700 uppercase border-b border-green-900/30 pb-2 flex items-center gap-2">
                <Database className="w-3 h-3" /> Historical Wisdom
              </h3>
              <div className="text-[10px] text-green-800 leading-tight">
                Memory.db initialized with 9 golden payloads. 
                Experience manager tracking successful mutations.
              </div>
            </div>
          </div>

          {/* Terminal Output */}
          <div className="lg:col-span-3 bg-zinc-950 border border-green-900 rounded-lg overflow-hidden flex flex-col h-[600px] shadow-2xl shadow-green-900/10">
            <div className="bg-zinc-900 px-4 py-2 border-b border-green-900 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TerminalIcon className="w-4 h-4 text-green-600" />
                <span className="text-xs font-bold text-green-600">prometheus@kali:~/unit804</span>
              </div>
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-zinc-800"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-zinc-800"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-green-900/50"></div>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-1 scrollbar-thin scrollbar-thumb-green-900 scrollbar-track-transparent">
              <AnimatePresence initial={false}>
                {logs.map((log, i) => (
                  <motion.div 
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={cn(
                      "text-sm whitespace-pre-wrap break-all leading-relaxed",
                      log.type === 'success' && "text-emerald-400",
                      log.type === 'error' && "text-red-500",
                      log.type === 'warning' && "text-amber-400",
                      log.type === 'critical' && "text-white bg-red-900/40 px-2 py-1 rounded",
                      log.type === 'info' && "text-green-500"
                    )}
                  >
                    {log.msg}
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={logEndRef} />
            </div>
          </div>

        </div>

        {/* Loot Display */}
        {loot && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-emerald-950/20 border border-emerald-500/30 rounded-lg p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
              <h2 className="text-xl font-bold text-emerald-400">HARVESTED DATA (LOOT)</h2>
            </div>
            <pre className="text-emerald-300 text-sm overflow-x-auto whitespace-pre-wrap font-mono bg-black/40 p-4 rounded border border-emerald-500/10">
              {loot}
            </pre>
          </motion.div>
        )}

      </div>
    </div>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}
