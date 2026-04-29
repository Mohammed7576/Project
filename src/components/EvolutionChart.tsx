import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAttack } from '../context/AttackContext';

export function EvolutionChart() {
  const { attemptHistory } = useAttack();

  // Process data for chart: Average score per generation
  const chartData = React.useMemo(() => {
    const genMap = new Map<number, { gen: number; sum: number; count: number; max: number }>();
    
    attemptHistory.forEach(att => {
      const g = att.gen;
      const current = genMap.get(g) || { gen: g, sum: 0, count: 0, max: 0 };
      current.sum += att.score;
      current.count += 1;
      current.max = Math.max(current.max, att.score);
      genMap.set(g, current);
    });

    return Array.from(genMap.values())
      .sort((a, b) => a.gen - b.gen)
      .map(d => ({
        gen: d.gen + 1,
        avg: parseFloat((d.sum / d.count).toFixed(2)),
        max: parseFloat(d.max.toFixed(2))
      }));
  }, [attemptHistory]);

  if (chartData.length === 0) {
    return (
      <div id="no-data-chart" className="flex items-center justify-center h-full bg-slate-900/10 rounded-xl border border-dashed border-slate-700/50">
        <p className="text-slate-500 text-sm">Waiting for evolution data...</p>
      </div>
    );
  }

  return (
    <div id="evolution-chart-container" className="h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis 
            dataKey="gen" 
            stroke="#94a3b8" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false}
            label={{ value: 'Generation', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 10 }}
          />
          <YAxis 
            stroke="#94a3b8" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false}
            domain={[0, 1]}
            ticks={[0, 0.25, 0.5, 0.75, 1]}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
            labelStyle={{ color: '#94a3b8' }}
            itemStyle={{ color: '#f8fafc' }}
          />
          <Line 
            type="monotone" 
            dataKey="max" 
            stroke="#10b981" 
            strokeWidth={3} 
            dot={{ fill: '#10b981', r: 4 }} 
            activeDot={{ r: 6 }} 
            name="Max Score"
          />
          <Line 
            type="monotone" 
            dataKey="avg" 
            stroke="#3b82f6" 
            strokeWidth={2} 
            dot={false}
            strokeDasharray="5 5"
            name="Avg Score"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
