"use client";

// URL de l'API backend (surridable via .env NEXT_PUBLIC_API_URL)
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

// ------------------------------------------------------------
// Enveloppe et helpers
// ------------------------------------------------------------
interface ApiEnvelope {
  success?: boolean;
  data?: unknown;
  mocked?: boolean;
  [key: string]: unknown;
}

/**
 * Résultat d'un endpoint : les données, et le fait qu'elles soient ou non
 * servies par le jeu de démonstration. Le backend le signale dans l'enveloppe
 * (`mocked`), et l'interface doit le montrer : un indicateur de démonstration
 * lu comme une mesure réelle est le principal risque de ce tableau de bord.
 */
export interface ApiResult<T> {
  data: T;
  mocked: boolean;
}

/**
 * Fetch un endpoint du backend de gouvernance. Lève une erreur si le backend
 * est indisponible ou en erreur, sinon renvoie l'enveloppe API.
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

/** Combine `dataOf` et le drapeau `mocked` de l'enveloppe. */
function resultOf<T>(env: ApiEnvelope): ApiResult<T> {
  return { data: dataOf<T>(env), mocked: env.mocked === true };
}

// ------------------------------------------------------------
// Endpoints gouvernance (moteur de déduplication et consentement)
// ------------------------------------------------------------

/** Finalités autorisées par le moteur : cf. `engine/governance/consent.py`. */
export type ConsentPurpose = "api_access" | "research" | "analytics";

export const CONSENT_PURPOSES: ConsentPurpose[] = [
  "api_access",
  "research",
  "analytics",
];

export const PURPOSE_LABELS: Record<ConsentPurpose, string> = {
  api_access: "Accès API",
  research: "Recherche",
  analytics: "Analyse",
};

/** KPI de déduplication : volumétrie, doublons, taux, répartition par méthode. */
export interface GovernanceDuplicates {
  total_patients: number;
  total_masters: number;
  duplicates: number;
  duplicate_rate: number;
  by_method: Record<string, number>;
}

export interface ConsentRow {
  master_patient_id: string;
  patient_uuid?: string;
  name: string;
  purpose: ConsentPurpose;
  granted: boolean;
  recorded_at: string;
}

export interface ConsentStats {
  total_consents: number;
  granted_count: number;
  patients: number;
}

export interface ConsentResult extends ApiResult<ConsentRow[]> {
  stats: ConsentStats;
}

export async function getDuplicates(): Promise<ApiResult<GovernanceDuplicates>> {
  const env = await fetchApi(`/api/governance/duplicates`);
  return resultOf<GovernanceDuplicates>(env);
}

export async function getConsent(limit = 200): Promise<ConsentResult> {
  const env = await fetchApi(`/api/governance/consent?limit=${limit}`);
  const stats: ConsentStats = {
    total_consents: (env.total_consents as number) ?? 0,
    granted_count: (env.granted_count as number) ?? 0,
    patients: (env.patients as number) ?? 0,
  };
  return { ...resultOf<ConsentRow[]>(env), stats };
}

// ------------------------------------------------------------
// Endpoints planification / pipeline (API gouvernance FastAPI :8000)
// ------------------------------------------------------------

/** URL de l'API gouvernance (FastAPI) — surridable via .env. */
export const GOVERNANCE_API_URL =
  process.env.NEXT_PUBLIC_GOVERNANCE_API_URL || "http://localhost:8000";

/** Clé API de démonstration (surridable via .env) pour la page /pipeline. */
const GOVERNANCE_API_KEY =
  process.env.NEXT_PUBLIC_GOVERNANCE_API_KEY || "";

/** Erreur levée par l'API gouvernance, avec le statut HTTP pour un traitement ciblé (403 consentement). */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export type ScheduleFrequency = "daily" | "weekly" | "monthly";
export type ResumeMode = "auto" | "since" | "full";

export interface PipelineSchedule {
  enabled: boolean;
  frequency: ScheduleFrequency;
  time: string;
  day_of_week: number;
  day_of_month: number;
  resume: { mode: ResumeMode; since: string | null };
}

