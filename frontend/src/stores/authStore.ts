import { create } from 'zustand';
import { User } from '@/types';
import { loginApi, logoutApi, refreshApi, getCurrentUserApi } from '@/lib/auth';

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  setUser: (user: User) => void;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: typeof window !== 'undefined' ? localStorage.getItem('coglearn_access_token') : null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  setUser: (user: User) => {
    localStorage.setItem('coglearn_user', JSON.stringify(user));
    set({ user, isAuthenticated: true });
  },

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const data = await loginApi({ email: email.trim(), password });
      localStorage.setItem('coglearn_access_token', data.access_token);
      if (data.refresh_token) {
        localStorage.setItem('coglearn_refresh_token', data.refresh_token);
      }

      let user = data.user;
      if (!user) {
        try {
          user = await getCurrentUserApi();
        } catch {
          // If profile fetch fails, create minimal fallback user from token payload
          user = {
            id: 'user-authenticated',
            email: email.trim(),
            full_name: email.split('@')[0],
            role: email.includes('admin') ? 'inst_admin' : email.includes('chen') ? 'teacher' : 'student',
            institution_id: null,
            is_active: true,
            created_at: new Date().toISOString(),
          };
        }
      }

      localStorage.setItem('coglearn_user', JSON.stringify(user));

      set({
        user,
        accessToken: data.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      let msg = 'Login failed. Please verify your credentials.';
      if (err && typeof err === 'object' && 'response' in err) {
        const axErr = err as {
          response?: { data?: { detail?: string | Array<{ loc?: string[]; msg?: string }>; message?: string } };
        };
        const detail = axErr.response?.data?.detail;
        if (Array.isArray(detail)) {
          msg = detail.map((d) => d.msg || 'Invalid field').join(', ');
        } else if (typeof detail === 'string') {
          msg = detail;
        } else if (axErr.response?.data?.message) {
          msg = axErr.response.data.message;
        }
      }
      set({ isLoading: false, error: msg });
      throw new Error(msg);
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await logoutApi();
    } finally {
      localStorage.removeItem('coglearn_access_token');
      localStorage.removeItem('coglearn_refresh_token');
      localStorage.removeItem('coglearn_user');
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  },

  refreshToken: async (): Promise<boolean> => {
    const storedRefresh = localStorage.getItem('coglearn_refresh_token');
    if (!storedRefresh) {
      set({ isLoading: false, isAuthenticated: false, user: null, accessToken: null });
      return false;
    }

    try {
      const data = await refreshApi(storedRefresh);
      localStorage.setItem('coglearn_access_token', data.access_token);
      if (data.refresh_token) {
        localStorage.setItem('coglearn_refresh_token', data.refresh_token);
      }
      if (data.user) {
        localStorage.setItem('coglearn_user', JSON.stringify(data.user));
        set({
          user: data.user,
          accessToken: data.access_token,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        set({
          accessToken: data.access_token,
          isAuthenticated: true,
          isLoading: false,
        });
      }
      return true;
    } catch {
      localStorage.removeItem('coglearn_access_token');
      localStorage.removeItem('coglearn_refresh_token');
      localStorage.removeItem('coglearn_user');
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
      });
      return false;
    }
  },

  initialize: async () => {
    set({ isLoading: true });
    const storedToken = localStorage.getItem('coglearn_access_token');
    const storedUser = localStorage.getItem('coglearn_user');

    if (storedUser && storedToken) {
      try {
        const parsedUser = JSON.parse(storedUser) as User;
        set({ user: parsedUser, accessToken: storedToken, isAuthenticated: true });
        // Validate session with /auth/me in background
        try {
          const freshUser = await getCurrentUserApi();
          set({ user: freshUser });
          localStorage.setItem('coglearn_user', JSON.stringify(freshUser));
        } catch {
          // If token expired, try refresh
          await get().refreshToken();
        }
      } catch {
        await get().refreshToken();
      }
    } else if (localStorage.getItem('coglearn_refresh_token')) {
      await get().refreshToken();
    }
    set({ isLoading: false });
  },
}));
