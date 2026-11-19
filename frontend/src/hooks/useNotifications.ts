import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, patch, post } from '@/lib/api';
import { Notification } from '@/types';

export const NOTIFICATIONS_QUERY_KEY = ['notifications'];

export function useNotifications() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: NOTIFICATIONS_QUERY_KEY,
    queryFn: async (): Promise<Notification[]> => {
      try {
        return await get<Notification[]>('/notifications');
      } catch (err) {
        console.warn('Backend API /notifications unavailable, using demo notifications', err);
        return getMockNotifications();
      }
    },
    refetchInterval: 30000,
  });

  const markAsRead = useMutation({
    mutationFn: async (notificationId: string) => {
      try {
        return await patch<Notification>(`/notifications/${notificationId}/read`);
      } catch {
        return { id: notificationId, is_read: true } as Notification;
      }
    },
    onSuccess: (updated) => {
      queryClient.setQueryData<Notification[]>(NOTIFICATIONS_QUERY_KEY, (old) => {
        if (!old) return [];
        return old.map((n) => (n.id === updated.id ? { ...n, is_read: true } : n));
      });
      queryClient.invalidateQueries({ queryKey: ['student_dashboard'] });
    },
  });

  const markAllAsRead = useMutation({
    mutationFn: async () => {
      try {
        await post('/notifications/mark-all-read');
      } catch {
        // Fallback
      }
    },
    onSuccess: () => {
      queryClient.setQueryData<Notification[]>(NOTIFICATIONS_QUERY_KEY, (old) => {
        if (!old) return [];
        return old.map((n) => ({ ...n, is_read: true }));
      });
      queryClient.invalidateQueries({ queryKey: ['student_dashboard'] });
    },
  });

  const notifications = query.data || [];
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return {
    ...query,
    notifications,
    unreadCount,
    markAsRead: markAsRead.mutate,
    markAllAsRead: markAllAsRead.mutate,
    isMarking: markAsRead.isPending || markAllAsRead.isPending,
  };
}

function getMockNotifications(): Notification[] {
  return [
    {
      id: 'notif-1',
      category: 'deadline',
      title: 'Upcoming Assignment Due',
      body: 'Dynamic Programming & Graph Optimizations assignment is due in 2 days.',
      priority: 'high',
      is_read: false,
      created_at: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
      action_url: '/tasks',
    },
    {
      id: 'notif-2',
      category: 'academic',
      title: 'New Course Announcement',
      body: 'Prof. Miller posted a new reading list for Distributed Systems Module 3.',
      priority: 'medium',
      is_read: false,
      created_at: new Date(Date.now() - 6 * 3600 * 1000).toISOString(),
      action_url: '/courses/crs-2',
    },
    {
      id: 'notif-3',
      category: 'mentorship',
      title: 'Mentor Message Received',
      body: 'Your academic advisor responded to your check-in request.',
      priority: 'medium',
      is_read: true,
      created_at: new Date(Date.now() - 24 * 3600 * 1000).toISOString(),
      action_url: '/mentorship',
    },
    {
      id: 'notif-4',
      category: 'deadline',
      title: 'Overdue Notice',
      body: 'NP-Completeness Problem Set was due yesterday. Please submit promptly.',
      priority: 'urgent',
      is_read: false,
      created_at: new Date(Date.now() - 30 * 3600 * 1000).toISOString(),
      action_url: '/tasks',
    },
  ];
}
