import React, { useEffect, useRef } from 'react';
import { Play, Square, Globe, Shield, Zap, Target, Terminal as TerminalIcon } from 'lucide-react';
import { useAttack } from '../context/AttackContext';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';

const formatLogLine = (log: string) => {
  if (typeof log !== 'string') return log;
  
  // 1. Identify context prefixes and baseline color
  let prefix = null;
  let content = log;
  let baseColorClass = "text-[#10b981]/80";

  if (log.includes('[ERROR]') || log.includes('[!]')) {
    baseColorClass = "text-red-400/90";
  }

  if (log.startsWith('[*]')) {
    prefix = <span className="text-cyan-400 font-bold ml-1.5">[*]</span>;
    content = log.substring(3);
  } else if (log.startsWith('[+]')) {
    prefix = <span className="text-emerald-400 font-bold ml-1.5">[+]</span>;
    content = log.substring(3);
  } else if (log.startsWith('[!]')) {
    prefix = <span className="text-red-500 font-bold ml-1.5">[!]</span>;
    content = log.substring(3);
  } else if (log.startsWith('[?]')) {
    prefix = <span className="text-yellow-400 font-bold ml-1.5">[?]</span>;
    content = log.substring(3);
  }

  // 2. Syntax highlight the remaining content
  // SQL Keywords
  const keywords = ['SELECT', 'UNION', 'ALL', 'OR', 'AND', 'XOR', 'WHERE', 'FROM', 'DATABASE', 'USER', 'VERSION', 'ORDER BY', 'GROUP BY', 'LIMIT', 'OFFSET', 'HAVING', 'SLEEP', 'BENCHMARK', 'CONNECTION_ID', 'LOAD_FILE'];
  
  // Regex to split by keywords, numbers, hex, quotes and backticks
  const parts = content.split(/(\b(?:SELECT|UNION|ALL|OR|AND|XOR|WHERE|FROM|DATABASE|USER|VERSION|ORDER BY|GROUP BY|LIMIT|OFFSET|HAVING|SLEEP|BENCHMARK|CONNECTION_ID|LOAD_FILE)\b|\b\d+\b|0x[0-9a-fA-F]+|'[^']*'|"[^"]*"|`[^`]*`)/gi);

  return (
    <div className={`flex flex-wrap items-center ${baseColorClass}`}>
      <span className="text-slate-600 ml-2">&lt;</span>
      {prefix}
      {parts.map((part, i) => {
        const upper = part.toUpperCase();
        if (keywords.includes(upper)) return <span key={i} className="text-yellow-400 font-bold mx-0.5">{part}</span>;
        if (/^\d+$/.test(part)) return <span key={i} className="text-purple-400 mx-0.5">{part}</span>;
        if (part.startsWith('0x')) return <span key={i} className="text-orange-400 font-mono mx-0.5">{part}</span>;
        if (part.startsWith("'") || part.startsWith('"') || part.startsWith('`')) return <span key={i} className="text-blue-300 italic mx-0.5">{part}</span>;
        
        // Highlight error segments
        if (/Unknown column|syntax error|doesn't exist|failed|denied|forbidden/i.test(part)) {
          return <span key={i} className="text-red-400 font-bold underline decoration-dotted mx-0.5">{part}</span>;
        }
        
        if (/success|bypassed|confirmed/i.test(part)) {
          return <span key={i} className="text-emerald-400 font-bold mx-0.5">{part}</span>;
        }
        
        return <span key={i}>{part}</span>;
      })}
    </div>
  );
};

export default function Sandbox() {
  const {
    url, setUrl,
    username, setUsername,
    password, setPassword,
    security, setSecurity,
    population, setPopulation,
    generations, setGenerations,
    isAttacking,
    logs,
    startAttack,
    stopAttack
  } = useAttack();

  const virtuosoRef = useRef<VirtuosoHandle>(null);

  useEffect(() => {
    if (virtuosoRef.current && logs.length > 0) {
      virtuosoRef.current.scrollToIndex({
        index: logs.length - 1,
        behavior: 'smooth'
      });
    }
  }, [logs]);

  const resetIntelligence = async () => {
    if (!window.confirm('هل أنت متأكد من رغبتك في إعادة ضبط ذكاء الوكيل؟ سيتم مسح جميع الخبرات المكتسبة والحمولات الناجحة.')) return;
    
    try {
      const response = await fetch('/api/reset-intelligence', { method: 'POST' });
      if (response.ok) {
        alert('تمت إعادة ضبط ذكاء الوكيل بنجاح.');
        window.location.reload(); // Refresh to clear local state and logs
      } else {
        alert('فشل في إعادة ضبط الذكاء.');
      }
    } catch (error) {
      alert('خطأ في الاتصال بالخادم.');
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
      {/* Configuration Panel */}
      <div className="lg:col-span-1 space-y-6">
        <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6">
          <h2 className="text-lg font-mono text-white mb-4 flex items-center">
            <Target className="w-5 h-5 ml-2 text-[#10b981]" />
            إعدادات الهجوم
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">رابط الهدف</label>
              <div className="relative">
                <Globe className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input 
                  type="text" 
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full bg-black/40 border border-[#10b981]/20 rounded-lg pr-10 pl-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-[#10b981]/50 transition-all font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">اسم المستخدم</label>
                <input 
                  type="text" 
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-black/40 border border-[#10b981]/20 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none font-mono" 
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">كلمة المرور</label>
                <input 
                  type="password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-black/40 border border-[#10b981]/20 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none font-mono" 
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">مستوى الحماية</label>
              <select 
                value={security}
                onChange={(e) => setSecurity(e.target.value)}
                className="w-full bg-black/40 border border-[#10b981]/20 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none font-mono"
              >
                <option value="low">منخفض (Low)</option>
                <option value="medium">متوسط (Medium)</option>
                <option value="high">عالي (High)</option>
                <option value="impossible">مستحيل (Impossible)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">حجم المجتمع</label>
                <input 
                  type="number" 
                  value={population}
                  onChange={(e) => setPopulation(parseInt(e.target.value))}
                  className="w-full bg-black/40 border border-[#10b981]/20 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none font-mono" 
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">عدد الأجيال</label>
                <input 
                  type="number" 
                  value={generations}
                  onChange={(e) => setGenerations(parseInt(e.target.value))}
                  className="w-full bg-black/40 border border-[#10b981]/20 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none font-mono" 
                />
              </div>
            </div>

            <div className="pt-4 space-y-3">
              {!isAttacking ? (
                <button 
                  onClick={startAttack}
                  disabled={!url}
                  className="w-full bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/30 py-3 rounded-lg font-mono font-bold flex items-center justify-center gap-2 hover:bg-[#10b981]/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed group shadow-[0_0_15px_rgba(16,185,129,0.1)]"
                >
                  <Play className="w-4 h-4 fill-current group-hover:scale-110 transition-transform" />
                  بدء الهجوم
                </button>
              ) : (
                <button 
                  onClick={stopAttack}
                  className="w-full bg-red-500/10 text-red-500 border border-red-500/30 py-3 rounded-lg font-mono font-bold flex items-center justify-center gap-2 hover:bg-red-500/20 transition-all group"
                >
                  <Square className="w-4 h-4 fill-current" />
                  إنهاء
                </button>
              )}

              <button 
                onClick={resetIntelligence}
                className="w-full bg-slate-800/50 text-slate-400 border border-slate-700 py-2 rounded-lg font-mono text-xs flex items-center justify-center gap-2 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/30 transition-all"
              >
                <Zap className="w-3 h-3" />
                إعادة ضبط ذكاء الوكيل
              </button>
            </div>
          </div>
        </div>

        <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6">
          <h2 className="text-sm font-mono text-white mb-4 flex items-center">
            <Shield className="w-4 h-4 ml-2 text-[#10b981]" />
            استراتيجيات التجاوز
          </h2>
          <div className="space-y-2">
            {[
              { en: 'AST Mutation', ar: 'طفرة AST' },
              { en: 'Genetic Crossover', ar: 'التداخل الجيني' },
              { en: 'WAF Fingerprinting', ar: 'بصمة WAF' },
              { en: 'Context Awareness', ar: 'الوعي بالسياق' }
            ].map(s => (
              <div key={s.en} className="flex items-center justify-between text-xs font-mono py-1 border-b border-[#10b981]/5">
                <span className="text-slate-400">{s.ar}</span>
                <span className="text-[#10b981]">مفعل</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Terminal / Logs Panel */}
      <div className="lg:col-span-2 flex flex-col bg-black border border-[#10b981]/20 rounded-lg overflow-hidden">
        <div className="bg-[#0a0a0a] border-b border-[#10b981]/20 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-2 space-x-reverse">
            <TerminalIcon className="w-4 h-4 text-[#10b981]" />
            <span className="text-xs font-mono text-slate-400">Prometheus_Console v1.0.4</span>
          </div>
          <div className="flex space-x-1.5 space-x-reverse">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/40"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/40"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/40"></div>
          </div>
        </div>
        
        <div className="flex-1 font-mono text-xs custom-scrollbar bg-[#050505]">
          {logs.length === 0 ? (
            <div className="p-4 text-slate-600 italic">في انتظار تشغيل النظام...</div>
          ) : (
            <Virtuoso
              ref={virtuosoRef}
              data={logs}
              totalCount={logs.length}
              itemContent={(index, log) => (
                <div key={index} className="py-0.5">
                  {formatLogLine(log)}
                </div>
              )}
              followOutput="smooth"
              style={{ height: '100%' }}
            />
          )}
          {isAttacking && logs.length > 0 && (
            <div className="px-4 py-1 text-[#10b981]">
              <span className="text-slate-600 ml-2">&lt;</span>
              جاري تنفيذ دورات التطور...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
