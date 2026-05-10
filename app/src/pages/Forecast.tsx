import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { TrendingUp, ChevronDown } from "lucide-react";
import { getChartColors, chartFont } from "../utils/chartTheme";

interface ForecastData {
  courses: string[];
  models: string[];
  model_data: Record<string, { courses: string[]; [metric: string]: number[] | string[] }>;
}

interface EnrollmentHistory {
  terms: string[];
  course_ids: string[];
  values: number[][];
  course_labels: Record<string, string>;
}

export default function Forecast() {
  const [data, setData] = useState<ForecastData | null>(null);
  const [history, setHistory] = useState<EnrollmentHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedMetric, setSelectedMetric] = useState("MAE");
  const [selectedModel, setSelectedModel] = useState<string>("");

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch("http://127.0.0.1:8765/forecast/results").then((r) => r.ok ? r.json() : null).catch(() => null),
      fetch("http://127.0.0.1:8765/forecast/enrollment-history").then((r) => r.ok ? r.json() : null).catch(() => null),
    ]).then(([forecastData, historyData]) => {
      if (forecastData) {
        setData(forecastData as ForecastData);
        if (forecastData.models?.length > 0) {
          setSelectedModel(forecastData.models[0]);
          const first = forecastData.model_data[forecastData.models[0]];
          const numericKeys = Object.keys(first).filter(
            (k) => k !== "courses" && Array.isArray(first[k]) && typeof (first[k] as number[])[0] === "number",
          );
          if (numericKeys.length > 0) setSelectedMetric(numericKeys[0]);
        }
      }
      if (historyData) setHistory(historyData as EnrollmentHistory);
    }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: "var(--text-muted)" }}>Loading forecast data...</p>;

  const hasModels = data && data.models.length > 0;

  return (
    <div>
      {/* Enrollment History Heatmap */}
      {history && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header">
            <span className="card-title">Enrollment History (All Courses x Terms)</span>
          </div>
          <EnrollmentHistoryHeatmap data={history} />
        </div>
      )}

      {!hasModels && (
        <div className="empty-state">
          <TrendingUp />
          <p>No trained models available. Train models first from the Models page.</p>
        </div>
      )}

      {hasModels && data && (
        <>
          {/* Model selector + metric bar chart */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-header">
              <span className="card-title">Per-Course Model Results</span>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <div style={{ position: "relative" }}>
                  <select
                    className="input"
                    style={{ width: 200, paddingRight: 28, appearance: "none", fontSize: 12 }}
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                  >
                    {data.models.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <ChevronDown
                    size={14}
                    style={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", pointerEvents: "none", color: "var(--text-muted)" }}
                  />
                </div>
                {(() => {
                  const firstModel = data.model_data[data.models[0]];
                  const availableMetrics = Object.keys(firstModel).filter(
                    (k) => k !== "courses" && Array.isArray(firstModel[k]) && (firstModel[k] as (number | null)[]).some((v) => typeof v === "number"),
                  );
                  return availableMetrics.map((m) => (
                    <button
                      key={m}
                      className={`btn ${selectedMetric === m ? "btn-primary" : "btn-secondary"}`}
                      onClick={() => setSelectedMetric(m)}
                      style={{ padding: "4px 12px", fontSize: 12 }}
                    >
                      {m}
                    </button>
                  ));
                })()}
              </div>
            </div>

            <SelectedModelChart data={data} selectedModel={selectedModel} selectedMetric={selectedMetric} />
          </div>

          {/* All models comparison bar chart */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-header">
              <span className="card-title">All Models Comparison — {selectedMetric}</span>
            </div>
            <AllModelsChart data={data} selectedMetric={selectedMetric} />
          </div>

          {/* Summary table */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Model Summary</span>
            </div>
            <SummaryTable data={data} />
          </div>
        </>
      )}
    </div>
  );
}

/* ── Enrollment History Heatmap ─────────────────────────────────────────── */

function EnrollmentHistoryHeatmap({ data }: { data: EnrollmentHistory }) {
  const c = getChartColors();
  const { terms, course_ids, values, course_labels } = data;

  // Use course labels if available, fallback to IDs
  const yLabels = course_ids.map((id) => course_labels[id] || id);

  // Transpose: values is (courses x terms) already
  return (
    <Plot
      data={[{
        z: values,
        x: terms,
        y: yLabels,
        type: "heatmap",
        colorscale: "YlGnBu",
        hoverinfo: "x+y+z",
        xgap: 1,
        ygap: 1,
        colorbar: {
          title: { text: "Students", font: { color: c.textMuted, size: 11 } },
          tickfont: { color: c.textMuted, size: 10 },
        },
      }]}
      layout={{
        height: Math.max(400, course_ids.length * 18),
        margin: { l: 120, r: 60, t: 10, b: 60 },
        paper_bgcolor: c.paper,
        plot_bgcolor: c.plot,
        font: { ...chartFont(), size: 9, color: c.textMuted },
        xaxis: { tickangle: -45, side: "bottom" },
        yaxis: { autorange: "reversed" },
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%" }}
    />
  );
}

/* ── Selected Model Chart ───────────────────────────────────────────────── */

function SelectedModelChart({
  data, selectedModel, selectedMetric,
}: { data: ForecastData; selectedModel: string; selectedMetric: string }) {
  const c = getChartColors();
  const mdata = data.model_data[selectedModel];
  if (!mdata) return null;

  const values = (mdata[selectedMetric] as number[]) || [];
  const courses = (mdata.courses as string[]) || [];

  return (
    <Plot
      data={[{
        x: courses,
        y: values,
        type: "bar",
        marker: {
          color: values.map((v) => {
            if (selectedMetric.toLowerCase().includes("mae")) {
              return v < 2 ? "#22c55e" : v < 5 ? "#f59e0b" : "#ef4444";
            }
            return v > 0.7 ? "#22c55e" : v > 0.4 ? "#f59e0b" : "#ef4444";
          }),
        },
        text: values.map((v) => v.toFixed(2)),
        textposition: "outside",
        textfont: { color: c.textMuted, size: 10 },
        hoverinfo: "x+y",
      }]}
      layout={{
        height: 350,
        margin: { l: 50, r: 20, t: 10, b: 100 },
        paper_bgcolor: c.paper,
        plot_bgcolor: c.plot,
        font: { ...chartFont(), size: 10 },
        xaxis: { tickangle: -60, gridcolor: c.grid },
        yaxis: { title: { text: selectedMetric, font: { size: 12 } }, gridcolor: c.grid },
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%" }}
    />
  );
}

/* ── All Models Comparison ──────────────────────────────────────────────── */

function AllModelsChart({
  data, selectedMetric,
}: { data: ForecastData; selectedMetric: string }) {
  const c = getChartColors();
  const colors = [
    "#0077C8", "#22c55e", "#f59e0b", "#ef4444", "#3b82f6",
    "#a855f7", "#ec4899", "#14b8a6", "#f97316", "#8b5cf6",
  ];

  const traces = data.models.map((model, i) => {
    const mdata = data.model_data[model];
    const rawValues = (mdata[selectedMetric] as (number | null)[]) || [];
    const values = rawValues.map((v) => (v != null ? v : 0));
    const courses = (mdata.courses as string[]) || [];
    return {
      name: model,
      type: "bar" as const,
      x: courses,
      y: values,
      marker: { color: colors[i % colors.length] },
    };
  });

  return (
    <Plot
      data={traces}
      layout={{
        height: 450,
        barmode: "group",
        margin: { l: 50, r: 20, t: 10, b: 120 },
        paper_bgcolor: c.paper,
        plot_bgcolor: c.plot,
        font: { ...chartFont(), size: 10 },
        xaxis: { tickangle: -60, gridcolor: c.grid },
        yaxis: { title: { text: selectedMetric, font: { size: 12 } }, gridcolor: c.grid },
        legend: { font: { color: c.textMuted }, bgcolor: "transparent" },
        bargap: 0.15,
        bargroupgap: 0.1,
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%" }}
    />
  );
}

/* ── Summary Table ──────────────────────────────────────────────────────── */

function SummaryTable({ data }: { data: ForecastData }) {
  const firstModel = data.model_data[data.models[0]];
  const availableMetrics = Object.keys(firstModel).filter(
    (k) => k !== "courses" && Array.isArray(firstModel[k]) && (firstModel[k] as (number | null)[]).some((v) => typeof v === "number"),
  );

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Model</th>
            {availableMetrics.map((m) => (
              <th key={m}>{m}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.models.map((model) => {
            const mdata = data.model_data[model];
            return (
              <tr key={model}>
                <td style={{ fontWeight: 600 }}>{model}</td>
                {availableMetrics.map((m) => {
                  const raw = (mdata[m] as (number | null)[]) || [];
                  const valid = raw.filter((v): v is number => v != null && !isNaN(v));
                  const avg = valid.length > 0 ? valid.reduce((a, b) => a + b, 0) / valid.length : NaN;
                  return <td key={m}>{isNaN(avg) ? "—" : avg.toFixed(3)}</td>;
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
