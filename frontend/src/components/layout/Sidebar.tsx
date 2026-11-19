import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  ListOrdered,
  Calendar,
  Bell,
  HeartHandshake,
  Users,
  Building2,
  BarChart3,
  FileCheck2,
  GraduationCap,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

export interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const role = user?.role;

  // Build role-specific navigation links
  const getNavLinks = () => {
    switch (role) {
      case 'student':
        return [
          { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { to: '/courses', label: 'My Courses', icon: BookOpen },
          { to: '/tasks', label: 'Task Queue', icon: ListOrdered, badge: 'FIFO' },
          { to: '/calendar', label: 'Academic Calendar', icon: Calendar },
          { to: '/notifications', label: 'Notifications', icon: Bell },
          { to: '/mentorship', label: 'Get Help (Mentorship)', icon: HeartHandshake },
        ];

      case 'teacher':
        return [
          { to: '/teacher/dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { to: '/teacher/courses', label: 'My Courses', icon: BookOpen },
          { to: '/teacher/assignments', label: 'Assignments', icon: FileCheck2 },
          { to: '/teacher/mentor', label: 'Mentor Dashboard', icon: Sparkles, badge: 'IORI' },
          { to: '/teacher/mentorship-requests', label: 'Mentorship Requests', icon: HeartHandshake },
          { to: '/notifications', label: 'Notifications', icon: Bell },
        ];

      case 'inst_admin':
        return [
          { to: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { to: '/admin/departments', label: 'Departments', icon: Building2 },
          { to: '/admin/users', label: 'Users Directory', icon: Users },
          { to: '/admin/analytics', label: 'Analytics Portal', icon: BarChart3 },
        ];

      case 'platform_admin':
        return [
          { to: '/platform/dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { to: '/platform/institutions', label: 'Institutions', icon: Building2 },
        ];

      default:
        return [];
    }
  };

  const navLinks = getNavLinks();

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar container */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform duration-200 ease-in-out lg:static lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo and Brand */}
        <div className="flex h-16 items-center gap-3 border-b border-slate-100 px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-coglearn-600 text-white shadow-md shadow-coglearn-500/20">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-slate-900 flex items-center gap-1.5">
              COGLEARN
            </span>
            <span className="block text-[10px] font-medium text-slate-400 uppercase tracking-wider">
              Intelligent Learning
            </span>
          </div>
        </div>

        {/* User Role Tag */}
        <div className="px-6 py-3 border-b border-slate-100 bg-slate-50/60">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Navigation
            </span>
            <span className="rounded-full bg-coglearn-100 px-2 py-0.5 text-[10px] font-semibold text-coglearn-800 capitalize">
              {role?.replace('_', ' ') || 'Guest'}
            </span>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-4">
          {navLinks.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    'group flex items-center justify-between rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all',
                    isActive
                      ? 'bg-coglearn-600 text-white shadow-sm shadow-coglearn-500/20'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <Icon
                        className={cn(
                          'h-5 w-5 shrink-0 transition-colors',
                          isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-600'
                        )}
                      />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span
                        className={cn(
                          'rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider',
                          isActive
                            ? 'bg-white/20 text-white'
                            : 'bg-slate-100 text-slate-600'
                        )}
                      >
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Institutional Multitenant Footer Notice */}
        <div className="border-t border-slate-100 p-4 bg-slate-50/50">
          <div className="rounded-xl border border-slate-200/80 bg-white p-3 shadow-xs">
            <p className="text-[11px] font-semibold text-slate-800 line-clamp-1">
              Multi-Tenant Isolation
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">
              Inst ID: <code className="font-mono text-coglearn-700">{user?.institution_id ? user.institution_id.slice(0, 8) : 'Global'}</code>
            </p>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
