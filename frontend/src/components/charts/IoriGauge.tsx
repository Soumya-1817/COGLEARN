import React from 'react';
import { ResponsiveContainer, RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts';
import { RiskZone } from '@/types';
import { Badge } from '@/components/ui/Badge';

export interface IoriGaugeProps {
  value: number; // 0.0 - 1.0
  riskZone?: RiskZone;
  className?: string;
  size?: number;
}

/**
 * IoriGauge Component (MENTOR ONLY)
 * Visualizes the Index of Overload & Resilience Indicator (IORI).
 *
 * Mathematical thresholds:
 * - Green (< 0.30): Low cognitive strain / resilient regime
 * - Yellow (0.30 - 0.59): Moderate strain / monitor queue growth
 * - Red (>= 0.60): Critical overload / requires proactive intervention
 */
export const IoriGauge: React.FC<IoriGaugeProps> = ({
  value,
  riskZone: propRiskZone,
  className,
  size = 200,
}) => {
  const normalizedValue = Math.min(Math.max(value || 0, 0), 1);
  const percentage = Math.round(normalizedValue * 100);

  const riskZone: RiskZone =
    propRiskZone || (normalizedValue >= 0.6 ? 'red' : normalizedValue >= 0.3 ? 'yellow' : 'green');

  const zoneConfig = {
    green: {
      color: '#22c55e',
      label: 'Low Risk (Green)',
      badgeVariant: 'success' as const,
      description: 'Cognitive load is well within sustainable capacity.',
    },
    yellow: {
      color: '#eab308',
      label: 'Moderate Risk (Yellow)',
      badgeVariant: 'warning' as const,
      description: 'Approaching queue congestion threshold. Monitor closely.',
    },
    red: {
      color: '#ef4444',
      label: 'High Overload Risk (Red)',
      badgeVariant: 'danger' as const,
      description: 'Immediate pedagogical or workload intervention advised.',
    },
  }[riskZone];

  const chartData = [
    {
      name: 'IORI',
      value: normalizedValue * 100,
      fill: zoneConfig.color,
    },
  ];

  return (
    <div className={`flex flex-col items-center justify-center text-center p-2 ${className || ''}`}>
      <div className="relative flex items-center justify-center" style={{ width: size, height: size * 0.65 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="80%"
            innerRadius="75%"
            outerRadius="105%"
            barSize={16}
            data={chartData}
            startAngle={180}
            endAngle={0}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar
              background={{ fill: '#f1f5f9' }}
              dataKey="value"
              cornerRadius={8}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        {/* Center score readout */}
        <div className="absolute top-[38%] flex flex-col items-center justify-center">
          <span className="text-3xl font-extrabold tracking-tight text-slate-900">
            {normalizedValue.toFixed(2)}
          </span>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            {percentage}% Index
          </span>
        </div>
      </div>

      <div className="mt-1 flex flex-col items-center gap-1">
        <Badge variant={zoneConfig.badgeVariant} size="md">
          {zoneConfig.label}
        </Badge>
        <p className="text-xs text-slate-500 max-w-[220px] mt-1">{zoneConfig.description}</p>
      </div>

      {/* Threshold markings */}
      <div className="flex justify-between w-full max-w-[210px] text-[10px] text-slate-400 font-mono mt-3 px-2 border-t border-slate-100 pt-1.5">
        <span>0.00 (Min)</span>
        <span className="text-amber-500">0.30</span>
        <span className="text-red-500">0.60</span>
        <span>1.00 (Max)</span>
      </div>
    </div>
  );
};

export default IoriGauge;
