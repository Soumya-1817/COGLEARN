import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Sparkles,
  Send,
  CheckCircle,
  FileText,
  AlertTriangle,
  Clock,
  Shield,
  MessageSquare,
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, patch, post } from '@/lib/api';
import { Intervention, MentorMessage } from '@/types';
import { formatDateTime, formatDate } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';

export const InterventionPage: React.FC = () => {
  const { interventionId } = useParams<{ interventionId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [newMessage, setNewMessage] = useState('');
  const [mentorNotes, setMentorNotes] = useState('Observed cognitive saturation following consecutive programming deadlines.');
  const [isCloseModalOpen, setIsCloseModalOpen] = useState(false);
  const [resolutionSummary, setResolutionSummary] = useState('');

  // Fetch intervention details
  const { data: intervention = defaultIntervention } = useQuery({
    queryKey: ['intervention_detail', interventionId],
    queryFn: async (): Promise<Intervention> => {
      try {
        return await get<Intervention>(`/interventions/${interventionId}`);
      } catch {
        return defaultIntervention;
      }
    },
  });

  // Fetch thread messages with 10s polling
  const [messages, setMessages] = useState<MentorMessage[]>(defaultMessages);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    const msg: MentorMessage = {
      id: `msg-${Date.now()}`,
      sender_id: 'tch-1',
      sender_name: 'Dr. Sarah Miller (Faculty Mentor)',
      body: newMessage.trim(),
      sent_at: new Date().toISOString(),
      is_read: true,
    };

    setMessages((prev) => [...prev, msg]);
    setNewMessage('');
  };

  const handleCloseIntervention = () => {
    setIsCloseModalOpen(false);
    navigate('/teacher/mentor');
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Back button */}
      <Link to="/teacher/mentor" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800">
        <ArrowLeft className="h-4 w-4" /> Back to Mentor Dashboard
      </Link>

      {/* Intervention Header Details */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={intervention.status === 'open' ? 'danger' : 'warning'} size="sm">
                Status: {intervention.status.toUpperCase()}
              </Badge>
              <span className="text-xs text-slate-400 font-mono">ID: {intervention.id}</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Intervention: {intervention.student_name}
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Triggered on {formatDate(intervention.created_at)} • Initial IORI: <strong className="text-red-600 font-mono">{intervention.iori_value_at_trigger?.toFixed(2)}</strong>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link to={`/teacher/mentor/students/${intervention.student_id}`}>
              <Button variant="outline" size="sm" className="text-xs">
                View Full Analytics
              </Button>
            </Link>
            <Button
              variant="success"
              size="sm"
              className="text-xs"
              onClick={() => setIsCloseModalOpen(true)}
              leftIcon={<CheckCircle className="h-4 w-4" />}
            >
              Resolve & Close
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Intervention Notes & Context */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Intervention Documentation</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div>
                <span className="font-semibold text-slate-700 block mb-1">Trigger Classification</span>
                <p className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-slate-700">
                  {intervention.trigger_type}
                </p>
              </div>

              <div>
                <span className="font-semibold text-slate-700 block mb-1">Mentor Clinical / Field Notes</span>
                <textarea
                  rows={5}
                  value={mentorNotes}
                  onChange={(e) => setMentorNotes(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
                />
              </div>

              <Button variant="outline" size="sm" className="w-full text-xs">
                Update Case Notes
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Direct Messaging Thread */}
        <div className="lg:col-span-2">
          <Card className="flex flex-col h-[580px]">
            <CardHeader className="border-b border-slate-100 py-3.5 px-5 bg-slate-50/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-coglearn-600" />
                  <CardTitle className="text-sm">Secure Support Thread</CardTitle>
                </div>
                <span className="text-[11px] text-slate-400">Updates live (10s polling)</span>
              </div>
            </CardHeader>

            {/* Message List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map((m) => {
                const isMentor = m.sender_name.includes('Mentor') || m.sender_name.includes('Dr.');
                return (
                  <div
                    key={m.id}
                    className={`flex flex-col ${isMentor ? 'items-end' : 'items-start'}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[11px] font-semibold text-slate-600">{m.sender_name}</span>
                      <span className="text-[10px] text-slate-400">{formatDateTime(m.sent_at)}</span>
                    </div>
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed ${
                        isMentor
                          ? 'bg-coglearn-600 text-white rounded-tr-xs'
                          : 'bg-slate-100 text-slate-800 rounded-tl-xs border border-slate-200/60'
                      }`}
                    >
                      {m.body}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Input form */}
            <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-100 bg-white">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Send guidance or scheduled check-in details..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  className="flex-1 rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
                />
                <Button type="submit" variant="primary" size="sm" leftIcon={<Send className="h-3.5 w-3.5" />}>
                  Send
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>

      {/* Close Intervention Modal */}
      <Modal
        isOpen={isCloseModalOpen}
        onClose={() => setIsCloseModalOpen(false)}
        title="Resolve & Close Intervention"
        description={`Conclude active support case for ${intervention.student_name}`}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsCloseModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="success" size="sm" onClick={handleCloseIntervention}>
              Confirm Closure
            </Button>
          </div>
        }
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-600">
            Confirm that the student's workload trajectory has stabilized or necessary deadline accommodations have been instituted.
          </p>
          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Final Resolution Summary
            </label>
            <textarea
              rows={3}
              value={resolutionSummary}
              onChange={(e) => setResolutionSummary(e.target.value)}
              placeholder="e.g. Granted 4-day extension on DP assignment; student attended office hours and demonstrated clear comprehension."
              className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
              required
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};

const defaultIntervention: Intervention = {
  id: 'int-2026-08',
  student_id: 'std-101',
  student_name: 'Marcus Bell',
  trigger_type: 'Cognitive Overload Spike (IORI >= 0.60, Rho > 1.0)',
  iori_value_at_trigger: 0.74,
  risk_zone: 'red',
  status: 'in_progress',
  created_at: '2026-11-17T11:20:00Z',
};

const defaultMessages: MentorMessage[] = [
  {
    id: 'm1',
    sender_id: 'tch-1',
    sender_name: 'Dr. Sarah Miller (Faculty Mentor)',
    body: "Hi Marcus, I noticed you have multiple assignments converging this week and wanted to check in to see how you're feeling about the Algorithms problem set.",
    sent_at: '2026-11-17T11:30:00Z',
    is_read: true,
  },
  {
    id: 'm2',
    sender_id: 'std-101',
    sender_name: 'Marcus Bell (Student)',
    body: "Hello Dr. Miller, thank you for reaching out. Yes, the combination of the distributed systems lab and dynamic programming homework got overwhelming.",
    sent_at: '2026-11-17T12:05:00Z',
    is_read: true,
  },
  {
    id: 'm3',
    sender_id: 'tch-1',
    sender_name: 'Dr. Sarah Miller (Faculty Mentor)',
    body: "I understand completely. I have approved a 3-day extension on the DP homework so you can focus on the lab first without falling behind.",
    sent_at: '2026-11-17T12:15:00Z',
    is_read: true,
  },
];

export default InterventionPage;
