import React from 'react';
import { CheckCircle, ShieldAlert } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

export interface RhoBarProps {
  rho: number;
  isStable: boolean;
  regime: 'underload' | 'flow' | 'strain' | 'overload';
  className?: string;
  showDetails?: boolean;
}

/**
 * RhoUtilizationBar Component (MENTOR ONLY)
 * Visualizes student task arrival intensity vs completion rate in M/M/1 queue model.
 *
 * Formula:
 *   Traffic Intensity (rho) = lambda / mu
 *   - Underload: rho < 0.5 (excess idle capacity)
 *   - Flow: 0.5 <= rho < 0.8 (optimal learning engagement)
 *   - Strain: 0.8 <= rho < 1.0 (queue buildup imminent)
 *   - Overload / Unstable: rho >= 1.0 (arrival rate exceeds processing capacity; queue diverges)
 */
export const RhoUtilizationBar: React.FC<RhoBarProps> = ({
  rho,
  isStable,
  regime,
  className,
  showDetails = true,
}) => {
  const cappedRho = Math.min(Math.max(rho || 0, 0), 1.5);
  // Display width percentage on 0-1.2 scale
  const barWidthPercent = Math.min((cappedRho / 1.0) * 100, 100);

  const regimeConfig = {
    underload: {
      label: 'Underload Regime',
      color: 'bg-blue-500',
      textColor: 'text-blue-700',
      badge: 'info' as const,
      desc: 'Arrival rate is significantly below cognitive capacity (rho < 0.50).',
    },
    flow: {
      label: 'Flow Regime',
      color: 'bg-emerald-500',
      textColor: 'text-emerald-700',
      badge: 'success' as const,
      desc: 'Balanced workload with high cognitive momentum and stability (0.50 <= rho < 0.80).',
    },
    strain: {
      label: 'Strain Regime',
      color: 'bg-amber-500',
      textColor: 'text-amber-700',
      badge: 'warning' as const,
      desc: 'Elevated queue buildup; pending tasks risk cascading delays (0.80 <= rho < 1.00).',
    },
    overload: {
      label: 'Overload Regime',
      color: 'bg-red-500',
      textColor: 'text-red-700',
      badge: 'danger' as const,
      desc: 'Cognitive system bottleneck; task arrival rate exceeds processing capacity (rho >= 1.00).',
    },
  }[regime];

  return (
    <div className={cn('space-y-2 w-full', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-700">Traffic Intensity (&rho;)</span>
          <Badge variant={regimeConfig.badge} size="sm">
            {regimeConfig.label}
          </Badge>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-xs">
          <span className="font-bold text-slate-900">{rho.toFixed(2)}</span>
          {!isStable && (
            <span className="inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase bg-red-100 text-red-700">
              <ShieldAlert className="h-3 w-3" /> Unstable (&rho; &ge; 1.0)
            </span>
          )}
          {isStable && (
            <span className="inline-flex items-center gap-0.5 text-[10px] text-emerald-600 font-medium">
              <CheckCircle className="h-3 w-3" /> Stable
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar Container with Zone Markers */}
      <div className="relative h-4 w-full rounded-full bg-slate-100 p-0.5 overflow-hidden border border-slate-200">
        {/* Background Zone Indicators */}
        <div className="absolute inset-0 flex h-full w-full opacity-30 pointer-events-none">
          <div className="w-[50%] bg-blue-200" title="Underload (<0.5)" />
          <div className="w-[30%] bg-emerald-200" title="Flow (0.5-0.8)" />
          <div className="w-[20%] bg-amber-200" title="Strain (0.8-1.0)" />
        </div>

        {/* Fill bar */}
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500 ease-out relative z-10',
            !isStable ? 'bg-red-600 animate-pulse' : regimeConfig.color
          )}
          style={{ width: `${barWidthPercent}%` }}
        />
      </div>

      {/* Scale indicators */}
      <div className="flex justify-between text-[10px] text-slate-400 font-mono px-0.5">
        <span>0.0</span>
        <span>0.5 (Flow)</span>
        <span>0.8 (Strain)</span>
        <span className="text-red-500 font-semibold">1.0 (Critical Limit)</span>
      </div>

      {showDetails && (
        <p className="text-xs text-slate-500 leading-relaxed pt-1">
          {regimeConfig.desc}
        </p>
      )}
    </div>
  );
};

export default RhoUtilizationBar;
