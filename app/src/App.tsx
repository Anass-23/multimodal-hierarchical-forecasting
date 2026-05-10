import { Route, Routes, useLocation } from "react-router-dom";
import Sidebar from "./layout/Sidebar";
import TopBar from "./layout/TopBar";
import Dashboard from "./pages/Dashboard";
import Setup from "./pages/Setup";
import Students from "./pages/Students";
import Courses from "./pages/Courses";
import Models from "./pages/Models";
import Evaluation from "./pages/Evaluation";
import Forecast from "./pages/Forecast";

const PAGE_TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/setup": "Setup",
  "/students": "Students",
  "/courses": "Courses",
  "/models": "Models",
  "/evaluation": "Evaluation",
  "/forecast": "Forecast",
};

export default function App() {
  const location = useLocation();
  const basePath = "/" + (location.pathname.split("/")[1] || "");
  const title = PAGE_TITLES[basePath] || "educast";

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="app-content">
        <TopBar title={title} />
        <div className="page-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/setup" element={<Setup />} />
            <Route path="/students" element={<Students />} />
            <Route path="/students/:id" element={<Students />} />
            <Route path="/courses" element={<Courses />} />
            <Route path="/models" element={<Models />} />
            <Route path="/evaluation" element={<Evaluation />} />
            <Route path="/forecast" element={<Forecast />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}
