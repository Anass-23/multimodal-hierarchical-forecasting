import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ComparisonResponse, HeatmapResponse, MetricsRow } from "../api/types";
import PerCourseMAEHeatmap from "../components/charts/PerCourseMAEHeatmap";
import MetricsRadar from "../components/charts/MetricsRadar";
import ForecastBars from "../components/charts/ForecastBars";
import { BarChart3 } from "lucide-react";

export default function Evaluation() {
  const [metrics, setMetrics] = useState<MetricsRow[]>([]);
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.getMetrics().catch(() => []),
      api.getHeatmap().catch(() => null),
      api.getComparison().catch(() => null),
    ])
      .then(([m, h, c]) => {
        setMetrics(m as MetricsRow[]);
        setHeatmap(h as HeatmapResponse | null);
        setComparison(c as ComparisonResponse | null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: "var(--text-muted)" }}>Loading evaluation data...</p>;

  if (metrics.length === 0) {
    return (
      <div className="empty-state">
        <BarChart3 />
        <p>No models have been trained yet. Go to Models and run some experiments first.</p>
      </div>
    );
  }

  return (
    <div>
      {/* Metrics table */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <span className="card-title">Model Comparison</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Model</th>
                {metrics.length > 0 &&
                  Object.keys(metrics[0])
                    .filter((k) => k !== "model" && k !== "status")
                    .map((k) => <th key={k}>{k}</th>)}
              </tr>
            </thead>
            <tbody>
              {metrics.map((row) => (
                <tr key={row.model}>
                  <td style={{ fontWeight: 600 }}>{row.model}</td>
                  {Object.entries(row)
                    .filter(([k]) => k !== "model" && k !== "status")
                    .map(([k, v]) => (
                      <td key={k}>
                        {typeof v === "number" ? v.toFixed(3) : String(v)}
                      </td>
                    ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Radar chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Metrics Radar</span>
          </div>
          {comparison ? (
            <MetricsRadar metricsTable={comparison.metrics_table} />
          ) : (
            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
              Need at least 2 models to compare
            </p>
          )}
        </div>

        {/* MAE bar chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Global MAE Comparison</span>
          </div>
          <ForecastBars
            models={metrics.map((m) => m.model as string)}
            values={metrics.map((m) => (m.MAE as number) || 0)}
            label="MAE"
          />
        </div>
      </div>

      {/* Per-course heatmap */}
      {heatmap && heatmap.courses.length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Per-Course MAE Heatmap</span>
          </div>
          <PerCourseMAEHeatmap data={heatmap} />
        </div>
      )}
    </div>
  );
}
