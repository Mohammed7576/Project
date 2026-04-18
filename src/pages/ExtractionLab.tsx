import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Database, Terminal, ShieldAlert, Cpu, DatabaseZap, Search, ChevronRight } from 'lucide-react';

export default function ExtractionLab() {
  const [logs, setLogs] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [loot, setLoot] = useState<string[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const startLab = async () => {
    setIsRunning(true);
    setLogs(["[*] Initializing Specialist Lab...", "[*] Requesting independent process..."]);
    setLoot([]);

    try {
      const response = await fetch('/api/run-exfiltration-lab');
      if (!response.body) throw new Error('No body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(l => l.trim());
        
        setLogs(prev => [...prev, ...lines]);

        // Logic to extract loot from logs for display
        lines.forEach(line => {
          if (line.includes('->')) {
            setLoot(prev => [...prev, line.split('->')[1].trim()]);
          }
        });
      }
    } catch (err) {
      setLogs(prev => [...prev, `[CRITICAL ERROR] ${err instanceof Error ? err.message : 'Unknown error'}`]);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <DatabaseZap className="text-amber-500" />
            المختبر الثاني: أخصائي استخراج البيانات
          </h1>
          <p className="text-gray-500 mt-1">وحدة مستقلة مخصصة لعمليات الاستغلال المتقدمة واستنزاف قواعد البيانات</p>
        </div>
        <button
          onClick={startLab}
          disabled={isRunning}
          className={`px-6 py-3 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg ${
            isRunning 
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
            : 'bg-amber-600 text-white hover:bg-amber-700 active:scale-95'
          }`}
        >
          {isRunning ? <Cpu className="animate-spin" /> : <Database />}
          {isRunning ? 'جاري التشغيل...' : 'بدء عملية الاستخراج'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Terminal Section */}
        <div className="lg:col-span-2 flex flex-col h-[600px] bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
          <div className="bg-slate-800/50 px-4 py-2 flex items-center justify-between border-b border-white/10">
            <div className="flex items-center gap-2">
              <Terminal size={14} className="text-amber-400" />
              <span className="text-xs font-mono text-slate-300">EXFILTRATION_CONTEXT_v2.0</span>
            </div>
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
              <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
              <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 font-mono text-sm space-y-1 scrollbar-thin scrollbar-thumb-slate-700">
            {logs.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 space-y-4">
                <Search size={48} strokeWidth={1} />
                <p>في انتظار بدء العملية المستقلة...</p>
              </div>
            )}
            <AnimatePresence mode="popLayout">
              {logs.map((log, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`${
                    log.includes('[ERROR]') ? 'text-red-400' :
                    log.includes('[!!!]') ? 'text-green-400 font-bold' :
                    log.includes('[+]') ? 'text-amber-300' :
                    log.includes('[*]') ? 'text-blue-300' :
                    'text-slate-300'
                  }`}
                >
                  <span className="text-slate-600 mr-2">[{i.toString().padStart(3, '0')}]</span>
                  {log}
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={logEndRef} />
          </div>
        </div>

        {/* Loot Cabinet */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <ShieldAlert className="text-red-500" size={20} />
              البيانات المستخرجة (LOOT)
            </h3>
            
            <div className="space-y-3">
              {loot.length === 0 ? (
                <div className="py-12 text-center text-gray-400 border-2 border-dashed border-gray-50 rounded-xl">
                  لا توجد بيانات مستخرجة حتى الآن
                </div>
              ) : (
                loot.map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-center justify-between text-sm group"
                  >
                    <div className="flex-1 font-mono text-red-700 truncate">{item}</div>
                    <ChevronRight size={14} className="text-red-300 group-hover:translate-x-1 transition-transform" />
                  </motion.div>
                ))
              )}
            </div>
            
            {loot.length > 0 && (
              <button 
                className="w-full mt-6 py-2 px-4 bg-gray-900 text-white rounded-xl text-sm font-bold hover:bg-black transition-colors"
                onClick={() => {
                  const blob = new Blob([loot.join('\n')], { type: 'text/plain' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `exfiltrated_data_${new Date().getTime()}.txt`;
                  a.click();
                }}
              >
                تنزيل ملف البيانات (.txt)
              </button>
            )}
          </div>

          <div className="bg-amber-50 rounded-2xl p-6 border border-amber-100">
            <h4 className="text-sm font-bold text-amber-900 mb-2 uppercase tracking-wider">ملاحظة أمنية</h4>
            <p className="text-xs text-amber-800 leading-relaxed">
              هذا المختبر يعمل بنظام الاستغلال المباشر (Direct Exploitation). 
              بخلاف المختبر الرئيسي الذي يطور نفسه، هذا المحرك مبرمج مسبقاً لاستنزاف الموارد بمجرد تأكيد قابلية الحقن.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
