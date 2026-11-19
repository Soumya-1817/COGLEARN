import React, { useState } from 'react';
import { HeartHandshake, Check, X, MessageSquare, Clock, User } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { get } from '@/lib/api';
import { MentorshipRequest } from '@/types';
import { formatDate } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';

export const MentorshipRequestsPage: React.FC = () => {
  const [requests, setRequests] = useState<MentorshipRequest[]>(defaultInquiries);

  const handleUpdateStatus = (id: string, newStatus: 'accepted' | 'declined') => {
    setRequests((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: newStatus } : r))
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <HeartHandshake className="h-6 w-6 text-coglearn-600" />
            Student Mentorship Inquiries
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Review incoming requests from students seeking academic office hours and course assistance.
          </p>
        </div>

        <Badge variant="outline" size="md">
          {requests.filter((r) => r.status === 'pending').length} Pending Requests
        </Badge>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student</TableHead>
                <TableHead>Course</TableHead>
                <TableHead>Reason & Inquired Topics</TableHead>
                <TableHead>Submitted</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {requests.map((req) => (
                <TableRow key={req.id}>
                  <TableCell className="font-semibold text-slate-900">
                    <div className="flex items-center gap-2">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-700">
                        {req.student_name[0]}
                      </div>
                      <span>{req.student_name}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-xs text-slate-700 font-medium">
                    {req.course_title || 'General Advising'}
                  </TableCell>
                  <TableCell className="text-xs text-slate-600 max-w-sm">
                    <p className="line-clamp-2 leading-relaxed">{req.reason}</p>
                  </TableCell>
                  <TableCell className="text-xs text-slate-500 whitespace-nowrap">
                    {formatDate(req.created_at)}
                  </TableCell>
                  <TableCell>
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
                  </TableCell>
                  <TableCell className="text-right">
                    {req.status === 'pending' ? (
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="success"
                          size="sm"
                          onClick={() => handleUpdateStatus(req.id, 'accepted')}
                          leftIcon={<Check className="h-3 w-3" />}
                        >
                          Accept
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleUpdateStatus(req.id, 'declined')}
                          className="text-slate-400 hover:text-red-600"
                        >
                          Decline
                        </Button>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400 font-medium">Processed</span>
                    )}
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

const defaultInquiries: MentorshipRequest[] = [
  {
    id: 'req-1',
    student_id: 'std-104',
    student_name: 'Alex Chen',
    course_title: 'CS301: Advanced Algorithms',
    reason: 'Requesting 1-on-1 office hour assistance with reduction proofs for 3-SAT to Vertex Cover.',
    status: 'pending',
    created_at: '2026-11-18T14:30:00Z',
  },
  {
    id: 'req-2',
    student_id: 'std-102',
    student_name: 'Elena Rostova',
    course_title: 'CS304: Distributed Systems',
    reason: 'Need advice on debug tracing consensus split-brain edge cases in Raft lab.',
    status: 'pending',
    created_at: '2026-11-18T11:00:00Z',
  },
  {
    id: 'req-3',
    student_id: 'std-101',
    student_name: 'Marcus Bell',
    course_title: 'CS301: Advanced Algorithms',
    reason: 'Discussing course workload pacing and deadline scheduling options.',
    status: 'accepted',
    created_at: '2026-11-16T09:15:00Z',
  },
];

export default MentorshipRequestsPage;
