import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { GraduationCap, Lock, Mail, ArrowRight, Sparkles } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';

const DEMO_CREDENTIALS = {
  student: {
    email: 'jokonkwo@greenfield.edu',
    password: 'DemoStudent123!',
    label: 'Student',
    sub: 'James Okonkwo',
  },
  teacher: {
    email: 'achen@greenfield.edu',
    password: 'DemoTeacher123!',
    label: 'Teacher / Mentor',
    sub: 'Dr. Alexandra Chen',
  },
  inst_admin: {
    email: 'admin@greenfield.edu',
    password: 'DemoAdmin123!',
    label: 'Institution Admin',
    sub: 'Greenfield Admin',
  },
  platform_admin: {
    email: 'admin@coglearn.platform',
    password: 'PlatformAdmin2026!',
    label: 'Platform Admin',
    sub: 'System Superadmin',
  },
};

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading, error } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [demoLoggingRole, setDemoLoggingRole] = useState<string | null>(null);

  const getRedirectPath = (role: string) => {
    switch (role) {
      case 'student':
        return '/dashboard';
      case 'teacher':
        return '/teacher/dashboard';
      case 'inst_admin':
        return '/admin/dashboard';
      case 'platform_admin':
        return '/platform/dashboard';
      default:
        return '/dashboard';
    }
  };

  const executeLogin = async (loginEmail: string, loginPass: string) => {
    setFormError(null);
    try {
      await login(loginEmail, loginPass);
      const user = useAuthStore.getState().user;
      if (user) {
        const from = (location.state as { from?: { pathname: string } })?.from?.pathname;
        navigate(from || getRedirectPath(user.role), { replace: true });
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message);
      } else {
        setFormError('Unable to connect to authentication service. Please check your credentials.');
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setFormError('Please enter both your institutional email and password.');
      return;
    }
    await executeLogin(email.trim(), password);
  };

  // Quick Demo Login Handler that uses the REAL database credentials
  const handleDemoLogin = async (roleKey: keyof typeof DEMO_CREDENTIALS) => {
    const cred = DEMO_CREDENTIALS[roleKey];
    setEmail(cred.email);
    setPassword(cred.password);
    setDemoLoggingRole(roleKey);
    try {
      await executeLogin(cred.email, cred.password);
    } finally {
      setDemoLoggingRole(null);
    }
  };

  return (
    <div className="flex min-h-screen flex-col justify-center bg-gradient-to-b from-slate-50 to-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Brand Header */}
        <div className="flex justify-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-coglearn-600 text-white shadow-lg shadow-coglearn-500/25">
            <GraduationCap className="h-8 w-8" />
          </div>
        </div>
        <h2 className="mt-4 text-center text-3xl font-extrabold tracking-tight text-slate-900">
          COGLEARN
        </h2>
        <p className="mt-1 text-center text-sm font-medium text-slate-500">
          Intelligent Learning & Cognitive Risk Management Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="shadow-lg border-slate-200/80">
          <CardHeader>
            <CardTitle className="text-xl">Sign in to your account</CardTitle>
            <CardDescription>
              Enter your institutional credentials to access your workspace
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            {(formError || error) && (
              <Alert variant="danger" title="Authentication Error">
                {formError || error}
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Institutional Email"
                type="text"
                placeholder="name@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                leftIcon={<Mail className="h-4 w-4" />}
                required
                autoComplete="email"
              />

              <div className="space-y-1">
                <Input
                  label="Password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  leftIcon={<Lock className="h-4 w-4" />}
                  required
                  autoComplete="current-password"
                />
                <div className="flex justify-end pt-1">
                  <Link
                    to="/forgot-password"
                    className="text-xs font-medium text-coglearn-600 hover:text-coglearn-700 hover:underline"
                  >
                    Forgot password?
                  </Link>
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full mt-2"
                isLoading={isLoading && !demoLoggingRole}
                rightIcon={<ArrowRight className="h-4 w-4" />}
              >
                Sign In
              </Button>
            </form>

            {/* Sign Up Link */}
            <div className="text-center pt-2 border-t border-slate-100">
              <span className="text-sm text-slate-500">
                Don't have an account?{' '}
                <Link
                  to="/register"
                  className="font-medium text-coglearn-600 hover:text-coglearn-700 hover:underline"
                >
                  Sign up
                </Link>
              </span>
            </div>

            {/* Quick Demo Access Bar for rapid evaluation of all 4 roles */}
            <div className="pt-4 border-t border-slate-100">
              <div className="flex items-center justify-center gap-1.5 mb-2.5 text-center">
                <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  1-Click Demo Login
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {(Object.keys(DEMO_CREDENTIALS) as Array<keyof typeof DEMO_CREDENTIALS>).map((key) => {
                  const item = DEMO_CREDENTIALS[key];
                  const isCurrentLoading = demoLoggingRole === key;
                  return (
                    <button
                      key={key}
                      type="button"
                      disabled={isLoading}
                      onClick={() => handleDemoLogin(key)}
                      className="flex flex-col items-start p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-coglearn-50/70 hover:border-coglearn-300 text-left transition-all disabled:opacity-50"
                    >
                      <span className="text-xs font-semibold text-slate-800">
                        {isCurrentLoading ? 'Signing in...' : item.label}
                      </span>
                      <span className="text-[10px] text-slate-500 truncate w-full">
                        {item.sub}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Multi-Tenant and Ethics Disclaimer */}
        <p className="mt-6 text-center text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
          COGLEARN ensures strict tenant isolation by institution. Cognitive indicators are pedagogical support metrics, never diagnostic determinations.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
