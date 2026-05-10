import Plot from "react-plotly.js";
import { getChartColors, chartFont } from "../../utils/chartTheme";
import type { HeatmapResponse } from "../../api/types";

interface Props {
  data: HeatmapResponse;
}

export default function PerCourseMAEHeatmap({ data }: Props) {
  const c = getChartColors();
  const { courses, models, values } = data;

  const hoverText = values.map((row, i) =>
    row.map((v, j) =>
      v !== null
        ? `${courses[i]} | ${models[j]}<br>MAE: ${v.toFixed(2)}`
        : `${courses[i]} | ${models[j]}<br>N/A`,
    ),
  );

  return (
    <Plot
      data={[
        {
          z: values,
          x: models,
          y: courses,
          type: "heatmap",
          colorscale: [
            [0, "#15803d"],
            [0.5, "#f59e0b"],
            [1.0, "#ef4444"],
          ],
          hoverinfo: "text",
          text: hoverText,
          xgap: 2,
          ygap: 2,
          colorbar: {
            title: { text: "MAE", font: { color: c.textMuted, size: 11 } },
            tickfont: { color: c.textMuted, size: 10 },
          },
        },
      ]}
      layout={{
        height: Math.max(400, courses.length * 20),
        margin: { l: 80, r: 80, t: 10, b: 60 },
        paper_bgcolor: c.paper,
        plot_bgcolor: c.plot,
        font: { ...chartFont(), size: 10, color: c.textMuted },
        xaxis: { side: "bottom", tickangle: -45 },
        yaxis: { autorange: "reversed" },
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%" }}
    />
  );
}
