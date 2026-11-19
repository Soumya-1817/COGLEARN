import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Users,
  BookOpen,
  FileCheck2,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  TrendingUp,
  HeartHandshake,
  ShieldAlert,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export const TeacherDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Summary statistics for teacher
  const stats = {
    activeCourses: 3,
    enrolledStudents: 142,
    atRiskStudents: 6, // IORI >= 0.6
    pendingMentorshipRequests: 4,
    activeInterventions: 3,
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-coglearn-900 via-coglearn-800 to-coglearn-900 p-6 text-white shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-semibold text-coglearn-200 uppercase tracking-wider">
              Faculty & Mentor Portal
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white mt-1">
              Welcome, {user?.full_name || 'Professor'}
            </h1>
            <p className="text-sm text-slate-300 mt-1 max-w-xl">
              Monitor student cognitive load trajectory (IORI), manage courses & assignments, and conduct proactive academic interventions.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link to="/teacher/mentor">
              <Button variant="primary" className="bg-white text-coglearn-900 hover:bg-slate-100 font-semibold shadow-none" leftIcon={<Sparkles className="h-4 w-4" />}>
                Open Mentor Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Mandatory Cognitive Ethics Disclaimer */}
      <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-3.5 text-xs text-amber-900 flex items-start gap-2.5">
        <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Pedagogical Support Notice:</span> The Index of Overload & Resilience Indicator (IORI) and M/M/1 queuing metrics are pedagogical research-based decision support tools designed to highlight academic bottlenecking, not medical or clinical diagnoses.
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* At-Risk Students (IORI >= 0.6) */}
        <Card className="hover:border-red-300 transition-colors">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                At-Risk Students (IORI &ge; 0.6)
              </p>
              <h3 className="text-2xl font-bold text-red-600 mt-1">{stats.atRiskStudents}</h3>
              <p className="text-xs text-red-700 font-medium mt-0.5">High cognitive overload</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-50 text-red-600">
              <ShieldAlert className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        {/* Enrolled Students */}
        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Total Enrolled Students
              </p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats.enrolledStudents}</h3>
              <p className="text-xs text-slate-500 mt-0.5">Across 3 active courses</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-sky-50 text-sky-600">
              <Users className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        {/* Active Interventions */}
        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Active Interventions
              </p>
              <h3 className="text-2xl font-bold text-amber-600 mt-1">{stats.activeInterventions}</h3>
              <p className="text-xs text-slate-500 mt-0.5">Workload & pacing extensions</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
              <Sparkles className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        {/* Pending Mentorship Inquiries */}
        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Mentorship Requests
              </p>
              <h3 className="text-2xl font-bold text-coglearn-600 mt-1">{stats.pendingMentorshipRequests}</h3>
              <p className="text-xs text-slate-500 mt-0.5">Awaiting faculty reply</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-coglearn-50 text-coglearn-600">
              <HeartHandshake className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid: At-Risk Quick Action List & Course Hub */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* At-Risk Students Snapshot */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-slate-100">
              <div>
                <CardTitle>Priority Student Overload Alerts</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">
                  Students exhibiting elevated queue saturation (&rho; &gt; 0.8) and IORI &ge; 0.60
                </p>
              </div>
              <Link to="/teacher/mentor">
                <Button variant="ghost" size="sm" className="text-xs" rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
                  Full Mentor Board
                </Button>
              </Link>
            </CardHeader>

            <CardContent className="p-4 space-y-3">
              {urgentStudents.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-red-200 bg-red-50/20 hover:bg-red-50/40 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-slate-900">{s.name}</span>
                      <Badge variant="danger" size="sm">IORI {s.iori.toFixed(2)}</Badge>
                      <span className="text-[11px] font-mono text-slate-500">&rho; = {s.rho.toFixed(2)}</span>
                    </div>
                    <p className="text-xs text-slate-500">
                      {s.course} • {s.overdueTasks} overdue tasks • State: <span className="font-semibold text-red-700 capitalize">{s.state}</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Link to={`/teacher/mentor/students/${s.id}`}>
                      <Button variant="outline" size="sm" className="text-xs">
                        View Analytics
                      </Button>
                    </Link>
                    <Link to={`/teacher/interventions/new?studentId=${s.id}`}>
                      <Button variant="danger" size="sm" className="text-xs">
                        Intervene
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Quick Management Navigation */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="text-base">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              <Link to="/teacher/courses" className="block">
                <Button variant="outline" className="w-full justify-start text-xs" leftIcon={<BookOpen className="h-4 w-4 text-coglearn-600" />}>
                  Manage Courses & Syllabi
                </Button>
              </Link>
              <Link to="/teacher/assignments" className="block">
                <Button variant="outline" className="w-full justify-start text-xs" leftIcon={<FileCheck2 className="h-4 w-4 text-sky-600" />}>
                  Publish New Assignment
                </Button>
              </Link>
              <Link to="/teacher/mentor" className="block">
                <Button variant="outline" className="w-full justify-start text-xs" leftIcon={<Sparkles className="h-4 w-4 text-amber-600" />}>
                  Open Live IORI Stream
                </Button>
              </Link>
              <Link to="/teacher/mentorship-requests" className="block">
                <Button variant="outline" className="w-full justify-start text-xs" leftIcon={<HeartHandshake className="h-4 w-4 text-emerald-600" />}>
                  Review Mentorship Inquiries ({stats.pendingMentorshipRequests})
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

const urgentStudents = [
  { id: 'std-101', name: 'Marcus Bell', iori: 0.74, rho: 1.15, course: 'CS301', overdueTasks: 3, state: 'overload' },
  { id: 'std-102', name: 'Elena Rostova', iori: 0.68, rho: 0.94, course: 'CS304', overdueTasks: 2, state: 'fatigue' },
  { id: 'std-103', name: 'Devon Lee', iori: 0.62, rho: 0.88, course: 'MATH240', overdueTasks: 1, state: 'strain' },
];

export default TeacherDashboard;
