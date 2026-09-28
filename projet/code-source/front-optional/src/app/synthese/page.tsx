"use client";

import { useEffect, useState } from "react";
import { Activity, CopyCheck, Layers, ShieldCheck } from "lucide-react";
import MockedBanner from "@/components/MockedBanner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getConsent, getDuplicates, GovernanceDuplicates } from "@/lib/api";

interface ConsentTotals {
  total_consents: number;
  granted_count: number;
  patients: number;
}

const PIPELINES = [
  { layer: "RAW", role: "Données sources conservées telles quelles, sans transformation." },
  { layer: "SILVER", role: "Données normalisées, nettoyées et validées." },
  { layer: "GOLD", role: "Données de référence, dédupliquées et prêtes à l'usage analytique." },
];

/**
 * Page de synthèse : elle rassemble les deux volets métier de la plateforme —
 * qualité d'identité (déduplication) et consentement purpose-by-purpose —
 * pour montrer qu'ils partagent la même source et le même indicateur de
 * fiabilité. Aucune valeur n'est recalculée côté interface.
 */
export default function SynthesePage() {
  const [dups, setDups] = useState<GovernanceDuplicates | null>(null);
  const [consent, setConsent] = useState<ConsentTotals | null>(null);
  const [mocked, setMocked] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const [dupsRes, consentRes] = await Promise.all([
          getDuplicates(),
          getConsent(),
        ]);

        if (cancelled) return;
        setDups(dupsRes.data);
        setConsent(consentRes.stats);
        setMocked(dupsRes.mocked || consentRes.mocked);
      } catch (err) {
        console.error("Erreur chargement synthèse:", err);
        if (!cancelled) {
          setDups(null);
          setConsent(null);
        }
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
          <Activity className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Chargement de la synthèse...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 space-y-6">
      <MockedBanner mocked={mocked} source="la zone GOLD" />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CopyCheck className="w-4 h-4 text-emerald-600" aria-hidden="true" />
              Qualité d&apos;identité
            </CardTitle>
            <CardDescription>Résultat de la déduplication exacte et probabiliste.</CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-600">Patients maîtresses</dt>
                <dd className="font-semibold">
                  {dups ? dups.total_masters.toLocaleString() : "n/d"}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Doublons résolus</dt>
                <dd className="font-semibold">
                  {dups ? dups.duplicates.toLocaleString() : "n/d"}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Taux de doublon</dt>
                <dd className="font-semibold">
                  {dups ? `${dups.duplicate_rate} %` : "n/d"}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ShieldCheck className="w-4 h-4 text-amber-600" aria-hidden="true" />
              Consentement
            </CardTitle>
            <CardDescription>Décisions enregistrées, finalité par finalité.</CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-600">Patients concernés</dt>
                <dd className="font-semibold">
                  {consent ? consent.patients.toLocaleString() : "n/d"}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Accords</dt>
                <dd className="font-semibold">
                  {consent
                    ? `${consent.granted_count} / ${consent.total_consents}`
                    : "n/d"}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Refus</dt>
                <dd className="font-semibold">
                  {consent ? (consent.total_consents - consent.granted_count).toLocaleString() : "n/d"}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Chaîne de traitement</CardTitle>
          <CardDescription>
            La qualité d&apos;identité et le consentement lisent la même zone GOLD :
            RAW et SILVER ne sont jamais exposées à l&apos;interface.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ol className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {PIPELINES.map((step) => (
              <li key={step.layer} className="rounded-lg border border-gray-200 bg-white p-4">
                <span className="inline-block rounded bg-gray-900 px-2 py-0.5 text-xs font-semibold text-white">
                  {step.layer}
                </span>
                <p className="mt-2 text-sm text-gray-700">{step.role}</p>
              </li>
            ))}
          </ol>
          <p className="mt-4 text-xs text-gray-500">
            Les statistiques affichées proviennent des endpoints de gouvernance
            (`/api/governance/duplicates`, `/api/governance/consent`) qui
            déclarent eux-mêmes le repli vers le jeu de démonstration.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}