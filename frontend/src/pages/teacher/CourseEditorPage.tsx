import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, Plus, Trash2, Video, FileText, ExternalLink, Layers, Check } from 'lucide-react';
import { Course, Module, Lesson } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export const CourseEditorPage: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const isEditing = Boolean(courseId && courseId !== 'new');

  const [title, setTitle] = useState(isEditing ? 'CS301: Advanced Algorithms' : '');
  const [description, setDescription] = useState(
    isEditing
      ? 'In-depth study of dynamic programming, network flow, randomized algorithms, and complexity reductions.'
      : ''
  );
  const [isPublished, setIsPublished] = useState(isEditing ? true : false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Modules state
  const [modules, setModules] = useState<Module[]>([
    {
      id: 'mod-1',
      course_id: courseId || 'crs-new',
      title: 'Module 1: Advanced Dynamic Programming',
      order_index: 1,
      lessons: [
        {
          id: 'les-1',
          title: 'Substructure and Overlapping Subproblems',
          lesson_type: 'video',
          content_url: 'https://example.com/video-1',
          duration_minutes: 45,
          is_published: true,
        },
      ],
    },
  ]);

  const handleAddModule = () => {
    const newMod: Module = {
      id: `mod-${Date.now()}`,
      course_id: courseId || 'crs-new',
      title: `Module ${modules.length + 1}: New Curriculum Topic`,
      order_index: modules.length + 1,
      lessons: [],
    };
    setModules([...modules, newMod]);
  };

  const handleAddLesson = (moduleIndex: number) => {
    const newLesson: Lesson = {
      id: `les-${Date.now()}`,
      title: 'New Lesson Lecture',
      lesson_type: 'video',
      content_url: '',
      duration_minutes: 30,
      is_published: true,
    };

    const updated = [...modules];
    updated[moduleIndex].lessons.push(newLesson);
    setModules(updated);
  };

  const handleRemoveLesson = (moduleIndex: number, lessonIndex: number) => {
    const updated = [...modules];
    updated[moduleIndex].lessons.splice(lessonIndex, 1);
    setModules(updated);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      setSavedSuccess(true);
      setTimeout(() => navigate('/teacher/courses'), 1000);
    }, 600);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Back button */}
      <Link to="/teacher/courses" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800">
        <ArrowLeft className="h-4 w-4" /> Back to Courses Management
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            {isEditing ? 'Edit Course Curriculum' : 'Create New Course'}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Author course details, structure lesson modules, and attach learning materials.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsPublished(!isPublished)}
          >
            {isPublished ? 'Status: Published' : 'Status: Draft'}
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            isLoading={isSaving}
            leftIcon={<Save className="h-4 w-4" />}
          >
            Save Course
          </Button>
        </div>
      </div>

      {savedSuccess && (
        <Alert variant="success" title="Course Saved">
          Your changes have been recorded successfully. Redirecting to course directory...
        </Alert>
      )}

      {/* Main Details Card */}
      <Card>
        <CardHeader>
          <CardTitle>Course Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            label="Course Code & Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. CS301: Advanced Algorithms"
            required
          />

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Course Description & Syllabus Summary
            </label>
            <textarea
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-slate-300 p-3 text-sm text-slate-900 focus:outline-none focus:border-coglearn-500"
              placeholder="Outline the core learning outcomes and prerequisites..."
            />
          </div>
        </CardContent>
      </Card>

      {/* Curriculum & Modules */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Layers className="h-5 w-5 text-coglearn-600" />
            Curriculum Modules
          </h2>
          <Button variant="outline" size="sm" onClick={handleAddModule} leftIcon={<Plus className="h-4 w-4" />}>
            Add Module
          </Button>
        </div>

        {modules.map((mod, modIdx) => (
          <Card key={mod.id} className="overflow-hidden">
            <CardHeader className="bg-slate-50/70 border-b border-slate-100 py-3 px-5">
              <div className="flex items-center justify-between gap-3">
                <input
                  type="text"
                  value={mod.title}
                  onChange={(e) => {
                    const updated = [...modules];
                    updated[modIdx].title = e.target.value;
                    setModules(updated);
                  }}
                  className="font-semibold text-sm bg-transparent border-b border-dashed border-slate-300 focus:border-coglearn-500 focus:outline-none w-full"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleAddLesson(modIdx)}
                  leftIcon={<Plus className="h-3.5 w-3.5" />}
                  className="text-xs shrink-0"
                >
                  Add Lesson
                </Button>
              </div>
            </CardHeader>

            <CardContent className="p-4 space-y-3">
              {mod.lessons.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-2">No lessons in this module yet.</p>
              ) : (
                mod.lessons.map((lesson, lIdx) => (
                  <div
                    key={lesson.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg border border-slate-200 bg-white"
                  >
                    <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <input
                        type="text"
                        value={lesson.title}
                        onChange={(e) => {
                          const updated = [...modules];
                          updated[modIdx].lessons[lIdx].title = e.target.value;
                          setModules(updated);
                        }}
                        className="text-xs font-semibold rounded border border-slate-200 p-1.5"
                        placeholder="Lesson Title"
                      />

                      <select
                        value={lesson.lesson_type}
                        onChange={(e) => {
                          const updated = [...modules];
                          updated[modIdx].lessons[lIdx].lesson_type = e.target.value as Lesson['lesson_type'];
                          setModules(updated);
                        }}
                        className="text-xs rounded border border-slate-200 p-1.5"
                      >
                        <option value="video">Video Lecture</option>
                        <option value="pdf">PDF Document</option>
                        <option value="text">Reading / Markdown</option>
                        <option value="external">External Link</option>
                      </select>

                      <input
                        type="number"
                        value={lesson.duration_minutes}
                        onChange={(e) => {
                          const updated = [...modules];
                          updated[modIdx].lessons[lIdx].duration_minutes = Number(e.target.value);
                          setModules(updated);
                        }}
                        className="text-xs rounded border border-slate-200 p-1.5"
                        placeholder="Duration (mins)"
                      />
                    </div>

                    <button
                      onClick={() => handleRemoveLesson(modIdx, lIdx)}
                      className="text-slate-400 hover:text-red-600 transition-colors self-end sm:self-center"
                      title="Remove Lesson"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default CourseEditorPage;
