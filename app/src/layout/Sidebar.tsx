import { NavLink } from "react-router-dom";
import {
  Database,
  LayoutDashboard,
  Users,
  BookOpen,
  Brain,
  BarChart3,
  TrendingUp,
} from "lucide-react";
import upcLogo from "../assets/logo.png";

const links = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/setup", icon: Database, label: "Setup" },
  { to: "/students", icon: Users, label: "Students" },
  { to: "/courses", icon: BookOpen, label: "Courses" },
  { to: "/models", icon: Brain, label: "Models" },
  { to: "/evaluation", icon: BarChart3, label: "Evaluation" },
  { to: "/forecast", icon: TrendingUp, label: "Forecast" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>educast</h1>
        <span>Enrollment Prediction</span>
      </div>
      <nav className="sidebar-nav">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `sidebar-link${isActive ? " active" : ""}`
            }
            end={to === "/"}
          >
            <Icon />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <img src={upcLogo} alt="UPC BarcelonaTech" className="sidebar-upc-logo" />
      </div>
    </aside>
  );
}
