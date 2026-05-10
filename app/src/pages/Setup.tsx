import { useState } from "react";
import { api } from "../api/client";
import type { LoadResponse } from "../api/types";
import { FolderOpen, CheckCircle, AlertCircle, Upload } from "lucide-react";

export default function Setup() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<LoadResponse | null>(null);
  const [error, setError] = useState("");
  const [mode, setMode] = useState<"legacy" | "manifest">("legacy");
  const [dataPath, setDataPath] = useState("");

  async function handleSelectFolder() {
    if (window.electronAPI) {
      const path = await window.electronAPI.selectDirectory();
      if (path) setDataPath(path);
    }
  }

  async function handleLoad() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.loadData(mode, mode === "manifest" ? dataPath : undefined);
      setResult(res);
      if (!res.ok) {
        setError(res.errors.join(", "));
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">Data Source</span>
        </div>

        <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
          <button
            className={`btn ${mode === "legacy" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setMode("legacy")}
          >
            Built-in EPSEM Data
          </button>
          <button
            className={`btn ${mode === "manifest" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setMode("manifest")}
          >
            Custom (educast.yaml)
          </button>
        </div>

        {mode === "manifest" && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", marginBottom: 6, fontSize: 12, color: "var(--text-muted)" }}>
              Data folder (must contain educast.yaml)
            </label>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                className="input"
                value={dataPath}
                onChange={(e) => setDataPath(e.target.value)}
                placeholder="/path/to/university_data"
              />
              <button className="btn btn-secondary" onClick={handleSelectFolder}>
                <FolderOpen size={16} />
              </button>
            </div>
          </div>
        )}

        <button
          className="btn btn-primary"
          onClick={handleLoad}
          disabled={loading || (mode === "manifest" && !dataPath)}
        >
          <Upload size={16} />
          {loading ? "Loading..." : "Load Data"}
        </button>
      </div>

      {error && (
        <div className="card" style={{ borderColor: "var(--error)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--error)" }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        </div>
      )}

      {result && result.ok && (
        <div className="card" style={{ borderColor: "var(--success)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--success)", marginBottom: 16 }}>
            <CheckCircle size={18} />
            <span style={{ fontWeight: 600 }}>Data loaded successfully</span>
          </div>
          <div className="grid-3">
            <div className="stat-card">
              <div className="stat-label">Students</div>
              <div className="stat-value">{result.n_students}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Courses</div>
              <div className="stat-value">{result.n_courses}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Semesters</div>
              <div className="stat-value">{result.n_terms}</div>
            </div>
          </div>
          {result.terms.length > 0 && (
            <p style={{ marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
              Range: {result.terms[0]} to {result.terms[result.terms.length - 1]}
            </p>
          )}
        </div>
      )}

      <div className="card" style={{ marginTop: 24 }}>
        <div className="card-header">
          <span className="card-title">educast.yaml Standard</span>
        </div>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 12 }}>
          To use custom university data, create a folder with:
        </p>
        <pre style={{
          background: "var(--bg-primary)",
          padding: 16,
          borderRadius: "var(--radius)",
          fontSize: 12,
          color: "var(--text-secondary)",
          overflow: "auto",
        }}>
{`university_data/
  educast.yaml        # manifest (required)
  enrollments.csv     # student_id, course, semester, grade
  courses.csv         # code, acronym, name, credits
  students.csv        # optional: student metadata`}
        </pre>
      </div>
    </div>
  );
}
