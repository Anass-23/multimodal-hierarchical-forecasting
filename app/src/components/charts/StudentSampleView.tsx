import Plot from "react-plotly.js";
import { getChartColors, chartFont } from "../../utils/chartTheme";
import type { SampleView } from "../../api/types";

interface Props {
  data: SampleView;
}

export default function StudentSampleView({ data }: Props) {
  const c = getChartColors();
  const FONT = { ...chartFont(), size: 10, color: c.textMuted };
  const BG = "transparent";

  const { course_labels, time_labels, enrollment, grades, attempts, target, meta } = data;
  const nCourses = course_labels.length;

  const yaxis = { autorange: "reversed" as const, gridcolor: c.grid };

  function cellAnnotations(
    matrix: number[][],
    xLabels: string[],
    fmt: (v: number) => string,
  ) {
    const annotations: Record<string, unknown>[] = [];
    for (let r = 0; r < matrix.length; r++) {
      for (let c = 0; c < matrix[r].length; c++) {
        const v = matrix[r][c];
        if (v > 0) {
          annotations.push({
            x: xLabels[c], y: course_labels[r],
            text: fmt(v), showarrow: false,
            font: { color: v > 0.5 ? "#fff" : "#000", size: 10 },
          });
        }
      }
    }
    return annotations;
  }

  function colAnnotations(vals: number[], xLabel: string) {
    return vals.map((v, r) => ({
      x: xLabel, y: course_labels[r],
      text: v > 0 ? "1" : "", showarrow: false,
      font: { color: "#fff", size: 10 },
    }));
  }

  const height = Math.max(250, nCourses * 26 + 60);
  const commonLayout = {
    paper_bgcolor: BG, plot_bgcolor: BG, font: FONT,
    margin: { l: 0, r: 5, t: 28, b: 20 },
    yaxis,
  };

  const gradeColorscale: [number, string][] = [
    [0, c.bgCard],
    [0.01, "#ef4444"],
    [0.49, "#fca5a5"],
    [0.5, "#86efac"],
    [1.0, "#15803d"],
  ];

  return (
    <div>
      <div style={{ fontSize: 13, color: "var(--text-primary)", marginBottom: 10, fontWeight: 600 }}>
        {meta.year} Q{meta.term} — Student {meta.student_id}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "60px 3fr 3fr 3fr 1fr", gap: 0 }}>
        {/* Y-axis labels column */}
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "flex-start", paddingTop: 28 }}>
          {course_labels.map((label, i) => (
            <div key={i} style={{
              height: 26, display: "flex", alignItems: "center", justifyContent: "flex-end",
              paddingRight: 6, fontSize: 10, color: "var(--text-secondary)", whiteSpace: "nowrap",
            }}>
              {label}
            </div>
          ))}
        </div>

        {/* Panel 1: Enrollment */}
        <Plot
          data={[{
            z: enrollment, x: time_labels, y: course_labels,
            type: "heatmap", colorscale: [[0, c.bgCard], [1, "#3b82f6"]],
            showscale: false, hoverinfo: "z", zmin: 0, zmax: 1, xgap: 2, ygap: 2,
          }]}
          layout={{
            ...commonLayout, title: { text: "Enrollment", font: { size: 12, color: c.text } },
            height, xaxis: { gridcolor: c.grid },
            yaxis: { ...yaxis, showticklabels: false },
            annotations: cellAnnotations(enrollment, time_labels, (v) => v > 0 ? "1" : ""),
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: "100%" }}
        />

        {/* Panel 2: Grades */}
        <Plot
          data={[{
            z: grades.map(row => row.map(v => v < 0 ? 0 : v)),
            x: time_labels, y: course_labels,
            type: "heatmap", colorscale: gradeColorscale,
            showscale: false, hoverinfo: "z", zmin: 0, zmax: 1, xgap: 2, ygap: 2,
          }]}
          layout={{
            ...commonLayout, title: { text: "Grades (0-10)", font: { size: 12, color: c.text } },
            height, xaxis: { gridcolor: c.grid },
            yaxis: { ...yaxis, showticklabels: false },
            annotations: cellAnnotations(
              grades.map(row => row.map(v => v < 0 ? 0 : v)),
              time_labels, (v) => (v * 10).toFixed(1),
            ),
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: "100%" }}
        />

        {/* Panel 3: Attempts */}
        <Plot
          data={[{
            z: attempts, x: time_labels, y: course_labels,
            type: "heatmap", colorscale: [[0, c.bgCard], [0.5, "#f59e0b"], [1, "#c2410c"]],
            showscale: false, hoverinfo: "z", zmin: 0, zmax: 1, xgap: 2, ygap: 2,
          }]}
          layout={{
            ...commonLayout, title: { text: "Attempts", font: { size: 12, color: c.text } },
            height, xaxis: { gridcolor: c.grid },
            yaxis: { ...yaxis, showticklabels: false },
            annotations: cellAnnotations(attempts, time_labels, (v) => (v * 5).toFixed(0)),
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: "100%" }}
        />

        {/* Panel 4: Target (actual next semester) */}
        <Plot
          data={[{
            z: target.map((v) => [v]),
            x: ["Actual"], y: course_labels,
            type: "heatmap", colorscale: [[0, c.bgCard], [1, "#ef4444"]],
            showscale: false, hoverinfo: "z", zmin: 0, zmax: 1, xgap: 2, ygap: 2,
          }]}
          layout={{
            ...commonLayout, title: { text: "Target", font: { size: 12, color: c.text } },
            height, xaxis: { gridcolor: c.grid },
            yaxis: { ...yaxis, showticklabels: false },
            annotations: colAnnotations(target, "Actual"),
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: "100%" }}
        />
      </div>
    </div>
  );
}
