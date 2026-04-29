import React, { useState, useEffect } from 'react';
import { Shield, Search, Filter, AlertCircle, XCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface WAFRule {
  pattern: string;
  confidence: number;
}

export default function WAFAnalysis() {
  const [intel, setIntel] = useState<any>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchIntel = async () => {
      try {
        const response = await fetch('/api/waf-intelligence'); 
        if (response.ok && isMounted) {
          setIntel(await response.json());
        }
      } catch (e) {
        console.error("Failed to fetch WAF intelligence", e);
      }
    };
    
    fetchIntel();
    const intervalId = setInterval(fetchIntel, 10000);
    
    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  const rules = intel?.patterns || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-white font-mono">تحليل <span className="text-[#10b981]">WAF</span></h1>
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30 text-[10px] font-mono whitespace-nowrap">
             WAF: {intel?.waf_name}
          </Badge>
          <Badge variant="outline" className="bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30 text-[10px] font-mono gap-1 whitespace-nowrap">
            <Shield className="w-3 h-3" />
            الذكاء الاصطناعي نشط
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rules Table */}
        <Card className="lg:col-span-2 bg-[#0a0a0a] border-[#10b981]/20 overflow-hidden">
          <div className="p-4 border-b border-[#10b981]/20 bg-black/40 flex justify-between items-center">
            <h2 className="text-sm font-mono text-white">بصمات جدار الحماية (WAF) المستخرجة</h2>
            <div className="flex gap-2">
              <Search className="w-4 h-4 text-slate-500" />
              <Filter className="w-4 h-4 text-slate-500" />
            </div>
          </div>
          <CardContent className="p-0 overflow-x-auto">
            <table className="w-full text-right font-mono text-xs">
              <thead>
                <tr className="text-slate-500 border-b border-[#10b981]/10">
                  <th className="p-4 font-bold">نمط البصمة (Pattern)</th>
                  <th className="p-4 font-bold">ثقة النموذج الذكي</th>
                  <th className="p-4 font-bold">الحالة</th>
                </tr>
              </thead>
              <tbody className="text-slate-300">
                {rules.length > 0 ? rules.map((rule: any, i: number) => (
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
                         محظور (BLOCKED)
                      </span>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={3} className="p-12 text-center text-slate-600 italic">لم يتم التعرف بنجاح على أي أنماط هيكلية محظورة لـ WAF حتى الآن.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>

        {/* Insights Sidebar */}
        <div className="space-y-6">
          <Card className="bg-[#0a0a0a] border-[#10b981]/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-mono text-white flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-yellow-500" />
                توصيات التخطي الخوارزمية
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {intel?.recommendations?.map((rec: any, i: number) => (
                <div key={i} className="p-3 bg-yellow-500/5 border border-yellow-500/20 rounded">
                  <p className="text-[10px] text-yellow-500 font-bold mb-1">{rec.title}</p>
                  <p className="text-[10px] text-slate-400 leading-relaxed">{rec.text}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="bg-[#0a0a0a] border-[#10b981]/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-mono text-white">القدرات التجريبية المكتشفة لـ WAF</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-slate-500">تعقيد WAF المستنتج</span>
                <span className="text-yellow-500">{intel?.stats?.intelligenceLevel || "جاري التحليل..."}</span>
              </div>
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-slate-500">دقة الاستنتاج الاستباقي</span>
                <span className="text-[#10b981]">{intel?.stats?.predictionAccuracy || "0%"}</span>
              </div>
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-slate-500">البصمات التي تم تخطيها</span>
                <span className="text-blue-400">{intel?.stats?.bypassedPatterns || 0}</span>
              </div>
              <div className="mt-4 pt-4 border-t border-[#10b981]/10">
                <div className="text-[9px] text-slate-500 font-mono mb-2">مجموعات الأحرف المحظورة المكتشفة:</div>
                <div className="flex flex-wrap gap-1.5">
                  {intel?.blocked_chars?.split(',').map((char: string, i: number) => (
                    <Badge key={i} variant="outline" className="bg-red-500/10 border-red-500/20 text-red-400 text-[10px] font-mono rounded">
                      {char.trim()}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
