import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { DataStatus } from "../api/types";
import { Database, Users, BookOpen, Brain } from "lucide-react";

export default function Dashboard() {
  const [status, setStatus] = useState<DataStatus | null>(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api
      .getStatus()
      .then(setStatus)
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="empty-state">
        <Database />
        <p>Cannot reach the API server. Make sure the Python backend is running.</p>
        <code style={{ marginTop: 8, fontSize: 12, color: "var(--text-muted)" }}>
          python -m educast.server
        </code>
      </div>
    );
  }

  if (!status) {
    return <p style={{ color: "var(--text-muted)" }}>Loading...</p>;
  }

  if (!status.data_loaded) {
    return (
      <div className="empty-state">
        <Database />
        <p>No data loaded yet. Go to Setup to load university data.</p>
        <button
          className="btn btn-primary"
          style={{ marginTop: 16 }}
          onClick={() => navigate("/setup")}
        >
          Go to Setup
        </button>
      </div>
    );
  }

  const modelsRun = Object.values(status.models_run || {});
  const completedModels = modelsRun.filter((m) => m.status === "done").length;

  return (
    <div>
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-label">Students</div>
          <div className="stat-value">{status.n_students}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Courses</div>
          <div className="stat-value">{status.n_courses}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Semesters</div>
          <div className="stat-value">{status.n_terms}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Models Trained</div>
          <div className="stat-value">{completedModels}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Quick Actions</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <button className="btn btn-secondary" onClick={() => navigate("/students")}>
              <Users size={16} /> Browse Students
            </button>
            <button className="btn btn-secondary" onClick={() => navigate("/models")}>
              <Brain size={16} /> Run Models
            </button>
            <button className="btn btn-secondary" onClick={() => navigate("/evaluation")}>
              <BookOpen size={16} /> View Results
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Model Status</span>
          </div>
          {modelsRun.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
              No models trained yet
            </p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Status</th>
                    <th>MAE</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(status.models_run).map(([name, m]) => (
                    <tr key={name}>
                      <td>{name}</td>
                      <td>
                        <span className={`badge badge-${m.status}`}>{m.status}</span>
                      </td>
                      <td>
                        {m.metrics?.global_mae != null
                          ? (m.metrics.global_mae as number).toFixed(2)
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
