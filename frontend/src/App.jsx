import { BrowserRouter } from "react-router-dom";

import NavBar from "./components/NavBar.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import AppRoutes from "./routes/AppRoutes.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NavBar />
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
