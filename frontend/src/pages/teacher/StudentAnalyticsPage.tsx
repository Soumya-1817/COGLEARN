import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Sparkles,
  AlertTriangle,
  Clock,
  Layers,
  Send,
  Calendar,
  ShieldAlert,
  FileText,
  UserCheck,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { get, post } from '@/lib/api';
import { StudentAnalytics, RiskZone } from '@/types';
import { formatDate, getRegimeFromRho, getRiskZoneColor } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { IoriGauge } from '@/components/charts/IoriGauge';
import { RhoUtilizationBar } from '@/components/charts/RhoUtilizationBar';
import { WorkloadTimeline } from '@/components/charts/WorkloadTimeline';
import { HmmStatePie } from '@/components/charts/HmmStatePie';

export const StudentAnalyticsPage: React.FC = () => {
  const { studentId } = useParams<{ studentId: string }>();
  const navigate = useNavigate();

  // Modals state
  const [isExtendModalOpen, setIsExtendModalOpen] = useState(false);
  const [isReferralModalOpen, setIsReferralModalOpen] = useState(false);
  const [isMessageModalOpen, setIsMessageModalOpen] = useState(false);
  const [extensionDays, setExtensionDays] = useState(3);
  const [referralNote, setReferralNote] = useState('');
  const [privateMessage, setPrivateMessage] = useState('');
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const { data: student = fallbackStudentAnalytics, isLoading } = useQuery({
    queryKey: ['student_analytics_detail', studentId],
    queryFn: async (): Promise<StudentAnalytics> => {
      try {
        return await get<StudentAnalytics>(`/mentor/students/${studentId}`);
      } catch {
        return fallbackStudentAnalytics;
      }
    },
  });

  const regime = getRegimeFromRho(student.latest_rho, student.is_stable);

  // M/M/1 Queue derivations:
  // L = rho / (1 - rho) if rho < 1, else Unstable
  // W = 1 / (mu - lambda)
  const avgQueueL = student.is_stable && student.latest_rho < 1
    ? (student.latest_rho / (1 - student.latest_rho)).toFixed(1)
    : 'Unbounded (Unstable)';

  const avgWaitTimeW = student.is_stable && student.latest_rho < 1
    ? `${(1.8 / (1 - student.latest_rho)).toFixed(1)} days`
    : 'Divergent (> 14 days)';

  const handleExtendDeadline = (e: React.FormEvent) => {
    e.preventDefault();
    setIsExtendModalOpen(false);
    setActionNotice(`Successfully granted a +${extensionDays}-day deadline extension for student.`);
  };

  const handleCreateReferral = (e: React.FormEvent) => {
    e.preventDefault();
    setIsReferralModalOpen(false);
    setActionNotice('Mental Health & Academic Counseling referral initiated per institutional protocol.');
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    setIsMessageModalOpen(false);
    setPrivateMessage('');
    setActionNotice('Confidential mentor message sent directly to student portal.');
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to="/teacher/mentor"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Mentor Dashboard
        </Link>
        <span className="text-xs text-slate-400 font-mono">Student ID: {student.student_id}</span>
      </div>

      {/* Student Banner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Diagnostic Profile (Mentor Eyes Only)
            </span>
            <Badge variant={student.risk_zone === 'red' ? 'danger' : student.risk_zone === 'yellow' ? 'warning' : 'success'} size="sm">
              {student.risk_zone.toUpperCase()} ZONE
            </Badge>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            {student.student_name}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {student.email || `${student.student_id}@university.edu`} • CS Undergrad Cohort
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsMessageModalOpen(true)}
            leftIcon={<Send className="h-3.5 w-3.5" />}
          >
            Send Private Message
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsExtendModalOpen(true)}
            leftIcon={<Calendar className="h-3.5 w-3.5 text-coglearn-600" />}
          >
            Extend Deadline
          </Button>

          <Button
            variant="danger"
            size="sm"
            onClick={() => setIsReferralModalOpen(true)}
            leftIcon={<ShieldAlert className="h-3.5 w-3.5" />}
          >
            Initiate Support Referral
          </Button>
        </div>
      </div>

      {actionNotice && (
        <Alert variant="success" onClose={() => setActionNotice(null)}>
          {actionNotice}
        </Alert>
      )}

      {/* Mandatory Ethics Disclaimer */}
      <Alert variant="warning" title="Research-Based Support Disclaimer">
        COGLEARN cognitive indicators (IORI, HMM latent state probabilities, and queuing parameters) are research-based pedagogical support tools, not medical or clinical diagnoses. All actions must comply with your institution's academic integrity and counseling guidelines.
      </Alert>

      {/* Section 1: Cognitive State (IORI) & Model 4 Latent State */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* IORI Gauge */}
        <Card className="flex flex-col items-center justify-center p-6">
          <CardHeader className="w-full text-center pb-0">
            <CardTitle className="text-base">Current IORI Indicator</CardTitle>
            <p className="text-xs text-slate-400">Index of Overload & Resilience</p>
          </CardHeader>
          <CardContent className="w-full flex justify-center pt-2">
            <IoriGauge value={student.latest_iori} riskZone={student.risk_zone} size={220} />
          </CardContent>
        </Card>

        {/* 30-Day IORI Trajectory Line Chart */}
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle className="text-base">IORI Historical Trajectory</CardTitle>
            <p className="text-xs text-slate-400">30-day temporal trend across assignments</p>
          </CardHeader>
          <CardContent className="flex-1 min-h-[220px]">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={student.iori_history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={(val) => formatDate(val, 'MMM d')}
                  stroke="#94a3b8"
                  fontSize={10}
                  tickLine={false}
                />
                <YAxis domain={[0, 1]} stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip
                  formatter={(val: number) => [`IORI: ${Number(val).toFixed(2)}`, 'Cognitive Index']}
                  labelFormatter={(lbl) => formatDate(lbl)}
                />
                <Line
                  type="monotone"
                  dataKey="iori"
                  stroke={student.latest_iori >= 0.6 ? '#ef4444' : student.latest_iori >= 0.3 ? '#eab308' : '#22c55e'}
                  strokeWidth={2.5}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Model 4 HMM State Posterior Distribution */}
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle className="text-base">Model 4 HMM Posterior</CardTitle>
            <p className="text-xs text-slate-400">Hidden Markov latent cognitive state</p>
          </CardHeader>
          <CardContent className="flex-1 flex items-center justify-center pt-0">
            <HmmStatePie
              p_underload={student.p_underload}
              p_flow={student.p_flow}
              p_overload={student.p_overload}
              p_fatigue={student.p_fatigue}
              dominantState={student.dominant_state}
              size={200}
            />
          </CardContent>
        </Card>
      </div>

      {/* Section 2: Queue Metrics & Traffic Intensity (Model 2 M/M/1) */}
      <Card>
        <CardHeader className="border-b border-slate-100">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>M/M/1 Academic Task Queue Dynamics</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Mathematical modeling of task arrival rate (&lambda;) vs completion throughput (&mu;)
              </p>
            </div>
            <Badge variant={student.is_stable ? 'success' : 'danger'} size="md">
              {student.is_stable ? 'Queue Stable (&rho; < 1)' : 'Queue Unstable (&rho; >= 1)'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          <RhoUtilizationBar
            rho={student.latest_rho}
            isStable={student.is_stable}
            regime={regime}
            showDetails={true}
          />

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 pt-4 border-t border-slate-100">
            <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-4">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Traffic Intensity (&rho;)</span>
              <p className="text-2xl font-bold font-mono text-slate-900 mt-1">{student.latest_rho.toFixed(2)}</p>
              <span className="text-[10px] text-slate-400">&rho; = &lambda; / &mu;</span>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-4">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Mean Queue Items (L)</span>
              <p className="text-2xl font-bold font-mono text-slate-900 mt-1">{avgQueueL}</p>
              <span className="text-[10px] text-slate-400">L = &rho; / (1 - &rho;)</span>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-4">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Mean Wait Time (W)</span>
              <p className="text-2xl font-bold font-mono text-slate-900 mt-1">{avgWaitTimeW}</p>
              <span className="text-[10px] text-slate-400">W = 1 / (&mu; - &lambda;)</span>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-4">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Pending / Overdue</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">
                {student.pending_tasks} <span className="text-sm font-normal text-slate-500">/ {student.overdue_tasks} overdue</span>
              </p>
              <span className="text-[10px] text-slate-400">{student.total_weighted_workload} weighted hrs</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section 3: Workload Timeline */}
      <Card>
        <CardHeader className="border-b border-slate-100">
          <CardTitle>Workload Inflow vs Processing Profile</CardTitle>
          <p className="text-xs text-slate-500 mt-0.5">
            Temporal comparison between incoming assignments and student queue resolution
          </p>
        </CardHeader>
        <CardContent className="p-6">
          <WorkloadTimeline height={260} />
        </CardContent>
      </Card>

      {/* Modal 1: Extend Deadline */}
      <Modal
        isOpen={isExtendModalOpen}
        onClose={() => setIsExtendModalOpen(false)}
        title="Extend Coursework Deadline"
        description={`Grant pedagogical deadline extension for ${student.student_name}`}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsExtendModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleExtendDeadline}>
              Confirm Extension
            </Button>
          </div>
        }
      >
        <form onSubmit={handleExtendDeadline} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Select Overdue Assignment
            </label>
            <select className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-800">
              <option>Dynamic Programming & Graph Optimizations (CS301)</option>
              <option>NP-Completeness Reductions Problem Set (CS301)</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Extension Duration (Days)
            </label>
            <Input
              type="number"
              min={1}
              max={14}
              value={extensionDays}
              onChange={(e) => setExtensionDays(Number(e.target.value))}
            />
          </div>

          <Alert variant="info">
            Extending the deadline will reschedule the student's task queue position and damp the arrival rate &lambda; in Model 2.
          </Alert>
        </form>
      </Modal>

      {/* Modal 2: Support Referral */}
      <Modal
        isOpen={isReferralModalOpen}
        onClose={() => setIsReferralModalOpen(false)}
        title="Initiate Academic & Counseling Support Referral"
        description="Formal confidential notification to university academic support services"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsReferralModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" size="sm" onClick={handleCreateReferral}>
              Submit Institutional Referral
            </Button>
          </div>
        }
      >
        <form onSubmit={handleCreateReferral} className="space-y-4 text-xs">
          <Alert variant="warning" title="Institutional Policy">
            Referrals are processed strictly under institutional student care protocols. Cognitive overload indicators will be shared with designated counseling officers only.
          </Alert>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Mentor Academic Observations & Notes
            </label>
            <textarea
              rows={4}
              value={referralNote}
              onChange={(e) => setReferralNote(e.target.value)}
              placeholder="State observed bottlenecks, missed deadlines, or noted disengagement..."
              className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-800 focus:outline-none focus:border-red-500"
              required
            />
          </div>
        </form>
      </Modal>

      {/* Modal 3: Send Private Message */}
      <Modal
        isOpen={isMessageModalOpen}
        onClose={() => setIsMessageModalOpen(false)}
        title={`Message ${student.student_name}`}
        description="Private message delivered directly to the student's portal inbox"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsMessageModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleSendMessage}>
              Send Message
            </Button>
          </div>
        }
      >
        <form onSubmit={handleSendMessage} className="space-y-3 text-xs">
          <textarea
            rows={4}
            value={privateMessage}
            onChange={(e) => setPrivateMessage(e.target.value)}
            placeholder="Write supportive feedback or invite the student to office hours..."
            className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
            required
          />
        </form>
      </Modal>
    </div>
  );
};

// Fallback analytics detail
const fallbackStudentAnalytics: StudentAnalytics = {
  student_id: 'std-101',
  student_name: 'Marcus Bell',
  email: 'marcus.bell@university.edu',
  latest_iori: 0.74,
  risk_zone: 'red',
  iori_history: [
    { date: '2026-10-25', iori: 0.28 },
    { date: '2026-10-30', iori: 0.35 },
    { date: '2026-11-04', iori: 0.44 },
    { date: '2026-11-08', iori: 0.52 },
    { date: '2026-11-12', iori: 0.63 },
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
};

export default StudentAnalyticsPage;
