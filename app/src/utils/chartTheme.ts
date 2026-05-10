/** Read a CSS custom property from :root at runtime. */
function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** Returns Plotly-ready colors that match the current theme. */
export function getChartColors() {
  return {
    paper: "transparent",
    plot: "transparent",
    grid: cssVar("--border"),
    text: cssVar("--text-primary"),
    textMuted: cssVar("--text-muted"),
    accent: cssVar("--accent"),
    bgCard: cssVar("--bg-card"),
    bgSecondary: cssVar("--bg-secondary"),
  };
}

/** Shared font config for Plotly charts. */
export function chartFont() {
  return { family: "Inter, system-ui, sans-serif", color: cssVar("--text-primary"), size: 12 };
}
