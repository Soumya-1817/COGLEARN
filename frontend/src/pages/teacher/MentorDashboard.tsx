import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Search,
  Filter,
  AlertTriangle,
  ArrowRight,
  Radio,
  Clock,
  ShieldAlert,
  UserCheck,
  Activity,
  Layers,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { get } from '@/lib/api';
import { StudentAnalytics, RiskZone } from '@/types';
import { useAuth } from '@/hooks/useAuth';
import { useMentorFeed } from '@/hooks/useMentorFeed';
import { getRiskZoneColor, getRegimeFromRho, formatRelative } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { RhoUtilizationBar } from '@/components/charts/RhoUtilizationBar';

export const MentorDashboard: React.FC = () => {
  const { user } = useAuth();
  const [search, setSearch] = useState('');
  const [selectedZone, setSelectedZone] = useState<RiskZone | 'all'>('all');

  // Real-time WebSocket hook for mentor feed
  const { alerts, isConnected, clearAlerts } = useMentorFeed(user?.id || 'tch-demo-1');

  // Query assigned students analytics
  const { data: students = defaultStudents, isLoading } = useQuery({
    queryKey: ['mentor_students_analytics'],
    queryFn: async (): Promise<StudentAnalytics[]> => {
      try {
        return await get<StudentAnalytics[]>('/mentor/students');
      } catch {
        return defaultStudents;
      }
    },
    refetchInterval: 15000,
  });

  const filteredStudents = students.filter((s) => {
    const matchesSearch = s.student_name.toLowerCase().includes(search.toLowerCase()) ||
      (s.email && s.email.toLowerCase().includes(search.toLowerCase()));
    const matchesZone = selectedZone === 'all' || s.risk_zone === selectedZone;
    return matchesSearch && matchesZone;
  });

  const redCount = students.filter((s) => s.risk_zone === 'red').length;
  const yellowCount = students.filter((s) => s.risk_zone === 'yellow').length;
  const greenCount = students.filter((s) => s.risk_zone === 'green').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-amber-500" />
            Mentor Cognitive Risk Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time IORI indicators, queuing bottleneck trajectories (&rho;), and academic intervention tracking.
          </p>
        </div>

        {/* Live WebSocket Status Indicator */}
        <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 shadow-xs">
          <span className="relative flex h-3 w-3">
            {isConnected && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            )}
            <span
              className={`relative inline-flex rounded-full h-3 w-3 ${
                isConnected ? 'bg-emerald-500' : 'bg-slate-300'
              }`}
            />
          </span>
          <span className="text-xs font-semibold text-slate-700">
            {isConnected ? 'Live WebSocket Active' : 'Connecting to Feed...'}
          </span>
        </div>
      </div>

      {/* Mandatory Disclaimer */}
      <Alert variant="warning" title="Pedagogical Decision Support Disclaimer">
        IORI is an academic load indicator, not a medical diagnosis. Indicator values reflect queue buildup and task arrival rate ratios to aid instructional pacing.
      </Alert>

      {/* Real-time Alert Stream Banner (if alerts received from WebSocket) */}
      {alerts.length > 0 && (
        <Card className="border-red-200 bg-red-50/40">
          <CardHeader className="py-3 px-5 flex flex-row items-center justify-between border-b border-red-100">
            <div className="flex items-center gap-2 text-red-900 font-bold text-xs uppercase tracking-wider">
              <Radio className="h-4 w-4 text-red-600 animate-pulse" />
              Real-time Inflow Alerts ({alerts.length})
            </div>
            <button onClick={clearAlerts} className="text-xs text-red-700 hover:underline font-medium">
              Dismiss All
            </button>
          </CardHeader>
          <CardContent className="p-3 max-h-32 overflow-y-auto space-y-2">
            {alerts.slice(0, 3).map((alert, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs bg-white p-2 rounded-lg border border-red-200 shadow-2xs">
                <span className="font-semibold text-slate-800">
                  {alert.student_name}: IORI jumped to <strong className="text-red-600">{alert.iori.toFixed(2)}</strong>
                </span>
                <span className="text-[10px] text-slate-400">{formatRelative(alert.timestamp)}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Risk Zone Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Red Zone */}
        <div
          onClick={() => setSelectedZone(selectedZone === 'red' ? 'all' : 'red')}
          className={`cursor-pointer rounded-2xl border p-5 transition-all shadow-xs ${
            selectedZone === 'red' ? 'ring-2 ring-red-500 bg-red-50/80 border-red-300' : 'bg-white border-slate-200 hover:border-red-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-red-700 uppercase tracking-wider">
              Critical Overload (Red &ge; 0.6)
            </span>
            <Badge variant="danger" size="sm">Urgent</Badge>
          </div>
          <h3 className="text-3xl font-extrabold text-red-600 mt-2">{redCount}</h3>
          <p className="text-xs text-slate-500 mt-1">Requires deadline review or workload extension</p>
        </div>

        {/* Yellow Zone */}
        <div
          onClick={() => setSelectedZone(selectedZone === 'yellow' ? 'all' : 'yellow')}
          className={`cursor-pointer rounded-2xl border p-5 transition-all shadow-xs ${
            selectedZone === 'yellow' ? 'ring-2 ring-amber-500 bg-amber-50/80 border-amber-300' : 'bg-white border-slate-200 hover:border-amber-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-amber-700 uppercase tracking-wider">
              Moderate Strain (Yellow 0.3 - 0.59)
            </span>
            <Badge variant="warning" size="sm">Monitor</Badge>
          </div>
          <h3 className="text-3xl font-extrabold text-amber-600 mt-2">{yellowCount}</h3>
          <p className="text-xs text-slate-500 mt-1">Elevated task queue buildup in progress</p>
        </div>

        {/* Green Zone */}
        <div
          onClick={() => setSelectedZone(selectedZone === 'green' ? 'all' : 'green')}
          className={`cursor-pointer rounded-2xl border p-5 transition-all shadow-xs ${
            selectedZone === 'green' ? 'ring-2 ring-emerald-500 bg-emerald-50/80 border-emerald-300' : 'bg-white border-slate-200 hover:border-emerald-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">
              Resilient / Low Risk (Green &lt; 0.3)
            </span>
            <Badge variant="success" size="sm">Stable</Badge>
          </div>
          <h3 className="text-3xl font-extrabold text-emerald-600 mt-2">{greenCount}</h3>
          <p className="text-xs text-slate-500 mt-1">Sustained flow and processing equilibrium</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative max-w-sm w-full">
          <Input
            placeholder="Search students by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={selectedZone === 'all' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSelectedZone('all')}
          >
            All Students ({students.length})
          </Button>
          <Button
            variant={selectedZone === 'red' ? 'danger' : 'outline'}
            size="sm"
            onClick={() => setSelectedZone('red')}
          >
            Red Zone ({redCount})
          </Button>
          <Button
            variant={selectedZone === 'yellow' ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => setSelectedZone('yellow')}
          >
            Yellow Zone ({yellowCount})
          </Button>
          <Button
            variant={selectedZone === 'green' ? 'success' : 'outline'}
            size="sm"
            onClick={() => setSelectedZone('green')}
          >
            Green Zone ({greenCount})
          </Button>
        </div>
      </div>

      {/* Students Analytics Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student</TableHead>
                <TableHead>Latest IORI</TableHead>
                <TableHead>Dominant State</TableHead>
                <TableHead>Queue Traffic Intensity (&rho;)</TableHead>
                <TableHead>Tasks (Pending / Overdue)</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredStudents.map((s) => {
                const zoneColor = getRiskZoneColor(s.risk_zone);
                const regime = getRegimeFromRho(s.latest_rho, s.is_stable);

                return (
                  <TableRow key={s.student_id} className={s.risk_zone === 'red' ? 'bg-red-50/20' : ''}>
                    <TableCell className="font-medium text-slate-900">
                      <div>
                        <span className="font-semibold">{s.student_name}</span>
                        <p className="text-xs text-slate-400">{s.email || `${s.student_id}@university.edu`}</p>
                      </div>
                    </TableCell>

                    <TableCell>
                      <span className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-mono font-bold ${zoneColor.badge}`}>
                        {s.latest_iori.toFixed(2)}
                      </span>
                    </TableCell>

                    <TableCell>
                      <span className="inline-flex items-center gap-1 text-xs font-semibold capitalize text-slate-700">
                        <Activity className="h-3.5 w-3.5 text-slate-400" />
                        {s.dominant_state}
                      </span>
                    </TableCell>

                    <TableCell className="min-w-[180px]">
                      <RhoUtilizationBar
                        rho={s.latest_rho}
                        isStable={s.is_stable}
                        regime={regime}
                        showDetails={false}
                      />
                    </TableCell>

                    <TableCell className="text-xs text-slate-600">
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-slate-900">{s.pending_tasks} pending</span>
                        {s.overdue_tasks > 0 && (
                          <Badge variant="danger" size="sm">
                            {s.overdue_tasks} overdue
                          </Badge>
                        )}
                      </div>
                    </TableCell>

                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link to={`/teacher/mentor/students/${s.student_id}`}>
                          <Button variant="outline" size="sm" className="text-xs">
                            View Analytics
                          </Button>
                        </Link>
                        {s.latest_iori >= 0.6 && (
                          <Link to={`/teacher/interventions/new?studentId=${s.student_id}`}>
                            <Button variant="danger" size="sm" className="text-xs">
                              Intervene
                            </Button>
                          </Link>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

// Fallback demo student analytics
const defaultStudents: StudentAnalytics[] = [
  {
    student_id: 'std-101',
    student_name: 'Marcus Bell',
    email: 'marcus.bell@university.edu',
    latest_iori: 0.74,
    risk_zone: 'red',
    iori_history: [
      { date: '2026-11-04', iori: 0.35 },
      { date: '2026-11-08', iori: 0.48 },
      { date: '2026-11-12', iori: 0.62 },
      { date: '2026-11-16', iori: 0.71 },
      { date: '2026-11-19', iori: 0.74 },
    ],
    latest_rho: 1.15,
    is_stable: false,
    queue_length: 6,
    pending_tasks: 6,
    overdue_tasks: 3,
    total_weighted_workload: 28.5,
    dominant_state: 'overload',
    p_underload: 0.05,
    p_flow: 0.15,
    p_overload: 0.65,
    p_fatigue: 0.15,
    is_provisional: false,
  },
  {
    student_id: 'std-102',
    student_name: 'Elena Rostova',
    email: 'elena.rostova@university.edu',
    latest_iori: 0.68,
    risk_zone: 'red',
    iori_history: [
      { date: '2026-11-04', iori: 0.40 },
      { date: '2026-11-08', iori: 0.52 },
      { date: '2026-11-12', iori: 0.58 },
      { date: '2026-11-16', iori: 0.65 },
      { date: '2026-11-19', iori: 0.68 },
    ],
    latest_rho: 0.94,
    is_stable: true,
    queue_length: 4,
    pending_tasks: 5,
    overdue_tasks: 2,
    total_weighted_workload: 22.0,
    dominant_state: 'fatigue',
    p_underload: 0.08,
    p_flow: 0.22,
    p_overload: 0.30,
    p_fatigue: 0.40,
    is_provisional: false,
  },
  {
    student_id: 'std-103',
    student_name: 'Devon Lee',
    email: 'devon.lee@university.edu',
    latest_iori: 0.48,
    risk_zone: 'yellow',
    iori_history: [
      { date: '2026-11-04', iori: 0.30 },
      { date: '2026-11-08', iori: 0.38 },
      { date: '2026-11-12', iori: 0.44 },
      { date: '2026-11-16', iori: 0.47 },
      { date: '2026-11-19', iori: 0.48 },
    ],
    latest_rho: 0.72,
    is_stable: true,
    queue_length: 3,
    pending_tasks: 4,
    overdue_tasks: 0,
    total_weighted_workload: 14.5,
    dominant_state: 'flow',
    p_underload: 0.15,
    p_flow: 0.55,
    p_overload: 0.18,
    p_fatigue: 0.12,
    is_provisional: false,
  },
  {
    student_id: 'std-104',
    student_name: 'Alex Chen',
    email: 'alex.chen@university.edu',
    latest_iori: 0.24,
    risk_zone: 'green',
    iori_history: [
      { date: '2026-11-04', iori: 0.22 },
      { date: '2026-11-08', iori: 0.28 },
      { date: '2026-11-12', iori: 0.25 },
      { date: '2026-11-16', iori: 0.23 },
      { date: '2026-11-19', iori: 0.24 },
    ],
    latest_rho: 0.45,
    is_stable: true,
    queue_length: 2,
    pending_tasks: 3,
    overdue_tasks: 0,
    total_weighted_workload: 11.0,
    dominant_state: 'flow',
    p_underload: 0.20,
    p_flow: 0.65,
    p_overload: 0.08,
    p_fatigue: 0.07,
    is_provisional: false,
  },
];

export default MentorDashboard;
