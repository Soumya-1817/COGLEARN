import React, { useState } from 'react';
import {
  HeartHandshake,
  Send,
  MessageSquare,
  Clock,
  CheckCircle,
  PlusCircle,
  HelpCircle,
  AlertCircle,
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post } from '@/lib/api';
import { MentorshipRequest, MentorMessage } from '@/types';
import { formatDate, formatDateTime } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';

export const MentorshipPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [courseTitle, setCourseTitle] = useState('CS301: Advanced Algorithms');
  const [reason, setReason] = useState('');
  const [newMessage, setNewMessage] = useState('');

  // Mentorship requests
  const { data: requests = defaultRequests } = useQuery({
    queryKey: ['student_mentorship_requests'],
    queryFn: async (): Promise<MentorshipRequest[]> => {
      try {
        return await get<MentorshipRequest[]>('/mentorship/requests');
      } catch {
        return defaultRequests;
      }
    },
  });

  // Active messages thread
  const [messages, setMessages] = useState<MentorMessage[]>(defaultMessages);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    const msg: MentorMessage = {
      id: `msg-${Date.now()}`,
      sender_id: 'std-demo-1',
      sender_name: 'You (Student)',
      body: newMessage.trim(),
      sent_at: new Date().toISOString(),
      is_read: true,
    };

    setMessages((prev) => [...prev, msg]);
    setNewMessage('');
  };

  const handleCreateRequest = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) return;

    const newReq: MentorshipRequest = {
      id: `req-${Date.now()}`,
      student_id: 'std-demo-1',
      student_name: 'Alex Chen',
      course_title: courseTitle,
      reason: reason.trim(),
      status: 'pending',
      created_at: new Date().toISOString(),
    };

    setIsRequestModalOpen(false);
    setReason('');
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <HeartHandshake className="h-6 w-6 text-coglearn-600" />
            Academic Mentorship & Guidance
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Connect directly with your course instructors and faculty advisors for personalized academic assistance.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsRequestModalOpen(true)}
          leftIcon={<PlusCircle className="h-4 w-4" />}
        >
          Request Guidance
        </Button>
      </div>

      {/* Student Privacy Notice */}
      <Alert variant="info" title="Student Support Space">
        This conversation channel is confidential between you and assigned faculty mentors. Use this space to seek help on concepts, ask about problem sets, or request pacing adjustments.
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Previous Guidance Requests */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Your Guidance Requests
          </h3>

          <div className="space-y-3">
            {requests.map((req) => (
              <Card key={req.id} className="p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <Badge
                    variant={
                      req.status === 'accepted'
                        ? 'success'
                        : req.status === 'pending'
                        ? 'warning'
                        : 'secondary'
                    }
                    size="sm"
                  >
                    {req.status}
                  </Badge>
                  <span className="text-[11px] text-slate-400 font-medium">
                    {formatDate(req.created_at)}
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-slate-800">{req.course_title}</h4>
                <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">{req.reason}</p>
              </Card>
            ))}
          </div>
        </div>

        {/* Right Column: Direct Messaging Thread */}
        <div className="lg:col-span-2">
          <Card className="flex flex-col h-[560px]">
            <CardHeader className="border-b border-slate-100 py-3.5 px-5 bg-slate-50/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-coglearn-100 text-coglearn-700 font-bold text-xs">
                    SM
                  </div>
                  <div>
                    <CardTitle className="text-sm">Dr. Sarah Miller</CardTitle>
                    <p className="text-[11px] text-emerald-600 font-medium">Faculty Mentor • Online</p>
                  </div>
                </div>
                <span className="text-xs text-slate-400 font-medium">Active Thread</span>
              </div>
            </CardHeader>

            {/* Messages Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map((m) => {
                const isStudent = m.sender_name.includes('Student') || m.sender_name.includes('You');
                return (
                  <div
                    key={m.id}
                    className={`flex flex-col ${isStudent ? 'items-end' : 'items-start'}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[11px] font-semibold text-slate-600">{m.sender_name}</span>
                      <span className="text-[10px] text-slate-400">{formatDateTime(m.sent_at)}</span>
                    </div>
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed ${
                        isStudent
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

            {/* Message input */}
            <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-100 bg-white">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Type a message to your mentor..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  className="flex-1 rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500 focus:ring-1 focus:ring-coglearn-500"
                />
                <Button type="submit" variant="primary" size="sm" leftIcon={<Send className="h-3.5 w-3.5" />}>
                  Send
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>

      {/* Request Guidance Modal */}
      <Modal
        isOpen={isRequestModalOpen}
        onClose={() => setIsRequestModalOpen(false)}
        title="Request Academic Mentorship Guidance"
        description="Submit a request to meet or communicate with your course instructor."
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsRequestModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreateRequest}>
              Submit Request
            </Button>
          </div>
        }
      >
        <form onSubmit={handleCreateRequest} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Select Course</label>
            <select
              value={courseTitle}
              onChange={(e) => setCourseTitle(e.target.value)}
              className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
            >
              <option value="CS301: Advanced Algorithms">CS301: Advanced Algorithms</option>
              <option value="CS304: Distributed Systems">CS304: Distributed Systems</option>
              <option value="MATH240: Probability & Queues">MATH240: Probability & Queues</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              What do you need assistance with?
            </label>
            <textarea
              rows={4}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Describe concepts you're finding challenging or workload scheduling questions..."
              className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
              required
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};

// Fallback demo mentorship requests & messages
const defaultRequests: MentorshipRequest[] = [
  {
    id: 'req-1',
    student_id: 'std-demo-1',
    student_name: 'Alex Chen',
    course_title: 'CS301: Advanced Algorithms',
    reason: 'Struggling with reduction proofs for 3-SAT to Vertex Cover ahead of midterm.',
    status: 'accepted',
    created_at: '2026-11-16T14:00:00Z',
  },
  {
    id: 'req-2',
    student_id: 'std-demo-1',
    student_name: 'Alex Chen',
    course_title: 'MATH240: Probability & Queues',
    reason: 'Requesting clarification on state transition rate balance equations for M/M/1 queues.',
    status: 'pending',
    created_at: '2026-11-18T10:30:00Z',
  },
];

const defaultMessages: MentorMessage[] = [
  {
    id: 'msg-1',
    sender_id: 'tch-1',
    sender_name: 'Dr. Sarah Miller (Mentor)',
    body: 'Hi Alex, I saw your note about the NP-completeness reduction problems. How can I best guide you?',
    sent_at: '2026-11-16T15:20:00Z',
    is_read: true,
  },
  {
    id: 'msg-2',
    sender_id: 'std-demo-1',
    sender_name: 'You (Student)',
    body: "Thank you Dr. Miller! I'm specifically struggling with formulating the gadget construction for 3-SAT clauses to vertex components.",
    sent_at: '2026-11-16T15:35:00Z',
    is_read: true,
  },
  {
    id: 'msg-3',
    sender_id: 'tch-1',
    sender_name: 'Dr. Sarah Miller (Mentor)',
    body: "Good question. Try drawing the triangular gadget for each clause of 3 literals, and note why you must select at least 2 vertices per triangle. Let's do a 15-minute check-in during office hours tomorrow if you get stuck.",
    sent_at: '2026-11-16T16:00:00Z',
    is_read: true,
  },
];

export default MentorshipPage;
