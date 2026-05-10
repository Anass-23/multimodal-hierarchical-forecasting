// ── Data types ────────────────────────────────────────────────────────────────

export interface LoadResponse {
  ok: boolean;
  errors: string[];
  n_students: number;
  n_courses: number;
  n_terms: number;
  terms: string[];
}

export interface DataStatus {
  data_loaded: boolean;
  n_students: number;
  n_courses: number;
  n_terms: number;
  terms: string[];
  models_run: Record<string, { status: string; metrics: Record<string, number> }>;
}

// ── Student types ─────────────────────────────────────────────────────────────

export interface StudentSummary {
  id: string;
  n_semesters: number;
  n_courses_taken: number;
  first_term: string | null;
  last_term: string | null;
}

export interface StudentListResponse {
  total: number;
  offset: number;
  limit: number;
  students: StudentSummary[];
}

export interface CourseEnrollment {
  course_id: string;
  acronym: string;
  grade: number | null;
  attempt: number;
}

export interface SemesterDetail {
  term: string;
  courses: CourseEnrollment[];
}

export interface HeatmapData {
  courses: string[];
  course_ids: string[];
  terms: string[];
  enrollment: number[][];
  grades: (number | null)[][];
  attempts: number[][];
}

export interface SampleView {
  course_labels: string[];
  active_indices: number[];
  time_labels: string[];
  enrollment: number[][];   // (n_active_courses, window_size)
  grades: number[][];
  attempts: number[][];
  target: number[];         // (n_active_courses,) actual next semester
  meta: { year: number; term: number; student_id: string };
}

export interface StudentHistory {
  student_id: string;
  semesters: SemesterDetail[];
  heatmap_data: HeatmapData;
  sample_view?: SampleView | null;
  n_steps?: number;
  current_step?: number;
  available_models?: string[];
}

// ── Course types ──────────────────────────────────────────────────────────────

export interface CourseSummary {
  course_id: string;
  acronym: string;
  name: string;
  enrollment_by_term: number[];
  terms: string[];
  total_enrollments: number;
  avg_enrollment: number;
}

// ── Model types ───────────────────────────────────────────────────────────────

export interface ModelInfo {
  name: string;
  model_type: string;
  transform: string;
  params: Record<string, unknown>;
  status: "idle" | "training" | "done" | "error";
  metrics: Record<string, number>;
}

export interface ModelStatus {
  name: string;
  status: string;
  progress: number;
  metrics: Record<string, number>;
  error: string | null;
  metadata: Record<string, unknown>;
  per_course?: Record<string, unknown>[];
}

export interface TrainResult {
  ok: boolean;
  name: string;
  metrics?: Record<string, number>;
  per_course?: Record<string, unknown>[];
  error?: string;
}

export interface TrainingHistory {
  train_loss: number[];
  val_loss: number[];
}

export interface TreeStructure {
  subject: string;
  tree_text: string;
  max_depth: number;
  n_nodes: number;
  n_leaves: number;
  feature_names: string[] | null;
}

export interface TreeSummary {
  subject: string;
  summary: string;
  model_used: string;
  tree_text: string;
  metrics: string;
}

// ── Evaluation types ──────────────────────────────────────────────────────────

export interface MetricsRow {
  model: string;
  [metric: string]: string | number;
}

export interface HeatmapResponse {
  courses: string[];
  models: string[];
  values: (number | null)[][];
}

export interface ComparisonResponse {
  metrics_table: MetricsRow[];
  per_course_mae: Record<string, Record<string, number>>;
  model_names: string[];
  course_labels: string[];
}

// ── Electron API bridge ───────────────────────────────────────────────────────

declare global {
  interface Window {
    electronAPI?: {
      selectDirectory: () => Promise<string | null>;
      getApiUrl: () => Promise<string>;
    };
  }
}
