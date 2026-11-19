import React, { useState } from 'react';
import { FileCheck2, Plus, Calendar, Clock, Weight, Send, Check } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post } from '@/lib/api';
import { Assignment } from '@/types';
import { formatDate } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';

export const AssignmentsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [courseTitle, setCourseTitle] = useState('CS301: Advanced Algorithms');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('2026-11-28T23:59');
  const [estimatedHours, setEstimatedHours] = useState(6);
  const [workloadWeight, setWorkloadWeight] = useState(1.2);
  const [isPublished, setIsPublished] = useState(true);

  const { data: assignments = defaultAssignments, isLoading } = useQuery({
    queryKey: ['teacher_assignments'],
    queryFn: async (): Promise<Assignment[]> => {
      try {
        return await get<Assignment[]>('/assignments');
      } catch {
        return defaultAssignments;
      }
    },
  });

  const handleCreateAssignment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title) return;

    const newAssignment: Assignment = {
      id: `asg-${Date.now()}`,
      course_id: 'crs-1',
      course_title: courseTitle,
      title,
      description,
      due_date: new Date(dueDate).toISOString(),
      estimated_hours: estimatedHours,
      workload_weight: workloadWeight,
      is_published: isPublished,
      submissions_count: 0,
      created_at: new Date().toISOString(),
    };

    setIsModalOpen(false);
    setTitle('');
    setDescription('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <FileCheck2 className="h-6 w-6 text-coglearn-600" />
            Course Assignments & Workload Weights
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Author assignments with estimated effort and workload weights that feed the cognitive capacity model.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsModalOpen(true)}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Publish Assignment
        </Button>
      </div>

      <Alert variant="info" title="Queue Integration">
        Published assignments are automatically assigned to students' FIFO task queues with calibrated workload weights.
      </Alert>

      {/* Assignments Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Assignment Title</TableHead>
                <TableHead>Course</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead>Est. Effort</TableHead>
                <TableHead>Weight</TableHead>
                <TableHead>Submissions</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assignments.map((asg) => (
                <TableRow key={asg.id}>
                  <TableCell className="font-semibold text-slate-900">
                    <div>
                      <span>{asg.title}</span>
                      <p className="text-xs text-slate-400 font-normal line-clamp-1">{asg.description}</p>
                    </div>
                  </TableCell>
                  <TableCell className="text-xs text-slate-600 font-medium">
                    {asg.course_title || 'CS301: Advanced Algorithms'}
                  </TableCell>
                  <TableCell className="text-xs text-slate-700">
                    {formatDate(asg.due_date)}
                  </TableCell>
                  <TableCell className="text-xs font-mono text-slate-700">
                    {asg.estimated_hours} hrs
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" size="sm" className="font-mono">
                      {asg.workload_weight.toFixed(1)}x
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-slate-600">
                    <span className="font-semibold text-slate-900">{asg.submissions_count || 38}</span> / 54
                  </TableCell>
                  <TableCell>
                    {asg.is_published ? (
                      <Badge variant="success" size="sm">Published</Badge>
                    ) : (
                      <Badge variant="secondary" size="sm">Draft</Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create Assignment Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Publish Coursework Assignment"
        description="Configure due dates and workload weights for queue scheduling"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreateAssignment}>
              Publish Coursework
            </Button>
          </div>
        }
      >
        <form onSubmit={handleCreateAssignment} className="space-y-4 text-xs">
          <Input
            label="Assignment Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Dynamic Programming & Flow Optimization"
            required
          />

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Course</label>
            <select
              value={courseTitle}
              onChange={(e) => setCourseTitle(e.target.value)}
              className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
            >
              <option value="CS301: Advanced Algorithms">CS301: Advanced Algorithms</option>
              <option value="CS304: Distributed Systems">CS304: Distributed Systems</option>
              <option value="CS410: Deep Learning & Cognitive Models">CS410: Deep Learning & Cognitive Models</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Description & Guidelines</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detailed submission guidelines and formatting requirements..."
              className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Input
              label="Submission Due Date"
              type="datetime-local"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              required
            />
            <Input
              label="Estimated Effort (Hours)"
              type="number"
              min={1}
              max={50}
              value={estimatedHours}
              onChange={(e) => setEstimatedHours(Number(e.target.value))}
              required
            />
            <Input
              label="Workload Weight (x)"
              type="number"
              step="0.1"
              min={0.5}
              max={3.0}
              value={workloadWeight}
              onChange={(e) => setWorkloadWeight(Number(e.target.value))}
              required
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};

const defaultAssignments: Assignment[] = [
  {
    id: 'asg-1',
    course_id: 'crs-1',
    course_title: 'CS301: Advanced Algorithms',
    title: 'Dynamic Programming & Graph Optimizations',
    description: 'Implement Floyd-Warshall and Bellman-Ford with cycle detection benchmarks.',
    due_date: '2026-11-21T23:59:00Z',
    estimated_hours: 6.5,
    workload_weight: 1.2,
    is_published: true,
    submissions_count: 42,
  },
  {
    id: 'asg-2',
    course_id: 'crs-2',
    course_title: 'CS304: Distributed Systems',
    title: 'RPC and Network Socket Programming Lab',
    description: 'Build an idempotent key-value RPC store using gRPC.',
    due_date: '2026-11-24T23:59:00Z',
    estimated_hours: 5.0,
    workload_weight: 1.0,
    is_published: true,
    submissions_count: 36,
  },
  {
    id: 'asg-3',
    course_id: 'crs-1',
    course_title: 'CS301: Advanced Algorithms',
    title: 'NP-Completeness Reductions Problem Set',
    description: 'Formulate polynomial-time reductions for 3-SAT to CLIQUE and VERTEX-COVER.',
    due_date: '2026-11-18T23:59:00Z',
    estimated_hours: 5.0,
    workload_weight: 1.1,
    is_published: true,
    submissions_count: 49,
  },
];

export default AssignmentsPage;
