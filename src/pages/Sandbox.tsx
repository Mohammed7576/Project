import React, { useEffect, useRef } from 'react';
import { Play, Square, Globe, Shield, Zap, Target, Terminal as TerminalIcon, Activity } from 'lucide-react';
import { useAttack } from '../context/AttackContext';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';

const formatLogLine = (log: string) => {
  if (typeof log !== 'string') return log;
  
  let content = log.trim();
  let badge = null;
  let baseColorClass = "text-slate-300";

  // Clean up leading arrows often found in generic tool outputs
  if (content.startsWith('< ')) content = content.substring(2);
  if (content.startsWith('> ')) content = content.substring(2);

  // Extract a prefix badge like [TAG | SCORE]
  const badgeMatch = content.match(/^\[(.*?)\]\s*(.*)/);
  if (badgeMatch) {
    const rawTag = badgeMatch[1];
    content = badgeMatch[2]; // Remaining payload
    
    // Style badge based on content logic
    let badgeBg = "bg-slate-700 text-slate-300 border-slate-600";
    if (rawTag.includes('SUCCESS') || rawTag.includes('+')) badgeBg = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    else if (rawTag.includes('ERROR') || rawTag.includes('FAIL') || rawTag.includes('!') || rawTag.includes('BLOCK')) badgeBg = "bg-red-500/10 text-red-400 border-red-500/30";
    else if (rawTag.includes('BIASED') || rawTag.includes('MUTATION') || rawTag.includes('?')) badgeBg = "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
    else if (rawTag.includes('*') || rawTag.includes('INFO') || rawTag.includes('ISLAND')) badgeBg = "bg-blue-500/10 text-blue-400 border-blue-500/30";

    // Clean up the text of the badge for simpler presentation
    let tagText = rawTag
      .replace(/_/g, ' ')
      .replace(/MASS DATA DUMP/g, 'DATA DUMP')
      .replace(/SUCCESS/g, 'PASS')
      .replace(/BIASED/g, 'BIASED');

    badge = (
      <span className={`inline-block px-1.5 py-0.5 rounded border text-[9px] font-bold tracking-wider ml-1.5 shrink-0 ${badgeBg}`} dir="ltr">
        {tagText}
      </span>
    );
  }

  // Extract trailing island info like [1 Island]
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

  // Common SQL Keywords for Injection
  const keywords = ['SELECT', 'UNION', 'ALL', 'OR', 'AND', 'XOR', 'WHERE', 'FROM', 'DATABASE', 'USER', 'VERSION', 'ORDER BY', 'GROUP BY', 'LIMIT', 'OFFSET', 'HAVING', 'SLEEP', 'BENCHMARK', 'CONNECTION_ID', 'LOAD_FILE', 'TRUE', 'FALSE', 'NULL', 'LIKE', 'RLIKE', 'REGEXP'];
  
  // Syntax highlight the remaining content (keywords, numbers, hex, strings, comments)
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

export default function Sandbox() {
  console.log("[SANDBOX] Attempting to use AttackContext...");
  const {
    url, setUrl,
    username, setUsername,
    password, setPassword,
    security, setSecurity,
    population, setPopulation,
    generations, setGenerations,
    targetName, setTargetName,
    isAttacking,
    logs,
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
    <div className="flex flex-col h-full space-y-6">
      {/* Professional Lab Header */}
      <div className="bg-[#0a0a0a]/80 backdrop-blur-md border border-[#10b981]/20 rounded-xl p-4 sticky top-0 z-50 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <TerminalIcon className="w-5 h-5 text-[#10b981]" />
                <span>مختبر التجارب البحثية</span>
              </h1>
              <span className="text-[9px] text-slate-500 uppercase tracking-widest">
                Payload Mutation & Genetic Engineering Engine
              </span>
            </div>
            <div className="h-8 w-[1px] bg-[#10b981]/20 hidden lg:block"></div>
            <div className="flex items-center gap-4">
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${isAttacking ? 'bg-[#10b981] animate-pulse' : 'bg-slate-700'}`}></span>
                  <span className={`text-[10px] font-mono font-bold ${isAttacking ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {isAttacking ? 'RUNNING_SYNC' : 'SYSTEM_IDLE'}
                  </span>
                </div>
                <span className="text-[8px] text-slate-600 uppercase tracking-tighter">Engine Status</span>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <Zap className="w-3 h-3 text-yellow-400" />
                  <span className="text-[10px] font-mono font-bold text-white uppercase tracking-wider">
                    G-{currentGeneration}
                  </span>
                </div>
                <span className="text-[8px] text-slate-600 uppercase tracking-tighter">Current Gen</span>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <Activity className={`w-3 h-3 ${isAttacking ? 'text-[#10b981]' : 'text-slate-600'}`} />
                  <span className={`text-[10px] font-mono font-bold uppercase tracking-wider ${elapsedTime >= 1200 ? 'text-[#10b981]' : (isAttacking ? 'text-white' : 'text-slate-600')}`}>
                    {formatTime(elapsedTime)} / 20:00
                  </span>
                </div>
                <span className="text-[8px] text-slate-600 uppercase tracking-tighter">Persistence Timer</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {!isAttacking ? (
              <button 
                onClick={startAttack}
                disabled={!url}
                className="bg-[#10b981] text-black px-8 py-2 rounded-lg font-mono text-[11px] font-bold hover:bg-[#059669] transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.3)] disabled:opacity-50 disabled:grayscale"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                START_ENGINE
              </button>
            ) : (
              <button 
                onClick={stopAttack}
                className="bg-red-500 text-white px-8 py-2 rounded-lg font-mono text-[11px] font-bold hover:bg-red-600 transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(239,68,68,0.3)]"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                TERMINATE_PROCESS
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Lab Window Manager Controls */}
      <div className="flex flex-wrap items-center gap-2 bg-black/40 p-1.5 rounded-xl border border-white/5 border-dashed">
        <NavButton 
          active={windowVisibility.CONTROLS} 
          onClick={() => toggleWindow('CONTROLS')} 
          icon={Target} 
          label="إعدادات التجربة" 
          subLabel="CONTROLS"
        />
        <div className="w-[1px] h-6 bg-white/5 mx-1" />
        <NavButton 
          active={windowVisibility.LEARNING} 
          onClick={() => toggleWindow('LEARNING')} 
          icon={Zap} 
          label="التسجيل التجريبي (Heuristics)" 
          subLabel="LEARNING"
        />
        <NavButton 
          active={windowVisibility.SUCCESS} 
          onClick={() => toggleWindow('SUCCESS')} 
          icon={Play} 
          label="الحمولات المصادق عليها" 
          subLabel="SUCCESS"
        />
        <NavButton 
          active={windowVisibility.ENGINE} 
          onClick={() => toggleWindow('ENGINE')} 
          icon={TerminalIcon} 
          label="وحدة تحكم المحرك" 
          subLabel="ENGINE"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Row 1: Config & Success */}
        {windowVisibility.CONTROLS && (
          <div className="lg:col-span-3 flex flex-col space-y-4 h-full">
            <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-5 flex flex-col h-full overflow-hidden shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
              <h2 className="text-[10px] font-mono text-white mb-6 flex items-center shrink-0 uppercase tracking-widest border-b border-[#10b981]/10 pb-3">
                <Target className="w-4 h-4 ml-2 text-[#10b981]" />
                إعدادات الهدف البحثي
              </h2>
              <div className="space-y-5 overflow-y-auto pr-1 custom-scrollbar">
                <ConfigInput label="Target Name (Persistence ID)" value={targetName} onChange={setTargetName} icon={Activity} />
                <ConfigInput label="Target URL" value={url} onChange={setUrl} icon={Globe} />
                <div className="grid grid-cols-2 gap-3">
                  <ConfigInput label="User" value={username} onChange={setUsername} />
                  <ConfigInput label="Pass" value={password} onChange={setPassword} type="password" />
                </div>
                <div>
                  <label className="block text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 leading-none">Security Level</label>
                  <select 
                    value={security} 
                    onChange={(e) => setSecurity(e.target.value)}
                    className="w-full bg-black/40 border border-[#10b981]/20 rounded px-2 py-2 text-xs text-slate-200 focus:outline-none focus:border-[#10b981]/50 font-mono transition-all"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="impossible">Impossible</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <ConfigInput label="Population" value={population.toString()} onChange={(v) => setPopulation(parseInt(v) || 1)} type="number" />
                  <ConfigInput label="Generations" value={generations.toString()} onChange={(v) => setGenerations(parseInt(v) || 1)} type="number" />
                </div>
                <div className="pt-4 mt-auto">
                  <button 
                    onClick={resetIntelligence}
                    className="w-full bg-slate-800/30 text-slate-500 border border-slate-700/50 py-2 rounded font-mono text-[10px] flex items-center justify-center gap-2 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/30 transition-all uppercase tracking-widest"
                  >
                    <Zap className="w-3 h-3" />
                    إعادة ضبط الذكاء
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Console Windows */}
        <div className={`${windowVisibility.CONTROLS ? 'lg:col-span-9' : 'lg:col-span-12'} grid grid-cols-1 md:grid-cols-2 gap-4 h-full overflow-hidden`}>
          {windowVisibility.LEARNING && (
            <ConsoleBox 
              title="سجلات تعلم الآلة وتحليل WAF" 
              icon={Zap} 
              data={learningLogs} 
              ref={learningRef}
              className="border-yellow-400/10 lg:h-full"
              iconColor="text-yellow-400"
            />
          )}
          {windowVisibility.SUCCESS && (
            <ConsoleBox 
              title="أرشيف الحمولات المؤكدة الانعكاس" 
              icon={Play} 
              data={successLogs} 
              ref={successRef}
              className="border-emerald-400/10 lg:h-full"
              iconColor="text-emerald-400"
            />
          )}
          {windowVisibility.ENGINE && (
            <div className="md:col-span-2 h-full lg:h-[45%]">
              <ConsoleBox 
                title="سجلات القياس لمحرك السرب (Engine Telemetry logs)" 
                icon={TerminalIcon} 
                data={systemLogs} 
                ref={systemRef}
                className="border-blue-400/10 h-full"
                iconColor="text-blue-400"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function NavButton({ active, onClick, icon: Icon, label, subLabel }: any) {
  return (
    <button 
      onClick={onClick}
      className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-300 group ${
        active 
          ? 'bg-[#10b981]/10 border border-[#10b981]/40 text-[#10b981] shadow-[0_0_15px_rgba(16,185,129,0.1)]' 
          : 'border border-white/5 text-slate-500 hover:bg-white/5 hover:text-slate-300'
      }`}
    >
      <Icon className={`w-4 h-4 transition-transform group-hover:scale-110 ${active ? 'text-[#10b981]' : 'text-slate-600'}`} />
      <div className="flex flex-col items-start leading-none gap-1">
        <span className="text-[10px] font-bold tracking-wide">{label}</span>
        <span className="text-[8px] font-mono opacity-50 uppercase tracking-tighter">{subLabel}</span>
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
          className={`w-full bg-black/40 border border-[#10b981]/20 rounded ${Icon ? 'pl-7 pr-2' : 'px-2'} py-1.5 text-xs text-slate-200 focus:outline-none focus:border-[#10b981]/50 font-mono transition-all text-left placeholder:text-right`}
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
        <div className="text-[9px] font-mono text-slate-600 bg-black/40 px-1.5 rounded">{data.length} pts</div>
      </div>
      <div className="flex-1 font-mono text-[9px] custom-scrollbar bg-[rgba(5,5,5,0.8)] overflow-hidden">
        {data.length === 0 ? (
          <div className="p-3 text-slate-700 italic text-[10px]">في انتظار تدفق بيانات القياس (Telemetry)...</div>
        ) : (
          <Virtuoso
            ref={ref}
            data={data}
            totalCount={data.length}
            itemContent={(index, log) => (
              <div key={index} className="px-3 py-0.5 border-b border-white/5 last:border-0 hover:bg-white/[0.02]">
                {formatLogLine(log)}
              </div>
            )}
            followOutput="smooth"
            style={{ height: '100%' }}
          />
        )}
      </div>
    </div>
  );
});
