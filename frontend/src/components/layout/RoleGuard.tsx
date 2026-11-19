import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { UserRole } from '@/types';
import { Spinner } from '@/components/ui/Spinner';
import { Button } from '@/components/ui/Button';

export interface RoleGuardProps {
  allowedRoles: UserRole[];
  children: React.ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ allowedRoles, children }) => {
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <Spinner size="lg" className="text-coglearn-600" />
          <p className="text-sm font-medium text-slate-500">Verifying session permissions...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return (
      <div className="flex min-h-[80vh] flex-col items-center justify-center p-6 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-100 text-red-600">
          <ShieldAlert className="h-8 w-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">Access Restricted (403)</h2>
        <p className="mt-2 max-w-md text-sm text-slate-600">
          Your account role (<span className="font-semibold capitalize">{user.role.replace('_', ' ')}</span>) does not have authorization to view this resource.
        </p>
        <div className="mt-6 flex gap-3">
          <Button
            variant="primary"
            onClick={() => {
              if (user.role === 'student') window.location.href = '/dashboard';
              else if (user.role === 'teacher') window.location.href = '/teacher/dashboard';
              else if (user.role === 'inst_admin') window.location.href = '/admin/dashboard';
              else if (user.role === 'platform_admin') window.location.href = '/platform/dashboard';
              else window.location.href = '/login';
            }}
          >
            Return to Authorized Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default RoleGuard;
