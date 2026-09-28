"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Database,
  Gauge,
  History,
  Info,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getPipelineStatus, type PipelineStatus } from "@/lib/api";

const STEP_LABELS: Record<string, string> = {
  ensure_generator_data: "Données générées",
  gen_extract_raw: "Extraction RAW",
  gen_fhir_mapping: "Mapping FHIR",
  create_silver: "SILVER",
  create_gold: "GOLD",
};

const STEP_ORDER = [
  "ensure_generator_data",
  "gen_extract_raw",
  "gen_fhir_mapping",
  "create_silver",
  "create_gold",
];

const MODE_LABELS: Record<string, string> = {
  full: "chargement complet",
  resume: "reprise",
  since: "depuis une date",
  from: "depuis une étape",
};

const FREQUENCY_LABELS: Record<string, string> = {
  daily: "Quotidienne",
  weekly: "Hebdomadaire",
  monthly: "Mensuelle",
};

const WEEKDAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];

const DAY = 24 * 3600 * 1000;

function fmtRelative(iso: string | null | undefined): string {
  if (!iso) return "jamais";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const diff = Date.now() - date.getTime();
  if (diff < 45_000) return "à l'instant";
  if (diff < 3_600_000) return `il y a ${Math.round(diff / 60_000)} min`;
  if (diff < DAY) return `il y a ${Math.round(diff / 3_600_000)} h`;
  if (diff < 30 * DAY) return `il y a ${Math.round(diff / DAY)} j`;
  return `il y a ${Math.round(diff / (30 * DAY))} mois`;
}

function fmtCountdown(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const diff = date.getTime() - Date.now();
  if (diff <= 0) return "maintenant ou bientôt";
  if (diff < 3_600_000) return `dans ${Math.max(1, Math.round(diff / 60_000))} min`;
  if (diff < DAY) return `dans ${Math.round(diff / 3_600_000)} h`;
  return `dans ${Math.round(diff / DAY)} j`;
}

function fmtTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function fmtDuration(startIso?: string | null, endIso?: string | null): string {
  if (!startIso) return "—";
  const start = new Date(startIso).getTime();
  if (Number.isNaN(start)) return "—";
  const end = endIso ? new Date(endIso).getTime() : Date.now();
  const seconds = Math.max(0, Math.round((end - start) / 1000));
  if (seconds < 60) return `${seconds} s`;
  const m = Math.floor(seconds / 60);
  return `${m} min ${seconds % 60} s`;
}

