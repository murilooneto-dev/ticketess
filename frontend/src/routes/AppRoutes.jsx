import { Route, Routes } from "react-router-dom";

import DashboardPage from "../pages/DashboardPage.jsx";
import NewProjectPage from "../pages/NewProjectPage.jsx";
import NewTicketPage from "../pages/NewTicketPage.jsx";
import ProjectDetailPage from "../pages/ProjectDetailPage.jsx";
import ProjectIdeasPage from "../pages/ProjectIdeasPage.jsx";
import ProjectsPage from "../pages/ProjectsPage.jsx";
import ReportsPage from "../pages/ReportsPage.jsx";
import TicketDetailPage from "../pages/TicketDetailPage.jsx";
import TicketsPage from "../pages/TicketsPage.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/projects" element={<ProjectsPage />} />
      <Route path="/projects/new" element={<NewProjectPage />} />
      <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
      <Route path="/project-ideas" element={<ProjectIdeasPage />} />
      <Route path="/tickets" element={<TicketsPage />} />
      <Route path="/tickets/new" element={<NewTicketPage />} />
      <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
      <Route path="/reports" element={<ReportsPage />} />
    </Routes>
  );
}
