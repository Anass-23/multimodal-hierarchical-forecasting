import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { X, TreeDeciduous, Bot, Loader, ChevronDown } from "lucide-react";
import { api } from "../api/client";
import { getChartColors, chartFont } from "../utils/chartTheme";
import type { TrainingHistory, TreeStructure, TreeSummary, ModelInfo } from "../api/types";

interface Props {
  model: ModelInfo;
  onClose: () => void;
}

export default function ModelDetail({ model, onClose }: Props) {
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-header">
        <span className="card-title">
          {model.name} — Detail View
        </span>
        <button className="btn btn-secondary" onClick={onClose} style={{ padding: "4px 8px" }}>
          <X size={14} />
        </button>
      </div>

      {/* Metrics summary */}
      {model.status === "done" && Object.keys(model.metrics).length > 0 && (
        <div style={{ display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" }}>
          {Object.entries(model.metrics).map(([k, v]) => (
            <div key={k} className="stat-card" style={{ minWidth: 120 }}>
              <div className="stat-label">{k}</div>
              <div className="stat-value" style={{ fontSize: 20 }}>
                {typeof v === "number" ? v.toFixed(3) : v}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Loss curves for neural network models */}
      {(model.model_type.includes("lstm") || model.model_type === "course2vec_mlp") && model.status === "done" && (
        <LossCurves modelName={model.name} />
      )}

      {/* Tree viewer for tree-based models */}
      {(model.model_type === "decision_tree" || model.model_type === "random_forest") &&
        model.status === "done" && (
        <TreeViewer modelName={model.name} />
      )}

      {/* Per-course results */}
      <PerCourseResults modelName={model.name} />
    </div>
  );
}

/* ── Loss Curves ─────────────────────────────────────────────────────────── */

function LossCurves({ modelName }: { modelName: string }) {
  const [history, setHistory] = useState<TrainingHistory | null>(null);

  useEffect(() => {
    api.getTrainingHistory(modelName).then(setHistory).catch(() => {});
  }, [modelName]);

  if (!history || history.train_loss.length === 0) return null;

  const c = getChartColors();
  const epochs = history.train_loss.map((_, i) => i + 1);

  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Training History</h3>
      <Plot
        data={[
          {
            x: epochs,
            y: history.train_loss,
            type: "scatter",
            mode: "lines",
            name: "Train Loss",
            line: { color: c.accent, width: 2 },
          },
          ...(history.val_loss.length > 0
            ? [{
                x: epochs,
                y: history.val_loss,
                type: "scatter" as const,
                mode: "lines" as const,
                name: "Val Loss",
                line: { color: "#f59e0b", width: 2, dash: "dash" as const },
              }]
            : []),
        ]}
        layout={{
          height: 280,
          margin: { l: 50, r: 20, t: 10, b: 40 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { ...chartFont(), size: 10 },
          xaxis: { title: { text: "Epoch", font: { size: 11 } }, gridcolor: c.grid },
          yaxis: { title: { text: "Loss", font: { size: 11 } }, gridcolor: c.grid },
          legend: { font: { color: c.textMuted, size: 11 }, bgcolor: "transparent" },
          showlegend: true,
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: "100%" }}
      />
    </div>
  );
}

/* ── Tree Viewer ─────────────────────────────────────────────────────────── */

function TreeViewer({ modelName }: { modelName: string }) {
  const [subjects, setSubjects] = useState<string[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [tree, setTree] = useState<TreeStructure | null>(null);
  const [summary, setSummary] = useState<TreeSummary | null>(null);
  const [loadingTree, setLoadingTree] = useState(false);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [summaryError, setSummaryError] = useState("");

  useEffect(() => {
    api.getModelSubjects(modelName).then((r) => {
      setSubjects(r.subjects);
      if (r.subjects.length > 0) setSelected(r.subjects[0]);
    }).catch(() => {});
  }, [modelName]);

  useEffect(() => {
    if (!selected) return;
    setLoadingTree(true);
    setTree(null);
    setSummary(null);
    setSummaryError("");
    api.getTreeStructure(modelName, selected)
      .then(setTree)
      .catch(() => {})
      .finally(() => setLoadingTree(false));
  }, [modelName, selected]);

  async function handleSummarize() {
    if (!selected) return;
    setLoadingSummary(true);
    setSummaryError("");
    try {
      const result = await api.summarizeTree(modelName, selected);
      setSummary(result);
    } catch (e: unknown) {
      setSummaryError(e instanceof Error ? e.message : "Failed to connect to Ollama");
    } finally {
      setLoadingSummary(false);
    }
  }

  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
        <TreeDeciduous size={14} style={{ marginRight: 4, verticalAlign: "middle" }} />
        Decision Tree Viewer
      </h3>

      <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{ position: "relative" }}>
          <select
            className="input"
            style={{ width: 180, paddingRight: 28, appearance: "none" }}
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            {subjects.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <ChevronDown
            size={14}
            style={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", pointerEvents: "none", color: "var(--text-muted)" }}
          />
        </div>

        <button
          className="btn btn-secondary"
          onClick={handleSummarize}
          disabled={loadingSummary || !selected}
          title="Summarize with Ollama (requires ollama serve)"
        >
          {loadingSummary ? <Loader size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Bot size={14} />}
          {loadingSummary ? "Summarizing..." : "AI Summary"}
        </button>

        {tree && (
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
            depth={tree.max_depth} | {tree.n_nodes} nodes | {tree.n_leaves} leaves
          </span>
        )}
      </div>

      {loadingTree && <p style={{ fontSize: 12, color: "var(--text-muted)" }}>Loading tree...</p>}

      {tree && (
        <pre style={{
          background: "var(--bg-primary)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: 16,
          fontSize: 11,
          lineHeight: 1.6,
          overflow: "auto",
          maxHeight: 400,
          color: "var(--text-primary)",
          fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
        }}>
          {tree.tree_text}
        </pre>
      )}

      {summaryError && (
        <div style={{ marginTop: 8, padding: 12, background: "rgba(220,38,38,0.1)", borderRadius: "var(--radius)", fontSize: 12, color: "var(--error)" }}>
          {summaryError}
        </div>
      )}

      {summary && (
        <div style={{
          marginTop: 12,
          padding: 16,
          background: "var(--accent-subtle)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
        }}>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8, display: "flex", alignItems: "center", gap: 4 }}>
            <Bot size={12} /> AI Summary ({summary.model_used}) | {summary.metrics}
          </div>
          <div style={{ fontSize: 13, color: "var(--text-primary)", whiteSpace: "pre-wrap", lineHeight: 1.7 }}>
            {summary.summary}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Per-Course Results Table ────────────────────────────────────────────── */

function PerCourseResults({ modelName }: { modelName: string }) {
  const [data, setData] = useState<Record<string, unknown>[] | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    api.getModelMetrics(modelName)
      .then((r) => setData(r.per_course))
      .catch(() => {});
  }, [modelName]);

  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);
  const rows = expanded ? data : data.slice(0, 10);

  return (
    <div>
      <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
        Per-Course Results ({data.length} entries)
      </h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                {columns.map((col) => (
                  <td key={col}>
                    {typeof row[col] === "number"
                      ? (row[col] as number).toFixed(3)
                      : String(row[col] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.length > 10 && (
        <button
          className="btn btn-secondary"
          style={{ marginTop: 8, fontSize: 11 }}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "Show less" : `Show all ${data.length} rows`}
        </button>
      )}
    </div>
  );
}
