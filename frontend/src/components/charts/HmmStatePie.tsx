import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { DominantCognitiveState } from '@/types';
import { Badge } from '@/components/ui/Badge';

export interface HmmStatePieProps {
  p_underload: number;
  p_flow: number;
  p_overload: number;
  p_fatigue: number;
  dominantState: DominantCognitiveState;
  className?: string;
  size?: number;
}

/**
 * HmmStatePie Component (MENTOR ONLY)
 * Visualizes posterior state probabilities from Model 4 (Hidden Markov Model).
 *
 * Latent cognitive states:
 * - Underload: Insufficient cognitive demand; disengagement risk
 * - Flow: Balanced equilibrium of challenge and cognitive resource
 * - Overload: Demand exceeds working memory; queue accumulation
 * - Fatigue: Depleted executive function; reduced throughput mu
 */
export const HmmStatePie: React.FC<HmmStatePieProps> = ({
  p_underload,
  p_flow,
  p_overload,
  p_fatigue,
  dominantState,
  className,
  size = 220,
}) => {
  const data = [
    {
      name: 'Flow',
      value: Math.round((p_flow || 0) * 100),
      color: '#22c55e', // Emerald
      raw: p_flow,
    },
    {
      name: 'Underload',
      value: Math.round((p_underload || 0) * 100),
      color: '#3b82f6', // Blue
      raw: p_underload,
    },
    {
      name: 'Fatigue',
      value: Math.round((p_fatigue || 0) * 100),
      color: '#f59e0b', // Amber
      raw: p_fatigue,
    },
    {
      name: 'Overload',
      value: Math.round((p_overload || 0) * 100),
      color: '#ef4444', // Red
      raw: p_overload,
    },
  ];

  const dominantBadge = {
    flow: { label: 'Dominant: Flow', variant: 'success' as const },
    underload: { label: 'Dominant: Underload', variant: 'info' as const },
    fatigue: { label: 'Dominant: Fatigue', variant: 'warning' as const },
    overload: { label: 'Dominant: Overload', variant: 'danger' as const },
  }[dominantState] || { label: 'Dominant: Unknown', variant: 'secondary' as const };

  return (
    <div className={`flex flex-col items-center w-full ${className || ''}`}>
      <div className="mb-2 flex items-center justify-between w-full px-2">
        <span className="text-xs font-semibold text-slate-700">Model 4 HMM State Posterior</span>
        <Badge variant={dominantBadge.variant} size="sm">
          {dominantBadge.label}
        </Badge>
      </div>

      <div style={{ width: '100%', height: size }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={size * 0.25}
              outerRadius={size * 0.42}
              paddingAngle={3}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#ffffff" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0];
                  return (
                    <div className="rounded-lg border border-slate-200 bg-white p-2.5 shadow-md text-xs">
                      <p className="font-semibold text-slate-800">{item.name} State</p>
                      <p className="text-slate-600">
                        Probability: <span className="font-bold">{item.value}%</span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend
              layout="horizontal"
              verticalAlign="bottom"
              align="center"
              wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default HmmStatePie;
