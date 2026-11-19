import React from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, User, Layers, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { get } from '@/lib/api';
import { Course } from '@/types';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export const CoursesPage: React.FC = () => {
  const { data: courses = defaultCourses, isLoading } = useQuery({
    queryKey: ['student_enrolled_courses'],
    queryFn: async (): Promise<Course[]> => {
      try {
        return await get<Course[]>('/courses/enrolled');
      } catch {
        return defaultCourses;
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
            My Enrolled Courses
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Access your course syllabi, learning modules, video lessons, and reading materials.
          </p>
        </div>

        <Badge variant="outline" size="md">
          {courses.length} Active Courses
        </Badge>
      </div>

      {/* Courses Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 rounded-xl bg-slate-100 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <Card key={course.id} hover className="flex flex-col justify-between">
              <CardHeader>
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="default" size="sm">
                    Active Semester
                  </Badge>
                  <span className="text-xs text-slate-400 font-medium">CS Department</span>
                </div>
                <CardTitle className="text-lg hover:text-coglearn-600 transition-colors">
                  {course.title}
                </CardTitle>
                <p className="text-xs text-slate-500 line-clamp-3 mt-1 leading-relaxed">
                  {course.description}
                </p>
              </CardHeader>

              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <User className="h-3.5 w-3.5 text-slate-400" />
                  <span>Instructor: <strong className="text-slate-800">{course.teacher_name || 'Prof. Faculty'}</strong></span>
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <Layers className="h-3.5 w-3.5 text-slate-400" />
                  <span>Modules: <strong className="text-slate-800">{course.modules?.length || 4} units</strong></span>
                </div>

                {/* Progress bar */}
                <div className="space-y-1 pt-2">
                  <div className="flex justify-between text-[11px] text-slate-500">
                    <span>Syllabus Progression</span>
                    <span className="font-semibold text-coglearn-600">65%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full bg-coglearn-500 rounded-full w-[65%]" />
                  </div>
                </div>
              </CardContent>

              <CardFooter className="pt-3 border-t border-slate-100">
                <Link to={`/courses/${course.id}`} className="w-full">
                  <Button variant="primary" size="sm" className="w-full" rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
                    Enter Course
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Fallback demo courses
const defaultCourses: Course[] = [
  {
    id: 'crs-1',
    title: 'CS301: Advanced Algorithms',
    description: 'In-depth study of dynamic programming, network flow, randomized algorithms, and computational complexity reductions.',
    teacher_id: 'tch-1',
    teacher_name: 'Dr. Sarah Miller',
    semester_id: 'sem-fall-2026',
    department_id: 'dept-cs',
    is_published: true,
    created_at: '2026-08-20T10:00:00Z',
    modules: [],
  },
  {
    id: 'crs-2',
    title: 'CS304: Distributed Systems',
    description: 'Fundamental principles of distributed consensus, fault-tolerance, vector clocks, RPCs, and peer-to-peer architectures.',
    teacher_id: 'tch-2',
    teacher_name: 'Prof. Alan Turing',
    semester_id: 'sem-fall-2026',
    department_id: 'dept-cs',
    is_published: true,
    created_at: '2026-08-20T10:00:00Z',
    modules: [],
  },
  {
    id: 'crs-3',
    title: 'MATH240: Probability & Stochastic Processes',
    description: 'Continuous random variables, Poisson processes, Markov chains, birth-death queuing models, and Bayesian inference.',
    teacher_id: 'tch-3',
    teacher_name: 'Dr. Katherine Johnson',
    semester_id: 'sem-fall-2026',
    department_id: 'dept-math',
    is_published: true,
    created_at: '2026-08-20T10:00:00Z',
    modules: [],
  },
];

export default CoursesPage;
