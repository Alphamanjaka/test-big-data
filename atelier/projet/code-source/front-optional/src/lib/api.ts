"use client";

// URL de l'API backend (surridable via .env NEXT_PUBLIC_API_URL)
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

// ------------------------------------------------------------
// Types (alignés sur les réponses du backend Flask)
// ------------------------------------------------------------
export interface RmaFilters {
  start?: string | null;
  end?: string | null;
  sex?: string;
  limit?: number;
  page?: number;
}

export interface AdmissionsSummary {
  total_admissions: number;
  mortalite_infantile: number | null;
  mortalite_maternelle: number | null;
}

export interface TopDiagnostic {
  diagnosis_code: string;
  diagnosis: string;
  total: number;
}

export interface AgeColumns {
  age_0_28j: number;
  age_29_59j: number;
  age_2_11m: number;
  age_1_4a: number;
  age_5_14a: number;
  age_15_24a: number;
  age_25_59a: number;
  age_60plus: number;
}

export interface Diagnostic {
  diagnosis_code: string;
  diagnosis: string;
  total: number;
  age_0_28j: number;
  age_29_59j: number;
  age_2_11m: number;
  age_1_4a: number;
  age_5_14a: number;
  age_15_24a: number;
  age_25_59a: number;
  age_60plus: number;
}

export interface MortalityRow {
  service: string;
  code: string;
  diagnostic: string;
  cas: number;
  deces: number;
}

export interface MaternityPoint {
  month: string;
  total: number;
  accouchements: number;
  deces_maternels: number;
  live_births_total: number;
}

export interface LaboratoryRow {
  examen: string;
  total: number;
  nouveaux: number;
  positifs: number;
}

export interface MalariaData {
  consultants_fievre: number;
  tdr_effectues: number;
  lames_effectuees: number;
  tdr_positifs: number;
  lames_positives: number;
  traites: number;
  moustiquaires_distribuees: number;
  prevention: {
    enfants_0_5ans: number;
    femmes_enceintes: number;
    population_generale: number;
  };
  evolution_mensuelle: Array<{ mois: string; cas: number; traites: number }>;
}

// ------------------------------------------------------------
// Helpers
// ------------------------------------------------------------
function buildQuery(filters: RmaFilters = {}): string {
  const params = new URLSearchParams();
  if (filters.start) params.set("start", filters.start);
  if (filters.end) params.set("end", filters.end);
  if (filters.sex && filters.sex !== "all") params.set("sex", filters.sex);
  if (filters.limit) params.set("limit", String(filters.limit));
  if (filters.page) params.set("page", String(filters.page));
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

interface ApiEnvelope {
  success?: boolean;
  data?: unknown;
  last_sync?: string;
  [key: string]: unknown;
}

/**
 * Fetch un endpoint RMA. Lève une erreur si le backend est
 * indisponible ou en erreur, sinon renvoie l'enveloppe API.
 */
async function fetchApi(path: string): Promise<ApiEnvelope> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`[api] ${path} → HTTP ${res.status}`);
  }
  return (await res.json()) as ApiEnvelope;
}

/**
 * Extrait `env.data` typé. Lève une erreur si la réponse n'est pas
 * exploitable (success === false ou data absent).
 */
function dataOf<T>(env: ApiEnvelope): T {
  if (env.success === false || env.data === undefined) {
    throw new Error("Réponse API non exploitable");
  }
  return env.data as T;
}

// ------------------------------------------------------------
// Endpoints RMA
// ------------------------------------------------------------
export async function getAdmissionsSummary(filters?: RmaFilters): Promise<AdmissionsSummary> {
  const env = await fetchApi(`/rma/admissions_summary${buildQuery(filters)}`);
  return dataOf<AdmissionsSummary>(env);
}

export async function getTopDiagnostics(filters?: RmaFilters): Promise<TopDiagnostic[]> {
  const env = await fetchApi(
    `/rma/top_diagnostics${buildQuery({ ...filters, limit: filters?.limit ?? 5 })}`,
  );
  return dataOf<TopDiagnostic[]>(env);
}

export async function getDiagnosticsHeatmap(filters?: RmaFilters): Promise<Diagnostic[]> {
  const env = await fetchApi(
    `/rma/diagnostics_heatmap${buildQuery({ ...filters, limit: filters?.limit ?? 15 })}`,
  );
  return dataOf<Diagnostic[]>(env);
}

export async function getDiagnosticsList(filters?: RmaFilters): Promise<Diagnostic[]> {
  const env = await fetchApi(
    `/rma/diagnostics_list${buildQuery({ ...filters, limit: filters?.limit ?? 20, page: filters?.page ?? 1 })}`,
  );
  return dataOf<Diagnostic[]>(env);
}

export async function getMortality(filters?: RmaFilters): Promise<MortalityRow[]> {
  const env = await fetchApi(`/api/rma/mortality${buildQuery(filters)}`);
  return dataOf<MortalityRow[]>(env);
}

export async function getMaternity(filters?: RmaFilters): Promise<MaternityPoint[]> {
  const env = await fetchApi(`/api/rma/maternity${buildQuery(filters)}`);
  return dataOf<MaternityPoint[]>(env);
}

export async function getLaboratory(filters?: RmaFilters): Promise<LaboratoryRow[]> {
  const env = await fetchApi(`/api/rma/laboratory${buildQuery(filters)}`);
  return dataOf<LaboratoryRow[]>(env);
}

export async function getMalaria(filters?: RmaFilters): Promise<MalariaData> {
  const env = await fetchApi(`/api/rma/malaria${buildQuery(filters)}`);
  return dataOf<MalariaData>(env);
}

export async function getLastSync(): Promise<string> {
  const env = await fetchApi("/rma/last_sync");
  return env.last_sync ?? "";
}
