import React, { useState } from 'react';
import {
  BarChart3,
  Download,
  Filter,
  Users,
  AlertTriangle,
  TrendingUp,
  Layers,
  GraduationCap,
  Sparkles,
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export const AnalyticsPortalPage: React.FC = () => {
  const [selectedDept, setSelectedDept] = useState('all');
  const [selectedProg, setSelectedProg] = useState('all');
  const [selectedSem, setSelectedSem] = useState('fall-2026');

  // Filtered aggregate values (simulated based on selection)
  const currentMetrics = {
    deptName: selectedDept === 'all' ? 'All Departments' : selectedDept,
    studentCount: selectedDept === 'all' ? 840 : selectedDept === 'CSE' ? 320 : 240,
    avgIori: selectedDept === 'all' ? 0.38 : selectedDept === 'CSE' ? 0.44 : 0.35,
    interventionRate: selectedDept === 'all' ? '6.1%' : selectedDept === 'CSE' ? '7.5%' : '4.6%',
    avgWorkload: selectedDept === 'all' ? '16.5 hrs/wk' : selectedDept === 'CSE' ? '18.2 hrs/wk' : '15.0 hrs/wk',
    distribution: [
      {
        zone: 'Green (< 0.30)',
        count: selectedDept === 'all' ? 580 : selectedDept === 'CSE' ? 200 : 175,
        fill: '#22c55e',
      },
      {
        zone: 'Yellow (0.30 - 0.59)',
        count: selectedDept === 'all' ? 195 : selectedDept === 'CSE' ? 85 : 50,
        fill: '#eab308',
      },
      {
        zone: 'Red (>= 0.60)',
        count: selectedDept === 'all' ? 65 : selectedDept === 'CSE' ? 35 : 15,
        fill: '#ef4444',
      },
    ],
  };

  const handleDownloadCsv = () => {
    const csvRows = [
      ['Metric', 'Value'],
      ['Department', currentMetrics.deptName],
      ['Semester', selectedSem],
      ['Student Cohort Size', currentMetrics.studentCount.toString()],
      ['Average IORI', currentMetrics.avgIori.toFixed(2)],
      ['Intervention Rate', currentMetrics.interventionRate],
      ['Average Workload', currentMetrics.avgWorkload],
      ['Green Zone Count', currentMetrics.distribution[0].count.toString()],
      ['Yellow Zone Count', currentMetrics.distribution[1].count.toString()],
      ['Red Zone Count', currentMetrics.distribution[2].count.toString()],
    ];

    const csvContent = 'data:text/csv;charset=utf-8,' + csvRows.map((e) => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `coglearn_analytics_${selectedDept}_${selectedSem}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-coglearn-600" />
            Institutional Analytics Portal
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Analyze multi-semester cognitive load indicators and queuing congestion by degree programme.
          </p>
        </div>

        <Button
          variant="outline"
          onClick={handleDownloadCsv}
          leftIcon={<Download className="h-4 w-4" />}
        >
          Export Cohort CSV
        </Button>
      </div>

      {/* Institutional Privacy Authorization Notice */}
      <Alert variant="warning" title="Institutional Data Governance Notice">
        Individual student cognitive telemetry requires explicit institutional authorization. All metrics reported in this portal represent anonymized cohort aggregates to protect student privacy rights.
      </Alert>

      {/* Filter Bar */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
            <Filter className="h-4 w-4 text-slate-500" />
            <span>Cohort Filters:</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 flex-1 sm:max-w-2xl">
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
                Department
              </label>
              <select
                value={selectedDept}
                onChange={(e) => setSelectedDept(e.target.value)}
                className="w-full rounded-lg border border-slate-300 p-1.5 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
              >
                <option value="all">All Departments</option>
                <option value="CSE">Computer Science & Engineering</option>
                <option value="MATH">Mathematics & Statistics</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
                Programme
              </label>
              <select
                value={selectedProg}
                onChange={(e) => setSelectedProg(e.target.value)}
                className="w-full rounded-lg border border-slate-300 p-1.5 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
              >
                <option value="all">All Programmes</option>
                <option value="bsc">B.Sc Computer Science</option>
                <option value="msc">M.Sc Computational Systems</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
                Academic Semester
              </label>
              <select
                value={selectedSem}
                onChange={(e) => setSelectedSem(e.target.value)}
                className="w-full rounded-lg border border-slate-300 p-1.5 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
              >
                <option value="fall-2026">Fall 2026 (Current)</option>
                <option value="spring-2026">Spring 2026</option>
                <option value="fall-2025">Fall 2025</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Aggregate KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-5">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Filtered Cohort</span>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{currentMetrics.studentCount} students</h3>
            <p className="text-xs text-slate-500 mt-0.5">{currentMetrics.deptName}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Mean Cohort IORI</span>
            <h3 className="text-2xl font-bold text-amber-600 mt-1 font-mono">{currentMetrics.avgIori.toFixed(2)}</h3>
            <p className="text-xs text-slate-500 mt-0.5">Threshold benchmark 0.35</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Intervention Rate</span>
            <h3 className="text-2xl font-bold text-coglearn-600 mt-1">{currentMetrics.interventionRate}</h3>
            <p className="text-xs text-slate-500 mt-0.5">Faculty accommodations</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Mean Student Workload</span>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{currentMetrics.avgWorkload}</h3>
            <p className="text-xs text-slate-500 mt-0.5">Estimated effort pace</p>
          </CardContent>
        </Card>
      </div>

      {/* Cohort IORI Distribution Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Cohort Cognitive Risk Distribution ({currentMetrics.deptName})</CardTitle>
          <p className="text-xs text-slate-500 mt-0.5">
            Breakdown across sustainable flow (Green), congestion buildup (Yellow), and critical overload (Red)
          </p>
        </CardHeader>
        <CardContent className="p-6">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={currentMetrics.distribution} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="zone" stroke="#94a3b8" fontSize={12} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip formatter={(val: number) => [`${val} Students`, 'Total']} />
              <Bar dataKey="count" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsPortalPage;
