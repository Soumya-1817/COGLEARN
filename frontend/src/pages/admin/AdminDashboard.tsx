import React from 'react';
import { Link } from 'react-router-dom';
import {
  Building2,
  Users,
  GraduationCap,
  BookOpen,
  BarChart3,
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';
import { get } from '@/lib/api';
import { InstitutionalAnalytics } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';

export const AdminDashboard: React.FC = () => {
  const { data: analytics = defaultAnalytics, isLoading } = useQuery({
    queryKey: ['institutional_analytics_summary'],
    queryFn: async (): Promise<InstitutionalAnalytics> => {
      try {
        return await get<InstitutionalAnalytics>('/admin/analytics/summary');
      } catch {
        return defaultAnalytics;
      }
    },
  });

  const ioriChartData = [
    { zone: 'Green (< 0.30)', count: analytics.iori_summary.green, fill: '#22c55e' },
    { zone: 'Yellow (0.30-0.59)', count: analytics.iori_summary.yellow, fill: '#eab308' },
    { zone: 'Red (>= 0.60)', count: analytics.iori_summary.red, fill: '#ef4444' },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-coglearn-950 to-slate-900 p-6 text-white shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold text-coglearn-300 uppercase tracking-wider">
                University Administration Portal
              </span>
              <span className="rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold">
                Tenant Active
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Institutional Cognitive Risk Overview
            </h1>
            <p className="text-sm text-slate-300 mt-1 max-w-2xl">
              Cohort-level cognitive strain monitoring, departmental queuing metrics, and intervention volumes.
            </p>
          </div>

          <Link to="/admin/analytics">
            <Button variant="primary" className="bg-coglearn-500 hover:bg-coglearn-600 font-semibold" rightIcon={<ArrowRight className="h-4 w-4" />}>
              Advanced Analytics Portal
            </Button>
          </Link>
        </div>
      </div>

      {/* Cohort Privacy & Multi-Tenant Isolation Notice */}
      <Alert variant="info" title="Differential Privacy & Minimum Cohort Protection">
        Institutional dashboards aggregate student data across departments. Cohorts with fewer than 10 students are automatically suppressed to safeguard individual privacy and prevent re-identification.
      </Alert>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Total Enrolled Students
              </p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{analytics.total_students}</h3>
              <p className="text-xs text-slate-500 mt-0.5">Across 4 departments</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-sky-50 text-sky-600">
              <GraduationCap className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Faculty Instructors
              </p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{analytics.total_teachers}</h3>
              <p className="text-xs text-slate-500 mt-0.5">Active mentors</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
              <Users className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Campus Average IORI
              </p>
              <h3 className="text-2xl font-bold text-amber-600 mt-1 font-mono">
                {analytics.avg_institution_iori.toFixed(2)}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Sustainable equilibrium</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
              <BarChart3 className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Active Courses
              </p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{analytics.total_courses}</h3>
              <p className="text-xs text-slate-500 mt-0.5">Current Semester</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 text-purple-600">
              <BookOpen className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section: IORI Distribution BarChart & Intervention Volume */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* IORI Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Student Cognitive Risk Zone Distribution</CardTitle>
            <p className="text-xs text-slate-500">Number of students classified per IORI threshold</p>
          </CardHeader>
          <CardContent className="p-4">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={ioriChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="zone" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  formatter={(val: number) => [`${val} Students`, 'Count']}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Monthly Intervention Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Monthly Faculty Intervention Volume</CardTitle>
            <p className="text-xs text-slate-500">Accommodations and workload adjustments by month</p>
          </CardHeader>
          <CardContent className="p-4">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={analytics.intervention_volume} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  formatter={(val: number) => [`${val} Interventions`, 'Total']}
                />
                <Bar dataKey="count" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Department Analytics Table */}
      <Card>
        <CardHeader className="border-b border-slate-100 flex flex-row items-center justify-between">
          <div>
            <CardTitle>Departmental Analytics & Congestion Ratios</CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">
              Aggregated metrics evaluated across academic divisions
            </p>
          </div>
          <Link to="/admin/departments">
            <Button variant="ghost" size="sm" className="text-xs">
              Manage Departments
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Department</TableHead>
                <TableHead>Student Cohort</TableHead>
                <TableHead>Average IORI</TableHead>
                <TableHead>Risk Distribution (G / Y / R)</TableHead>
                <TableHead>Interventions</TableHead>
                <TableHead>Avg Workload</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analytics.departments.map((dept) => (
                <TableRow key={dept.department_id}>
                  <TableCell className="font-semibold text-slate-900">
                    {dept.department_name}
                  </TableCell>
                  <TableCell className="text-xs text-slate-700">
                    {dept.suppressed ? (
                      <span className="italic text-slate-400">Cohort &lt; 10 (Suppressed)</span>
                    ) : (
                      `${dept.student_count} students`
                    )}
                  </TableCell>
                  <TableCell>
                    {dept.suppressed ? (
                      <span className="italic text-slate-400">--</span>
                    ) : (
                      <span className="font-mono font-bold text-xs text-slate-800">
                        {dept.avg_iori.toFixed(2)}
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    {dept.suppressed ? (
                      <span className="italic text-slate-400">Protected</span>
                    ) : (
                      <div className="flex items-center gap-1.5 font-mono text-xs">
                        <span className="text-emerald-600 font-semibold">{dept.iori_distribution.green}</span> /
                        <span className="text-amber-600 font-semibold">{dept.iori_distribution.yellow}</span> /
                        <span className="text-red-600 font-semibold">{dept.iori_distribution.red}</span>
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-xs font-semibold text-slate-700">
                    {dept.suppressed ? '--' : dept.intervention_count}
                  </TableCell>
                  <TableCell className="text-xs text-slate-600">
                    {dept.suppressed ? '--' : `${dept.avg_workload.toFixed(1)} hrs/wk`}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

const defaultAnalytics: InstitutionalAnalytics = {
  total_students: 840,
  total_teachers: 48,
  total_courses: 36,
  avg_institution_iori: 0.38,
  cohort_size_suppressed: false,
  iori_summary: {
    green: 580,
    yellow: 195,
    red: 65,
  },
  intervention_volume: [
    { month: 'Jul', count: 12 },
    { month: 'Aug', count: 18 },
    { month: 'Sep', count: 34 },
    { month: 'Oct', count: 52 },
    { month: 'Nov', count: 41 },
  ],
  departments: [
    {
      department_id: 'dept-1',
      department_name: 'Computer Science & Engineering',
      student_count: 320,
      avg_iori: 0.44,
      iori_distribution: { green: 200, yellow: 85, red: 35 },
      intervention_count: 24,
      avg_workload: 18.2,
      suppressed: false,
    },
    {
      department_id: 'dept-2',
      department_name: 'Mathematics & Statistics',
      student_count: 240,
      avg_iori: 0.36,
      iori_distribution: { green: 175, yellow: 50, red: 15 },
      intervention_count: 11,
      avg_workload: 15.0,
      suppressed: false,
    },
    {
      department_id: 'dept-3',
      department_name: 'Electrical Engineering',
      student_count: 272,
      avg_iori: 0.35,
      iori_distribution: { green: 200, yellow: 58, red: 14 },
      intervention_count: 16,
      avg_workload: 16.4,
      suppressed: false,
    },
    {
      department_id: 'dept-4',
      department_name: 'Quantum Information Minor',
      student_count: 8,
      avg_iori: 0.30,
      iori_distribution: { green: 5, yellow: 2, red: 1 },
      intervention_count: 1,
      avg_workload: 12.0,
      suppressed: true, // below min cohort size
    },
  ],
};

export default AdminDashboard;
