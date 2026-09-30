"use client";

import { useEffect, useState } from "react";
import { CopyCheck, Fingerprint, Layers, Users } from "lucide-react";
import MockedBanner from "@/components/MockedBanner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getDuplicates, GovernanceDuplicates } from "@/lib/api";

/** Méthodes de rapprochement, dans l'ordre du moteur de déduplication. */
const METHOD_LABELS: Record<string, string> = {
  exact: "Exacte",
  probabilistic: "Probabiliste",
};

const METHOD_HINTS: Record<string, string> = {
  exact: "Identifiants identiques (CNI) : fusion certaine.",
  probabilistic:
    "Similarité de noms, dates de naissance et genre sous seuil : fusion justifiée par les scores.",
};

export default function DoublonsPage() {
  const [stats, setStats] = useState<GovernanceDuplicates | null>(null);
  const [mocked, setMocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getDuplicates();
        if (cancelled) return;
        setStats(res.data);
        setMocked(res.mocked);
      } catch (err) {
        if (cancelled) return;
        console.error("Erreur chargement déduplication:", err);
        setError("Le service de déduplication n'a pas répondu.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <CopyCheck className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Chargement des statistiques de déduplication...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 space-y-6">
      <MockedBanner mocked={mocked} source="la table des identités" />

      {error ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-red-700">{error}</p>
          </CardContent>
        </Card>
      ) : null}

      {stats ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <Kpi
              label="Patients en base"
              value={stats.total_patients.toLocaleString()}
              icon={Users}
              tone="text-slate-700"
              hint="Enregistrements de la table maître avant rapprochement."
            />
            <Kpi
              label="Patients maîtres"
              value={stats.total_masters.toLocaleString()}
              icon={Fingerprint}
              tone="text-blue-700"
              hint="Identifiants de référence après fusion."
            />
            <Kpi
              label="Doublons résolus"
              value={stats.duplicates.toLocaleString()}
              icon={CopyCheck}
              tone="text-emerald-700"
              hint="Enregistrements rattachés à un patient maître."
            />
            <Kpi
              label="Taux de doublon"
              value={`${stats.duplicate_rate} %`}
              icon={Layers}
              tone="text-amber-700"
              hint="Part des enregistrements fusionnés."
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Répartition par méthode de rapprochement</CardTitle>
              <CardDescription>
                Chaque patient maître est justifié par au moins une correspondance
                : une fusion sans match explicable n&apos;est jamais produite par le moteur.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <table className="min-w-full border">
                <thead className="bg-gray-100 text-gray-700 text-sm">
                  <tr>
                    <th className="px-4 py-2 border text-left">Méthode</th>
                    <th className="px-4 py-2 border text-right">Correspondances</th>
                    <th className="px-4 py-2 border text-right">Part</th>
                    <th className="px-4 py-2 border text-left">Justification</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(stats.by_method).map(([method, count]) => {
                    const total = Object.values(stats.by_method).reduce((s, v) => s + v, 0);
                    const part = total > 0 ? ((count / total) * 100).toFixed(1) : "0,0";
                    return (
                      <tr key={method} className="hover:bg-gray-50">
                        <td className="px-4 py-2 border font-medium">
                          {METHOD_LABELS[method] ?? method}
                        </td>
                        <td className="px-4 py-2 border text-right">{count.toLocaleString()}</td>
                        <td className="px-4 py-2 border text-right">{part} %</td>
                        <td className="px-4 py-2 border text-sm text-gray-600">
                          {METHOD_HINTS[method] ?? "Méthode non documentée."}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <p className="mt-4 text-xs text-gray-500">
                Le taux de doublon est recalculé par l&apos;API
                (`douplicates / total_patients`) : un écart avec la somme des
                correspondances signalerait des fusions non attribuées à une méthode.
              </p>
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

function Kpi({
  label,
  value,
  icon: Icon,
  tone,
  hint,
}: {
  label: string;
  value: string;
  icon: typeof Users;
  tone: string;
  hint: string;
}) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{label}</p>
          <p className={`text-2xl font-bold ${tone}`}>{value}</p>
          <p className="mt-1 text-xs text-gray-500">{hint}</p>
        </div>
        <div className="p-3 rounded-full bg-gray-100">
          <Icon className="w-6 h-6 text-gray-600" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}
