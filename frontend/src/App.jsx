import React, { lazy, Suspense, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { LanguageProvider } from './context/LanguageContext';

// Components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ProtectedRoute from './components/ProtectedRoute';

// Keep the public landing page eager for a fast first paint; load application screens on demand.
import LandingPage from './pages/LandingPage';
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const PasswordRecoveryPage = lazy(() => import('./pages/PasswordRecoveryPage'));
const StudentDashboard = lazy(() => import('./pages/StudentDashboard'));
const StaffDashboard = lazy(() => import('./pages/StaffDashboard'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const AdvancedInsightsPage = lazy(() => import('./pages/AdvancedInsightsPage'));
const CreateTicketPage = lazy(() => import('./pages/CreateTicketPage'));
const TicketListPage = lazy(() => import('./pages/TicketListPage'));
const TicketDetailPage = lazy(() => import('./pages/TicketDetailPage'));
const KnowledgeBasePage = lazy(() => import('./pages/KnowledgeBasePage'));
const SLAManagementPage = lazy(() => import('./pages/SLAManagementPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const UserManagementPage = lazy(() => import('./pages/UserManagementPage'));
const AuditLogsPage = lazy(() => import('./pages/AuditLogsPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const FeatureRequestsPage = lazy(() => import('./pages/FeatureRequestsPage'));
const CampusManagementPage = lazy(() => import('./pages/CampusManagementPage'));
const CategoryManagementPage = lazy(() => import('./pages/CategoryManagementPage'));
const IncidentManagementPage = lazy(() => import('./pages/IncidentManagementPage'));
const PlatformAdminDashboard = lazy(() => import('./pages/PlatformAdminDashboard'));
const InstitutionAdminInvitationsPage = lazy(() => import('./pages/InstitutionAdminInvitationsPage'));
const AcceptInvitationPage = lazy(() => import('./pages/AcceptInvitationPage'));

const PUBLIC_REGISTRATION_ENABLED = import.meta.env.VITE_PUBLIC_REGISTRATION_ENABLED !== 'false';

// Layout wrapper for authenticated users
function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-container">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="main-content">
        <Navbar onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}

// Router switcher for role-specific dashboard
function RoleDashboard() {
  const { user } = useAuth();
  if (user?.role === 'platform_admin') {
    return <PlatformAdminDashboard />;
  }
  if (user?.role === 'admin') {
    return <AdminDashboard />;
  } else if (user?.role === 'staff') {
    return <StaffDashboard />;
  }
  return <StudentDashboard />;
}

export default function App() {
  return (
    <LanguageProvider>
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<div className="app-loading" role="status" aria-live="polite">Loading FixIt…</div>}>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/accept-invitation" element={<AcceptInvitationPage />} />
            <Route path="/register" element={PUBLIC_REGISTRATION_ENABLED ? <RegisterPage /> : <Navigate to="/login" replace />} />
            <Route path="/forgot-password" element={<PasswordRecoveryPage />} />
            <Route path="/reset-password" element={<PasswordRecoveryPage />} />

            {/* Authenticated Application Routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/dashboard" element={<RoleDashboard />} />
                <Route element={<ProtectedRoute allowedRoles={['platform_admin']} />}>
                  <Route path="/platform/institutions" element={<PlatformAdminDashboard />} />
                </Route>
                <Route path="/tickets" element={<TicketListPage />} />
                <Route path="/tickets/new" element={<CreateTicketPage />} />
                <Route path="/tickets/:id" element={<TicketDetailPage />} />
                <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/features" element={<FeatureRequestsPage />} />

                {/* Staff & Admin Routes */}
                <Route element={<ProtectedRoute allowedRoles={['staff', 'admin']} />}>
                  <Route path="/sla" element={<SLAManagementPage />} />
                  <Route path="/admin/sla" element={<SLAManagementPage />} />
                  <Route path="/incidents" element={<IncidentManagementPage />} />
                </Route>

                {/* Admin Only Routes */}
                <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
                  <Route path="/admin/administrators" element={<InstitutionAdminInvitationsPage />} />
                  <Route path="/users" element={<UserManagementPage />} />
                  <Route path="/admin/users" element={<UserManagementPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/admin/reports" element={<ReportsPage />} />
                  <Route path="/audit-logs" element={<AuditLogsPage />} />
                  <Route path="/admin/audit-logs" element={<AuditLogsPage />} />
                  <Route path="/admin/campus" element={<CampusManagementPage />} />
                  <Route path="/admin/categories" element={<CategoryManagementPage />} />
                  <Route path="/admin/insights" element={<AdvancedInsightsPage />} />
                </Route>
              </Route>
            </Route>

            {/* Fallback route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
    </LanguageProvider>
  );
}
