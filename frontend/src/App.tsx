import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/context/AuthContext';
import { ProtectedRoute } from '@/components/common/ProtectedRoute';

// Layouts
import { StudentLayout } from '@/layouts/StudentLayout';
import { AdminLayout } from '@/layouts/AdminLayout';
import { AuthLayout } from '@/layouts/AuthLayout';

// Pages
import { LandingPage } from '@/pages/LandingPage';
import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';
import { StudentDashboardPage } from '@/pages/student/StudentDashboardPage';
import { ChatPage } from '@/pages/student/ChatPage';
import { DocumentIntelligencePage } from '@/pages/student/DocumentIntelligencePage';
import { ProfilePage } from '@/pages/student/ProfilePage';
import { AdminDashboardPage } from '@/pages/admin/AdminDashboardPage';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Landing Page */}
          <Route path="/" element={<LandingPage />} />

          {/* Authentication Pages */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>

          {/* Student Portal Protected Routes */}
          <Route
            path="/student"
            element={
              <ProtectedRoute allowedRoles={['STUDENT', 'ADMIN']}>
                <StudentLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/student/dashboard" replace />} />
            <Route path="dashboard" element={<StudentDashboardPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="document-ai" element={<DocumentIntelligencePage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="notifications" element={<StudentDashboardPage />} />
          </Route>

          {/* Admin Portal Protected Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboardPage />} />
            <Route path="students" element={<AdminDashboardPage />} />
            <Route path="faculty" element={<AdminDashboardPage />} />
            <Route path="documents" element={<AdminDashboardPage />} />
            <Route path="analytics" element={<AdminDashboardPage />} />
            <Route path="settings" element={<AdminDashboardPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
