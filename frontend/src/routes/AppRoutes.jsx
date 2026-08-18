import { Route, Routes } from "react-router-dom";

import AdminRoute from "../components/AdminRoute.jsx";
import ProtectedRoute from "../components/ProtectedRoute.jsx";
import DashboardPage from "../pages/DashboardPage.jsx";
import LoginPage from "../pages/LoginPage.jsx";
import NewProjectPage from "../pages/NewProjectPage.jsx";
import NewTicketPage from "../pages/NewTicketPage.jsx";
import ProjectDetailPage from "../pages/ProjectDetailPage.jsx";
import ProjectsPage from "../pages/ProjectsPage.jsx";
import ReportsPage from "../pages/ReportsPage.jsx";
import TicketDetailPage from "../pages/TicketDetailPage.jsx";
import TicketsPage from "../pages/TicketsPage.jsx";
import UsersPage from "../pages/UsersPage.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/projects"
        element={
          <ProtectedRoute>
            <ProjectsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/projects/new"
        element={
          <AdminRoute>
            <NewProjectPage />
          </AdminRoute>
        }
      />
      <Route
        path="/projects/:projectId"
        element={
          <ProtectedRoute>
            <ProjectDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tickets"
        element={
          <ProtectedRoute>
            <TicketsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tickets/new"
        element={
          <ProtectedRoute>
            <NewTicketPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tickets/:ticketId"
        element={
          <ProtectedRoute>
            <TicketDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <ReportsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/users"
        element={
          <AdminRoute>
            <UsersPage />
          </AdminRoute>
        }
      />
    </Routes>
  );
}
