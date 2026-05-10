import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CourseSummary } from "../api/types";
import CourseTimeline from "../components/charts/CourseTimeline";
import { BookOpen } from "lucide-react";

export default function Courses() {
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [selected, setSelected] = useState<CourseSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getCourses()
      .then(setCourses)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: "var(--text-muted)" }}>Loading courses...</p>;

  if (courses.length === 0) {
    return (
      <div className="empty-state">
        <BookOpen />
        <p>No course data available. Load data first.</p>
      </div>
    );
  }

  return (
    <div className="grid-2">
      <div className="card" style={{ maxHeight: "calc(100vh - 120px)", overflowY: "auto" }}>
        <div className="card-header">
          <span className="card-title">Course Catalog ({courses.length})</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Acronym</th>
                <th>Name</th>
                <th>Total</th>
                <th>Avg/Sem</th>
              </tr>
            </thead>
            <tbody>
              {courses.map((c) => (
                <tr
                  key={c.course_id}
                  style={{
                    cursor: "pointer",
                    background:
                      selected?.course_id === c.course_id ? "var(--bg-hover)" : undefined,
                  }}
                  onClick={() => setSelected(c)}
                >
                  <td style={{ fontWeight: 600, color: "var(--accent)" }}>{c.acronym}</td>
                  <td>{c.name}</td>
                  <td>{c.total_enrollments}</td>
                  <td>{c.avg_enrollment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        {selected ? (
          <div className="card">
            <div className="card-header">
              <span className="card-title">
                {selected.acronym} — {selected.name}
              </span>
            </div>
            <div className="grid-2" style={{ marginBottom: 16 }}>
              <div className="stat-card">
                <div className="stat-label">Total Enrollments</div>
                <div className="stat-value">{selected.total_enrollments}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Avg / Semester</div>
                <div className="stat-value">{selected.avg_enrollment}</div>
              </div>
            </div>
            <CourseTimeline
              terms={selected.terms}
              enrollment={selected.enrollment_by_term}
              title={`${selected.acronym} Enrollment Over Time`}
            />
          </div>
        ) : (
          <div className="card empty-state">
            <BookOpen />
            <p>Select a course to see details</p>
          </div>
        )}
      </div>
    </div>
  );
}
