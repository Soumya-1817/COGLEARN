import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, patch, post } from '@/lib/api';
import { AcademicTask, TaskStatus } from '@/types';

export const TASK_QUERY_KEY = ['academic_tasks'];

export function useTasks(statusFilter?: TaskStatus | 'all') {
  return useQuery({
    queryKey: [...TASK_QUERY_KEY, statusFilter || 'all'],
    queryFn: async (): Promise<AcademicTask[]> => {
      try {
        const params: Record<string, unknown> = {};
        if (statusFilter && statusFilter !== 'all') {
          params.status = statusFilter;
        }
        const tasks = await get<AcademicTask[]>('/tasks', params);
        // Ensure FIFO order strictly by queue_position
        return [...tasks].sort((a, b) => a.queue_position - b.queue_position);
      } catch (err) {
        console.warn('Backend API /tasks unavailable, using fallback task data', err);
        return getMockTasks(statusFilter);
      }
    },
    staleTime: 30 * 1000,
  });
}

export function useTask(taskId: string) {
  return useQuery({
    queryKey: ['academic_task', taskId],
    queryFn: async (): Promise<AcademicTask> => {
      return get<AcademicTask>(`/tasks/${taskId}`);
    },
    enabled: !!taskId,
  });
}

export function useUpdateTaskStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ taskId, status }: { taskId: string; status: TaskStatus }) => {
      try {
        return await patch<AcademicTask>(`/tasks/${taskId}/status`, { status });
      } catch {
        // Optimistic local update fallback
        return { id: taskId, status } as AcademicTask;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TASK_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['student_dashboard'] });
    },
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskData: Partial<AcademicTask>) => {
      return post<AcademicTask>('/tasks', taskData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TASK_QUERY_KEY });
    },
  });
}

// Fallback demo tasks (FIFO queue)
function getMockTasks(statusFilter?: TaskStatus | 'all'): AcademicTask[] {
  const mockList: AcademicTask[] = [
    {
      id: 'task-1',
      student_id: 'std-1',
      course_id: 'crs-1',
      course_title: 'CS301: Advanced Algorithms',
      task_type: 'assignment',
      title: 'Dynamic Programming & Graph Optimizations',
      description: 'Implement Floyd-Warshall and Bellman-Ford with cycle detection benchmarks.',
      arrival_timestamp: '2026-11-15T08:00:00Z',
      queue_position: 1,
      due_date: '2026-11-21T23:59:00Z',
      estimated_workload: 6.5,
      workload_weight: 1.2,
      status: 'active',
      is_overdue: false,
    },
    {
      id: 'task-2',
      student_id: 'std-1',
      course_id: 'crs-2',
      course_title: 'CS304: Distributed Systems',
      task_type: 'quiz',
      title: 'Consensus & Raft Protocol Quiz',
      description: 'Weekly checkpoint quiz covering Raft leader election and log replication.',
      arrival_timestamp: '2026-11-16T10:00:00Z',
      queue_position: 2,
      due_date: '2026-11-20T18:00:00Z',
      estimated_workload: 2.0,
      workload_weight: 0.8,
      status: 'pending',
      is_overdue: false,
    },
    {
      id: 'task-3',
      student_id: 'std-1',
      course_id: 'crs-3',
      course_title: 'MATH240: Probability & Stochastic Processes',
      task_type: 'assessment',
      title: 'Midterm Assessment: Markov Chains & Queues',
      description: 'Covers discrete-time Markov chains, birth-death processes, and M/M/1 queue derivations.',
      arrival_timestamp: '2026-11-17T12:00:00Z',
      queue_position: 3,
      due_date: '2026-11-25T14:00:00Z',
      estimated_workload: 8.0,
      workload_weight: 1.5,
      status: 'pending',
      is_overdue: false,
    },
    {
      id: 'task-4',
      student_id: 'std-1',
      course_id: 'crs-1',
      course_title: 'CS301: Advanced Algorithms',
      task_type: 'assignment',
      title: 'NP-Completeness Reductions Problem Set',
      description: 'Formulate polynomial-time reductions for 3-SAT to CLIQUE and VERTEX-COVER.',
      arrival_timestamp: '2026-11-10T09:00:00Z',
      queue_position: 4,
      due_date: '2026-11-18T23:59:00Z',
      estimated_workload: 5.0,
      workload_weight: 1.1,
      status: 'overdue',
      is_overdue: true,
    },
    {
      id: 'task-5',
      student_id: 'std-1',
      course_id: 'crs-2',
      course_title: 'CS304: Distributed Systems',
      task_type: 'assignment',
      title: 'RPC and Network Socket Programming Lab',
      description: 'Build an idempotent key-value RPC store using gRPC.',
      arrival_timestamp: '2026-11-05T14:00:00Z',
      queue_position: 5,
      due_date: '2026-11-14T23:59:00Z',
      estimated_workload: 4.5,
      workload_weight: 1.0,
      status: 'completed',
      is_overdue: false,
    },
  ];

  if (!statusFilter || statusFilter === 'all') {
    return mockList;
  }
  return mockList.filter((t) => t.status === statusFilter);
}
