import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { StudentSummary, StudentHistory } from "../api/types";
import StudentSampleView from "../components/charts/StudentSampleView";
import { Search, ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";

export default function Students() {
  const { id } = useParams();
  return id ? <StudentDetail id={id} /> : <StudentList />;
}

// ── Student List ──────────────────────────────────────────────────────────────

function StudentList() {
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const limit = 30;

  useEffect(() => {
    setLoading(true);
    api.getStudents(offset, limit, search)
      .then((res) => { setStudents(res.students); setTotal(res.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [offset, search]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <div style={{ position: "relative", flex: 1, maxWidth: 400 }}>
          <Search size={16} style={{
            position: "absolute", left: 12, top: "50%",
            transform: "translateY(-50%)", color: "var(--text-muted)",
          }} />
          <input className="input" style={{ paddingLeft: 36 }}
            placeholder="Search students by ID..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
          />
        </div>
        <span style={{ alignSelf: "center", fontSize: 13, color: "var(--text-muted)" }}>
          {total} students
        </span>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Student ID</th><th>Semesters</th><th>Courses Taken</th>
                <th>First Term</th><th>Last Term</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} style={{ color: "var(--text-muted)" }}>Loading...</td></tr>
              ) : students.length === 0 ? (
                <tr><td colSpan={5} style={{ color: "var(--text-muted)" }}>No students found</td></tr>
              ) : students.map((s) => (
                <tr key={s.id} style={{ cursor: "pointer" }} onClick={() => navigate(`/students/${s.id}`)}>
                  <td style={{ fontFamily: "monospace", color: "var(--accent)" }}>{s.id}</td>
                  <td>{s.n_semesters}</td>
                  <td>{s.n_courses_taken}</td>
                  <td>{s.first_term || "-"}</td>
                  <td>{s.last_term || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {total > limit && (
          <div style={{ display: "flex", gap: 8, marginTop: 12, justifyContent: "center" }}>
            <button className="btn btn-secondary" disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - limit))}>Previous</button>
            <span style={{ alignSelf: "center", fontSize: 12, color: "var(--text-muted)" }}>
              {offset + 1}-{Math.min(offset + limit, total)} of {total}
            </span>
            <button className="btn btn-secondary" disabled={offset + limit >= total}
              onClick={() => setOffset(offset + limit)}>Next</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Student Detail ────────────────────────────────────────────────────────────

function StudentDetail({ id }: { id: string }) {
  const [history, setHistory] = useState<StudentHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [step, setStep] = useState(-1);
  const navigate = useNavigate();

  const fetchStudent = useCallback((s: number) => {
    setLoading(true);
    const url = `http://127.0.0.1:8765/students/${id}?step=${s}`;
    fetch(url)
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then((h: StudentHistory) => {
        setHistory(h);
        setStep(h.current_step ?? 0);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    setStep(-1);
    fetchStudent(-1);
  }, [id, fetchStudent]);

  if (loading && !history) return <p style={{ color: "var(--text-muted)" }}>Loading student {id}...</p>;
  if (error) return <p style={{ color: "var(--error)" }}>Error: {error}</p>;
  if (!history) return <p style={{ color: "var(--text-muted)" }}>Student not found</p>;

  const sampleView = history.sample_view;
  const nSteps = history.n_steps || 0;
  const currentStep = history.current_step ?? 0;

  function goStep(s: number) {
    fetchStudent(s);
  }

  return (
    <div>
      <button className="btn btn-secondary" style={{ marginBottom: 16 }}
        onClick={() => navigate("/students")}>
        <ArrowLeft size={16} /> Back to list
      </button>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom: 20 }}>
        <div className="stat-card">
          <div className="stat-label">Student</div>
          <div style={{ fontFamily: "monospace", fontSize: 16, fontWeight: 700 }}>{id}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Semesters</div>
          <div className="stat-value">{history.semesters.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">First Term</div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>{history.semesters[0]?.term || "-"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Last Term</div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>
            {history.semesters[history.semesters.length - 1]?.term || "-"}
          </div>
        </div>
      </div>

      {/* Sample view */}
      {sampleView ? (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header" style={{ flexWrap: "wrap", gap: 12 }}>
            <span className="card-title">Academic History</span>

            {nSteps > 1 && (
              <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <button className="btn btn-secondary" style={{ padding: "4px 6px" }}
                  disabled={currentStep <= 0}
                  onClick={() => goStep(currentStep - 1)}>
                  <ChevronLeft size={16} />
                </button>
                <span style={{ fontSize: 12, color: "var(--text-secondary)", minWidth: 70, textAlign: "center" }}>
                  {currentStep + 1} / {nSteps}
                </span>
                <button className="btn btn-secondary" style={{ padding: "4px 6px" }}
                  disabled={currentStep >= nSteps - 1}
                  onClick={() => goStep(currentStep + 1)}>
                  <ChevronRight size={16} />
                </button>
              </div>
            )}
          </div>

          <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8, display: "flex", gap: 16, flexWrap: "wrap" }}>
            <span><Dot color="#3b82f6" /> Enrolled</span>
            <span><Dot color="#15803d" /> Passed</span>
            <span><Dot color="#ef4444" /> Failed / Target</span>
            <span><Dot color="#f59e0b" /> Attempts</span>
          </div>

          <StudentSampleView data={sampleView} />
        </div>
      ) : (
        <div className="card" style={{ marginBottom: 20 }}>
          <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
            Not enough history for sample view (need at least 2 semesters).
          </p>
        </div>
      )}

      {/* Semester detail */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Semester Detail</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Semester</th><th>Courses</th><th>Details</th></tr>
            </thead>
            <tbody>
              {history.semesters.map((sem) => (
                <tr key={sem.term}>
                  <td style={{ fontWeight: 600 }}>{sem.term}</td>
                  <td>{sem.courses.length}</td>
                  <td>
                    {sem.courses.map((c) => (
                      <span key={c.course_id} style={{
                        display: "inline-block", padding: "2px 6px", marginRight: 4, marginBottom: 2,
                        borderRadius: 4, fontSize: 11,
                        background: c.grade !== null && c.grade >= 5 ? "#14532d"
                          : c.grade !== null && c.grade < 5 ? "#7f1d1d" : "var(--bg-hover)",
                        color: c.grade !== null && c.grade >= 5 ? "var(--success)"
                          : c.grade !== null && c.grade < 5 ? "var(--error)" : "var(--text-secondary)",
                      }}>
                        {c.acronym}{c.grade !== null ? ` (${c.grade})` : ""}{c.attempt > 1 ? ` x${c.attempt}` : ""}
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Dot({ color }: { color: string }) {
  return <span style={{
    display: "inline-block", width: 10, height: 10, borderRadius: 2,
    background: color, marginRight: 4, verticalAlign: "middle",
  }} />;
}