const STEP_BADGES: Record<string, string> = {
  pending: "bg-gray-100 text-gray-500",
  started: "bg-yellow-100 text-yellow-700 animate-pulse",
  ok: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

const STEP_NODE: Record<string, string> = {
  pending: "bg-gray-200 text-gray-400",
  started: "bg-yellow-400 text-white animate-pulse",
  ok: "bg-emerald-500 text-white",
  failed: "bg-red-500 text-white",
};

interface AlertItem {
  severity: "error" | "warning" | "info";
  message: string;
}

function buildAlerts(status: PipelineStatus): AlertItem[] {
  const alerts: AlertItem[] = [];
  const p = status.pipeline;
  if (p.status === "failed") {
    alerts.push({
      severity: "error",
      message: `Le dernier run a échoué${p.last_error ? ` : ${p.last_error}` : ""}.`,
    });
  }
  if (p.status === "ok" && Object.keys(status.zones).length > 0) {
    alerts.push({ severity: "info", message: "Dernier run terminé avec succès." });
  }
  Object.entries(status.zones).forEach(([name, zone]) => {
    if (zone?.status === "error") {
      alerts.push({ severity: "error", message: `Zone ${name} en erreur.` });
    }
  });
  if (status.schedule_error) {
    alerts.push({ severity: "warning", message: `Planification invalide : ${status.schedule_error}` });
  }
  if (Object.keys(status.sources).length === 0) {
    alerts.push({
      severity: "info",
      message: "Aucune source suivie (watermark vide — le premier run initialisera les empreintes).",
    });
  }
  if (p.status === "running") {
    alerts.push({ severity: "info", message: "Un run est en cours…" });
  }
  return alerts;
}

interface Props {
  userName: string;
}

export default function DashboardClient({ userName }: Props) {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getPipelineStatus();
      setStatus(data);
      setError(null);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "API gouvernance (port 8000) injoignable — vérifiez NEXT_PUBLIC_GOVERNANCE_API_URL / clé API."
      );
    } finally {
      setLoading(false);
      setLastUpdated(new Date());
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(() => {
      if (autoRefresh) load();
    }, 10_000);
    return () => clearInterval(timer);
  }, [load, autoRefresh]);

  const pipeline = status?.pipeline ?? {};
  const steps = pipeline.steps ?? {};
  const zones = status?.zones ?? {};
  const sources = status?.sources ?? {};
  const alerts = status ? buildAlerts(status) : [];

  const okSteps = STEP_ORDER.filter((s) => steps[s] === "ok").length;
  const totalTables = Object.values(sources).reduce((sum, s) => sum + (s.tables ?? 0), 0);
  const sourceNames = Object.keys(sources);

  const globalTone =
    pipeline.status === "running"
      ? { bg: "bg-yellow-50 border-yellow-200 text-yellow-800", label: "Run en cours" }
      : pipeline.status === "ok"
        ? { bg: "bg-emerald-50 border-emerald-200 text-emerald-800", label: "Dernier run réussi" }
        : pipeline.status === "failed"
          ? { bg: "bg-red-50 border-red-200 text-red-800", label: "Dernier run en échec" }
          : { bg: "bg-gray-50 border-gray-200 text-gray-600", label: "Aucun run exécuté" };

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between flex-wrap gap-3">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <Gauge className="w-5 h-5 text-blue-600" />
                <span>Tableau de bord — Pipeline ELT</span>
              </CardTitle>
              <CardDescription>
                État visuel du pipeline Medallion et de son planification — données fictives.
              </CardDescription>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-gray-600">Rafraîchir auto (10 s)</span>
              </label>
              <button
                onClick={() => load()}
                disabled={loading}
                className="flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                Actualiser
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading && !status && <p className="text-sm text-gray-500">Chargement…</p>}
          {!loading && error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-md text-sm">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {status && (
        <>
          {/* Bannière état global */}
          <div className={`flex items-center justify-between flex-wrap gap-2 p-4 rounded-lg border ${globalTone.bg}`}>
            <div className="flex items-center gap-3">
              {pipeline.status === "ok" && <CheckCircle2 className="w-6 h-6" />}
              {pipeline.status === "failed" && <XCircle className="w-6 h-6" />}
              {pipeline.status === "running" && (
                <span className="w-3 h-3 rounded-full bg-yellow-400 animate-pulse" />
              )}
              {!pipeline.status && <Info className="w-6 h-6" />}
              <div>
                <p className="font-semibold">{globalTone.label}</p>
                <p className="text-xs opacity-80">
                  {pipeline.run_id ? `Run ${pipeline.run_id} · mode ${MODE_LABELS[pipeline.mode ?? ""] ?? pipeline.mode ?? "—"}` : "Le pipeline n'a pas encore tourné."}
                </p>
              </div>
            </div>
            {pipeline.last_error && (
              <p className="text-xs max-w-md text-right">{pipeline.last_error}</p>
            )}
          </div>

          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
            <Kpi label="Étapes du run" value={`${okSteps} / 5`} hint="Étapes validées du dernier run" />
            <Kpi label="Durée du run" value={fmtDuration(pipeline.started_at, pipeline.finished_at)} hint="Début → fin (ou maintenant)" />
            <Kpi label="Zones Medallion" value={`${Object.keys(zones).length} / 3`} hint="RAW · SILVER · GOLD" />
            <Kpi label="Sources suivies" value={`${sourceNames.length}`} hint={`${totalTables} table(s) watermark`} />
            <Kpi label="Prochain run" value={fmtCountdown(status.next_run)} hint={`Planifié à ${fmtTime(status.next_run)}`} />
          </div>

          {/* Schéma Medallion */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Database className="w-5 h-5 text-blue-600" />
                <span>Schéma Medallion</span>
              </CardTitle>
              <CardDescription>
                Fraîcheur et statut de chaque zone Medallion.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-stretch gap-3">
                <ZoneCard name="RAW" zone={zones.RAW} step={steps.gen_extract_raw} />
                <ArrowBetween />
                <ZoneCard name="SILVER" zone={zones.SILVER} step={steps.create_silver} />
                <ArrowBetween />
                <ZoneCard name="GOLD" zone={zones.GOLD} step={steps.create_gold} />
              </div>
            </CardContent>
          </Card>

          {/* Déroulé du dernier run */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <PlayStep />
                <span>Déroulé du dernier run</span>
              </CardTitle>
              <CardDescription>
                Les 5 étapes de la chaîne d&apos;ingestion, dans l&apos;ordre d&apos;exécution.
              </CardDescription>
            </CardHeader>
            <CardContent>
<div className="flex items-start">
                    {STEP_ORDER.map((step, index) => {
                      const state = steps[step] ?? "pending";
                      return (
                        <div key={step} className="flex-1">
                          <div className="flex items-center">
                            <Node state={state} connector={index < STEP_ORDER.length - 1} />
                          </div>
                      <div className="flex flex-col gap-1 pl-1">
                        <p className="text-xs font-medium text-gray-700 mt-2">{STEP_LABELS[step]}</p>
                        <span className={`inline-block w-fit text-xs px-2 py-0.5 rounded ${STEP_BADGES[state]}`}>
                          {state === "started" ? "en cours" : state}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="flex flex-wrap gap-3 mt-4 text-xs text-gray-500">
                <span>Début : {fmtTime(pipeline.started_at)}</span>
                <span>Fin : {fmtTime(pipeline.finished_at)}</span>
                {pipeline.last_ok_step && <span>Dernière étape OK : {STEP_LABELS[pipeline.last_ok_step] ?? pipeline.last_ok_step}</span>}
                {pipeline.last_failed_step && (
                  <span className="text-red-600">Étape en échec : {STEP_LABELS[pipeline.last_failed_step] ?? pipeline.last_failed_step}</span>
                )}
                {pipeline.ingest_since && <span>Ingestion depuis : {pipeline.ingest_since}</span>}
              </div>
            </CardContent>
          </Card>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Fraîcheur des sources */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="w-5 h-5 text-blue-600" />
                  <span>Ingestion par empreinte (watermark)</span>
                </CardTitle>
                <CardDescription>
                  Dernière extraction de chaque source — anti-retraitement des fichiers inchangés.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {sourceNames.length === 0 ? (
                  <p className="text-sm text-gray-500">
                    Aucune source suivie pour l&apos;instant — le premier run planifié initialisera les empreintes.
                  </p>
                ) : (
                  sourceNames.map((name) => <FreshnessBar key={name} name={name} info={sources[name]} />)
                )}
              </CardContent>
            </Card>

            {/* Planification */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CalendarClock className="w-5 h-5 text-blue-600" />
                  <span>Planification automatique</span>
                </CardTitle>
                <CardDescription>Réglage lu par le cron de la VM (éditable sur la page Pipeline ELT).</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">État</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${status.schedule.enabled ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-600"}`}>
                    {status.schedule.enabled ? "Activée" : "Désactivée"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Fréquence</span>
                  <span className="font-medium">{FREQUENCY_LABELS[status.schedule.frequency]}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Heure (fuseau VM)</span>
                  <span className="font-medium">{status.schedule.time}</span>
                </div>
                {status.schedule.frequency === "weekly" && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Jour</span>
                    <span className="font-medium">{WEEKDAYS[status.schedule.day_of_week]}</span>
                  </div>
                )}
                {status.schedule.frequency === "monthly" && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Jour du mois</span>
                    <span className="font-medium">{status.schedule.day_of_month}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">Mode de reprise</span>
                  <span className="font-medium">{MODE_LABELS[status.schedule.resume.mode] ?? status.schedule.resume.mode}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Prochain run</span>
                  <span className="font-medium">{fmtTime(status.next_run)}</span>
                </div>
                {status.run_flags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {status.run_flags.map((flag) => (
                      <span key={flag} className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700">
                        {flag}
                      </span>
                    ))}
                  </div>
                )}
                {status.schedule_error && (
                  <div className="bg-amber-50 border border-amber-200 text-amber-800 p-2 rounded-md text-xs">
                    {status.schedule_error}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Historique cron + alertes */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <History className="w-5 h-5 text-blue-600" />
                  <span>Derniers déclenchements cron</span>
                </CardTitle>
                <CardDescription>Les 5 dernières tentatives du planificateur VM.</CardDescription>
              </CardHeader>
              <CardContent>
                {status.scheduler.runs.length === 0 ? (
                  <p className="text-sm text-gray-500">Aucun déclenchement — la planification est désactivée ou le cron n&apos;a pas encore tourné.</p>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 text-left text-gray-500">
                        <th className="py-2 pr-4 font-medium">Slot</th>
                        <th className="py-2 pr-4 font-medium">Déclenché à</th>
                        <th className="py-2 pr-4 font-medium">Drapeaux</th>
                        <th className="py-2 font-medium">PID</th>
                      </tr>
                    </thead>
                    <tbody>
                      {status.scheduler.runs.map((run, i) => (
                        <tr key={i} className="border-b border-gray-100">
                          <td className="py-2 pr-4 text-gray-800">{run.slot}</td>
                          <td className="py-2 pr-4 text-gray-600">{fmtTime(run.at)}</td>
                          <td className="py-2 pr-4">
                            {run.flags.length > 0 ? run.flags.join(" ") : "—"}
                          </td>
                          <td className="py-2 text-gray-600">{run.pid ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5 text-blue-600" />
                  <span>État de santé</span>
                </CardTitle>
                <CardDescription>Points d&apos;attention consolidés du pipeline.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {alerts.length === 0 ? (
                  <p className="text-sm text-gray-500">Aucun point d&apos;attention.</p>
                ) : (
                  alerts.map((a, i) => (
                    <div
                      key={i}
                      className={`p-3 rounded-md text-sm ${
                        a.severity === "error"
                          ? "bg-red-50 border border-red-200 text-red-800"
                          : a.severity === "warning"
                            ? "bg-amber-50 border border-amber-200 text-amber-800"
                            : "bg-blue-50 border border-blue-200 text-blue-800"
                      }`}
                    >
                      {a.message}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          <div className="text-xs text-gray-400">
            Connecté : {userName} · mis à jour à {lastUpdated?.toLocaleTimeString("fr-FR")} —
            source : API gouvernance :8000 (<code>/pipeline/status</code>), données fictives.
          </div>
        </>
      )}
    </div>
  );
}

function Kpi({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="bg-white p-4 rounded-lg shadow-lg">
      <p className="text-sm font-medium text-gray-600">{label}</p>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
      <p className="mt-1 text-xs text-gray-500">{hint}</p>
    </div>
  );
}

function ZoneCard({
  name,
  zone,
  step,
}: {
  name: string;
  zone?: { status?: string; last_sync?: string | null };
  step?: string;
}) {
  const dot =
    zone?.status === "ok"
      ? "bg-emerald-500"
      : zone?.status === "error"
        ? "bg-red-500"
        : "bg-gray-300";
  const label =
    zone?.status === "ok"
      ? "à jour"
      : zone?.status === "error"
        ? "en erreur"
        : "jamais synchronisée";
  return (
    <div className="flex-1 border border-gray-200 rounded-lg p-4 bg-gray-50">
      <div className="flex items-center gap-2">
        <span className={`w-3 h-3 rounded-full ${dot}`} />
        <p className="font-semibold text-gray-800">{name}</p>
      </div>
      <p className="text-xs text-gray-500 mt-1">
        {zone?.last_sync ? `Dernière synchro : ${fmtRelative(zone.last_sync)}` : "Non synchronisée"}
      </p>
      <p className="text-xs text-gray-500">Statut : {label}</p>
      {step && (
        <p className="text-xs text-gray-400 mt-1">Étape liée : {STEP_LABELS[step] ?? step}</p>
      )}
    </div>
  );
}

function ArrowBetween() {
  return (
    <div className="flex items-center px-1 text-gray-400" aria-hidden>
      <svg width="24" height="12" viewBox="0 0 24 12">
        <path d="M0 6 H20 M16 1 L22 6 L16 11" stroke="currentColor" fill="none" strokeWidth="2" />
      </svg>
    </div>
  );
}

function Node({ state, connector }: { state: string; connector: boolean }) {
  return (
    <div className="flex items-center w-full">
      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${STEP_NODE[state] ?? "bg-gray-200 text-gray-400"}`}>
        {state === "ok" ? "✓" : state === "failed" ? "✗" : ""}
      </div>
      {connector && <div className="h-0.5 flex-1 bg-gray-300" />}
    </div>
  );
}

function PlayStep() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" className="text-blue-600">
      <path d="M8 6 L18 12 L8 18 Z" fill="currentColor" />
      <circle cx="6" cy="6" r="2" fill="currentColor" />
      <circle cx="6" cy="18" r="2" fill="currentColor" />
    </svg>
  );
}

function FreshnessBar({
  name,
  info,
}: {
  name: string;
  info: { tables: number; last_extracted_at: string | null };
}) {
  let tone = "bg-red-500";
  let width = 100;
  if (info.last_extracted_at) {
    const age = Date.now() - new Date(info.last_extracted_at).getTime();
    if (age < 7 * DAY) {
      tone = "bg-emerald-500";
      width = Math.max(10, Math.round(100 - (age / (7 * DAY)) * 90));
    } else if (age < 30 * DAY) {
      tone = "bg-amber-500";
      width = Math.max(10, Math.round(100 - ((age - 7 * DAY) / (23 * DAY)) * 90));
    }
  }
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className="font-medium text-gray-800">{name}</span>
        <span className="text-gray-500">{info.tables} table(s) · {fmtRelative(info.last_extracted_at)}</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 mt-1">
        <div className={`h-2 rounded-full ${tone}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}