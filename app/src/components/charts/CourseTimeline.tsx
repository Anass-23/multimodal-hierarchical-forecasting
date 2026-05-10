import Plot from "react-plotly.js";
import { getChartColors, chartFont } from "../../utils/chartTheme";

interface Props {
  terms: string[];
  enrollment: number[];
  title: string;
}

export default function CourseTimeline({ terms, enrollment, title }: Props) {
  const c = getChartColors();
  return (
    <Plot
      data={[
        {
          x: terms,
          y: enrollment,
          type: "scatter",
          mode: "lines+markers",
          line: { color: c.accent, width: 2 },
          marker: { size: 6, color: c.accent },
          fill: "tozeroy",
          fillcolor: "rgba(0, 119, 200, 0.1)",
          hoverinfo: "x+y",
        },
      ]}
      layout={{
        height: 280,
        title: { text: title, font: { ...chartFont(), size: 13 } },
        margin: { l: 50, r: 20, t: 40, b: 60 },
        paper_bgcolor: c.paper,
        plot_bgcolor: c.plot,
        font: { ...chartFont(), size: 10, color: c.textMuted },
        xaxis: { tickangle: -45, gridcolor: c.grid },
        yaxis: { title: { text: "Students", font: { size: 11 } }, gridcolor: c.grid },
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%" }}
    />
  );
}
