import { useEffect, useState } from "react";
import { Sun, Moon, Monitor } from "lucide-react";
import { api } from "../api/client";
import { useTheme } from "../hooks/useTheme";

const ICON = { system: Monitor, light: Sun, dark: Moon } as const;
const LABEL = { system: "System theme", light: "Light theme", dark: "Dark theme" } as const;

export default function TopBar({ title }: { title: string }) {
  const [connected, setConnected] = useState(false);
  const { mode, cycle } = useTheme();

  useEffect(() => {
    api
      .getStatus()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

  const ThemeIcon = ICON[mode];

  return (
    <header className="topbar">
      <span className="topbar-title">{title}</span>
      <div className="topbar-actions">
        <button
          className="theme-toggle"
          onClick={cycle}
          title={LABEL[mode]}
          aria-label={LABEL[mode]}
        >
          <ThemeIcon />
        </button>
        <div className="topbar-status">
          <span className={`status-dot${connected ? " connected" : ""}`} />
          {connected ? "API connected" : "API offline"}
        </div>
      </div>
    </header>
  );
}
