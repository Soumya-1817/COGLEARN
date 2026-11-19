import React, { useState } from 'react';
import { Bell, CheckCheck, Filter } from 'lucide-react';
import { useNotifications } from '@/hooks/useNotifications';
import { NotificationList } from '@/components/notifications/NotificationList';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

export const NotificationsPage: React.FC = () => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, isLoading, isMarking } = useNotifications();
  const [filter, setFilter] = useState<'all' | 'unread' | 'deadline' | 'mentorship'>('all');

  const filteredNotifications = notifications.filter((n) => {
    if (filter === 'unread') return !n.is_read;
    if (filter === 'deadline') return n.category === 'deadline';
    if (filter === 'mentorship') return n.category === 'mentorship';
    return true;
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Bell className="h-6 w-6 text-coglearn-600" />
            Notifications & Alerts
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Stay up to date with course announcements, deadline notices, and faculty replies.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {unreadCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => markAllAsRead()}
              isLoading={isMarking}
              leftIcon={<CheckCheck className="h-4 w-4" />}
            >
              Mark All as Read
            </Button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setFilter('all')}
          className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors ${
            filter === 'all'
              ? 'bg-coglearn-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          All ({notifications.length})
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors ${
            filter === 'unread'
              ? 'bg-coglearn-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Unread ({unreadCount})
        </button>
        <button
          onClick={() => setFilter('deadline')}
          className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors ${
            filter === 'deadline'
              ? 'bg-coglearn-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Deadlines
        </button>
        <button
          onClick={() => setFilter('mentorship')}
          className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors ${
            filter === 'mentorship'
              ? 'bg-coglearn-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Mentorship & Faculty
        </button>
      </div>

      {/* Notifications List */}
      <NotificationList
        notifications={filteredNotifications}
        onMarkAsRead={markAsRead}
        isLoading={isLoading}
      />
    </div>
  );
};

export default NotificationsPage;
