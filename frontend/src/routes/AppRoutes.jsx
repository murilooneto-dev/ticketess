import { Route, Routes } from "react-router-dom";

import HomePage from "../pages/HomePage.jsx";
import NewTicketPage from "../pages/NewTicketPage.jsx";
import ReportsPage from "../pages/ReportsPage.jsx";
import TicketDetailPage from "../pages/TicketDetailPage.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/tickets/new" element={<NewTicketPage />} />
      <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
      <Route path="/reports" element={<ReportsPage />} />
    </Routes>
  );
}
