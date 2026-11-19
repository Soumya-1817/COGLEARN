import React, { useState } from 'react';
import { Users, Plus, Upload, Search, Filter, ShieldCheck, Mail, CheckCircle2 } from 'lucide-react';
import { User, UserRole } from '@/types';
import { formatDate } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';

export const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>(defaultUsers);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<UserRole | 'all'>('all');

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<UserRole>('student');
  const [csvContent, setCsvContent] = useState('');
  const [csvNotice, setCsvNotice] = useState<string | null>(null);

  const filteredUsers = users.filter((u) => {
    const matchesSearch = u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase());
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email) return;

    const newUser: User = {
      id: `usr-${Date.now()}`,
      full_name: fullName,
      email,
      role,
      institution_id: 'inst-oxford-01',
      is_active: true,
      created_at: new Date().toISOString(),
    };

    setUsers([newUser, ...users]);
    setIsCreateModalOpen(false);
    setFullName('');
    setEmail('');
  };

  const handleImportCsv = (e: React.FormEvent) => {
    e.preventDefault();
    // Parse CSV lines
    const lines = csvContent.split('\n').filter((l) => l.trim().length > 0);
    const imported: User[] = [];

    lines.forEach((line, idx) => {
      const parts = line.split(',').map((p) => p.trim());
      if (parts.length >= 2 && !parts[0].toLowerCase().includes('email')) {
        imported.push({
          id: `usr-csv-${Date.now()}-${idx}`,
          email: parts[0],
          full_name: parts[1] || 'Imported User',
          role: (parts[2] as UserRole) || 'student',
          institution_id: 'inst-oxford-01',
          is_active: true,
          created_at: new Date().toISOString(),
        });
      }
    });

    setUsers([...imported, ...users]);
    setIsCsvModalOpen(false);
    setCsvContent('');
    setCsvNotice(`Successfully imported ${imported.length} users into institutional tenant.`);
  };

  const toggleUserActive = (userId: string) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, is_active: !u.is_active } : u))
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Users className="h-6 w-6 text-coglearn-600" />
            Institutional User Directory
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage academic identities, student cohorts, faculty credentials, and role authorizations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setIsCsvModalOpen(true)}
            leftIcon={<Upload className="h-4 w-4" />}
          >
            Import CSV
          </Button>
          <Button
            variant="primary"
            onClick={() => setIsCreateModalOpen(true)}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Create User
          </Button>
        </div>
      </div>

      {csvNotice && (
        <Alert variant="success" onClose={() => setCsvNotice(null)}>
          {csvNotice}
        </Alert>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative max-w-sm w-full">
          <Input
            placeholder="Search by user name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={roleFilter === 'all' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setRoleFilter('all')}
          >
            All Roles ({users.length})
          </Button>
          <Button
            variant={roleFilter === 'student' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setRoleFilter('student')}
          >
            Students
          </Button>
          <Button
            variant={roleFilter === 'teacher' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setRoleFilter('teacher')}
          >
            Faculty
          </Button>
          <Button
            variant={roleFilter === 'inst_admin' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setRoleFilter('inst_admin')}
          >
            Admins
          </Button>
        </div>
      </div>

      {/* Users Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Full Name</TableHead>
                <TableHead>Institutional Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Institution ID</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead className="text-right">Account Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredUsers.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-semibold text-slate-900">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-coglearn-50 text-coglearn-700 font-bold text-xs">
                        {user.full_name[0]}
                      </div>
                      <span>{user.full_name}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-xs text-slate-600 font-mono">
                    {user.email}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        user.role === 'inst_admin'
                          ? 'default'
                          : user.role === 'teacher'
                          ? 'info'
                          : 'secondary'
                      }
                      size="sm"
                    >
                      {user.role.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs font-mono text-slate-400">
                    {user.institution_id || 'System Global'}
                  </TableCell>
                  <TableCell className="text-xs text-slate-500">
                    {formatDate(user.created_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <button
                      onClick={() => toggleUserActive(user.id)}
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold transition-colors ${
                        user.is_active
                          ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                          : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                      }`}
                    >
                      {user.is_active ? 'Active' : 'Disabled'}
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create User Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Academic User"
        description="Register a student, faculty member, or institutional administrator"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreateUser}>
              Register User
            </Button>
          </div>
        }
      >
        <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
          <Input
            label="Full Name"
            placeholder="e.g. Alex Chen"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />

          <Input
            label="Institutional Email"
            type="email"
            placeholder="e.g. alex.chen@university.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Assigned Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
            >
              <option value="student">Student (Task Queue, Courses, Mentorship)</option>
              <option value="teacher">Teacher / Faculty (IORI Diagnostics, Syllabi)</option>
              <option value="inst_admin">Institution Admin (Departments, Cohort Analytics)</option>
            </select>
          </div>
        </form>
      </Modal>

      {/* Import CSV Modal */}
      <Modal
        isOpen={isCsvModalOpen}
        onClose={() => setIsCsvModalOpen(false)}
        title="Batch Import Users via CSV"
        description="Paste comma-delimited lines formatted as: email, full_name, role"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsCsvModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleImportCsv}>
              Process Batch Import
            </Button>
          </div>
        }
      >
        <form onSubmit={handleImportCsv} className="space-y-3 text-xs">
          <div className="rounded-lg bg-slate-50 p-2.5 font-mono text-[11px] text-slate-600 border border-slate-200">
            Example:<br />
            emma.watson@university.edu, Emma Watson, student<br />
            prof.higgins@university.edu, Prof. Henry Higgins, teacher
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">CSV Content</label>
            <textarea
              rows={6}
              value={csvContent}
              onChange={(e) => setCsvContent(e.target.value)}
              placeholder="Paste comma-separated user records here..."
              className="w-full rounded-lg border border-slate-300 p-2.5 font-mono text-xs text-slate-800 focus:outline-none focus:border-coglearn-500"
              required
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};

const defaultUsers: User[] = [
  {
    id: 'usr-1',
    email: 'marcus.bell@university.edu',
    full_name: 'Marcus Bell',
    role: 'student',
    institution_id: 'inst-oxford-01',
    is_active: true,
    created_at: '2026-09-01T10:00:00Z',
  },
  {
    id: 'usr-2',
    email: 'elena.rostova@university.edu',
    full_name: 'Elena Rostova',
    role: 'student',
    institution_id: 'inst-oxford-01',
    is_active: true,
    created_at: '2026-09-01T10:00:00Z',
  },
  {
    id: 'usr-3',
    email: 'alex.chen@university.edu',
    full_name: 'Alex Chen',
    role: 'student',
    institution_id: 'inst-oxford-01',
    is_active: true,
    created_at: '2026-09-01T10:00:00Z',
  },
  {
    id: 'usr-4',
    email: 'dr.miller@university.edu',
    full_name: 'Dr. Sarah Miller',
    role: 'teacher',
    institution_id: 'inst-oxford-01',
    is_active: true,
    created_at: '2026-08-15T09:00:00Z',
  },
  {
    id: 'usr-5',
    email: 'dean.academic@university.edu',
    full_name: 'Dean Robert Vance',
    role: 'inst_admin',
    institution_id: 'inst-oxford-01',
    is_active: true,
    created_at: '2026-08-01T09:00:00Z',
  },
];

export default UsersPage;
