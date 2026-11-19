import React, { useState } from 'react';
import { Building2, Plus, Layers, Users, BookOpen } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { get, post } from '@/lib/api';
import { Department } from '@/types';
import { formatDate } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';

export const DepartmentsPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deptName, setDeptName] = useState('');
  const [deptCode, setDeptCode] = useState('');

  const [departments, setDepartments] = useState<Department[]>(defaultDepartments);

  const handleCreateDepartment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!deptName || !deptCode) return;

    const newDept: Department = {
      id: `dept-${Date.now()}`,
      institution_id: 'inst-oxford-01',
      name: deptName,
      code: deptCode.toUpperCase(),
      created_at: new Date().toISOString(),
    };

    setDepartments((prev) => [...prev, newDept]);
    setIsModalOpen(false);
    setDeptName('');
    setDeptCode('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Building2 className="h-6 w-6 text-coglearn-600" />
            University Departments & Academic Units
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Organize degree programmes, faculty allocations, and departmental workload policies.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsModalOpen(true)}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Add Department
        </Button>
      </div>

      {/* Departments Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Department Name</TableHead>
                <TableHead>Degree Programmes</TableHead>
                <TableHead>Institution ID</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {departments.map((dept) => (
                <TableRow key={dept.id}>
                  <TableCell className="font-mono font-bold text-xs text-coglearn-700">
                    {dept.code}
                  </TableCell>
                  <TableCell className="font-semibold text-slate-900">
                    {dept.name}
                  </TableCell>
                  <TableCell className="text-xs text-slate-600">
                    B.Sc, M.Sc, Ph.D Programmes
                  </TableCell>
                  <TableCell className="text-xs font-mono text-slate-400">
                    {dept.institution_id}
                  </TableCell>
                  <TableCell className="text-xs text-slate-500">
                    {formatDate(dept.created_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant="success" size="sm">Active</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create Department Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Register New Academic Department"
        description="Establish an organizational unit within your university tenant"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreateDepartment}>
              Create Department
            </Button>
          </div>
        }
      >
        <form onSubmit={handleCreateDepartment} className="space-y-4 text-xs">
          <Input
            label="Department Code"
            placeholder="e.g. CS, MATH, EE"
            value={deptCode}
            onChange={(e) => setDeptCode(e.target.value)}
            required
          />

          <Input
            label="Department Full Name"
            placeholder="e.g. Department of Computer Science & Engineering"
            value={deptName}
            onChange={(e) => setDeptName(e.target.value)}
            required
          />
        </form>
      </Modal>
    </div>
  );
};

const defaultDepartments: Department[] = [
  {
    id: 'dept-1',
    institution_id: 'inst-oxford-01',
    name: 'Computer Science & Engineering',
    code: 'CSE',
    created_at: '2026-01-15T09:00:00Z',
  },
  {
    id: 'dept-2',
    institution_id: 'inst-oxford-01',
    name: 'Mathematics & Stochastic Modeling',
    code: 'MATH',
    created_at: '2026-01-15T09:00:00Z',
  },
  {
    id: 'dept-3',
    institution_id: 'inst-oxford-01',
    name: 'Electrical & Computer Engineering',
    code: 'ECE',
    created_at: '2026-02-01T09:00:00Z',
  },
];

export default DepartmentsPage;
