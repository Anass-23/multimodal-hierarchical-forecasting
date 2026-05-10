import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import type { ModelInfo, TrainResult } from "../api/types";
import { Play, PlayCircle, Loader, XCircle, Eye } from "lucide-react";
import ModelDetail from "../components/ModelDetail";

const TIME_SERIES_TYPES = new Set(["naive", "lstm_macro", "lstm_micro", "course2vec_mlp"]);

function isTimeSeries(m: ModelInfo): boolean {
  return TIME_SERIES_TYPES.has(m.model_type);
}

export default function Models() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [trainingName, setTrainingName] = useState<string | null>(null);
  const [trainResult, setTrainResult] = useState<TrainResult | null>(null);
  const [detailModel, setDetailModel] = useState<ModelInfo | null>(null);

  const refresh = useCallback(() => {
    api.getModels().then(setModels).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleTrain(name: string) {
    setTrainingName(name);
    setTrainResult(null);
    try {
      const result = await api.trainModel(name);
      setTrainResult(result);
      refresh();
    } catch (e: unknown) {
      setTrainResult({
        ok: false,
        name,
        error: e instanceof Error ? e.message : "Unknown error",
      });
    } finally {
      setTrainingName(null);
    }
  }

  async function handleTrainAll() {
    setTrainingName("all");
    setTrainResult(null);
    try {
      await api.trainAll();
      refresh();
    } catch (e: unknown) {
      setTrainResult({
        ok: false,
        name: "all",
        error: e instanceof Error ? e.message : "Unknown error",
      });
    } finally {
      setTrainingName(null);
    }
  }

  if (loading) return <p style={{ color: "var(--text-muted)" }}>Loading models...</p>;

  const tsModels = models.filter(isTimeSeries);
  const classModels = models.filter((m) => !isTimeSeries(m));

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600 }}>Experiments</h2>
        <button
          className="btn btn-primary"
          disabled={trainingName !== null}
          onClick={handleTrainAll}
        >
          <PlayCircle size={16} />
          {trainingName === "all" ? "Training All..." : "Train All"}
        </button>
      </div>

      {trainResult && !trainResult.ok && (
        <div className="card" style={{ borderColor: "var(--error)", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--error)" }}>
            <XCircle size={16} />
            <span>{trainResult.error}</span>
          </div>
        </div>
      )}

      {detailModel && (
        <ModelDetail model={detailModel} onClose={() => setDetailModel(null)} />
      )}

      {/* Time Series Models */}
      {tsModels.length > 0 && (
        <>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 12 }}>
            Time Series Models
          </h3>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
            gap: 16,
            marginBottom: 24,
          }}>
            {tsModels.map((m) => (
              <ModelCard
                key={m.name}
                model={m}
                isTraining={trainingName === m.name}
                onTrain={() => handleTrain(m.name)}
                onDetail={() => setDetailModel(m)}
                disabled={trainingName !== null}
                isSelected={detailModel?.name === m.name}
              />
            ))}
          </div>
        </>
      )}

      {/* Classification Models */}
      {classModels.length > 0 && (
        <>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 12 }}>
            Classification Models
          </h3>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
            gap: 16,
          }}>
            {classModels.map((m) => (
              <ModelCard
                key={m.name}
                model={m}
                isTraining={trainingName === m.name}
                onTrain={() => handleTrain(m.name)}
                onDetail={() => setDetailModel(m)}
                disabled={trainingName !== null}
                isSelected={detailModel?.name === m.name}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function ModelCard({
  model,
  isTraining,
  onTrain,
  onDetail,
  disabled,
  isSelected,
}: {
  model: ModelInfo;
  isTraining: boolean;
  onTrain: () => void;
  onDetail: () => void;
  disabled: boolean;
  isSelected: boolean;
}) {
  return (
    <div className="card" style={isSelected ? { borderColor: "var(--accent)" } : undefined}>
      <div className="card-header">
        <span className="card-title">{model.name}</span>
        <span className={`badge badge-${model.status}`}>{model.status}</span>
      </div>

      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>
        <div>Model: <strong>{model.model_type}</strong></div>
        <div>Transform: <strong>{model.transform}</strong></div>
      </div>

      {/* Key params */}
      <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 12 }}>
        {Object.entries(model.params).slice(0, 4).map(([k, v]) => (
          <span
            key={k}
            style={{
              display: "inline-block",
              padding: "1px 6px",
              marginRight: 4,
              marginBottom: 2,
              background: "var(--bg-primary)",
              borderRadius: 4,
            }}
          >
            {k}={String(v)}
          </span>
        ))}
      </div>

      {/* Metrics if done */}
      {model.status === "done" && Object.keys(model.metrics).length > 0 && (
        <div style={{ fontSize: 12, marginBottom: 12 }}>
          {Object.entries(model.metrics).map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-secondary)" }}>{k}</span>
              <span style={{ fontWeight: 600 }}>{typeof v === "number" ? v.toFixed(3) : v}</span>
            </div>
          ))}
        </div>
      )}

      {isTraining && (
        <div className="progress-bar" style={{ marginBottom: 12 }}>
          <div className="progress-fill" style={{ width: "100%", animation: "pulse 2s infinite" }} />
        </div>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <button
          className="btn btn-primary"
          style={{ flex: 1 }}
          disabled={disabled}
          onClick={onTrain}
        >
          {isTraining ? (
            <>
              <Loader size={14} style={{ animation: "spin 1s linear infinite" }} /> Training...
            </>
          ) : (
            <>
              <Play size={14} /> Train
            </>
          )}
        </button>
        {model.status === "done" && (
          <button
            className="btn btn-secondary"
            onClick={onDetail}
            title="View details"
          >
            <Eye size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
