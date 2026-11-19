import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { formatDate } from '@/lib/utils';

export interface WorkloadDataPoint {
  date: string;
  incomingWorkload: number;
  completedWorkload: number;
  weightedWorkload: number;
}

export interface WorkloadTimelineProps {
  data?: WorkloadDataPoint[];
  height?: number;
  className?: string;
}

export const WorkloadTimeline: React.FC<WorkloadTimelineProps> = ({
  data = defaultData,
  height = 280,
  className,
}) => {
  return (
    <div className={`w-full ${className || ''}`}>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="incomingGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="weightedGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#818cf8" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#818cf8" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={(val) => formatDate(val, 'MMM d')}
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
          />
          <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-lg text-xs">
                    <p className="font-semibold text-slate-700 mb-1.5">{formatDate(label)}</p>
                    {payload.map((entry, index) => (
                      <div key={`item-${index}`} className="flex items-center justify-between gap-4 py-0.5">
                        <span className="flex items-center gap-1.5 text-slate-600">
                          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
                          {entry.name}:
                        </span>
                        <span className="font-semibold text-slate-900">
                          {Number(entry.value).toFixed(1)} hrs
                        </span>
                      </div>
                    ))}
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend
            verticalAlign="top"
            align="right"
            wrapperStyle={{ paddingBottom: 12, fontSize: 11 }}
          />
          <Area
            type="monotone"
            dataKey="incomingWorkload"
            name="Incoming Workload"
            stroke="#0ea5e9"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#incomingGrad)"
          />
          <Area
            type="monotone"
            dataKey="weightedWorkload"
            name="Weighted Queue Workload"
            stroke="#6366f1"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#weightedGrad)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// Fallback timeline data over recent 14 days
const defaultData: WorkloadDataPoint[] = [
  { date: '2026-11-06', incomingWorkload: 8.0, completedWorkload: 7.5, weightedWorkload: 9.0 },
  { date: '2026-11-08', incomingWorkload: 12.0, completedWorkload: 9.0, weightedWorkload: 11.5 },
  { date: '2026-11-10', incomingWorkload: 15.5, completedWorkload: 8.0, weightedWorkload: 16.0 },
  { date: '2026-11-12', incomingWorkload: 11.0, completedWorkload: 10.0, weightedWorkload: 14.5 },
  { date: '2026-11-14', incomingWorkload: 18.0, completedWorkload: 6.5, weightedWorkload: 21.0 },
  { date: '2026-11-16', incomingWorkload: 14.0, completedWorkload: 11.0, weightedWorkload: 19.5 },
  { date: '2026-11-18', incomingWorkload: 16.5, completedWorkload: 9.5, weightedWorkload: 22.0 },
];

export default WorkloadTimeline;
