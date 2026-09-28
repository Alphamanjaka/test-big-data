"use client";

import { useEffect, useState } from "react";
import { PlayCircle, CalendarClock, Database } from "lucide-react";
import { toast } from "react-toastify";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getPipelineStatus,
  putPipelineSchedule,
  type PipelineSchedule,
  type PipelineStatus,
} from "@/lib/api";

const FREQUENCY_LABELS: Record<string, string> = {
  daily: "Quotidienne",
  weekly: "Hebdomadaire",
  monthly: "Mensuelle",
};

const MODE_LABELS: Record<string, string> = {
  auto: "Auto (incrémental)",
  since: "Depuis une date",
  full: "Rechargement complet",
};

const WEEKDAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];
const STEP_LABELS: Record<string, string> = {
  ensure_generator_data: "Données générées",
  gen_extract_raw: "Extraction RAW",
  gen_fhir_mapping: "Mapping FHIR",
  create_silver: "SILVER",
  create_gold: "GOLD",
};

interface Props {
  userName: string;
  isAdmin: boolean;
}

const DEFAULT_SCHEDULE: PipelineSchedule = {
  enabled: false,
  frequency: "daily",
  time: "03:00",
  day_of_week: 0,
  day_of_month: 1,
  resume: { mode: "auto", since: null },
};

