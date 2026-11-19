import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Clock, AlertTriangle, AlertCircle, Info, ExternalLink } from 'lucide-react';
import { Notification, NotificationPriority } from '@/types';
import { formatRelative } from '@/lib/utils';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

export interface NotificationListProps {
  notifications: Notification[];
  onMarkAsRead: (id: string) => void;
  isLoading?: boolean;
}

export const NotificationList: React.FC<NotificationListProps> = ({
  notifications,
  onMarkAsRead,
  isLoading = false,
}) => {
  const navigate = useNavigate();

  const getPriorityBadge = (priority: NotificationPriority) => {
    switch (priority) {
      case 'urgent':
        return <Badge variant="danger" size="sm">Urgent</Badge>;
      case 'high':
        return <Badge variant="warning" size="sm">High Priority</Badge>;
      case 'medium':
        return <Badge variant="info" size="sm">Medium</Badge>;
      case 'low':
      default:
        return <Badge variant="secondary" size="sm">Low</Badge>;
    }
  };

  const getPriorityIcon = (priority: NotificationPriority) => {
    switch (priority) {
      case 'urgent':
        return <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />;
      case 'high':
        return <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />;
      case 'medium':
        return <Info className="h-5 w-5 text-sky-500 shrink-0 mt-0.5" />;
      case 'low':
      default:
        return <Clock className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 rounded-xl bg-slate-100 animate-pulse" />
        ))}
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 p-12 text-center">
        <Clock className="h-10 w-10 text-slate-300 mx-auto mb-3" />
        <h4 className="text-sm font-semibold text-slate-700">No notifications yet</h4>
        <p className="text-xs text-slate-500 mt-1">
          When deadlines, course announcements, or mentor updates arrive, they will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`flex items-start justify-between gap-4 p-4 rounded-xl border transition-all ${
            notification.is_read
              ? 'bg-white border-slate-200'
              : 'bg-sky-50/30 border-sky-200 shadow-sm'
          }`}
        >
          <div className="flex items-start gap-3 flex-1">
            {getPriorityIcon(notification.priority)}
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <h4 className="text-sm font-semibold text-slate-900">{notification.title}</h4>
                {getPriorityBadge(notification.priority)}
                <span className="text-[11px] text-slate-400 ml-auto">
                  {formatRelative(notification.created_at)}
                </span>
              </div>
              <p className="text-sm text-slate-600 leading-relaxed">{notification.body}</p>

              {notification.action_url && (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3 text-xs"
                  rightIcon={<ExternalLink className="h-3 w-3" />}
                  onClick={() => {
                    if (!notification.is_read) onMarkAsRead(notification.id);
                    navigate(notification.action_url!);
                  }}
                >
                  View details
                </Button>
              )}
            </div>
          </div>

          {!notification.is_read && (
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-slate-400 hover:text-coglearn-600 shrink-0"
              onClick={() => onMarkAsRead(notification.id)}
              leftIcon={<Check className="h-3.5 w-3.5" />}
            >
              Mark read
            </Button>
          )}
        </div>
      ))}
    </div>
  );
};

export default NotificationList;
