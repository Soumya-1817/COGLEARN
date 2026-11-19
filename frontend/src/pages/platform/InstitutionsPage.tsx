import React, { useState } from 'react';
import { Building2, Plus, Check, ShieldAlert, CheckCircle2, Clock, Globe } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { get, post } from '@/lib/api';
import { Institution } from '@/types';
import { formatDate } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';

export const InstitutionsPage: React.FC = () => {
  const [institutions, setInstitutions] = useState<Institution[]>(defaultInstitutions);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [isDemo, setIsDemo] = useState(false);

  const handleCreateInstitution = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !slug) return;

    const newInst: Institution = {
      id: `inst-${Date.now()}`,
      name,
      slug: slug.toLowerCase().replace(/\s+/g, '-'),
      is_demo: isDemo,
      is_active: true,
      approved_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      student_count: 0,
      teacher_count: 0,
    };

    setInstitutions([newInst, ...institutions]);
    setIsModalOpen(false);
    setName('');
    setSlug('');
    setIsDemo(false);
  };

  const handleApprove = (id: string) => {
    setInstitutions((prev) =>
      prev.map((inst) =>
        inst.id === id ? { ...inst, approved_at: new Date().toISOString(), is_active: true } : inst
      )
    );
  };

  const toggleActive = (id: string) => {
    setInstitutions((prev) =>
      prev.map((inst) => (inst.id === id ? { ...inst, is_active: !inst.is_active } : inst))
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Building2 className="h-6 w-6 text-coglearn-600" />
            University Tenants Management
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Provision and verify tenant partitions, approve academic onboarding, and manage sandbox demo instances.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsModalOpen(true)}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Provision University Tenant
        </Button>
      </div>

      {/* Institutions Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Institution Name</TableHead>
                <TableHead>Tenant Slug</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Approval Status</TableHead>
                <TableHead>Enrolled Cohort</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {institutions.map((inst) => (
                <TableRow key={inst.id}>
                  <TableCell className="font-semibold text-slate-900">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-coglearn-700 font-bold text-xs">
                        <Building2 className="h-4 w-4" />
                      </div>
                      <span>{inst.name}</span>
                    </div>
                  </TableCell>

                  <TableCell className="font-mono text-xs text-slate-600">
                    {inst.slug}
                  </TableCell>

                  <TableCell>
                    {inst.is_demo ? (
                      <Badge variant="warning" size="sm">Demo Sandbox</Badge>
                    ) : (
                      <Badge variant="default" size="sm">Production</Badge>
                    )}
                  </TableCell>

                  <TableCell>
                    {inst.approved_at ? (
                      <span className="inline-flex items-center gap-1 text-xs text-emerald-700 font-medium">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                        Approved ({formatDate(inst.approved_at)})
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs text-amber-700 font-medium">
                        <Clock className="h-3.5 w-3.5 text-amber-600" />
                        Pending Approval
                      </span>
                    )}
                  </TableCell>

                  <TableCell className="text-xs text-slate-600">
                    {inst.student_count || 350} students
                  </TableCell>

                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {!inst.approved_at && (
                        <Button
                          variant="success"
                          size="sm"
                          onClick={() => handleApprove(inst.id)}
                          leftIcon={<Check className="h-3 w-3" />}
                        >
                          Approve
                        </Button>
                      )}
                      <button
                        onClick={() => toggleActive(inst.id)}
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold transition-colors ${
                          inst.is_active
                            ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                            : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                        }`}
                      >
                        {inst.is_active ? 'Active Tenant' : 'Suspended'}
                      </button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Provision Tenant Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Provision University Tenant Partition"
        description="Establish an isolated institutional workspace with dedicated database tenant identifier"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreateInstitution}>
              Create Tenant
            </Button>
          </div>
        }
      >
        <form onSubmit={handleCreateInstitution} className="space-y-4 text-xs">
          <Input
            label="University Name"
            placeholder="e.g. Stanford University"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              if (!slug) setSlug(e.target.value.toLowerCase().replace(/\s+/g, '-'));
            }}
            required
          />

          <Input
            label="Tenant Subdomain Slug"
            placeholder="e.g. stanford"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            required
          />

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="is_demo_check"
              checked={isDemo}
              onChange={(e) => setIsDemo(e.target.checked)}
              className="rounded border-slate-300 text-coglearn-600 focus:ring-coglearn-500"
            />
            <label htmlFor="is_demo_check" className="font-semibold text-slate-700 cursor-pointer">
              Provision as Demo Sandbox (Pre-populated with synthetic student cohort)
            </label>
          </div>
        </form>
      </Modal>
    </div>
  );
};

const defaultInstitutions: Institution[] = [
  {
    id: 'inst-oxford-01',
    name: 'University of Oxford',
    slug: 'oxford',
    is_demo: false,
    is_active: true,
    approved_at: '2026-01-10T10:00:00Z',
    student_count: 840,
    teacher_count: 48,
  },
  {
    id: 'inst-cambridge-02',
    name: 'University of Cambridge',
    slug: 'cambridge',
    is_demo: false,
    is_active: true,
    approved_at: '2026-02-14T11:00:00Z',
    student_count: 720,
    teacher_count: 38,
  },
  {
    id: 'inst-mit-demo-03',
    name: 'MIT Evaluation Sandbox',
    slug: 'mit-sandbox',
    is_demo: true,
    is_active: true,
    approved_at: '2026-03-01T09:30:00Z',
    student_count: 50,
    teacher_count: 5,
  },
  {
    id: 'inst-zurich-pending',
    name: 'ETH Zurich Faculty of CS',
    slug: 'eth-zurich',
    is_demo: false,
    is_active: false,
    approved_at: null, // pending approval
    student_count: 0,
    teacher_count: 0,
  },
];

export default InstitutionsPage;
