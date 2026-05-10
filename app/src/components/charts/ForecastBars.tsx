import Plot from "react-plotly.js";
import { getChartColors, chartFont } from "../../utils/chartTheme";

interface Props {
  models: string[];
  values: number[];
  label: string;
}

export default function ForecastBars({ models, values, label }: Props) {
  const c = getChartColors();
  const colors = [
    "#0077C8", "#22c55e", "#f59e0b", "#ef4444", "#3b82f6",
    "#a855f7", "#ec4899", "#14b8a6", "#f97316", "#8b5cf6",
  ];

  return (
    <Plot
      data={[
        {
          x: models,
          y: values,
          type: "bar",
          marker: {
            color: models.map((_, i) => colors[i % colors.length]),
            line: { width: 0 },
          },
          text: values.map((v) => v.toFixed(2)),
          textposition: "outside",
          textfont: { color: c.textMuted, size: 11 },
          hoverinfo: "x+y",
        },
      ]}
      layout={{
        height: 300,
        margin: { l: 50, r: 20, t: 20, b: 80 },
        paper_bgcolor: c.paper,
        plot_bgcolor: c.plot,
        font: { ...chartFont(), size: 11, color: c.textMuted },
        xaxis: { tickangle: -45, gridcolor: c.grid },
        yaxis: { title: { text: label, font: { size: 12 } }, gridcolor: c.grid },
        bargap: 0.3,
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%" }}
    />
  );
}
