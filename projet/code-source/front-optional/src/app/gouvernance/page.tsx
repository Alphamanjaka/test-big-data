"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Scale, ShieldCheck, Users, XCircle } from "lucide-react";
import MockedBanner from "@/components/MockedBanner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CONSENT_PURPOSES,
  ConsentRow,
  getConsent,
  PURPOSE_LABELS,
} from "@/lib/api";

/**
 * Le consentement est managed finalité par finalité : un refus sur une finalité
 * ne vaut pas refus global. Le tableau affiche donc une ligne par couple
 * (patient, finalité) plutôt qu'un statut unique par patient.
 */
export default function GouvernancePage() {
  const [rows, setRows] = useState<ConsentRow[]>([]);
  const [stats, setStats] = useState({ total_consents: 0, granted_count: 0, patients: 0 });
  const [mocked, setMocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | "all">("all");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getConsent();
        if (cancelled) return;
        setRows(res.data);
        setStats(res.stats);
        setMocked(res.mocked);
      } catch (err) {
        if (cancelled) return;
        console.error("Erreur chargement consentements:", err);
        setError("Le service de consentement n'a pas répondu.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(
    () => (selected === "all" ? rows : rows.filter((r) => r.purpose === selected)),
    [rows, selected],
  );

  const granted = stats.total_consents > 0 ? stats.granted_count : 0;
  const taux =
    stats.total_consents > 0
      ? ((granted / stats.total_consents) * 100).toFixed(1)
      : null;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ShieldCheck className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Chargement des consentements...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 space-y-6">
      <MockedBanner mocked={mocked} source="la table des consentements" />

      {error ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-red-700">{error}</p>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Patients concernés</p>
              <p className="text-2xl font-bold text-slate-700">
                {stats.patients.toLocaleString()}
              </p>
            </div>
            <Users className="w-6 h-6 text-gray-500" aria-hidden="true" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Consentements accordés</p>
              <p className="text-2xl font-bold text-emerald-700">
                {granted.toLocaleString()}{" "}
                <span className="text-sm font-normal text-gray-500">
                  / {stats.total_consents.toLocaleString()}
                </span>
              </p>
            </div>
            <CheckCircle2 className="w-6 h-6 text-emerald-600" aria-hidden="true" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Taux d&apos;accord</p>
              <p className="text-2xl font-bold text-slate-700">
                {taux === null ? "n/d" : `${taux} %`}
              </p>
              <p className="mt-1 text-xs text-gray-500">Sur toutes finalités confondues</p>
            </div>
            <Scale className="w-6 h-6 text-gray-500" aria-hidden="true" />
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Consentements par finalité</CardTitle>
          <CardDescription>
            Filtrez sur une finalité pour vérifier qu&apos;un patient peut être
            accordé pour la recherche et refusé pour l&apos;analyse.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex flex-wrap gap-2">
            <FilterButton active={selected === "all"} onClick={() => setSelected("all")}>
              Toutes
            </FilterButton>
            {CONSENT_PURPOSES.map((purpose) => (
              <FilterButton
                key={purpose}
                active={selected === purpose}
                onClick={() => setSelected(purpose)}
              >
                {PURPOSE_LABELS[purpose]}
              </FilterButton>
            ))}
          </div>

          {filtered.length === 0 ? (
            <p className="text-sm text-gray-500">
              Aucun consentement enregistré pour cette finalité.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full border">
                <thead className="bg-gray-100 text-gray-700 text-sm">
                  <tr>
                    <th className="px-4 py-2 border text-left">Patient maître</th>
                    <th className="px-4 py-2 border text-left">Identifiant patient</th>
                    <th className="px-4 py-2 border text-left">Nom</th>
                    <th className="px-4 py-2 border text-left">Finalité</th>
                    <th className="px-4 py-2 border text-center">Décision</th>
                    <th className="px-4 py-2 border text-left">Enregistré le</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((row, index) => (
                    <tr key={`${row.master_patient_id}-${row.purpose}-${index}`} className="hover:bg-gray-50">
                      <td className="px-4 py-2 border font-mono text-sm">{row.master_patient_id}</td>
                      <td className="px-4 py-2 border font-mono text-sm text-gray-500">
                        {row.patient_uuid ?? "n/d"}
                      </td>
                      <td className="px-4 py-2 border">{row.name}</td>
                      <td className="px-4 py-2 border">
                        {PURPOSE_LABELS[row.purpose] ?? row.purpose}
                      </td>
                      <td className="px-4 py-2 border text-center">
                        {row.granted ? (
                          <span className="inline-flex items-center gap-1 text-emerald-700">
                            <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
                            Accordé
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-red-700">
                            <XCircle className="w-4 h-4" aria-hidden="true" />
                            Refusé
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2 border text-sm text-gray-600">{row.recorded_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <p className="mt-4 text-xs text-gray-500">
            Les noms affichés proviennent du jeu de démonstration : ce sont des
            identifiants synthétiques, sans lien avec une personne réelle.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-full border px-3 py-1 text-sm transition-colors ${
        active
          ? "border-blue-600 bg-blue-600 text-white"
          : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
      }`}
    >
      {children}
    </button>
  );
}
