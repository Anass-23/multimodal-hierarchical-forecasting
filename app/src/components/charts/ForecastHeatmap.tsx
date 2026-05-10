import Plot from "react-plotly.js";
import { getChartColors, chartFont } from "../../utils/chartTheme";

interface Props {
  /** Course names (y-axis) */
  courses: string[];
  /** Term labels (x-axis groups) */
  terms: string[];
  /** Actual enrollment: courses x terms */
  actual: number[][];
  /** Predicted enrollment: courses x terms */
  predicted: number[][];
  /** Model name for title */
  modelName?: string;
}

/**
 * Side-by-side heatmap showing Actual vs Predicted enrollment counts
 * per course per term. Same visualization style as notebook 03.
 */
export default function ForecastHeatmap({
  courses,
  terms,
  actual,
  predicted,
  modelName = "Model",
}: Props) {
  const c = getChartColors();

  // Build interleaved columns: [term1_Act, term1_Pred, term2_Act, term2_Pred, ...]
  const xLabels: string[] = [];
  const zValues: number[][] = [];

  for (let ci = 0; ci < courses.length; ci++) {
    const row: number[] = [];
    for (let ti = 0; ti < terms.length; ti++) {
      row.push(actual[ci]?.[ti] ?? 0);
      row.push(predicted[ci]?.[ti] ?? 0);
    }
    zValues.push(row);
  }

  for (const t of terms) {
    xLabels.push(`${t} Act`);
    xLabels.push(`${t} Pred`);
  }

  // Vertical separator lines between term groups
  const shapes = terms.slice(1).map((_, i) => ({
    type: "line" as const,
    x0: (i + 1) * 2 - 0.5,
    x1: (i + 1) * 2 - 0.5,
    y0: -0.5,
    y1: courses.length - 0.5,
    line: { color: c.text, width: 1, dash: "dot" as const },
  }));

  return (
    <Plot
      data={[
        {
          z: zValues,
          x: xLabels,
          y: courses,
          type: "heatmap",
          colorscale: "YlGnBu",
          hoverinfo: "x+y+z",
          xgap: 1,
          ygap: 1,
          colorbar: {
            title: { text: "Students", font: { color: c.textMuted, size: 11 } },
            tickfont: { color: c.textMuted, size: 10 },
          },
        },
      ]}
      layout={{
        title: { text: `${modelName}: Actual vs Predicted`, font: { ...chartFont(), size: 14 } },
        height: Math.max(400, courses.length * 22),
        margin: { l: 120, r: 80, t: 40, b: 80 },
        paper_bgcolor: c.paper,
        plot_bgcolor: c.plot,
        font: { ...chartFont(), size: 9, color: c.textMuted },
        xaxis: { tickangle: -60, side: "bottom" },
        yaxis: { autorange: "reversed" },
        shapes,
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%" }}
    />
  );
}
