import React, { useState, useEffect } from 'react';
import { Database, Plus, Trash2, ExternalLink, Shield, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

interface Target {
  url: string;
  waf_name: string;
  db_type: string;
  lastAttack: string;
}

export default function Targets() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [newUrl, setNewUrl] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTargets = async () => {
      try {
        const response = await fetch('/api/targets');
        if (response.ok) {
          const data = await response.json();
          setTargets(data.map((d: any) => ({
            url: d.target_url,
            waf_name: d.waf_name,
            db_type: d.db_type,
            lastAttack: d.last_updated
          })));
        }
      } catch (e) {
        console.error("Failed to fetch targets", e);
      }
    };
    fetchTargets();
  }, []);

  const handleTargetClick = (url: string) => {
    navigate(`/dashboard?target=${encodeURIComponent(url)}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white font-mono">بيئات التطبيقات <span className="text-[#10b981]">المستهدفة</span></h1>
        <div className="flex gap-2">
          <Input 
            type="text" 
            placeholder="إضافة رابط بيئة اختبار جديدة..."
            value={newUrl}
            dir="ltr"
            onChange={(e) => setNewUrl(e.target.value)}
            className="w-64 bg-black/40 border-[#10b981]/20 focus-visible:ring-[#10b981]/50 text-slate-200 font-mono text-left placeholder:text-right"
          />
          <Button className="bg-[#10b981] hover:bg-[#10b981]/80 text-black font-bold flex items-center gap-2">
            <Plus className="w-4 h-4" />
            إدراج الهدف
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {targets.length > 0 ? targets.map((target, i) => (
          <Card key={i} className="bg-[#0a0a0a] border-[#10b981]/20 hover:border-[#10b981]/40 transition-all group overflow-hidden">
            <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-4 cursor-pointer" onClick={() => handleTargetClick(target.url)}>
                <div className="w-10 h-10 rounded-lg bg-[#10b981]/10 flex items-center justify-center group-hover:bg-[#10b981]/20 transition-colors">
                  <Shield className="w-5 h-5 text-[#10b981]" />
                </div>
                <div>
                  <h3 className="text-sm font-mono text-white flex items-center gap-2 group-hover:text-[#10b981] transition-colors" dir="ltr">
                    {target.url}
                    <ExternalLink className="w-3 h-3 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer mx-2" />
                  </h3>
                  <div className="flex flex-wrap gap-3 mt-1">
                    <span className="text-[10px] font-mono text-slate-500">آخر قياس (Telemetry): {new Date(target.lastAttack).toLocaleString('ar-EG')}</span>
                    <span className="text-[10px] font-mono text-[#10b981]">DB: {target.db_type}</span>
                    <span className="text-[10px] font-mono text-blue-400">WAF: {target.waf_name}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-4 self-end sm:self-auto">
                <Button 
                  variant="outline"
                  size="sm"
                  onClick={() => handleTargetClick(target.url)}
                  className="h-8 text-[10px] font-bold bg-[#10b981]/10 text-[#10b981] border-[#10b981]/20 hover:bg-[#10b981]/20 hover:text-[#10b981]"
                >
                  <Eye className="w-3 h-3 ml-2" />
                  تحليل المقاييس
                </Button>
                <Button variant="ghost" size="icon" className="text-slate-500 hover:text-red-500 hover:bg-red-500/10">
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )) : (
          <Card className="bg-[#0a0a0a] border-dashed border-[#10b981]/20">
            <CardContent className="p-12 text-center flex flex-col items-center">
              <Database className="w-12 h-12 text-[#10b981] opacity-20 mx-auto mb-4" />
              <p className="text-slate-500 font-mono text-sm">لا توجد بيئات مستهدفة مسجلة. قم ببدء خط الاختبار من المختبر لتوليد بيانات القياس عن بعد.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
