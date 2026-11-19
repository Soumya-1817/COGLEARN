import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  Video,
  FileText,
  ExternalLink,
  CheckCircle,
  ChevronRight,
  BookOpen,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export const LessonPage: React.FC = () => {
  const { courseId, lessonId } = useParams<{ courseId: string; lessonId: string }>();
  const navigate = useNavigate();
  const [isCompleted, setIsCompleted] = useState(false);

  // Lesson mock detail
  const lesson = {
    id: lessonId || 'les-101',
    title: 'Substructure and Overlapping Subproblems in DP',
    moduleTitle: 'Module 1: Advanced Dynamic Programming',
    courseTitle: 'CS301: Advanced Algorithms',
    lesson_type: 'video' as const,
    duration_minutes: 45,
    content_url: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    bodyText: `
### Key Principles of Dynamic Programming

In this lecture, we examine two core properties necessary for dynamic programming to apply:
1. **Optimal Substructure**: An optimal solution to any instance contains optimal solutions to subinstances.
2. **Overlapping Subproblems**: The recursive space contains a polynomial number of distinct subproblems that are revisited repeatedly.

#### Bellman Equation Formulation
For a Markov Decision or discrete optimization problem, we define value iteration recursively:
$$V(s) = \max_a \left( R(s, a) + \gamma \sum_{s'} P(s' \mid s, a) V(s') \right)$$

Ensure you review the supplementary problem set on Matrix Chain Multiplication before proceeding to the quiz.
    `,
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to={`/courses/${courseId}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Course Syllabus
        </Link>
        <span className="text-xs text-slate-400 font-medium">{lesson.moduleTitle}</span>
      </div>

      {/* Lesson Header */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="info" size="sm">
                {lesson.lesson_type.toUpperCase()}
              </Badge>
              <span className="flex items-center gap-1 text-xs text-slate-500 font-medium">
                <Clock className="h-3.5 w-3.5" /> {lesson.duration_minutes} minutes
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              {lesson.title}
            </h1>
            <p className="text-xs text-slate-500 mt-1">{lesson.courseTitle}</p>
          </div>

          <Button
            variant={isCompleted ? 'success' : 'primary'}
            size="sm"
            onClick={() => setIsCompleted(!isCompleted)}
            leftIcon={<CheckCircle className="h-4 w-4" />}
          >
            {isCompleted ? 'Lesson Completed' : 'Mark Complete'}
          </Button>
        </div>
      </div>

      {/* Media & Content Player */}
      <Card className="overflow-hidden">
        {lesson.lesson_type === 'video' && (
          <div className="relative aspect-video w-full bg-slate-900 flex items-center justify-center text-white">
            <div className="text-center p-6 space-y-3">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-coglearn-600/90 text-white shadow-xl cursor-pointer hover:scale-105 transition-transform">
                <Video className="h-8 w-8" />
              </div>
              <p className="text-sm font-semibold text-slate-200">Interactive Lecture Stream</p>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Watch full video player with slide timestamp bookmarking and transcript search.
              </p>
            </div>
          </div>
        )}

        {/* Written Notes / Supplemental Reading */}
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-semibold text-slate-800 text-sm flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-coglearn-600" />
              Lecture Notes & Key Formulas
            </h3>
            <span className="text-xs text-slate-400">PDF Syllabus Version 2.4</span>
          </div>

          <div className="prose prose-sm max-w-none text-slate-700 leading-relaxed font-sans space-y-3">
            <p>
              An algorithm solves a problem using <strong>Dynamic Programming</strong> if the problem can be broken down into subproblems, which are sub-solutions of other subproblems. Unlike divide-and-conquer, subproblems overlap significantly.
            </p>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 font-mono text-xs text-slate-800">
              dp[i][w] = max(dp[i-1][w], dp[i-1][w - weight[i]] + value[i])
            </div>
            <p>
              When memoizing or tabulating solutions, remember to verify space-complexity optimizations from $O(n \cdot W)$ down to $O(W)$ using 1D rolling array buffers.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Bottom Completion Bar */}
      <div className="flex items-center justify-between p-4 rounded-xl border border-slate-200 bg-white">
        <span className="text-xs text-slate-500 font-medium">Ready for next topic?</span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/courses/${courseId}`)}
          rightIcon={<ChevronRight className="h-4 w-4" />}
        >
          Proceed to Next Lesson
        </Button>
      </div>
    </div>
  );
};

export default LessonPage;