export interface PipelineStatus {
  schedule: PipelineSchedule;
  schedule_error: string | null;
  next_run: string;
  run_flags: string[];
  pipeline: {
    status?: string;
    run_id?: string;
    mode?: string;
    steps?: Record<string, string>;
    [key: string]: unknown;
  };
  scheduler: {
    last_launched_slot?: string | null;
    last_launch_at?: string | null;
    runs: { at: string; slot: string; flags: string[]; pid: number }[];
  };
  zones: Record<string, unknown>;
  sources: Record<string, { tables: number; last_extracted_at: string | null }>;
}

/** Fetch de l'API gouvernance FastAPI (page /pipeline), avec Bearer si une clé est définie. */
async function fetchGovernance(
  path: string,
  init: RequestInit = {}
): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (GOVERNANCE_API_KEY) {
    headers["Authorization"] = `Bearer ${GOVERNANCE_API_KEY}`;
  }
  return fetch(`${GOVERNANCE_API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}

export async function getPipelineStatus(): Promise<PipelineStatus> {
  const res = await fetchGovernance("/pipeline/status");
  if (!res.ok) throw new Error(`/pipeline/status → HTTP ${res.status}`);
  return (await res.json()) as PipelineStatus;
}

export async function putPipelineSchedule(
  schedule: PipelineSchedule
): Promise<PipelineSchedule> {
  const res = await fetchGovernance("/pipeline/schedule", {
    method: "PUT",
    body: JSON.stringify(schedule),
  });
  if (!res.ok) {
    const detail = (await res.json().catch(() => null))?.detail;
    throw new Error(detail ? `HTTP ${res.status} — ${detail}` : `HTTP ${res.status}`);
  }
  return (await res.json()) as PipelineSchedule;
}

// ------------------------------------------------------------
// Endpoints patients (API gouvernance FastAPI :8000)
// ------------------------------------------------------------

/** Identité d'un patient master — colonnes de sql/schema.sql (master_patient). */
export interface PatientSummary {
  master_patient_id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  birth_date: string | null;
  cin: string | null;
  birth_city: string | null;
  address: string | null;
  gender: "M" | "F" | "" | null;
}

export interface PatientList {
  items: PatientSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface IdentityMapEntry {
  source_system: string;
  source_patient_id: string;
  match_method: "new_master" | "exact" | "probabilistic";
  match_score: number;
}

export interface PatientConsentRow {
  purpose: ConsentPurpose;
  granted: boolean;
  recorded_at: string;
}

/** Dossier d'un patient master : identité + correspondances de déduplication + avis. */
export interface PatientDetail extends PatientSummary {
  identity_map: IdentityMapEntry[];
  consents: PatientConsentRow[];
}

/**
 * Liste des patients masters ayant consenti à la finalité demandée.
 * Recherche (nom/CIN/id) et pagination côté API.
 */
export async function listPatients(options?: {
  search?: string;
  page?: number;
  pageSize?: number;
  purpose?: ConsentPurpose;
}): Promise<PatientList> {
  const params = new URLSearchParams({ purpose: options?.purpose ?? "api_access" });
  if (options?.search) params.set("search", options.search);
  if (options?.page) params.set("page", String(options.page));
  if (options?.pageSize) params.set("page_size", String(options.pageSize));
  const res = await fetchGovernance(`/patients?${params.toString()}`);
  if (!res.ok) throw new ApiError(`/patients → HTTP ${res.status}`, res.status);
  return (await res.json()) as PatientList;
}

/**
 * Dossier d'un patient master. Sans consentement pour `purpose`, l'API répond
 * 403 (refus journalisé dans l'audit) : l'erreur est soulevée avec `.status`.
 */
export async function getPatient(
  masterPatientId: string,
  purpose: ConsentPurpose = "api_access"
): Promise<PatientDetail> {
  const path = `/patients/${encodeURIComponent(masterPatientId)}?purpose=${purpose}`;
  const res = await fetchGovernance(path);
  if (res.status === 403) {
    const detail = (await res.json().catch(() => null))?.detail;
    throw new ApiError(detail ?? "Consentement non accordé", 403);
  }
  if (!res.ok) throw new ApiError(`${path} → HTTP ${res.status}`, res.status);
  return (await res.json()) as PatientDetail;
}