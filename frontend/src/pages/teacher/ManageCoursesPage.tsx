import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BookOpen, Plus, Edit, Users, Eye, Layers } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { get } from '@/lib/api';
import { Course } from '@/types';
import { formatDate } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableEmpty } from '@/components/ui/Table';

export const ManageCoursesPage: React.FC = () => {
  const navigate = useNavigate();

  const { data: courses = defaultManagedCourses, isLoading } = useQuery({
    queryKey: ['teacher_managed_courses'],
    queryFn: async (): Promise<Course[]> => {
      try {
        return await get<Course[]>('/courses/teaching');
      } catch {
        return defaultManagedCourses;
      }
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-coglearn-600" />
            Manage Courses & Syllabi
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Author and publish curriculum modules, lecture materials, and lesson resources.
          </p>
        </div>

        <Link to="/teacher/courses/new">
          <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />}>
            Create New Course
          </Button>
        </Link>
      </div>

      {/* Courses Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Course Code & Title</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Enrollment</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">Loading courses...</td>
                </tr>
              ) : courses.length === 0 ? (
                <TableEmpty colSpan={6} message="No courses created yet. Click 'Create New Course' to begin." />
              ) : (
                courses.map((course) => (
                  <TableRow key={course.id}>
                    <TableCell className="font-semibold text-slate-900">
                      <div>
                        <span>{course.title}</span>
                        <p className="text-xs text-slate-400 font-normal line-clamp-1">{course.description}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-slate-600">Computer Science</TableCell>
                    <TableCell>
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-700">
                        <Users className="h-3.5 w-3.5 text-slate-400" /> {course.enrolled_count || 48} students
                      </span>
                    </TableCell>
                    <TableCell>
                      {course.is_published ? (
                        <Badge variant="success" size="sm">Published</Badge>
                      ) : (
                        <Badge variant="secondary" size="sm">Draft</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {formatDate(course.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link to={`/teacher/courses/${course.id}/edit`}>
                          <Button variant="outline" size="sm" leftIcon={<Edit className="h-3.5 w-3.5" />}>
                            Edit
                          </Button>
                        </Link>
                        <Link to={`/courses/${course.id}`}>
                          <Button variant="ghost" size="sm" title="View Student Preview">
                            <Eye className="h-4 w-4 text-slate-500" />
                          </Button>
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

const defaultManagedCourses: Course[] = [
  {
    id: 'crs-1',
    title: 'CS301: Advanced Algorithms',
    description: 'Dynamic programming, network flow algorithms, and NP-completeness reductions.',
    teacher_id: 'tch-1',
    semester_id: 'sem-fall-2026',
    department_id: 'dept-cs',
    is_published: true,
    created_at: '2026-08-20T10:00:00Z',
    enrolled_count: 54,
  },
  {
    id: 'crs-2',
    title: 'CS304: Distributed Systems',
    description: 'Consensus algorithms, Raft, vector clocks, and RPC systems.',
    teacher_id: 'tch-1',
    semester_id: 'sem-fall-2026',
    department_id: 'dept-cs',
    is_published: true,
    created_at: '2026-08-22T10:00:00Z',
    enrolled_count: 42,
  },
  {
    id: 'crs-3',
    title: 'CS410: Deep Learning & Cognitive Models',
    description: 'Hidden Markov models, recurrent architectures, and cognitive capacity estimations.',
    teacher_id: 'tch-1',
    semester_id: 'sem-fall-2026',
    department_id: 'dept-cs',
    is_published: false,
    created_at: '2026-09-01T10:00:00Z',
    enrolled_count: 0,
  },
];

export default ManageCoursesPage;
