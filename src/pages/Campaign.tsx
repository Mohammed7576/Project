import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Play, Square, Globe, Shield, Zap, Target, Terminal as TerminalIcon, Activity, Flame } from 'lucide-react';
import { useAttack } from '../context/AttackContext';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';

const formatLogLine = (log: string) => {
  if (typeof log !== 'string') return log;
  
  let content = log.trim();
  let badge = null;
  let baseColorClass = "text-slate-300";

  if (content.startsWith('< ')) content = content.substring(2);
  if (content.startsWith('> ')) content = content.substring(2);

  const badgeMatch = content.match(/^\[(.*?)\]\s*(.*)/);
  if (badgeMatch) {
    const rawTag = badgeMatch[1];
    content = badgeMatch[2];
    
    let badgeBg = "bg-slate-700 text-slate-300 border-slate-600";
    if (rawTag.includes('SUCCESS') || rawTag.includes('+')) badgeBg = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    else if (rawTag.includes('ERROR') || rawTag.includes('FAIL') || rawTag.includes('!') || rawTag.includes('BLOCK')) badgeBg = "bg-red-500/10 text-red-400 border-red-500/30";
    else if (rawTag.includes('BIASED') || rawTag.includes('MUTATION') || rawTag.includes('?')) badgeBg = "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
    else if (rawTag.includes('*') || rawTag.includes('INFO') || rawTag.includes('ISLAND')) badgeBg = "bg-blue-500/10 text-blue-400 border-blue-500/30";

    let tagText = rawTag
      .replace(/_/g, ' ')
      .replace(/MASS DATA DUMP/g, 'DATA DUMP')
      .replace(/SUCCESS/g, 'PASS');

    badge = (
      <span className={`inline-block px-1.5 py-0.5 rounded border text-[9px] font-bold tracking-wider ml-1.5 shrink-0 ${badgeBg}`} dir="ltr">
        {tagText}
      </span>
    );
  }

  let suffix = null;
  const suffixMatch = content.match(/(.*)\s+\[(\d+)\s+Island\]$/i);
  if (suffixMatch) {
    content = suffixMatch[1];
    suffix = (
      <span className="mr-2 px-1.5 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded text-[8px] font-mono shrink-0">
        Island {suffixMatch[2]}
      </span>
    );
  }

  const keywords = ['SELECT', 'UNION', 'ALL', 'OR', 'AND', 'XOR', 'WHERE', 'FROM', 'DATABASE', 'USER', 'VERSION', 'ORDER BY', 'GROUP BY', 'LIMIT', 'OFFSET', 'HAVING', 'SLEEP', 'BENCHMARK', 'CONNECTION_ID', 'LOAD_FILE', 'TRUE', 'FALSE', 'NULL', 'LIKE', 'RLIKE', 'REGEXP'];
  const parts = content.split(/(\b(?:SELECT|UNION|ALL|OR|AND|XOR|WHERE|FROM|DATABASE|USER|VERSION|ORDER BY|GROUP BY|LIMIT|OFFSET|HAVING|SLEEP|BENCHMARK|CONNECTION_ID|LOAD_FILE|TRUE|FALSE|NULL|LIKE|RLIKE|REGEXP)\b|\b\d+\b|0x[0-9a-fA-F]+|'[^']*'|"[^"]*"|`[^`]*`|--\s*.*$|#.*$|\/\*[\s\S]*?\*\/)/gi);

  return (
    <div className={`flex flex-wrap sm:flex-nowrap items-start sm:items-center py-1 ${baseColorClass} w-full`}>
      <span className="text-slate-600 shrink-0 opacity-50 mt-0.5 sm:mt-0 font-mono text-[10px]">&gt;</span>
      {badge}
      <div className="flex-1 min-w-0 font-mono tracking-tight leading-relaxed break-all mx-2" dir="ltr">
        {parts.map((part, i) => {
          if (!part) return null;
          const upper = part.toUpperCase();
          if (keywords.includes(upper)) return <span key={i} className="text-pink-400 font-bold mx-0.5">{part}</span>;
          if (/^\d+$/.test(part)) return <span key={i} className="text-purple-400 mx-0.5">{part}</span>;
          if (part.startsWith('0x')) return <span key={i} className="text-orange-400 font-mono mx-0.5">{part}</span>;
          if (part.startsWith("'") || part.startsWith('"') || part.startsWith('`')) return <span key={i} className="text-emerald-300 mx-0.5">{part}</span>;
          if (part.startsWith('--') || part.startsWith('#') || part.startsWith('/*')) return <span key={i} className="text-slate-500 italic mx-0.5">{part}</span>;
          return <span key={i} className="opacity-90">{part}</span>;
        })}
      </div>
      {suffix}
    </div>
  );
};

export default function Campaign() {
  const {
    url, setUrl,
    username, setUsername,
    password, setPassword,
    security, setSecurity,
    population, setPopulation,
    generations, setGenerations,
    targetName, setTargetName,
    isAttacking,
    learningLogs,
    successLogs,
    systemLogs,
    currentGeneration,
    elapsedTime,
    startAttack,
    stopAttack
  } = useAttack();

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const [windowVisibility, setWindowVisibility] = React.useState({
    CONTROLS: true,
    LEARNING: true,
    SUCCESS: true,
    ENGINE: true
  });

  const [summary, setSummary] = React.useState({ successfulPayloads: 0, sqlErrorPayloads: 0, totalPayloads: 0 });

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await fetch('/api/stats-summary');
        if (res.ok) setSummary(await res.json());
      } catch (e) {}
    };
    fetchSummary();
    const inv = setInterval(fetchSummary, 5000);
    return () => clearInterval(inv);
  }, []);

  const toggleWindow = (win: keyof typeof windowVisibility) => {
    setWindowVisibility(prev => ({ ...prev, [win]: !prev[win] }));
  };

  const learningRef = useRef<VirtuosoHandle>(null);
  const successRef = useRef<VirtuosoHandle>(null);
  const systemRef = useRef<VirtuosoHandle>(null);

  useEffect(() => {
    if (learningRef.current && learningLogs.length > 0) {
      learningRef.current.scrollToIndex({ index: learningLogs.length - 1, behavior: 'auto' });
    }
  }, [learningLogs]);

  useEffect(() => {
    if (successRef.current && successLogs.length > 0) {
      successRef.current.scrollToIndex({ index: successLogs.length - 1, behavior: 'auto' });
    }
  }, [successLogs]);

  useEffect(() => {
    if (systemRef.current && systemLogs.length > 0) {
      systemRef.current.scrollToIndex({ index: systemLogs.length - 1, behavior: 'auto' });
    }
  }, [systemLogs]);

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="bg-[#0a0a0a] border border-red-500/20 rounded-xl shadow-2xl overflow-hidden sticky top-0 z-50">
        <div className="bg-red-500/5 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-red-500/10">
          <div className="flex items-center gap-5">
            <div className="flex flex-col">
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <Flame className="w-5 h-5 text-red-500" />
                <span>حملة الاختراق الفعلي (Elite Attack Campaign)</span>
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <div className={`w-1.5 h-1.5 rounded-full ${isAttacking ? 'bg-red-500 animate-pulse' : 'bg-slate-700'}`}></div>
                <span className={`text-[9px] font-mono tracking-widest uppercase ${isAttacking ? 'text-red-400' : 'text-slate-500'}`}>
                  {isAttacking ? 'Offensive Swarm Active' : 'Waiting for Deployment'}
                </span>
              </div>
            </div>

            <div className="h-10 w-[1px] bg-red-500/10 hidden lg:block"></div>

            <div className="hidden sm:flex items-center gap-6">
              <div className="flex flex-col">
                <span className="text-[8px] text-slate-500 uppercase font-bold tracking-tighter">Exploit Gen</span>
                <div className="flex items-center gap-2 text-red-400">
                  <Zap className="w-3 h-3" />
                  <span className="text-sm font-mono">{currentGeneration}</span>
                </div>
              </div>
              <div className="flex flex-col">
                <span className="text-[8px] text-slate-500 uppercase font-bold tracking-tighter">Mission Time</span>
                <div className="flex items-center gap-2 text-white">
                  <Activity className={`w-3 h-3 ${isAttacking ? 'text-red-500' : 'text-slate-600'}`} />
                  <span className="text-sm font-mono">{formatTime(elapsedTime)}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {!isAttacking ? (
              <button 
                onClick={() => startAttack('attack')}
                disabled={!url}
                className="bg-red-600 text-white px-6 py-2.5 rounded-lg font-mono text-[11px] font-bold hover:bg-red-700 transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(239,68,68,0.2)] disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                بدء حملة الهجوم (EXECUTE)
              </button>
            ) : (
              <button 
                onClick={stopAttack}
                className="bg-slate-800 text-white border border-slate-700 px-6 py-2.5 rounded-lg font-mono text-[11px] font-bold hover:bg-slate-700 transition-all flex items-center gap-2"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                إلغاء الحملة (ABORT)
              </button>
            )}
          </div>
        </div>

        <div className="px-4 py-2 bg-black/40 flex items-center gap-2 overflow-x-auto no-scrollbar">
           <NavButton active={windowVisibility.CONTROLS} onClick={() => toggleWindow('CONTROLS')} icon={Target} label="الهدف" subLabel="TARGET" color="text-red-400" />
           <NavButton active={windowVisibility.LEARNING} onClick={() => toggleWindow('LEARNING')} icon={Zap} label="الاختراق" subLabel="BYPASS" color="text-yellow-400" />
           <NavButton active={windowVisibility.SUCCESS} onClick={() => toggleWindow('SUCCESS')} icon={Flame} label="الغنائم" subLabel="LOOT" color="text-emerald-400" />
           <NavButton active={windowVisibility.ENGINE} onClick={() => toggleWindow('ENGINE')} icon={TerminalIcon} label="القيادة" subLabel="CNC" color="text-blue-400" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1 min-h-0">
        <AnimatePresence mode="popLayout">
          {windowVisibility.CONTROLS && (
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="lg:col-span-3 flex flex-col space-y-4 h-full"
            >
              <div className="bg-[#0a0a0a] border border-red-500/20 rounded-lg p-5 flex flex-col h-full overflow-hidden shadow-2xl">
                <h2 className="text-[10px] font-mono text-white mb-6 flex items-center shrink-0 uppercase tracking-widest border-b border-red-500/10 pb-3">
                  <Target className="w-4 h-4 ml-2 text-red-500" />
                  مواصفات الأهداف الفعلية
                </h2>
                <div className="space-y-5 overflow-y-auto pr-1 custom-scrollbar">
                  <ConfigInput label="Target ID" value={targetName} onChange={setTargetName} icon={Activity} />
                  <ConfigInput label="Exploit URL" value={url} onChange={setUrl} icon={Globe} />
                  <div className="grid grid-cols-2 gap-3">
                    <ConfigInput label="User" value={username} onChange={setUsername} />
                    <ConfigInput label="Pass" value={password} onChange={setPassword} type="password" />
                  </div>
                  <div>
                    <label className="block text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 leading-none">Security Override</label>
                    <select 
                      value={security} 
                      onChange={(e) => setSecurity(e.target.value)}
                      className="w-full bg-black/40 border border-red-500/20 rounded px-2 py-2 text-xs text-slate-200 focus:outline-none focus:border-red-500/50 font-mono transition-all"
                    >
                      <option value="low">Low Persistence</option>
                      <option value="medium">Medium Hardening</option>
                      <option value="high">High Security (Stealth)</option>
                      <option value="impossible">Forbidden Zone</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <ConfigInput label="Swarm Size" value={population.toString()} onChange={(v: string) => setPopulation(parseInt(v) || 1)} type="number" />
                    <ConfigInput label="Cycles" value={generations.toString()} onChange={(v: string) => setGenerations(parseInt(v) || 1)} type="number" />
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          <motion.div 
            layout
            className={`${windowVisibility.CONTROLS ? 'lg:col-span-9' : 'lg:col-span-12'} grid grid-cols-1 md:grid-cols-2 gap-4 h-full overflow-hidden`}
          >
            {windowVisibility.LEARNING && (
              <ConsoleBox title="تحليل استراتيجيات الالتفاف" icon={Zap} data={learningLogs} ref={learningRef} className="border-yellow-400/10" iconColor="text-yellow-400" />
            )}
            {windowVisibility.SUCCESS && (
              <ConsoleBox title="سجل الاختراقات الناجحة" icon={Flame} data={successLogs} ref={successRef} className="border-emerald-400/10" iconColor="text-emerald-400" />
            )}
            {windowVisibility.ENGINE && (
              <div className="md:col-span-2 h-full lg:h-[45%]">
                <ConsoleBox title="وحدة التحكم Command & Control" icon={TerminalIcon} data={systemLogs} ref={systemRef} className="border-blue-400/10" iconColor="text-blue-400" />
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

function NavButton({ active, onClick, icon: Icon, label, subLabel, color }: any) {
  return (
    <button 
      onClick={onClick}
      className={`flex items-center gap-3 px-4 py-1.5 rounded-md transition-all duration-300 group relative ${
        active 
          ? 'bg-red-500/10 text-red-400' 
          : 'text-slate-500 hover:bg-white/5 hover:text-slate-300'
      }`}
    >
      {active && (
        <span className="absolute bottom-0 left-0 w-full h-[2px] bg-red-500 rounded-full"></span>
      )}
      <Icon className={`w-4 h-4 ${active ? color : 'text-slate-600'}`} />
      <div className="flex flex-col items-start leading-none gap-0.5">
        <span className="text-[10px] font-bold tracking-wide whitespace-nowrap">{label}</span>
        <span className="text-[7px] font-mono opacity-50 uppercase tracking-tighter whitespace-nowrap">{subLabel}</span>
      </div>
    </button>
  );
}

function ConfigInput({ label, value, onChange, icon: Icon, type = "text" }: any) {
  return (
    <div>
      <label className="block text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1">{label}</label>
      <div className="relative">
        {Icon && <Icon className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-500" />}
        <input 
          type={type} 
          value={value}
          dir="ltr"
          onChange={(e) => onChange(e.target.value)}
          className={`w-full bg-black/40 border border-slate-800 rounded ${Icon ? 'pl-7 pr-2' : 'px-2'} py-1.5 text-xs text-slate-200 focus:outline-none focus:border-red-500/30 font-mono transition-all text-left`}
        />
      </div>
    </div>
  );
}

const ConsoleBox = React.forwardRef(({ title, icon: Icon, data, className, iconColor }: any, ref: any) => {
  return (
    <div className={`flex flex-col bg-black/80 border rounded-lg overflow-hidden h-[300px] ${className}`}>
      <div className="bg-[#0a0a0a] border-b border-white/5 px-3 py-1.5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <Icon className={`w-3 h-3 ${iconColor}`} />
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">{title}</span>
        </div>
      </div>
      <div className="flex-1 font-mono text-[9px] custom-scrollbar bg-black/40 overflow-hidden">
        <Virtuoso
          ref={ref}
          data={data}
          totalCount={data.length}
          itemContent={(index, log) => (
            <div key={index} className="px-3 py-0.5 border-b border-white/5 hover:bg-white/[0.02]">
              {formatLogLine(log)}
            </div>
          )}
          style={{ height: '100%' }}
        />
      </div>
    </div>
  );
});
