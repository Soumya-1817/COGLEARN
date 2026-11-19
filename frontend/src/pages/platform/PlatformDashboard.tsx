import React from 'react';
import { Link } from 'react-router-dom';
import { Building2, ShieldCheck, Database, Server, Activity, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export const PlatformDashboard: React.FC = () => {
  const systemMetrics = {
    totalInstitutions: 18,
    activeTenants: 15,
    demoTenants: 3,
    totalPlatformStudents: 14250,
    systemUptime: '99.98%',
    dbConnections: 'Healthy (PostgreSQL Multi-Tenant Pool)',
    redisCacheStatus: 'Connected (Celery Workers Ready)',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-950 via-slate-900 to-coglearn-950 p-6 text-white shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold text-coglearn-300 uppercase tracking-wider">
                COGLEARN Platform Administration
              </span>
              <span className="rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30 px-2 py-0.5 text-[10px] font-bold">
                Root Superadmin
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Platform & Multi-Tenant Infrastructure Hub
            </h1>
            <p className="text-sm text-slate-300 mt-1 max-w-2xl">
              Oversee university tenant provisionings, institutional compliance agreements, and cognitive model version pipelines.
            </p>
          </div>

          <Link to="/platform/institutions">
            <Button variant="primary" className="bg-coglearn-500 hover:bg-coglearn-600 font-semibold" rightIcon={<ArrowRight className="h-4 w-4" />}>
              Manage University Tenants
            </Button>
          </Link>
        </div>
      </div>

      {/* Infrastructure Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Total Universities
              </p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{systemMetrics.totalInstitutions}</h3>
              <p className="text-xs text-slate-500 mt-0.5">{systemMetrics.activeTenants} active deployments</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-coglearn-50 text-coglearn-600">
              <Building2 className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Platform Students
              </p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{systemMetrics.totalPlatformStudents.toLocaleString()}</h3>
              <p className="text-xs text-slate-500 mt-0.5">Across all tenants</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-sky-50 text-sky-600">
              <Activity className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Database Isolation
              </p>
              <h3 className="text-lg font-bold text-emerald-600 mt-1">RLS Verified</h3>
              <p className="text-xs text-slate-500 mt-0.5">institution_id partitioned</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
              <Database className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                System SLA Uptime
              </p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1 font-mono">{systemMetrics.systemUptime}</h3>
              <p className="text-xs text-slate-500 mt-0.5">Continuous operational status</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 text-purple-600">
              <Server className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Model Pipeline Governance */}
      <Card>
        <CardHeader className="border-b border-slate-100">
          <CardTitle>Cognitive Risk Analytics Pipeline Engine</CardTitle>
          <p className="text-xs text-slate-500 mt-0.5">
            Operational status of Models 1 through 4 running across Celery Beat cron tasks
          </p>
        </CardHeader>
        <CardContent className="p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="rounded-xl border border-slate-200 p-4 bg-slate-50/50">
              <span className="text-xs font-bold text-slate-800 block">Model 1: Dynamic Capacity</span>
              <p className="text-xs text-slate-500 mt-1">Bayesian updating of cognitive processing budget &mu;</p>
              <Badge variant="success" size="sm" className="mt-2">Online (v2.1)</Badge>
            </div>

            <div className="rounded-xl border border-slate-200 p-4 bg-slate-50/50">
              <span className="text-xs font-bold text-slate-800 block">Model 2: M/M/1 Queue</span>
              <p className="text-xs text-slate-500 mt-1">FIFO traffic intensity (&rho;) and queue stability monitor</p>
              <Badge variant="success" size="sm" className="mt-2">Online (v2.1)</Badge>
            </div>

            <div className="rounded-xl border border-slate-200 p-4 bg-slate-50/50">
              <span className="text-xs font-bold text-slate-800 block">Model 3: Workload Index</span>
              <p className="text-xs text-slate-500 mt-1">Temporal incoming weight aggregation and deadline friction</p>
              <Badge variant="success" size="sm" className="mt-2">Online (v2.1)</Badge>
            </div>

            <div className="rounded-xl border border-slate-200 p-4 bg-slate-50/50">
              <span className="text-xs font-bold text-slate-800 block">Model 4: Latent HMM</span>
              <p className="text-xs text-slate-500 mt-1">Hidden Markov posterior state distribution estimation</p>
              <Badge variant="success" size="sm" className="mt-2">Online (v2.1)</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PlatformDashboard;
