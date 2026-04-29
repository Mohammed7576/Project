import React from 'react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import { useAttack } from '../context/AttackContext';

export function TelemetryDashboard() {
  const { telemetryHistory } = useAttack();

  const latestData = React.useMemo(() => {
    if (telemetryHistory.length === 0) return [];
    
    // Group by island and get latest for each
    const islands = new Map<number, any>();
    telemetryHistory.forEach(item => {
      islands.set(item.island, item);
    });

    return Array.from(islands.values()).map(island => ({
      name: `Island ${island.island}`,
      score: island.max_score * 100,
      diversity: island.diversity * 100,
      intensity: (island.intensity / 6) * 100, // Normalized 1-6
      stability: (1 - (island.stagnation / 10)) * 100, // Normalized 0-10
      fullMark: 100,
    }));
  }, [telemetryHistory]);

  const historyData = React.useMemo(() => {
    // Average across islands per generation
    const genMap = new Map<number, { gen: number; diversity: number; intensity: number; count: number }>();
    
    telemetryHistory.forEach(item => {
      const g = item.gen;
      const current = genMap.get(g) || { gen: g, diversity: 0, intensity: 0, count: 0 };
      current.diversity += item.diversity;
      current.intensity += item.intensity;
      current.count += 1;
      genMap.set(g, current);
    });

    return Array.from(genMap.values())
      .sort((a, b) => a.gen - b.gen)
      .map(d => ({
        gen: d.gen + 1,
        diversity: parseFloat((d.diversity / d.count).toFixed(2)),
        intensity: parseFloat((d.intensity / d.count).toFixed(1))
      }));
  }, [telemetryHistory]);

  if (telemetryHistory.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 text-sm italic">
        Awaiting swarm intelligence synchronization...
      </div>
    );
  }

  return (
    <div id="telemetry-dashboard" className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      {/* Real-time Swarm Distribution */}
      <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-800/50">
        <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
            Island Capability Map
        </h3>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={latestData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="name" stroke="#94a3b8" fontSize={10} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#475569" fontSize={8} />
              <Radar name="Fitness" dataKey="score" stroke="#ef4444" fill="#ef4444" fillOpacity={0.4} />
              <Radar name="Diversity" dataKey="diversity" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.4} />
              <Radar name="Chaos" dataKey="intensity" stroke="#10b981" fill="#10b981" fillOpacity={0.4} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                itemStyle={{ fontSize: '10px' }}
              />
              <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Swarm Dynamics History */}
      <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-800/50">
        <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Swarm Dynamics History</h3>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="gen" stroke="#64748b" fontSize={10} />
              <YAxis yAxisId="left" stroke="#64748b" fontSize={10} label={{ value: 'Diversity', angle: -90, position: 'insideLeft', fill: '#3b82f6', fontSize: 10 }} />
              <YAxis yAxisId="right" orientation="right" stroke="#64748b" fontSize={10} label={{ value: 'Intensity', angle: 90, position: 'insideRight', fill: '#10b981', fontSize: 10 }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
              />
              <Line yAxisId="left" type="monotone" dataKey="diversity" stroke="#3b82f6" strokeWidth={2} dot={false} name="Genotypic Diversity" />
              <Line yAxisId="right" type="monotone" dataKey="intensity" stroke="#10b981" strokeWidth={2} dot={false} name="Mutation Pressure" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
