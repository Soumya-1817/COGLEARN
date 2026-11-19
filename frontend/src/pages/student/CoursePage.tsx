import React from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  BookOpen,
  Layers,
  Video,
  FileText,
  ExternalLink,
  Clock,
  CheckCircle,
  PlayCircle,
  ChevronRight,
  ArrowLeft,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { get } from '@/lib/api';
import { Course, Module, Lesson } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export const CoursePage: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();

  const { data: course = defaultCourseDetail, isLoading } = useQuery({
    queryKey: ['course_detail', courseId],
    queryFn: async (): Promise<Course> => {
      try {
        return await get<Course>(`/courses/${courseId}`);
      } catch {
        return defaultCourseDetail;
      }
    },
  });

  const getLessonIcon = (type: Lesson['lesson_type']) => {
    switch (type) {
      case 'video':
        return <Video className="h-4 w-4 text-sky-500" />;
      case 'pdf':
        return <FileText className="h-4 w-4 text-red-500" />;
      case 'external':
        return <ExternalLink className="h-4 w-4 text-emerald-500" />;
      case 'text':
      default:
        return <FileText className="h-4 w-4 text-slate-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Back to courses */}
      <Link to="/courses" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800">
        <ArrowLeft className="h-4 w-4" /> Back to All Courses
      </Link>

      {/* Course Header Banner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <Badge variant="default" size="sm">Fall 2026</Badge>
              <span className="text-xs text-slate-400 font-medium">Department of Computer Science</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              {course.title}
            </h1>
            <p className="text-sm text-slate-600 mt-2 max-w-3xl leading-relaxed">
              {course.description}
            </p>
          </div>

          <div className="flex flex-col items-start md:items-end gap-1 shrink-0 bg-slate-50 p-4 rounded-xl border border-slate-100">
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Instructor</span>
            <span className="text-sm font-bold text-slate-800">{course.teacher_name || 'Dr. Sarah Miller'}</span>
            <span className="text-xs text-coglearn-600 font-medium mt-1">Office Hours: Mon/Wed 2-4 PM</span>
          </div>
        </div>
      </div>

      {/* Course Syllabus & Modules */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Layers className="h-5 w-5 text-coglearn-600" />
            Course Curriculum & Lessons
          </h2>
          <span className="text-xs text-slate-500">
            {course.modules?.length || 0} Modules Available
          </span>
        </div>

        {course.modules?.map((mod, modIdx) => (
          <Card key={mod.id || modIdx} className="overflow-hidden">
            <CardHeader className="bg-slate-50/70 border-b border-slate-100 py-3.5 px-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-coglearn-100 font-mono text-xs font-bold text-coglearn-800">
                    M{mod.order_index}
                  </span>
                  <CardTitle className="text-base text-slate-800">{mod.title}</CardTitle>
                </div>
                <span className="text-xs text-slate-400 font-medium">
                  {mod.lessons.length} Lesson{mod.lessons.length > 1 ? 's' : ''}
                </span>
              </div>
            </CardHeader>

            <CardContent className="p-0 divide-y divide-slate-100">
              {mod.lessons.map((lesson, lIdx) => (
                <div
                  key={lesson.id || lIdx}
                  className="flex items-center justify-between p-4 hover:bg-slate-50/80 transition-colors"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100">
                      {getLessonIcon(lesson.lesson_type)}
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-800 hover:text-coglearn-600 transition-colors">
                        {lesson.title}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
                        <span className="capitalize">{lesson.lesson_type} material</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" /> {lesson.duration_minutes} mins
                        </span>
                      </div>
                    </div>
                  </div>

                  <Link to={`/courses/${courseId}/lessons/${lesson.id}`}>
                    <Button variant="outline" size="sm" rightIcon={<ChevronRight className="h-3.5 w-3.5" />}>
                      Open
                    </Button>
                  </Link>
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

// Fallback course detail data
const defaultCourseDetail: Course = {
  id: 'crs-1',
  title: 'CS301: Advanced Algorithms',
  description: 'In-depth study of dynamic programming, network flow, randomized algorithms, and computational complexity reductions.',
  teacher_id: 'tch-1',
  teacher_name: 'Dr. Sarah Miller',
  semester_id: 'sem-fall-2026',
  department_id: 'dept-cs',
  is_published: true,
  created_at: '2026-08-20T10:00:00Z',
  modules: [
    {
      id: 'mod-1',
      course_id: 'crs-1',
      title: 'Module 1: Advanced Dynamic Programming',
      order_index: 1,
      lessons: [
        {
          id: 'les-101',
          title: 'Substructure and Overlapping Subproblems',
          lesson_type: 'video',
          content_url: 'https://example.com/videos/dp-substructure',
          duration_minutes: 45,
          is_published: true,
        },
        {
          id: 'les-102',
          title: 'Matrix Chain Multiplication & All-Pairs Shortest Path',
          lesson_type: 'pdf',
          content_url: 'https://example.com/notes/matrix-chain.pdf',
          duration_minutes: 30,
          is_published: true,
        },
      ],
    },
    {
      id: 'mod-2',
      course_id: 'crs-1',
      title: 'Module 2: Network Flow & Matching',
      order_index: 2,
      lessons: [
        {
          id: 'les-201',
          title: 'Ford-Fulkerson Method & Max-Flow Min-Cut Theorem',
          lesson_type: 'video',
          content_url: 'https://example.com/videos/ford-fulkerson',
          duration_minutes: 50,
          is_published: true,
        },
        {
          id: 'les-202',
          title: 'Bipartite Matching and Disjoint Paths Problem',
          lesson_type: 'text',
          content_url: 'https://example.com/readings/matching',
          duration_minutes: 25,
          is_published: true,
        },
      ],
    },
  ],
};

export default CoursePage;
