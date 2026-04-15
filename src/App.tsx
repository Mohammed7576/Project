import React from 'react';

export default function App() {
  return (
    <div className="min-h-screen bg-[#050505] text-[#10b981] flex flex-col items-center justify-center font-mono p-4">
      <div className="border-2 border-[#10b981] p-8 rounded-lg shadow-[0_0_20px_rgba(16,185,129,0.2)] text-center max-w-lg w-full">
        <h1 className="text-2xl font-bold mb-4 uppercase tracking-widest">System Reset Complete</h1>
        <div className="h-px w-full bg-[#10b981]/30 my-4"></div>
        <p className="mb-6 text-slate-300">تم مسح جميع ملفات الواجهة القديمة بنجاح.</p>
        
        <div className="bg-black/50 p-4 rounded border border-[#10b981]/20 text-sm text-left mb-6">
          <p className="text-cyber-blue animate-pulse">&gt; Waiting for new UI modules...</p>
          <p className="text-slate-500">&gt; Ready to build interface by interface.</p>
        </div>

        <p className="text-xs text-slate-500">
          أخبرني: ما هي أول واجهة تريد أن نبدأ بتصميمها؟
        </p>
      </div>
    </div>
  );
}
