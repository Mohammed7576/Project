import React, { useState } from 'react';
import { Play, Code, Hash, FileText, RefreshCw, ArrowRight, ShieldAlert, Activity, Globe } from 'lucide-react';

export default function Sandbox({ defaultUrl }: { defaultUrl: string }) {
  const [url, setUrl] = useState(defaultUrl || 'http://localhost/');
  const [payload, setPayload] = useState("1' OR '1'='1");
  const [method, setMethod] = useState('GET');
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const applyMutation = (type: string) => {
    let newPayload = payload;
    switch(type) {
      case 'url': newPayload = encodeURIComponent(payload); break;
      case 'base64': newPayload = btoa(payload); break;
      case 'hex': newPayload = payload.split('').map(c => c.charCodeAt(0).toString(16)).join(''); break;
      case 'comment': newPayload = `/*${payload}*/`; break;
      case 'inline': newPayload = payload.replace(/ /g, '/**/'); break;
    }
    setPayload(newPayload);
  };

  const handleSend = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/sandbox', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, method, payload })
      });
      const data = await res.json();
      setResponse(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      {/* Left: Request Configuration */}
      <div className="space-y-6">
        <section className="cyber-card p-5 space-y-4">
          <h3 className="text-xs font-bold text-cyber-blue uppercase tracking-widest flex items-center gap-2 border-b border-cyber-border pb-3">
            <Code className="w-4 h-4" /> تكوين الطلب (Request Setup)
          </h3>
          
          <div className="flex gap-3">
            <select 
              value={method} 
              onChange={(e) => setMethod(e.target.value)}
              className="cyber-input w-24 font-bold text-cyber-amber"
            >
              <option>GET</option>
              <option>POST</option>
            </select>
            <div className="relative flex-1">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input 
                type="text" 
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="cyber-input pl-10 font-mono text-sm"
                placeholder="http://target.local/page.php?id="
              />
            </div>
          </div>

          <div>
            <label className="cyber-label flex justify-between">
              <span>الحمولة (Payload)</span>
              <span className="text-slate-600">{payload.length} chars</span>
            </label>
            <textarea 
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              className="cyber-input font-mono text-sm h-32 resize-none"
              placeholder="Enter your injection payload here..."
            />
          </div>

          <div className="space-y-2">
            <label className="cyber-label">فلاتر التمويه السريعة (Quick Mutations)</label>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => applyMutation('url')} className="px-3 py-1.5 bg-black/40 border border-cyber-border rounded text-xs font-mono hover:border-cyber-blue hover:text-cyber-blue transition-colors">URL Encode</button>
              <button onClick={() => applyMutation('base64')} className="px-3 py-1.5 bg-black/40 border border-cyber-border rounded text-xs font-mono hover:border-cyber-blue hover:text-cyber-blue transition-colors">Base64</button>
              <button onClick={() => applyMutation('hex')} className="px-3 py-1.5 bg-black/40 border border-cyber-border rounded text-xs font-mono hover:border-cyber-blue hover:text-cyber-blue transition-colors">Hex</button>
              <button onClick={() => applyMutation('comment')} className="px-3 py-1.5 bg-black/40 border border-cyber-border rounded text-xs font-mono hover:border-cyber-blue hover:text-cyber-blue transition-colors">/* Wrap */</button>
              <button onClick={() => applyMutation('inline')} className="px-3 py-1.5 bg-black/40 border border-cyber-border rounded text-xs font-mono hover:border-cyber-blue hover:text-cyber-blue transition-colors">Inline /**/</button>
            </div>
          </div>

          <button 
            onClick={handleSend}
            disabled={loading}
            className="cyber-button cyber-button-primary w-full justify-center mt-4"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {loading ? 'جاري الإرسال...' : 'إرسال الحمولة (Execute)'}
          </button>
        </section>
      </div>

      {/* Right: Response Viewer */}
      <div className="space-y-6">
        <section className="cyber-card p-5 h-full flex flex-col">
          <h3 className="text-xs font-bold text-cyber-green uppercase tracking-widest flex items-center gap-2 border-b border-cyber-border pb-3 mb-4">
            <Activity className="w-4 h-4" /> استجابة الهدف (Target Response)
          </h3>
          
          {response ? (
            <div className="flex-1 flex flex-col space-y-4">
              <div className="flex gap-4">
                <div className="p-3 bg-black/40 rounded-lg border border-cyber-border flex-1">
                  <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">Status</p>
                  <p className={`text-xl font-display font-bold ${response.status === 200 ? 'text-cyber-green' : response.status >= 400 ? 'text-cyber-red' : 'text-cyber-amber'}`}>
                    {response.status}
                  </p>
                </div>
                <div className="p-3 bg-black/40 rounded-lg border border-cyber-border flex-1">
                  <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">Latency</p>
                  <p className="text-xl font-display font-bold text-cyber-blue">
                    {response.latency} <span className="text-sm text-slate-500">ms</span>
                  </p>
                </div>
                <div className="p-3 bg-black/40 rounded-lg border border-cyber-border flex-1">
                  <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">Size</p>
                  <p className="text-xl font-display font-bold text-slate-300">
                    {response.data?.length || 0} <span className="text-sm text-slate-500">B</span>
                  </p>
                </div>
              </div>

              <div className="flex-1 bg-black/60 border border-cyber-border rounded-lg p-3 overflow-hidden flex flex-col">
                <p className="text-[10px] text-slate-500 font-bold uppercase mb-2">Response Body</p>
                <div className="flex-1 overflow-auto custom-scrollbar">
                  <pre className="text-xs font-mono text-slate-400 whitespace-pre-wrap break-all">
                    {response.data}
                  </pre>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-600 space-y-3 opacity-50">
              <ShieldAlert className="w-12 h-12" />
              <p className="text-sm font-mono">في انتظار إرسال الحمولة...</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
