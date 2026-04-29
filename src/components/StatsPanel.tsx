import React from 'react';
import { useAttack } from '../context/AttackContext';
import { Target, Zap, Waves, ShieldAlert } from 'lucide-react';

export function StatsPanel() {
  const { attemptHistory, currentGeneration, generations } = useAttack();

  const stats = React.useMemo(() => {
    const total = attemptHistory.length;
    const successes = attemptHistory.filter(a => a.score >= 0.7).length;
    const blocks = attemptHistory.filter(a => a.score <= 0.1).length;
    const avgLatency = total > 0 ? attemptHistory.reduce((acc, curr) => acc + (curr.latency || 0), 0) / total : 0;
    
    return {
      successRate: total > 0 ? (successes / total) * 100 : 0,
      blockRate: total > 0 ? (blocks / total) * 100 : 0,
      latency: Math.round(avgLatency),
      efficiency: total > 0 ? (successes / (currentGeneration + 1)) : 0
    };
  }, [attemptHistory, currentGeneration]);

  return (
    <div id="stats-panel" className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 flex items-center space-x-4">
        <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-500">
          <Target className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Success Rate</p>
          <p className="text-2xl font-bold text-slate-100">{stats.successRate.toFixed(1)}%</p>
        </div>
      </div>

      <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 flex items-center space-x-4">
        <div className="p-3 bg-amber-500/10 rounded-lg text-amber-500">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Block Rate</p>
          <p className="text-2xl font-bold text-slate-100">{stats.blockRate.toFixed(1)}%</p>
        </div>
      </div>

      <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 flex items-center space-x-4">
        <div className="p-3 bg-blue-500/10 rounded-lg text-blue-500">
          <Zap className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Avg Latency</p>
          <p className="text-2xl font-bold text-slate-100">{stats.latency}ms</p>
        </div>
      </div>

      <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 flex items-center space-x-4">
        <div className="p-3 bg-indigo-500/10 rounded-lg text-indigo-500">
          <Waves className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Progress</p>
          <p className="text-2xl font-bold text-slate-100">{currentGeneration + 1} / {generations}</p>
        </div>
      </div>
    </div>
  );
}
