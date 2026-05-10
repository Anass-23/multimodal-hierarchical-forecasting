/**
 * Typed API client for the educast FastAPI backend.
 */

import type {
  ComparisonResponse,
  CourseSummary,
  DataStatus,
  HeatmapResponse,
  LoadResponse,
  ModelInfo,
  ModelStatus,
  StudentHistory,
  StudentListResponse,
  TrainResult,
  TrainingHistory,
  TreeStructure,
  TreeSummary,
} from "./types";

const DEFAULT_API_URL = "http://127.0.0.1:8765";

let _apiUrl = DEFAULT_API_URL;

export async function initApiUrl(): Promise<void> {
  if (window.electronAPI) {
    _apiUrl = await window.electronAPI.getApiUrl();
  }
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${_apiUrl}${path}`);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${_apiUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

// ── Data endpoints ────────────────────────────────────────────────────────────

export const api = {
  // Data
  loadData: (mode: "legacy" | "manifest" = "legacy", path?: string) =>
    post<LoadResponse>("/data/load", { mode, path }),

  getStatus: () => get<DataStatus>("/data/status"),

  getCourses: () => get<CourseSummary[]>("/data/courses"),

  // Students
  getStudents: (offset = 0, limit = 50, search = "") =>
    get<StudentListResponse>(
      `/students/?offset=${offset}&limit=${limit}&search=${encodeURIComponent(search)}`,
    ),

  getStudent: (id: string) => get<StudentHistory>(`/students/${id}`),

  // Models
  getModels: () => get<ModelInfo[]>("/models/"),

  getModelStatus: (name: string) => get<ModelStatus>(`/models/${name}/status`),

  getTrainingHistory: (name: string) => get<TrainingHistory>(`/models/${name}/history`),

  getModelSubjects: (name: string) => get<{ subjects: string[] }>(`/models/${name}/subjects`),

  getTreeStructure: (name: string, subject: string) =>
    get<TreeStructure>(`/models/${name}/tree/${subject}`),

  summarizeTree: (name: string, subject: string) =>
    post<TreeSummary>(`/models/${name}/summarize/${subject}`),

  trainModel: (name: string, seed = 42) =>
    post<TrainResult>(`/models/${name}/train`, { seed }),

  trainAll: (seed = 42, experiments?: string[]) =>
    post<{ ok: boolean; results: Record<string, TrainResult> }>("/models/train-all", {
      seed,
      experiments,
    }),

  // Evaluation
  getMetrics: () => get<Record<string, unknown>[]>("/evaluation/metrics"),

  getHeatmap: () => get<HeatmapResponse>("/evaluation/heatmap"),

  getComparison: () => get<ComparisonResponse>("/evaluation/compare"),

  getModelMetrics: (name: string) =>
    get<{ model: string; per_course: Record<string, unknown>[] }>(
      `/evaluation/metrics/${name}`,
    ),

  // Forecast
  getForecast: (modelName?: string, term?: string) =>
    post<Record<string, unknown>>("/forecast/run", {
      model_name: modelName,
      term,
    }),

  getTerms: () => get<{ terms: string[]; n_terms: number }>("/forecast/terms"),

  // WebSocket for training progress
  trainModelWs: (name: string): WebSocket =>
    new WebSocket(`ws://127.0.0.1:8765/models/${name}/train-ws`),
};
