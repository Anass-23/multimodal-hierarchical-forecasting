import Plot from "react-plotly.js";
import { getChartColors, chartFont } from "../../utils/chartTheme";

interface Props {
  features: string[];
  importances: number[];
  title?: string;
}

export default function FeatureImportance({
  features,
  importances,
  title = "Feature Importance",
}: Props) {
  const c = getChartColors();
  const sorted = features
    .map((f, i) => ({ feature: f, importance: importances[i] }))
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 20);

  return (
    <Plot
      data={[
        {
          y: sorted.map((s) => s.feature).reverse(),
          x: sorted.map((s) => s.importance).reverse(),
          type: "bar",
          orientation: "h",
          marker: {
            color: sorted
              .map((_, i) => {
                const t = i / sorted.length;
                return `rgba(0, 119, 200, ${0.4 + t * 0.6})`;
              })
              .reverse(),
          },
          hoverinfo: "x+y",
        },
      ]}
      layout={{
        height: Math.max(300, sorted.length * 24),
        title: { text: title, font: { ...chartFont(), size: 13 } },
        margin: { l: 80, r: 20, t: 40, b: 40 },
        paper_bgcolor: c.paper,
        plot_bgcolor: c.plot,
        font: { ...chartFont(), size: 10, color: c.textMuted },
        xaxis: { title: { text: "Importance", font: { size: 11 } }, gridcolor: c.grid },
        yaxis: { gridcolor: c.grid },
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%" }}
    />
  );
}
