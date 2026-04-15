import React, { useState, useEffect } from 'react';
import { Shield, Search, Filter, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';

interface WAFRule {
  pattern: string;
  confidence: number;
}

export default function WAFAnalysis() {
  const [rules, setRules] = useState<WAFRule[]>([]);

  useEffect(() => {
    const fetchRules = async () => {
      try {
        const response = await fetch('/api/swarm-radar'); // Assuming this returns blocking patterns
        if (response.ok) {
          const data = await response.json();
          // Map data to rules
          setRules(data.map((d: any) => ({
            pattern: d.pattern || d.payload,
            confidence: d.confidence || 0.85
          })));
        }
      } catch (e) {
        console.error("Failed to fetch WAF rules", e);
      }
    };
    fetchRules();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white font-mono">تحليل <span className="text-[#10b981]">WAF</span></h1>
        <div className="flex items-center gap-2 bg-[#10b981]/10 text-[#10b981] px-3 py-1 rounded border border-[#10b981]/30 text-xs font-mono">
          <Shield className="w-3 h-3" />
          <span>الذكاء الاصطناعي نشط</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rules Table */}
        <div className="lg:col-span-2 bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-[#10b981]/20 bg-black/40 flex justify-between items-center">
            <h2 className="text-sm font-mono text-white">أنماط الحظر المكتشفة</h2>
            <div className="flex gap-2">
              <Search className="w-4 h-4 text-slate-500" />
              <Filter className="w-4 h-4 text-slate-500" />
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-right font-mono text-xs">
              <thead>
                <tr className="text-slate-500 border-b border-[#10b981]/10">
                  <th className="p-4 font-bold">النمط (Pattern)</th>
                  <th className="p-4 font-bold">الثقة</th>
                  <th className="p-4 font-bold">الحالة</th>
                </tr>
              </thead>
              <tbody>
                {rules.length > 0 ? rules.map((rule, i) => (
                  <tr key={i} className="border-b border-[#10b981]/5 hover:bg-[#10b981]/5 transition-colors">
                    <td className="p-4 text-slate-300 break-all">{rule.pattern}</td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1 bg-slate-800 rounded-full w-16">
                          <div className="h-1 bg-[#10b981] rounded-full" style={{ width: `${rule.confidence * 100}%` }}></div>
                        </div>
                        <span className="text-[#10b981]">{(rule.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <span className="text-red-400 flex items-center gap-1">
                        <XCircle className="w-3 h-3" />
                        محظور
                      </span>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={3} className="p-12 text-center text-slate-600">لا توجد أنماط مكتشفة بعد.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Insights Sidebar */}
        <div className="space-y-6">
          <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6">
            <h2 className="text-sm font-mono text-white mb-4 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-500" />
              توصيات التجاوز
            </h2>
            <div className="space-y-4">
              <div className="p-3 bg-yellow-500/5 border border-yellow-500/20 rounded">
                <p className="text-[10px] text-yellow-500 font-bold mb-1">تنبيه: حظر UNION</p>
                <p className="text-[10px] text-slate-400 leading-relaxed">تم اكتشاف حظر قوي لكلمة UNION. يُنصح باستخدام التعليقات المضمنة مثل /*!UNION*/ للتجاوز.</p>
              </div>
              <div className="p-3 bg-[#10b981]/5 border border-[#10b981]/20 rounded">
                <p className="text-[10px] text-[#10b981] font-bold mb-1">استراتيجية مقترحة</p>
                <p className="text-[10px] text-slate-400 leading-relaxed">استخدام ترميز URL المزدوج (Double URL Encoding) لتجاوز فلاتر الإدخال البسيطة.</p>
              </div>
            </div>
          </div>

          <div className="bg-[#0a0a0a] border border-[#10b981]/20 rounded-lg p-6">
            <h2 className="text-sm font-mono text-white mb-4">إحصائيات الحماية</h2>
            <div className="space-y-3">
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-slate-500">مستوى ذكاء WAF</span>
                <span className="text-yellow-500">متوسط</span>
              </div>
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-slate-500">دقة التنبؤ</span>
                <span className="text-[#10b981]">89.4%</span>
              </div>
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-slate-500">الأنماط التي تم تجاوزها</span>
                <span className="text-blue-400">42</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
