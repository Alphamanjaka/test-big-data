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