import { useAuthStore } from '@/stores/authStore';
import { UserRole } from '@/types';

export function useAuth() {
  const { user, accessToken, isAuthenticated, isLoading, error, login, logout, refreshToken, setUser } = useAuthStore();

  const hasRole = (role: UserRole | UserRole[]): boolean => {
    if (!user) return false;
    if (Array.isArray(role)) {
      return role.includes(user.role);
    }
    return user.role === role;
  };

  return {
    user,
    accessToken,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    refreshToken,
    setUser,
    hasRole,
    isPlatformAdmin: user?.role === 'platform_admin',
    isInstAdmin: user?.role === 'inst_admin',
    isTeacher: user?.role === 'teacher',
    isStudent: user?.role === 'student',
  };
}

export default useAuth;
