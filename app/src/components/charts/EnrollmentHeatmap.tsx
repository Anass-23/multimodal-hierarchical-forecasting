import Plot from "react-plotly.js";
import { getChartColors, chartFont } from "../../utils/chartTheme";
import type { HeatmapData } from "../../api/types";

interface Props {
  data: HeatmapData;
  /** Single model prediction: probability per course (length = n_courses) */
  prediction?: number[] | null;
  predictionLabel?: string;
}

export default function EnrollmentHeatmap({ data, prediction, predictionLabel }: Props) {
  const { courses, terms, enrollment, grades, attempts } = data;

  // Filter to courses that were enrolled OR have prediction > 0.15
  const activeIndices: number[] = [];
  for (let c = 0; c < courses.length; c++) {
    const enrolled = enrollment[c].some((v) => v > 0);
    const predicted = prediction ? prediction[c] > 0.15 : false;
    if (enrolled || predicted) activeIndices.push(c);
  }

  const showPrediction = prediction && prediction.some((p) => p > 0.05);
  const xLabels = [...terms];
  if (showPrediction) xLabels.push(predictionLabel || "Predicted");

  const zValues: number[][] = [];
  const hoverText: string[][] = [];

  for (const c of activeIndices) {
    const row: number[] = [];
    const textRow: string[] = [];

    for (let t = 0; t < terms.length; t++) {
      const e = enrollment[c][t];
      const g = grades[c][t];
      const a = attempts[c][t];

      if (!e) {
        row.push(0);
        textRow.push(`${courses[c]} | ${terms[t]}<br>Not enrolled`);
      } else if (g === null || g === undefined) {
        row.push(0.3);
        textRow.push(`${courses[c]} | ${terms[t]}<br>Enrolled (no grade)${a > 1 ? `<br>Attempt ${a}` : ""}`);
      } else if (g < 5) {
        row.push(0.5);
        textRow.push(`${courses[c]} | ${terms[t]}<br>Grade: ${g} (failed)${a > 1 ? `<br>Attempt ${a}` : ""}`);
      } else {
        row.push(0.7 + ((g - 5) / 5) * 0.3);
        textRow.push(`${courses[c]} | ${terms[t]}<br>Grade: ${g}${a > 1 ? `<br>Attempt ${a}` : ""}`);
      }
    }

    // Prediction column
    if (showPrediction) {
      const prob = prediction![c];
      if (prob > 0.05) {
        row.push(0.3); // same blue as "enrolled"
        textRow.push(`${courses[c]} | Predicted<br>Score: ${(prob * 100).toFixed(0)}%`);
      } else {
        row.push(0);
        textRow.push(`${courses[c]} | Predicted<br>Not predicted`);
      }
    }

    zValues.push(row);
    hoverText.push(textRow);
  }

  const yLabels = activeIndices.map((c) => courses[c]);

  const shapes: Record<string, unknown>[] = [];
  if (showPrediction) {
    shapes.push({
      type: "line",
      x0: terms.length - 0.5,
      x1: terms.length - 0.5,
      y0: -0.5,
      y1: yLabels.length - 0.5,
      line: { color: "#0077C8", width: 2, dash: "dot" },
    });
  }

  const c = getChartColors();

  return (
    <Plot
      data={[
        {
          z: zValues,
          x: xLabels,
          y: yLabels,
          type: "heatmap",
          colorscale: [
            [0, c.bgCard],
            [0.3, "#3b82f6"],
            [0.5, "#ef4444"],
            [0.7, "#22c55e"],
            [1.0, "#15803d"],
          ],
          showscale: false,
          hoverinfo: "text",
          text: hoverText,
          xgap: 2,
          ygap: 2,
        },
      ]}
      layout={{
        height: Math.max(300, yLabels.length * 22),
        margin: { l: 70, r: 20, t: 10, b: 60 },
        paper_bgcolor: c.paper,
        plot_bgcolor: c.plot,
        font: { ...chartFont(), size: 10, color: c.textMuted },
        xaxis: { tickangle: -45, side: "bottom", gridcolor: c.grid },
        yaxis: { autorange: "reversed", gridcolor: c.grid },
        shapes,
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%" }}
    />
  );
}
