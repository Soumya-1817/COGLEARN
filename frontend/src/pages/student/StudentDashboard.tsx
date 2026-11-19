import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ListOrdered,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  BookOpen,
  Bell,
  HeartHandshake,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useTasks } from '@/hooks/useTasks';
import { useNotifications } from '@/hooks/useNotifications';
import { formatDate, formatRelative, checkIsOverdue } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data: tasks = [], isLoading: tasksLoading } = useTasks('all');
  const { notifications, unreadCount } = useNotifications();

  // Compute safe dashboard statistics (no cognitive load internals)
  const pendingTasks = tasks.filter((t) => t.status === 'pending');
  const activeTasks = tasks.filter((t) => t.status === 'active');
  const overdueTasks = tasks.filter((t) => t.status === 'overdue' || (t.status !== 'completed' && checkIsOverdue(t.due_date)));
  const completedTasks = tasks.filter((t) => t.status === 'completed');

  // Next deadline calculation
  const upcomingIncomplete = [...tasks]
    .filter((t) => t.status !== 'completed')
    .sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime());
  const nextDeadline = upcomingIncomplete.length > 0 ? upcomingIncomplete[0] : null;

  return (
    <div className="space-y-6">
      {/* Welcome banner */}
      <div className="rounded-2xl bg-gradient-to-r from-coglearn-900 via-coglearn-800 to-coglearn-900 p-6 text-white shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-semibold text-coglearn-200 uppercase tracking-wider">
              Student Workspace
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white mt-1">
              Welcome back, {user?.full_name || 'Student'}
            </h1>
            <p className="text-sm text-slate-300 mt-1 max-w-xl">
              Stay focused with your prioritized academic task queue. Track upcoming course deadlines and submit coursework systematically.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link to="/tasks">
              <Button variant="primary" className="bg-white text-coglearn-900 hover:bg-slate-100 font-semibold shadow-none">
                Open Task Queue
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Metric Cards (Safe Academic Metrics) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Pending Tasks */}
        <Card className="hover:border-slate-300">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Pending Tasks
              </p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {pendingTasks.length + activeTasks.length}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {activeTasks.length} currently active in progress
              </p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-sky-50 text-sky-600">
              <ListOrdered className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        {/* Overdue Tasks */}
        <Card className="hover:border-slate-300">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Overdue Tasks
              </p>
              <h3 className={`text-2xl font-bold mt-1 ${overdueTasks.length > 0 ? 'text-red-600' : 'text-slate-900'}`}>
                {overdueTasks.length}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {overdueTasks.length > 0 ? 'Requires immediate action' : 'All up to date'}
              </p>
            </div>
            <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${
              overdueTasks.length > 0 ? 'bg-red-50 text-red-600' : 'bg-slate-50 text-slate-400'
            }`}>
              <AlertTriangle className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        {/* Completed Tasks */}
        <Card className="hover:border-slate-300">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Completed
              </p>
              <h3 className="text-2xl font-bold text-emerald-600 mt-1">
                {completedTasks.length}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                This term
              </p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
              <CheckCircle2 className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        {/* Next Due Deadline */}
        <Card className="hover:border-slate-300">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="flex-1 pr-2">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Next Deadline
              </p>
              <h3 className="text-sm font-bold text-slate-900 mt-1 line-clamp-1">
                {nextDeadline ? nextDeadline.title : 'None pending'}
              </h3>
              <p className="text-xs text-amber-600 font-medium mt-0.5">
                {nextDeadline ? formatRelative(nextDeadline.due_date) : 'All submissions clear'}
              </p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50 text-amber-600 shrink-0">
              <Clock className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid: Priority FIFO Tasks + Deadlines & Notifications */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Top Pending Tasks (FIFO Queue preview) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-slate-100">
              <div>
                <CardTitle>Academic Task Queue</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">
                  Ordered by system arrival queue position (FIFO)
                </p>
              </div>
              <Link to="/tasks">
                <Button variant="ghost" size="sm" className="text-xs" rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
                  View full queue
                </Button>
              </Link>
            </CardHeader>

            <CardContent className="p-5">
              {tasksLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-16 rounded-xl bg-slate-100 animate-pulse" />
                  ))}
                </div>
              ) : upcomingIncomplete.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <CheckCircle2 className="h-10 w-10 text-emerald-400 mx-auto mb-2" />
                  <p className="text-sm font-medium text-slate-700">All tasks completed!</p>
                  <p className="text-xs text-slate-500">You currently have no outstanding assignments.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {upcomingIncomplete.slice(0, 4).map((task) => {
                    const isOver = checkIsOverdue(task.due_date);
                    return (
                      <div
                        key={task.id}
                        className={`flex items-center justify-between p-4 rounded-xl border transition-all ${
                          isOver ? 'border-red-200 bg-red-50/30' : 'border-slate-200 bg-white hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-100 font-mono text-xs font-bold text-slate-600">
                            #{task.queue_position}
                          </span>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="text-sm font-semibold text-slate-900">{task.title}</h4>
                              <Badge
                                variant={task.task_type === 'assessment' ? 'danger' : task.task_type === 'quiz' ? 'info' : 'secondary'}
                                size="sm"
                              >
                                {task.task_type}
                              </Badge>
                            </div>
                            <p className="text-xs text-slate-500 mt-0.5">
                              {task.course_title || 'Course Academic Unit'} • Due {formatDate(task.due_date)}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          {isOver ? (
                            <Badge variant="danger" size="sm">Overdue</Badge>
                          ) : (
                            <span className="text-xs font-medium text-slate-500">
                              {formatRelative(task.due_date)}
                            </span>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-xs"
                            onClick={() => navigate('/tasks')}
                          >
                            Work On
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Nav Shortcuts */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Link to="/courses" className="block group">
              <div className="rounded-xl border border-slate-200 bg-white p-4 hover:border-coglearn-400 hover:shadow-sm transition-all">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-coglearn-50 p-2.5 text-coglearn-600 group-hover:bg-coglearn-600 group-hover:text-white transition-colors">
                    <BookOpen className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-800">My Courses</h4>
                    <p className="text-xs text-slate-500">Access modules & lectures</p>
                  </div>
                </div>
              </div>
            </Link>

            <Link to="/calendar" className="block group">
              <div className="rounded-xl border border-slate-200 bg-white p-4 hover:border-coglearn-400 hover:shadow-sm transition-all">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-sky-50 p-2.5 text-sky-600 group-hover:bg-sky-600 group-hover:text-white transition-colors">
                    <Calendar className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-800">Academic Calendar</h4>
                    <p className="text-xs text-slate-500">Deadlines & exam schedule</p>
                  </div>
                </div>
              </div>
            </Link>

            <Link to="/mentorship" className="block group">
              <div className="rounded-xl border border-slate-200 bg-white p-4 hover:border-coglearn-400 hover:shadow-sm transition-all">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-emerald-50 p-2.5 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                    <HeartHandshake className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-800">Mentorship & Help</h4>
                    <p className="text-xs text-slate-500">Consult with your faculty</p>
                  </div>
                </div>
              </div>
            </Link>
          </div>
        </div>

        {/* Right column: Recent Notifications & Deadlines */}
        <div className="space-y-6">
          {/* Notifications Card */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-slate-500" />
                <CardTitle className="text-base">Recent Notices</CardTitle>
              </div>
              <Link to="/notifications" className="text-xs text-coglearn-600 hover:underline">
                View all ({unreadCount})
              </Link>
            </CardHeader>
            <CardContent className="p-4 divide-y divide-slate-100">
              {notifications.slice(0, 4).map((n) => (
                <div key={n.id} className="py-3 first:pt-0 last:pb-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-800 line-clamp-1">{n.title}</span>
                    <span className="text-[10px] text-slate-400">{formatRelative(n.created_at)}</span>
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">{n.body}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Academic Deadlines Widget */}
          <Card>
            <CardHeader className="border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-slate-500" />
                <CardTitle className="text-base">Next 7 Days</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              {upcomingIncomplete.slice(0, 3).map((task) => (
                <div key={task.id} className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-50">
                  <div>
                    <p className="font-semibold text-slate-800">{task.title}</p>
                    <p className="text-slate-500">{task.course_title}</p>
                  </div>
                  <span className="font-medium text-amber-600 shrink-0">
                    {formatDate(task.due_date, 'MMM d')}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
