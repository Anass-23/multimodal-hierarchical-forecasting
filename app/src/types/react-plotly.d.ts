declare module "*.png" {
  const src: string;
  export default src;
}

declare module "react-plotly.js" {
  import { Component } from "react";

  interface PlotParams {
    data: Plotly.Data[];
    layout?: Partial<Plotly.Layout>;
    config?: Partial<Plotly.Config>;
    style?: React.CSSProperties;
    className?: string;
    onInitialized?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
    onUpdate?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
    onPurge?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
    onClick?: (event: Plotly.PlotMouseEvent) => void;
    onHover?: (event: Plotly.PlotMouseEvent) => void;
    revision?: number;
  }

  class Plot extends Component<PlotParams> {}
  export default Plot;
}

declare namespace Plotly {
  interface Data {
    [key: string]: unknown;
    type?: string;
    x?: unknown[];
    y?: unknown[];
    z?: unknown[][];
    text?: unknown;
    name?: string;
    mode?: string;
    marker?: Record<string, unknown>;
    line?: Record<string, unknown>;
    fill?: string;
    fillcolor?: string;
    colorscale?: string | [number, string][];
    hoverinfo?: string;
    orientation?: string;
    r?: number[];
    theta?: string[];
    showscale?: boolean;
    colorbar?: Record<string, unknown>;
    xgap?: number;
    ygap?: number;
    textposition?: string;
    textfont?: Record<string, unknown>;
  }

  interface Layout {
    [key: string]: unknown;
  }

  interface Config {
    responsive?: boolean;
    displayModeBar?: boolean;
    [key: string]: unknown;
  }

  interface Figure {
    data: Data[];
    layout: Layout;
  }

  interface PlotMouseEvent {
    points: Array<{
      pointIndex: number;
      [key: string]: unknown;
    }>;
  }
}