export default function PipelineClient({ isAdmin }: Props) {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [form, setForm] = useState<PipelineSchedule>(DEFAULT_SCHEDULE);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPipelineStatus();
      setStatus(data);
      setForm({ ...DEFAULT_SCHEDULE, ...data.schedule });
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "API gouvernance (port 8000) injoignable — vérifiez NEXT_PUBLIC_GOVERNANCE_API_URL / clé API."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange = (patch: Partial<PipelineSchedule>) => {
    setForm((prev) => ({ ...prev, ...patch }));
  };

  const handleResumeChange = (patch: Partial<PipelineSchedule["resume"]>) => {
    setForm((prev) => ({ ...prev, resume: { ...prev.resume, ...patch } }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAdmin) return;
    setSaving(true);
    try {
      const saved = await putPipelineSchedule(form);
      setForm({ ...DEFAULT_SCHEDULE, ...saved });
      toast.success("Planification enregistrée — le cron VM la prendra en compte.");
      load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de l'enregistrement");
    } finally {
      setSaving(false);
    }
  };

  const pipeline = status?.pipeline ?? {};
  const steps = pipeline.steps ?? {};
  const badges: Record<string, string> = {
    running: "bg-yellow-100 text-yellow-700",
    ok: "bg-emerald-100 text-emerald-700",
    failed: "bg-red-100 text-red-700",
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <PlayCircle className="w-5 h-5 text-blue-600" />
            <span>Pipeline ELT — planification</span>
          </CardTitle>
          <CardDescription>
            Planification des données fictives RAW → SILVER → GOLD via le cron de la VM.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading && <p className="text-sm text-gray-500">Chargement…</p>}
          {!loading && error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-md text-sm">
              {error}
            </div>
          )}

          {!loading && !error && status && (
            <div className="space-y-6">
              {/* Planification */}
              <form onSubmit={handleSave} className="space-y-4 max-w-xl">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <input
                      type="checkbox"
                      checked={form.enabled}
                      disabled={!isAdmin}
                      onChange={(e) => handleChange({ enabled: e.target.checked })}
                      className="w-4 h-4"
                    />
                    Activer la planification automatique
                  </label>
                  {!isAdmin && (
                    <span className="text-xs text-gray-400">Lecture seule (admin requis pour modifier)</span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fréquence</label>
                    <select
                      value={form.frequency}
                      disabled={!isAdmin}
                      onChange={(e) => handleChange({ frequency: e.target.value as PipelineSchedule["frequency"] })}
                      className="w-full p-2 border border-gray-300 rounded-md disabled:bg-gray-100"
                    >
                      <option value="daily">Quotidienne</option>
                      <option value="weekly">Hebdomadaire</option>
                      <option value="monthly">Mensuelle</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Heure (fuseau VM, UTC+3)
                    </label>
                    <input
                      type="time"
                      value={form.time}
                      disabled={!isAdmin}
                      onChange={(e) => handleChange({ time: e.target.value })}
                      className="w-full p-2 border border-gray-300 rounded-md disabled:bg-gray-100"
                    />
                  </div>
                  {form.frequency === "weekly" && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Jour de la semaine</label>
                      <select
                        value={form.day_of_week}
                        disabled={!isAdmin}
                        onChange={(e) => handleChange({ day_of_week: Number(e.target.value) })}
                        className="w-full p-2 border border-gray-300 rounded-md disabled:bg-gray-100"
                      >
                        {WEEKDAYS.map((d, i) => (
                          <option key={i} value={i}>{d}</option>
                        ))}
                      </select>
                    </div>
                  )}
                  {form.frequency === "monthly" && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Jour du mois</label>
                      <input
                        type="number"
                        min={1}
                        max={31}
                        value={form.day_of_month}
                        disabled={!isAdmin}
                        onChange={(e) => handleChange({ day_of_month: Number(e.target.value) })}
                        className="w-full p-2 border border-gray-300 rounded-md disabled:bg-gray-100"
                      />
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Mode de reprise</label>
                    <select
                      value={form.resume.mode}
                      disabled={!isAdmin}
                      onChange={(e) =>
                        handleResumeChange({ mode: e.target.value as PipelineSchedule["resume"]["mode"] })
                      }
                      className="w-full p-2 border border-gray-300 rounded-md disabled:bg-gray-100"
                    >
                      <option value="auto">Auto (incrémental — aucun retraitement)</option>
                      <option value="since">Depuis une date</option>
                      <option value="full">Rechargement complet</option>
                    </select>
                  </div>
                  {form.resume.mode === "since" && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Date depuis</label>
                      <input
                        type="date"
                        value={form.resume.since ?? ""}
                        disabled={!isAdmin}
                        onChange={(e) => handleResumeChange({ since: e.target.value || null })}
                        className="w-full p-2 border border-gray-300 rounded-md disabled:bg-gray-100"
                      />
                    </div>
                  )}
                </div>

                {isAdmin && (
                  <button
                    type="submit"
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    <CalendarClock className="w-4 h-4" />
                    {saving ? "Enregistrement…" : "Enregistrer la planification"}
                  </button>
                )}
              </form>

              <hr className="border-gray-200" />

              {/* État du dernier run */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">État du dernier run</h3>
                <div className="grid grid-cols-3 gap-3 max-w-2xl">
                  <div className="bg-gray-50 p-3 rounded-md">
                    <p className="text-xs text-gray-500">Statut</p>
                    <p className={`text-sm font-medium ${badges[pipeline.status ?? ""] ?? "bg-gray-100 text-gray-700 inline-block px-2 py-0.5 rounded"}`}>
                      {pipeline.status ?? "aucun run"}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-md">
                    <p className="text-xs text-gray-500">Run id</p>
                    <p className="text-sm font-medium">{pipeline.run_id ?? "—"}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-md">
                    <p className="text-xs text-gray-500">Mode</p>
                    <p className="text-sm font-medium">{pipeline.mode ?? "—"}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 mt-3 max-w-2xl">
                  {Object.entries(STEP_LABELS).map(([key, label]) => {
                    const state = steps[key] ?? "pending";
                    return (
                      <span
                        key={key}
                        className={`text-xs px-2 py-1 rounded ${badges[state] ?? "bg-gray-100 text-gray-500"}`}
                      >
                        {label}: {state}
                      </span>
                    );
                  })}
                </div>
              </div>

              <hr className="border-gray-200" />

              {/* Sources suivies (watermark) */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  Ingestion par empreinte (anti-retraitement)
                </h3>
                {Object.keys(status.sources).length === 0 ? (
                  <p className="text-sm text-gray-500">
                    Aucune source suivie pour l'instant (watermark vide — le premier run planifié
                    initialisera les empreintes).
                  </p>
                ) : (
                  <div className="space-y-2 max-w-2xl">
                    {Object.entries(status.sources).map(([name, info]) => (
                      <div key={name} className="flex justify-between bg-gray-50 p-3 rounded-md text-sm">
                        <span className="font-medium">{name}</span>
                        <span className="text-gray-600">
                          {info.tables} table(s) · dernière extraction {info.last_extracted_at ?? "—"}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="text-xs text-gray-400">
                Dernier déclenchement cron : {status.scheduler.last_launched_slot ?? "jamais"} —{" "}
                prochain run planifié : {status.next_run}
                {status.run_flags.length > 0 ? ` (drapeaux: ${status.run_flags.join(" ")})` : ""}
                {status.schedule_error ? ` — avertissement: ${status.schedule_error}` : ""}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}