import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

// Layout & Guards
import { Layout } from '@/components/layout/Layout';
import { RoleGuard } from '@/components/layout/RoleGuard';

// Auth Pages
import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage';

// Student Pages
import { StudentDashboard } from '@/pages/student/StudentDashboard';
import { CoursesPage } from '@/pages/student/CoursesPage';
import { CoursePage } from '@/pages/student/CoursePage';
import { LessonPage } from '@/pages/student/LessonPage';
import { TaskQueuePage } from '@/pages/student/TaskQueuePage';
import { CalendarPage } from '@/pages/student/CalendarPage';
import { NotificationsPage } from '@/pages/student/NotificationsPage';
import { MentorshipPage } from '@/pages/student/MentorshipPage';

// Teacher & Mentor Pages
import { TeacherDashboard } from '@/pages/teacher/TeacherDashboard';
import { ManageCoursesPage } from '@/pages/teacher/ManageCoursesPage';
import { CourseEditorPage } from '@/pages/teacher/CourseEditorPage';
import { AssignmentsPage } from '@/pages/teacher/AssignmentsPage';
import { MentorDashboard } from '@/pages/teacher/MentorDashboard';
import { StudentAnalyticsPage } from '@/pages/teacher/StudentAnalyticsPage';
import { InterventionPage } from '@/pages/teacher/InterventionPage';
import { MentorshipRequestsPage } from '@/pages/teacher/MentorshipRequestsPage';

// Institution Admin Pages
import { AdminDashboard } from '@/pages/admin/AdminDashboard';
import { DepartmentsPage } from '@/pages/admin/DepartmentsPage';
import { UsersPage } from '@/pages/admin/UsersPage';
import { AnalyticsPortalPage } from '@/pages/admin/AnalyticsPortalPage';

// Platform Admin Pages
import { PlatformDashboard } from '@/pages/platform/PlatformDashboard';
import { InstitutionsPage } from '@/pages/platform/InstitutionsPage';

export const App: React.FC = () => {
  const initialize = useAuthStore((state) => state.initialize);

  useEffect(() => {
    initialize();
  }, [initialize]);

  return (
    <Routes>
      {/* Public Authentication routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />

      {/* Student routes */}
      <Route
        path="/dashboard"
        element={
          <RoleGuard allowedRoles={['student']}>
            <Layout>
              <StudentDashboard />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/courses"
        element={
          <RoleGuard allowedRoles={['student']}>
            <Layout>
              <CoursesPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/courses/:courseId"
        element={
          <RoleGuard allowedRoles={['student']}>
            <Layout>
              <CoursePage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/courses/:courseId/lessons/:lessonId"
        element={
          <RoleGuard allowedRoles={['student']}>
            <Layout>
              <LessonPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/tasks"
        element={
          <RoleGuard allowedRoles={['student']}>
            <Layout>
              <TaskQueuePage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/calendar"
        element={
          <RoleGuard allowedRoles={['student']}>
            <Layout>
              <CalendarPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/notifications"
        element={
          <RoleGuard allowedRoles={['student', 'teacher']}>
            <Layout>
              <NotificationsPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/mentorship"
        element={
          <RoleGuard allowedRoles={['student']}>
            <Layout>
              <MentorshipPage />
            </Layout>
          </RoleGuard>
        }
      />

      {/* Teacher / Mentor routes */}
      <Route
        path="/teacher/dashboard"
        element={
          <RoleGuard allowedRoles={['teacher']}>
            <Layout>
              <TeacherDashboard />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/teacher/courses"
        element={
          <RoleGuard allowedRoles={['teacher']}>
            <Layout>
              <ManageCoursesPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/teacher/courses/new"
        element={
          <RoleGuard allowedRoles={['teacher']}>
            <Layout>
              <CourseEditorPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/teacher/courses/:courseId/edit"
        element={
          <RoleGuard allowedRoles={['teacher']}>
            <Layout>
              <CourseEditorPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/teacher/assignments"
        element={
          <RoleGuard allowedRoles={['teacher']}>
            <Layout>
              <AssignmentsPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/teacher/mentor"
        element={
          <RoleGuard allowedRoles={['teacher']}>
            <Layout>
              <MentorDashboard />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/teacher/mentor/students/:studentId"
        element={
          <RoleGuard allowedRoles={['teacher']}>
            <Layout>
              <StudentAnalyticsPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/teacher/interventions/:interventionId"
        element={
          <RoleGuard allowedRoles={['teacher']}>
            <Layout>
              <InterventionPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/teacher/mentorship-requests"
        element={
          <RoleGuard allowedRoles={['teacher']}>
            <Layout>
              <MentorshipRequestsPage />
            </Layout>
          </RoleGuard>
        }
      />

      {/* Institution Admin routes */}
      <Route
        path="/admin/dashboard"
        element={
          <RoleGuard allowedRoles={['inst_admin']}>
            <Layout>
              <AdminDashboard />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/admin/departments"
        element={
          <RoleGuard allowedRoles={['inst_admin']}>
            <Layout>
              <DepartmentsPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/admin/users"
        element={
          <RoleGuard allowedRoles={['inst_admin']}>
            <Layout>
              <UsersPage />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/admin/analytics"
        element={
          <RoleGuard allowedRoles={['inst_admin']}>
            <Layout>
              <AnalyticsPortalPage />
            </Layout>
          </RoleGuard>
        }
      />

      {/* Platform Admin routes */}
      <Route
        path="/platform/dashboard"
        element={
          <RoleGuard allowedRoles={['platform_admin']}>
            <Layout>
              <PlatformDashboard />
            </Layout>
          </RoleGuard>
        }
      />
      <Route
        path="/platform/institutions"
        element={
          <RoleGuard allowedRoles={['platform_admin']}>
            <Layout>
              <InstitutionsPage />
            </Layout>
          </RoleGuard>
        }
      />

      {/* Redirects */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};

export default App;
