import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { GraduationCap, Lock, Mail, User as UserIcon, ArrowRight, Building } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { registerApi, getPublicInstitutionsApi } from '@/lib/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';

interface PublicInstitution {
  id: string;
  name: string;
  slug: string;
  is_demo: boolean;
}

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<'student' | 'teacher'>('student');
  const [institutionId, setInstitutionId] = useState<string>('');
  const [institutions, setInstitutions] = useState<PublicInstitution[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    async function loadInstitutions() {
      try {
        const list = await getPublicInstitutionsApi();
        setInstitutions(list);
        if (list.length > 0) {
          setInstitutionId(list[0].id);
        }
      } catch {
        // Fallback default
        setInstitutions([
          { id: '', name: 'Greenfield University (Default)', slug: 'greenfield-university', is_demo: true },
        ]);
      }
    }
    loadInstitutions();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!fullName.trim() || !email.trim() || !password) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter.');
      return;
    }

    setIsLoading(true);
    try {
      await registerApi({
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
        role,
        institution_id: institutionId ? institutionId : null,
      });

      setSuccessMsg('Account created successfully! Logging you in...');

      // Automatically log in newly registered user
      try {
        await login(email.trim().toLowerCase(), password);
        const user = useAuthStore.getState().user;
        if (user?.role === 'teacher') {
          navigate('/teacher/dashboard', { replace: true });
        } else {
          navigate('/dashboard', { replace: true });
        }
      } catch {
        // If auto-login fails, redirect to login page after short delay
        setTimeout(() => navigate('/login'), 1500);
      }
    } catch (err: unknown) {
      let msg = 'Registration failed. Please try again.';
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
      setError(msg);
    } finally {
      setIsLoading(false);
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
          Create your academic account
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="shadow-lg border-slate-200/80">
          <CardHeader>
            <CardTitle className="text-xl">Sign up for COGLEARN</CardTitle>
            <CardDescription>
              Join your university workspace to access courses and task management
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            {error && (
              <Alert variant="danger" title="Registration Error">
                {error}
              </Alert>
            )}

            {successMsg && (
              <Alert variant="success" title="Success">
                {successMsg}
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Full Name"
                type="text"
                placeholder="Jane Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                leftIcon={<UserIcon className="h-4 w-4" />}
                required
                autoComplete="name"
              />

              <Input
                label="Institutional Email"
                type="email"
                placeholder="jane.doe@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                leftIcon={<Mail className="h-4 w-4" />}
                required
                autoComplete="email"
              />

              {/* Role Selection */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                  Academic Role
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setRole('student')}
                    className={`py-2 px-3 text-xs font-medium rounded-lg border text-center transition-all ${
                      role === 'student'
                        ? 'bg-coglearn-50 border-coglearn-600 text-coglearn-700 font-semibold shadow-sm'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    Student
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole('teacher')}
                    className={`py-2 px-3 text-xs font-medium rounded-lg border text-center transition-all ${
                      role === 'teacher'
                        ? 'bg-coglearn-50 border-coglearn-600 text-coglearn-700 font-semibold shadow-sm'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    Teacher / Mentor
                  </button>
                </div>
              </div>

              {/* Institution Selection */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                  Institution
                </label>
                <div className="relative">
                  <select
                    value={institutionId}
                    onChange={(e) => setInstitutionId(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-slate-800 shadow-sm focus:border-coglearn-500 focus:outline-none focus:ring-1 focus:ring-coglearn-500"
                  >
                    {institutions.map((inst) => (
                      <option key={inst.id || 'default'} value={inst.id}>
                        {inst.name} {inst.is_demo ? '(Demo)' : ''}
                      </option>
                    ))}
                  </select>
                  <Building className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                </div>
              </div>

              <Input
                label="Password"
                type="password"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                leftIcon={<Lock className="h-4 w-4" />}
                required
                autoComplete="new-password"
              />

              <Input
                label="Confirm Password"
                type="password"
                placeholder="Re-enter password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                leftIcon={<Lock className="h-4 w-4" />}
                required
                autoComplete="new-password"
              />

              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full mt-2"
                isLoading={isLoading}
                rightIcon={<ArrowRight className="h-4 w-4" />}
              >
                Create Account
              </Button>
            </form>

            <div className="text-center pt-2 border-t border-slate-100">
              <span className="text-sm text-slate-500">
                Already have an account?{' '}
                <Link
                  to="/login"
                  className="font-medium text-coglearn-600 hover:text-coglearn-700 hover:underline"
                >
                  Sign in
                </Link>
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Footer info */}
        <p className="mt-6 text-center text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
          COGLEARN ensures strict tenant isolation by institution. Cognitive indicators are pedagogical support metrics, never diagnostic determinations.
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
