import React from 'react';

export default function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <h1 className="text-2xl font-mono text-[#10b981] mb-2">{title}</h1>
        <p className="text-slate-500 font-mono text-sm">الوحدة قيد الإنشاء...</p>
      </div>
    </div>
  );
}
