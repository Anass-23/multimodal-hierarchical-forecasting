import Plot from "react-plotly.js";
import { getChartColors, chartFont } from "../../utils/chartTheme";
import type { MetricsRow } from "../../api/types";

interface Props {
  metricsTable: MetricsRow[];
}

export default function MetricsRadar({ metricsTable }: Props) {
  const c = getChartColors();

  if (metricsTable.length === 0) return null;

  const metricKeys = Object.keys(metricsTable[0]).filter(
    (k) => k !== "model" && k !== "status" && typeof metricsTable[0][k] === "number",
  );

  if (metricKeys.length < 3) {
    return (
      <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
        Need at least 3 metrics for radar chart
      </p>
    );
  }

  const invertMetrics = new Set(["global_mae", "mae", "mae_positive", "mae_negative"]);

  const normalizedData: Record<string, number[]> = {};
  for (const row of metricsTable) {
    normalizedData[row.model as string] = [];
  }

  for (const key of metricKeys) {
    const vals = metricsTable.map((r) => r[key] as number);
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const range = max - min || 1;

    for (const row of metricsTable) {
      const raw = (row[key] as number - min) / range;
      const val = invertMetrics.has(key) ? 1 - raw : raw;
      normalizedData[row.model as string].push(val);
    }
  }

  const colors = [
    "#0077C8", "#22c55e", "#f59e0b", "#ef4444", "#3b82f6",
    "#a855f7", "#ec4899", "#14b8a6",
  ];

  const traces = metricsTable.map((row, i) => ({
    type: "scatterpolar" as const,
    r: [...normalizedData[row.model as string], normalizedData[row.model as string][0]],
    theta: [...metricKeys, metricKeys[0]],
    fill: "toself" as const,
    name: row.model as string,
    line: { color: colors[i % colors.length] },
    fillcolor: colors[i % colors.length] + "20",
  }));

  return (
    <Plot
      data={traces}
      layout={{
        height: 350,
        margin: { l: 60, r: 60, t: 30, b: 30 },
        paper_bgcolor: c.paper,
        plot_bgcolor: c.plot,
        font: { ...chartFont(), size: 10, color: c.textMuted },
        polar: {
          bgcolor: "transparent",
          radialaxis: { visible: true, range: [0, 1], gridcolor: c.grid, linecolor: c.grid },
          angularaxis: { gridcolor: c.grid, linecolor: c.grid },
        },
        legend: { font: { color: c.textMuted, size: 11 }, bgcolor: "transparent" },
        showlegend: true,
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%" }}
    />
  );
}
