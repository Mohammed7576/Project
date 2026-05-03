import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Play, Square, Globe, Shield, Zap, Target, Terminal as TerminalIcon, Activity, ArrowRight, ArrowLeft, Settings, BrainCircuit, ShieldAlert } from 'lucide-react';
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
      .replace(/SUCCESS/g, 'PASS')
      .replace(/BIASED/g, 'BIASED');

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

  const [step, setStep] = useState(1);
  const [learningRate, setLearningRate] = useState("0.05");
  const [explorationRate, setExplorationRate] = useState("0.5");
  const [curiosityWeight, setCuriosityWeight] = useState("1.0");

  useEffect(() => {
    if (isAttacking) {
      setStep(3); // Auto forward to monitoring when attack is strictly active remotely
    }
  }, [isAttacking]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const [windowVisibility, setWindowVisibility] = React.useState({
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
    const inv = setInterval(fetchSummary, 10000);
    return () => clearInterval(inv);
  }, []);

  const toggleWindow = (win: keyof typeof windowVisibility) => {
    setWindowVisibility(prev => ({ ...prev, [win]: !prev[win] }));
  };

  const currentPhase = () => {
    if (!isAttacking && currentGeneration === 0 && systemLogs.length === 0) return 0;
    if (successLogs.some(l => l.includes('EXFILTRATION') || l.includes('DATABASE'))) return 6;
    if (successLogs.some(l => l.includes('SUCCESS') || l.includes('EXPLOIT') || l.includes('VERIFIED'))) return 5;
    if (currentGeneration >= 5) return 4;
    if (currentGeneration >= 1) return 3;
    if (learningLogs.length > 0 || systemLogs.some(l => l.includes('Discovery'))) return 2;
    if (isAttacking) return 1;
    return 6; // completed
  };

  const phase = currentPhase();

  const phasesList = [
    { id: 1, label: "استطلاع الموارد", sub: "RECONNAISSANCE" },
    { id: 2, label: "تنميط الهدف", sub: "FUZZ & PROFILE" },
    { id: 3, label: "طفرات جينية", sub: "GA MUTATION" },
    { id: 4, label: "التعلم المعزز", sub: "POLICY GRADIENT" },
    { id: 5, label: "اختراق الجدار", sub: "WAF EVASION" },
    { id: 6, label: "استخراج البيانات", sub: "EXFILTRATION" },
  ];

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
        window.location.reload(); 
      } else {
        alert('فشل في إعادة ضبط الذكاء.');
      }
    } catch (error) {
      alert('خطأ في الاتصال بالخادم.');
    }
  };

  // --- WIZARD RENDERERS ---

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center gap-4 mb-8">
      {[1, 2, 3].map((s) => (
        <React.Fragment key={s}>
          <div className="flex flex-col items-center">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold font-mono transition-all duration-300 ${step === s ? 'bg-[#10b981] text-black shadow-[0_0_15px_rgba(16,185,129,0.5)] scale-110' : step > s ? 'bg-[#10b981]/20 text-[#10b981] border border-[#10b981]/50' : 'bg-slate-800 text-slate-500 border border-slate-700'}`}>
              {s === 1 && <Globe className="w-5 h-5" />}
              {s === 2 && <BrainCircuit className="w-5 h-5" />}
              {s === 3 && <TerminalIcon className="w-5 h-5" />}
            </div>
            <span className={`text-[10px] uppercase font-mono mt-2 tracking-widest ${step >= s ? 'text-[#10b981]' : 'text-slate-600'}`}>
              {s === 1 ? 'TARGET' : s === 2 ? 'RL TUNING' : 'EXECUTE'}
            </span>
          </div>
          {s < 3 && (
            <div className={`w-16 h-1 rounded-full ${step > s ? 'bg-[#10b981]/50' : 'bg-slate-800'}`}></div>
          )}
        </React.Fragment>
      ))}
    </div>
  );

  const renderStep1 = () => (
    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="max-w-2xl mx-auto border border-[#10b981]/20 bg-[#0a0a0a] rounded-xl p-6 shadow-2xl relative">
      <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
        <Target className="w-48 h-48 text-[#10b981]" />
      </div>
      <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2 relative z-10"><Globe className="text-[#10b981]" /> الخطوة 1: تحديد وتشكيل بيئة الهدف</h2>
      <p className="text-sm text-slate-400 mb-8 max-w-lg leading-relaxed relative z-10">
        قم بتحديد مسار بيئة الاختبار (Sandbox) ومستوى تعقيد الإجراءات الدفاعية المستهدفة (WAF Rules / SQL Filters).
      </p>

      <div className="space-y-5 relative z-10">
        <ConfigInput label="معرف الهدف (Target ID / Project Name)" value={targetName} onChange={setTargetName} icon={Target} />
        <ConfigInput label="نقطة الدخول (Target URL)" value={url} onChange={setUrl} icon={Globe} />
        
        <div className="grid grid-cols-2 gap-4">
          <ConfigInput label="اسم المستخدم (اختياري للحقن المباشر)" value={username} onChange={setUsername} />
          <ConfigInput label="كلمة المرور (نقطة الحقن الافتراضية)" value={password} onChange={setPassword} type="text" />
        </div>

        <div className="pt-2">
          <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 leading-none flex items-center gap-2">
            <ShieldAlert className="w-3 h-3 text-yellow-500" />
            مستوى تصعيد الجدار الناري (Security Level)
          </label>
          <div className="grid grid-cols-4 gap-2">
            {['low', 'medium', 'high', 'impossible'].map((lvl) => (
              <button 
                key={lvl}
                onClick={() => setSecurity(lvl)}
                className={`py-3 px-2 rounded-md font-mono text-[10px] uppercase tracking-widest transition-all ${
                  security === lvl 
                  ? 'bg-[#10b981]/20 text-[#10b981] border border-[#10b981] shadow-[0_0_10px_rgba(16,185,129,0.2)]' 
                  : 'bg-slate-900 border border-slate-800 text-slate-500 hover:bg-slate-800'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end mt-10 relative z-10">
        <button onClick={() => setStep(2)} className="bg-[#10b981] text-black px-8 py-3 rounded text-sm font-bold font-mono hover:bg-[#059669] transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.2)]">
          التالي: إعدادات شبكة RL <ArrowLeft className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );

  const renderStep2 = () => (
    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="max-w-2xl mx-auto border border-blue-500/20 bg-[#0a0a0a] rounded-xl p-6 shadow-2xl relative">
      <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
        <BrainCircuit className="w-48 h-48 text-blue-500" />
      </div>
      <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2 relative z-10"><BrainCircuit className="text-blue-500" /> الخطوة 2: تهيئة معلمات التعلم التعزيزي (RL Hyperparameters)</h2>
      <p className="text-sm text-slate-400 mb-8 max-w-lg leading-relaxed relative z-10">
        قم بضبط إعدادات الشبكة العصبية الوكيلة. هذه المعلمات ستتحكم في كيفية استكشاف الوكيل للثغرات وتقييمه للمخاطر (Exploitation vs Exploration).
      </p>

      <div className="space-y-6 relative z-10">
        <div className="grid grid-cols-2 gap-6 bg-slate-900/50 p-4 rounded-lg border border-slate-800">
          <div>
            <label className="block text-[10px] text-slate-400 uppercase tracking-widest mb-1.5 font-bold">الحجم السكاني لجزيرة الحلول (Population Size)</label>
            <input type="range" min="5" max="100" value={population} onChange={(e) => setPopulation(parseInt(e.target.value))} className="w-full accent-blue-500" />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1"><span>5 (Rapid)</span><span className="text-blue-400 font-bold">{population} وكيل</span><span>100 (Deep)</span></div>
          </div>
          <div>
            <label className="block text-[10px] text-slate-400 uppercase tracking-widest mb-1.5 font-bold">عدد أجيال التطور المعرفي (Generations)</label>
            <input type="range" min="1" max="50" value={generations} onChange={(e) => setGenerations(parseInt(e.target.value))} className="w-full accent-blue-500" />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1"><span>1 (Quick)</span><span className="text-blue-400 font-bold">{generations} جيل</span><span>50 (Extended)</span></div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ConfigInput label="معدل التعلم (Alpha)" value={learningRate} onChange={setLearningRate} type="number" tooltip="0.01 - 0.1: سرعة تحديث أوزان الشبكة العصبية." />
          <ConfigInput label="معدل الاستكشاف (Epsilon)" value={explorationRate} onChange={setExplorationRate} type="number" tooltip="يحدد مدى تجربة الوكيل لطفرات عشوائية جديدة مقارنة باستغلال الطفرات الناجحة." />
          <ConfigInput label="وزن الفضول (Curiosity Reward)" value={curiosityWeight} onChange={setCuriosityWeight} type="number" tooltip="مكافأة الوكيل لاكتساب استجابات خادم جديدة (HTTP Status/Size changes)." />
        </div>
        
         <div className="bg-yellow-500/10 border border-yellow-500/20 p-4 rounded-lg">
            <h3 className="text-xs font-bold text-yellow-500 mb-2 flex items-center gap-2"><Zap className="w-4 h-4"/> توصية الخبير</h3>
            <p className="text-[10px] text-yellow-400/80 leading-relaxed max-w-xl">
              لتحقيق الهروب من جدار الحماية التنبؤي، اضبط معدل الاستكشاف بنسبة أعلى (≈ 0.5) في الأجيال الأولى، وقم برفع معدل الفضول إلى (1.5) لدفع الوكيل لإيجاد ثغرات جانبية غير مدرجة في القواعد النمطية.
            </p>
         </div>
      </div>

      <div className="flex justify-between mt-10 relative z-10">
        <button onClick={() => setStep(1)} className="text-slate-400 px-4 py-2 rounded text-sm font-bold font-mono hover:text-white hover:bg-slate-800 transition-all flex items-center gap-2">
          <ArrowRight className="w-4 h-4" /> رجوع
        </button>
        <button onClick={() => setStep(3)} className="bg-blue-500 text-black px-8 py-3 rounded text-sm font-bold font-mono hover:bg-blue-400 transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(59,130,246,0.3)]">
          التالي: تجهيز المحرك <ArrowLeft className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );

  const renderStep3 = () => (
    <div className="flex flex-col h-full space-y-4">
      {/* 🚀 Integrated Lab Command Center */}
      <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-xl shadow-2xl overflow-hidden sticky top-0 z-50">
        <div className="bg-[#10b981]/5 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#10b981]/10">
          <div className="flex items-center gap-5">
            <div className="flex flex-col">
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <TerminalIcon className="w-5 h-5 text-[#10b981]" />
                <span>مختبر التدريب المحاكي (Simulation Training Lab)</span>
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <div className={`w-1.5 h-1.5 rounded-full ${isAttacking ? 'bg-[#10b981] animate-pulse' : 'bg-slate-700'}`}></div>
                <span className={`text-[9px] font-mono tracking-widest uppercase ${isAttacking ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {isAttacking ? 'Evolution Engine Active' : 'System Ready'}
                </span>
              </div>
            </div>

            <div className="h-10 w-[1px] bg-[#10b981]/10 hidden lg:block"></div>

            <div className="hidden sm:flex items-center gap-6">
              <div className="flex flex-col">
                <span className="text-[8px] text-slate-500 uppercase font-bold tracking-tighter">الجيل الحالي</span>
                <div className="flex items-center gap-2">
                  <Zap className="w-3 h-3 text-yellow-400" />
                  <span className="text-sm font-mono text-white">G-{currentGeneration}</span>
                </div>
              </div>
              <div className="flex flex-col">
                <span className="text-[8px] text-slate-500 uppercase font-bold tracking-tighter">مدة الجلسة</span>
                <div className="flex items-center gap-2 text-white">
                  <Activity className={`w-3 h-3 ${isAttacking ? 'text-[#10b981]' : 'text-slate-600'}`} />
                  <span className="text-sm font-mono">{formatTime(elapsedTime)}</span>
                </div>
              </div>

              <div className="h-6 w-[1px] bg-[#10b981]/10 mx-1"></div>

              <div className="flex flex-col">
                <span className="text-[8px] text-slate-500 uppercase font-bold tracking-tighter">مقياس عن بعد (Telemetry)</span>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5" title="Successful Bypasses">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    <span className="text-xs font-mono text-white">{summary.successfulPayloads}</span>
                  </div>
                  <div className="flex items-center gap-1.5" title="SQL Errors">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                    <span className="text-xs font-mono text-white">{summary.sqlErrorPayloads}</span>
                  </div>
                  <div className="flex items-center gap-1.5" title="Total Throughput">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                    <span className="text-xs font-mono text-white">{summary.totalPayloads}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {!isAttacking && <button onClick={() => setStep(2)} className="text-slate-400 px-3 py-2 rounded text-xs font-mono hover:text-white transition-all"><Settings className="w-4 h-4"/></button>}
            
            <button 
                onClick={resetIntelligence}
                className="bg-slate-800/50 text-slate-400 border border-slate-700 px-3 py-2.5 rounded-lg font-mono text-[10px] hover:bg-red-500/10 hover:text-red-400 transition-all flex items-center gap-2 uppercase"
                title="إعادة تهيئة الذكاء الاصطناعي بالكامل"
              >
                <BrainCircuit className="w-3.5 h-3.5" /> مسح الذاكرة
            </button>

            {!isAttacking ? (
              <button 
                onClick={() => startAttack('training', { learningRate, explorationRate, curiosityWeight })}
                disabled={!url}
                className="bg-[#10b981] text-black px-6 py-2.5 rounded-lg font-mono text-[11px] font-bold hover:bg-[#059669] transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.2)] disabled:opacity-50 disabled:grayscale"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                بدء عملية التدريب (COMMENCE TRAINING)
              </button>
            ) : (
              <button 
                onClick={stopAttack}
                className="bg-red-500/10 text-red-500 border border-red-500/20 px-6 py-2.5 rounded-lg font-mono text-[11px] font-bold hover:bg-red-500 hover:text-white transition-all flex items-center gap-2"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                إيقاف التدريب (PAUSE LEARNING)
              </button>
            )}
          </div>
        </div>

        {/* 🎛️ Navigation & Window Manager */}
        <div className="px-4 py-2 bg-black/40 flex flex-col md:flex-row md:items-center justify-between gap-4 overflow-x-auto no-scrollbar border-t border-[#10b981]/10">
          <div className="flex items-center gap-2">
            <NavButton active={windowVisibility.LEARNING} onClick={() => toggleWindow('LEARNING')} icon={Zap} label="استقراء WAF" subLabel="HEURISTICS" />
            <NavButton active={windowVisibility.SUCCESS} onClick={() => toggleWindow('SUCCESS')} icon={Target} label="اختراقات ناجحة" subLabel="PAYLOADS" />
            <NavButton active={windowVisibility.ENGINE} onClick={() => toggleWindow('ENGINE')} icon={TerminalIcon} label="محرك السرب" subLabel="CORE LOGS" />
          </div>
          
          <div className="flex items-center gap-2 pr-4 md:border-r md:border-[#10b981]/10">
            {phasesList.map((p, idx) => (
              <React.Fragment key={p.id}>
                <div 
                  className={`flex flex-col items-center justify-center p-2 rounded-lg transition-all duration-500
                    ${phase === p.id ? 'bg-[#10b981]/20 border border-[#10b981] shadow-[0_0_15px_rgba(16,185,129,0.2)]' : 
                      phase > p.id ? 'opacity-50' : 'opacity-20 grayscale'
                    }`}
                >
                  <span className={`text-[10px] font-bold ${phase === p.id ? 'text-[#10b981]' : 'text-slate-400'}`}>{p.label}</span>
                  <span className="text-[8px] font-mono text-slate-500 uppercase">{p.sub}</span>
                </div>
                {idx < phasesList.length - 1 && (
                  <div className={`h-[1px] w-4 ${phase > p.id ? 'bg-[#10b981]' : 'bg-slate-700'}`}></div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1 min-h-0">
        <AnimatePresence mode="popLayout">
          {/* Console Windows */}
          <motion.div layout className={`lg:col-span-12 grid grid-cols-1 md:grid-cols-2 gap-4 h-full overflow-hidden`}>
            {windowVisibility.LEARNING && (
              <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.3 }} className="h-full">
                <ConsoleBox title="سجلات اكتشاف أنماط الحجب وتقييم المكافآت" icon={Zap} data={learningLogs} ref={learningRef} className="border-yellow-400/20 lg:h-[45vh]" iconColor="text-yellow-400" />
              </motion.div>
            )}
            {windowVisibility.SUCCESS && (
              <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.3, delay: 0.1 }} className="h-full">
                <ConsoleBox title="نافذة تسجيل الطفرات المنتصرة وحمولات C2" icon={Target} data={successLogs} ref={successRef} className="border-emerald-400/20 lg:h-[45vh]" iconColor="text-emerald-400" />
              </motion.div>
            )}
            {windowVisibility.ENGINE && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }} transition={{ duration: 0.4 }} className="md:col-span-2 h-full">
                <ConsoleBox title="سجلات نظام التدريب والمحاكي المتقدم" icon={TerminalIcon} data={systemLogs} ref={systemRef} className="border-blue-400/20 h-[35vh]" iconColor="text-blue-400" />
              </motion.div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {!isAttacking && step < 3 && renderStepIndicator()}
      <AnimatePresence mode="wait">
        {step === 1 && <motion.div key="step1" className="h-full">{renderStep1()}</motion.div>}
        {step === 2 && <motion.div key="step2" className="h-full">{renderStep2()}</motion.div>}
        {step === 3 && <motion.div key="step3" className="h-full">{renderStep3()}</motion.div>}
      </AnimatePresence>
    </div>
  );
}

function NavButton({ active, onClick, icon: Icon, label, subLabel }: any) {
  return (
    <button 
      onClick={onClick}
      className={`flex items-center gap-3 px-4 py-1.5 rounded-md transition-all duration-300 group relative ${
        active 
          ? 'bg-[#10b981]/10 text-[#10b981]' 
          : 'text-slate-500 hover:bg-white/5 hover:text-slate-300'
      }`}
    >
      {active && (
        <span className="absolute bottom-0 left-0 w-full h-[2px] bg-[#10b981] rounded-full shadow-[0_0_10px_#10b981]"></span>
      )}
      <Icon className={`w-4 h-4 transition-transform group-hover:scale-110 ${active ? 'text-[#10b981]' : 'text-slate-600'}`} />
      <div className="flex flex-col items-start leading-none gap-0.5">
        <span className="text-[10px] font-bold tracking-wide whitespace-nowrap">{label}</span>
        <span className="text-[7px] font-mono opacity-50 uppercase tracking-tighter whitespace-nowrap">{subLabel}</span>
      </div>
    </button>
  );
}

function ConfigInput({ label, value, onChange, icon: Icon, type = "text", tooltip }: any) {
  return (
    <div>
      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5 flex items-center gap-2">
        {label}
      </label>
      <div className="relative">
        {Icon && <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />}
        <input 
          type={type} 
          value={value}
          dir="ltr"
          onChange={(e) => onChange(e.target.value)}
          className={`w-full bg-black/60 border border-slate-700/50 rounded-lg ${Icon ? 'pl-9 pr-3' : 'px-3'} py-2.5 text-sm text-slate-200 focus:outline-none focus:border-[#10b981]/60 focus:bg-[#10b981]/5 focus:ring-1 focus:ring-[#10b981]/50 font-mono transition-all text-left placeholder:text-right`}
        />
      </div>
      {tooltip && <p className="text-[9px] text-slate-500 mt-1.5 mr-1 pr-2 border-r border-slate-700/50">{tooltip}</p>}
    </div>
  );
}

const ConsoleBox = React.forwardRef(({ title, icon: Icon, data, className, iconColor }: any, ref: any) => {
  return (
    <div className={`flex flex-col bg-black/80 border rounded-lg overflow-hidden h-full ${className}`}>
      <div className="bg-[#0a0a0a] border-b border-white/5 px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <Icon className={`w-4 h-4 ${iconColor}`} />
          <span className="text-xs font-bold text-slate-300 tracking-wide">{title}</span>
        </div>
        <div className="text-[10px] font-mono text-slate-500 bg-white/5 px-2 py-0.5 rounded-full border border-white/10">{data.length} pts</div>
      </div>
      <div className="flex-1 font-mono text-[10px] custom-scrollbar bg-[rgba(3,3,3,0.9)] overflow-hidden">
        {data.length === 0 ? (
          <div className="p-5 text-slate-600/80 italic text-xs flex items-center gap-3">
             <div className="w-2 h-2 rounded-full bg-slate-700 animate-ping" />
             في انتظار تدفق بيانات القياس عن بعد أثناء أطوار التدريب...
          </div>
        ) : (
          <Virtuoso
            ref={ref}
            data={data}
            totalCount={data.length}
            itemContent={(index, log) => (
              <div key={index} className="px-4 py-0.5 border-b border-white/[0.03] last:border-0 hover:bg-white/[0.015] transition-colors">
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

