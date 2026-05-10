import { useCallback, useEffect, useMemo, useState } from "react";

type ThemeMode = "light" | "dark" | "system";

function getSystemTheme(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function resolveTheme(mode: ThemeMode): "light" | "dark" {
  return mode === "system" ? getSystemTheme() : mode;
}

function applyTheme(resolved: "light" | "dark") {
  document.documentElement.setAttribute("data-theme", resolved);
}

/** Read stored preference or default to system. */
function loadMode(): ThemeMode {
  const stored = localStorage.getItem("educast-theme");
  if (stored === "light" || stored === "dark" || stored === "system") return stored;
  return "system";
}

export function useTheme() {
  const [mode, setModeRaw] = useState<ThemeMode>(loadMode);

  const resolved = useMemo(() => resolveTheme(mode), [mode]);

  const setMode = useCallback((m: ThemeMode) => {
    localStorage.setItem("educast-theme", m);
    setModeRaw(m);
    applyTheme(resolveTheme(m));
  }, []);

  // Cycle: system -> light -> dark -> system
  const cycle = useCallback(() => {
    const next: Record<ThemeMode, ThemeMode> = { system: "light", light: "dark", dark: "system" };
    setMode(next[mode]);
  }, [mode, setMode]);

  // Apply on mount
  useEffect(() => {
    applyTheme(resolved);
  }, [resolved]);

  // Listen for OS theme changes when in system mode
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      if (loadMode() === "system") {
        applyTheme(getSystemTheme());
        // Force re-render so resolved updates
        setModeRaw("system");
      }
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  return { mode, resolved, setMode, cycle };
}

/** Call once before React renders to avoid a dark flash on light systems. */
export function applyInitialTheme() {
  applyTheme(resolveTheme(loadMode()));
}
