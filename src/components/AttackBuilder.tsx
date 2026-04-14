import React, { useState } from 'react';
import { Plus, ArrowDown, Play, Trash2, Cpu, ShieldAlert, Code, Hash } from 'lucide-react';

type Node = { id: string, type: 'payload' | 'encoder' | 'obfuscator', value: string };

export default function AttackBuilder() {
  const [nodes, setNodes] = useState<Node[]>([
    { id: '1', type: 'payload', value: "1 UNION SELECT 1,2,3--" }
  ]);
  const [result, setResult] = useState("");

  const addNode = (type: Node['type']) => {
    setNodes([...nodes, { id: Math.random().toString(), type, value: type === 'encoder' ? 'url' : type === 'obfuscator' ? 'comments' : '' }]);
  };

  const removeNode = (id: string) => {
    setNodes(nodes.filter(n => n.id !== id));
  };

  const updateNode = (id: string, value: string) => {
    setNodes(nodes.map(n => n.id === id ? { ...n, value } : n));
  };

  const simulateChain = () => {
    let current = "";
    nodes.forEach(node => {
      if (node.type === 'payload') current = node.value;
      if (node.type === 'encoder') {
        if (node.value === 'url') current = encodeURIComponent(current);
        if (node.value === 'base64') current = btoa(current);
        if (node.value === 'hex') current = current.split('').map(c => c.charCodeAt(0).toString(16)).join('');
      }
      if (node.type === 'obfuscator') {
        if (node.value === 'comments') current = `/*${current}*/`;
        if (node.value === 'inline') current = current.replace(/ /g, '/**/');
      }
    });
    setResult(current);
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 h-full">
      {/* Left: Node Builder */}
      <div className="xl:col-span-8 space-y-6">
        <section className="cyber-card p-5 min-h-[500px]">
          <div className="flex items-center justify-between border-b border-cyber-border pb-3 mb-6">
            <h3 className="text-xs font-bold text-cyber-amber uppercase tracking-widest flex items-center gap-2">
              <Cpu className="w-4 h-4" /> منشئ سلسلة الهجوم (Attack Chain Builder)
            </h3>
            <div className="flex gap-2">
              <button onClick={() => addNode('encoder')} className="px-3 py-1.5 bg-cyber-blue/10 text-cyber-blue border border-cyber-blue/30 rounded text-xs font-bold hover:bg-cyber-blue/20 transition-colors flex items-center gap-1"><Plus className="w-3 h-3"/> تشفير</button>
              <button onClick={() => addNode('obfuscator')} className="px-3 py-1.5 bg-cyber-amber/10 text-cyber-amber border border-cyber-amber/30 rounded text-xs font-bold hover:bg-cyber-amber/20 transition-colors flex items-center gap-1"><Plus className="w-3 h-3"/> تمويه</button>
            </div>
          </div>

          <div className="flex flex-col items-center space-y-2">
            {nodes.map((node, index) => (
              <React.Fragment key={node.id}>
                <div className="w-full max-w-2xl bg-black/40 border border-cyber-border rounded-lg p-4 relative group">
                  <button onClick={() => removeNode(node.id)} className="absolute top-3 right-3 text-slate-600 hover:text-cyber-red opacity-0 group-hover:opacity-100 transition-opacity">
                    <Trash2 className="w-4 h-4" />
                  </button>
                  
                  <div className="flex items-start gap-4">
                    <div className={`p-2 rounded-lg ${node.type === 'payload' ? 'bg-cyber-green/20 text-cyber-green' : node.type === 'encoder' ? 'bg-cyber-blue/20 text-cyber-blue' : 'bg-cyber-amber/20 text-cyber-amber'}`}>
                      {node.type === 'payload' ? <Code className="w-5 h-5" /> : node.type === 'encoder' ? <Hash className="w-5 h-5" /> : <ShieldAlert className="w-5 h-5" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-[10px] font-bold uppercase tracking-widest mb-2 text-slate-400">
                        {node.type === 'payload' ? 'الحمولة الأساسية (Base Payload)' : node.type === 'encoder' ? 'عقدة تشفير (Encoder Node)' : 'عقدة تمويه (Obfuscator Node)'}
                      </p>
                      
                      {node.type === 'payload' ? (
                        <input 
                          type="text" 
                          value={node.value} 
                          onChange={(e) => updateNode(node.id, e.target.value)}
                          className="cyber-input font-mono text-sm"
                          placeholder="Enter SQL injection payload..."
                        />
                      ) : node.type === 'encoder' ? (
                        <select value={node.value} onChange={(e) => updateNode(node.id, e.target.value)} className="cyber-input font-mono text-sm">
                          <option value="url">URL Encode</option>
                          <option value="base64">Base64 Encode</option>
                          <option value="hex">Hex Encode</option>
                        </select>
                      ) : (
                        <select value={node.value} onChange={(e) => updateNode(node.id, e.target.value)} className="cyber-input font-mono text-sm">
                          <option value="comments">Wrap with /* */</option>
                          <option value="inline">Inline Comments /**/</option>
                        </select>
                      )}
                    </div>
                  </div>
                </div>
                
                {index < nodes.length - 1 && (
                  <div className="text-cyber-border py-1">
                    <ArrowDown className="w-6 h-6" />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </section>
      </div>

      {/* Right: Output & Execution */}
      <div className="xl:col-span-4 space-y-6">
        <section className="cyber-card p-5">
          <h3 className="text-xs font-bold text-cyber-green uppercase tracking-widest flex items-center gap-2 border-b border-cyber-border pb-3 mb-4">
            <Play className="w-4 h-4" /> محاكاة السلسلة (Chain Simulation)
          </h3>
          
          <button onClick={simulateChain} className="cyber-button cyber-button-primary w-full justify-center mb-6">
            توليد الحمولة النهائية
          </button>

          <div className="space-y-2">
            <label className="cyber-label">النتيجة (Final Output)</label>
            <div className="bg-black/60 border border-cyber-border rounded-lg p-4 min-h-[150px] break-all font-mono text-sm text-cyber-green">
              {result || <span className="text-slate-600 italic">اضغط على توليد لرؤية النتيجة...</span>}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
