import React, { useState } from 'react';
import {
  ListOrdered,
  CheckCircle,
  PlayCircle,
  Calendar,
} from 'lucide-react';
import { useTasks, useUpdateTaskStatus } from '@/hooks/useTasks';
import { AcademicTask, TaskStatus } from '@/types';
import { formatDate, formatRelative, checkIsOverdue } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';

export const TaskQueuePage: React.FC = () => {
  const [filter, setFilter] = useState<TaskStatus | 'all'>('all');
  const [selectedTask, setSelectedTask] = useState<AcademicTask | null>(null);

  const { data: rawTasks = [], isLoading } = useTasks(filter === 'all' ? undefined : filter);
  const updateStatus = useUpdateTaskStatus();

  // Strict FIFO queue ordering by queue_position
  const tasks = [...rawTasks].sort((a, b) => a.queue_position - b.queue_position);

  const handleStartTask = (taskId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    updateStatus.mutate({ taskId, status: 'active' });
  };

  const handleCompleteTask = (taskId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    updateStatus.mutate({ taskId, status: 'completed' });
    if (selectedTask?.id === taskId) {
      setSelectedTask(null);
    }
  };

  const filterTabs: { label: string; value: TaskStatus | 'all'; count?: number }[] = [
    { label: 'All Tasks', value: 'all' },
    { label: 'Pending', value: 'pending' },
    { label: 'In Progress (Active)', value: 'active' },
    { label: 'Overdue', value: 'overdue' },
    { label: 'Completed', value: 'completed' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <ListOrdered className="h-6 w-6 text-coglearn-600" />
            Academic Task Queue (FIFO)
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Tasks are scheduled in First-In-First-Out sequence based on pedagogical arrival time.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" size="md">
            FIFO Discipline Enforced
          </Badge>
        </div>
      </div>

      {/* Explanation Banner */}
      <Alert variant="info" title="Queue Management Notice">
        Your assignments and assessments are positioned in FIFO order. Urgent deadlines are highlighted with distinct warning badges so you can balance queue discipline with imminent submission dates.
      </Alert>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto border-b border-slate-200 pb-2">
        {filterTabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setFilter(tab.value)}
            className={`rounded-lg px-4 py-2 text-xs font-semibold whitespace-nowrap transition-colors ${
              filter === tab.value
                ? 'bg-coglearn-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tasks List */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 rounded-xl bg-slate-100 animate-pulse" />
          ))}
        </div>
      ) : tasks.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-12 text-center">
          <CheckCircle className="h-10 w-10 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No tasks in this category</h3>
          <p className="text-xs text-slate-500 mt-1">Your academic queue is clear for the selected filter.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => {
            const isOver = task.status === 'overdue' || (task.status !== 'completed' && checkIsOverdue(task.due_date));
            const isActive = task.status === 'active';
            const isCompleted = task.status === 'completed';

            return (
              <Card
                key={task.id}
                hover
                onClick={() => setSelectedTask(task)}
                className={`cursor-pointer transition-all ${
                  isOver
                    ? 'border-red-300 bg-red-50/20 shadow-xs'
                    : isActive
                    ? 'border-sky-300 bg-sky-50/20 shadow-xs'
                    : isCompleted
                    ? 'border-slate-200 opacity-75'
                    : 'border-slate-200 bg-white'
                }`}
              >
                <CardContent className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-start gap-4">
                    {/* Queue position badge */}
                    <div className="flex flex-col items-center justify-center rounded-xl bg-slate-100 px-3 py-2 border border-slate-200 min-w-[56px] shrink-0">
                      <span className="text-[10px] uppercase font-bold text-slate-400">Pos</span>
                      <span className="text-lg font-black text-slate-800">#{task.queue_position}</span>
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-base font-semibold text-slate-900">{task.title}</h3>
                        <Badge
                          variant={
                            task.task_type === 'assessment'
                              ? 'danger'
                              : task.task_type === 'quiz'
                              ? 'info'
                              : 'secondary'
                          }
                          size="sm"
                        >
                          {task.task_type}
                        </Badge>

                        {/* Status Badge */}
                        {isCompleted && <Badge variant="success" size="sm">Completed</Badge>}
                        {isActive && <Badge variant="info" size="sm">In Progress</Badge>}
                        {isOver && <Badge variant="danger" size="sm">Overdue</Badge>}
                      </div>

                      <p className="text-xs text-slate-500 font-medium">
                        {task.course_title || 'Enrolled Course'} • Arrival: {formatDate(task.arrival_timestamp)}
                      </p>

                      {task.description && (
                        <p className="text-xs text-slate-600 line-clamp-2 pt-1 leading-relaxed">
                          {task.description}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Actions & Urgency */}
                  <div className="flex items-center gap-4 shrink-0 md:self-center border-t md:border-t-0 pt-3 md:pt-0">
                    <div className="text-right">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                        <span>Due {formatDate(task.due_date)}</span>
                      </div>
                      <span className={`text-[11px] block ${isOver ? 'text-red-600 font-bold' : 'text-slate-400'}`}>
                        {formatRelative(task.due_date)}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {task.status === 'pending' && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={(e) => handleStartTask(task.id, e)}
                          leftIcon={<PlayCircle className="h-4 w-4" />}
                        >
                          Start Task
                        </Button>
                      )}

                      {task.status === 'active' && (
                        <Button
                          variant="success"
                          size="sm"
                          onClick={(e) => handleCompleteTask(task.id, e)}
                          leftIcon={<CheckCircle className="h-4 w-4" />}
                        >
                          Complete
                        </Button>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTask(task);
                        }}
                      >
                        Details
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Task Details Modal */}
      {selectedTask && (
        <Modal
          isOpen={!!selectedTask}
          onClose={() => setSelectedTask(null)}
          title={selectedTask.title}
          description={`${selectedTask.course_title || 'Academic Course'} (Position #${selectedTask.queue_position})`}
          footer={
            <div className="flex items-center justify-between w-full">
              <span className="text-xs text-slate-500">
                Estimated Workload: <strong className="text-slate-800">{selectedTask.estimated_workload} hrs</strong>
              </span>
              <div className="flex gap-2">
                {selectedTask.status === 'pending' && (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={(e) => handleStartTask(selectedTask.id, e)}
                  >
                    Set as Active
                  </Button>
                )}
                {selectedTask.status === 'active' && (
                  <Button
                    variant="success"
                    size="sm"
                    onClick={(e) => handleCompleteTask(selectedTask.id, e)}
                  >
                    Mark as Completed
                  </Button>
                )}
                <Button variant="outline" size="sm" onClick={() => setSelectedTask(null)}>
                  Close
                </Button>
              </div>
            </div>
          }
        >
          <div className="space-y-4 text-sm">
            <div>
              <h5 className="font-semibold text-slate-800 text-xs uppercase tracking-wider mb-1">
                Instructions & Details
              </h5>
              <p className="text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
                {selectedTask.description || 'No detailed instructions provided for this coursework unit.'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg border border-slate-100 p-2.5 bg-white">
                <span className="text-slate-400 block mb-0.5">Task Type</span>
                <span className="font-semibold text-slate-800 capitalize">{selectedTask.task_type}</span>
              </div>
              <div className="rounded-lg border border-slate-100 p-2.5 bg-white">
                <span className="text-slate-400 block mb-0.5">Due Date</span>
                <span className="font-semibold text-slate-800">{formatDate(selectedTask.due_date)}</span>
              </div>
              <div className="rounded-lg border border-slate-100 p-2.5 bg-white">
                <span className="text-slate-400 block mb-0.5">Queue Arrival</span>
                <span className="font-semibold text-slate-800">{formatDate(selectedTask.arrival_timestamp)}</span>
              </div>
              <div className="rounded-lg border border-slate-100 p-2.5 bg-white">
                <span className="text-slate-400 block mb-0.5">Status</span>
                <span className="font-semibold text-slate-800 capitalize">{selectedTask.status}</span>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default TaskQueuePage;
