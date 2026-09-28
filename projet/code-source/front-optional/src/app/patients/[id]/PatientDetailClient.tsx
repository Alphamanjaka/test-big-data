"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, FileText, GitMerge, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiError,
  CONSENT_PURPOSES,
  getPatient,
  PURPOSE_LABELS,
  type IdentityMapEntry,
  type PatientConsentRow,
  type PatientDetail,
} from "@/lib/api";

const GENDER_LABELS: Record<string, string> = {
  M: "Masculin",
  F: "Féminin",
  "": "Non renseigné",
};

const METHOD_BADGES: Record<string, string> = {
  new_master: "bg-blue-100 text-blue-700",
  exact: "bg-emerald-100 text-emerald-700",
  probabilistic: "bg-amber-100 text-amber-700",
};

const METHOD_LABELS: Record<string, string> = {
  new_master: "Nouveau master",
  exact: "Correspondance exacte",
  probabilistic: "Correspondance probable",
};

const PURPOSE_BADGES: Record<string, string> = {
  api_access: "bg-blue-100 text-blue-700",
  research: "bg-emerald-100 text-emerald-700",
  analytics: "bg-purple-100 text-purple-700",
};

interface Props {
  masterPatientId: string;
}

export default function PatientDetailClient({ masterPatientId }: Props) {
  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [denied, setDenied] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      setDenied(null);
      setNotFound(false);
      try {
        const data = await getPatient(masterPatientId);
        if (!cancelled) setPatient(data);
      } catch (e) {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 403) {
          setDenied(e.message);
        } else if (e instanceof ApiError && e.status === 404) {
          setNotFound(true);
        } else {
          setError(e instanceof Error ? e.message : "Erreur de chargement du dossier.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [masterPatientId]);

  const latestConsent = (
    purpose: string,
    consents: PatientConsentRow[]
  ): PatientConsentRow | undefined => consents.find((c) => c.purpose === purpose);

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      <Link
        href="/patients"
        className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
      >
        <ArrowLeft className="w-4 h-4" /> Retour à la liste des patients
      </Link>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-blue-600" />
            <span>Dossier du patient</span>
          </CardTitle>
          <CardDescription>
            Identité master, correspondances de déduplication et consentements
            purpose-by-purpose — données fictives, lecture seule.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading && <p className="text-sm text-gray-500">Chargement…</p>}

          {!loading && denied && (
            <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-md text-sm">
              <ShieldCheck className="inline w-4 h-4 mr-2" />
              Consentement non accordé : {denied}. Le refus a été journalisé dans
              l'audit d'accès de la plateforme.
            </div>
          )}

          {!loading && notFound && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-md text-sm">
              Patient master introuvable ({masterPatientId}).
            </div>
          )}

          {!loading && error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-md text-sm">
              {error}
            </div>
          )}

          {!loading && !denied && !notFound && !error && patient && (
            <div className="space-y-6">
              {/* Identité */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Nom complet</p>
                  <p className="text-lg font-semibold text-gray-800">{patient.full_name}</p>
                  <p className="text-xs text-gray-400">{patient.master_patient_id}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Naissance</p>
                  <p className="text-sm font-medium">{patient.birth_date ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Genre</p>
                  <p className="text-sm font-medium">
                    {GENDER_LABELS[patient.gender ?? ""] ?? "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">CIN</p>
                  <p className="text-sm font-medium">{patient.cin ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Ville de naissance</p>
                  <p className="text-sm font-medium">{patient.birth_city ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Adresse</p>
                  <p className="text-sm font-medium">{patient.address ?? "—"}</p>
                </div>
              </div>

              <hr className="border-gray-200" />

              {/* Correspondances (identity map) */}
              <div>
                <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-800 mb-3">
                  <GitMerge className="w-4 h-4" />
                  Correspondances de déduplication
                </h3>
                {patient.identity_map.length === 0 ? (
                  <p className="text-sm text-gray-500">Aucune correspondance enregistrée.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 text-left text-gray-500">
                          <th className="py-2 pr-4 font-medium">Source</th>
                          <th className="py-2 pr-4 font-medium">Identifiant source</th>
                          <th className="py-2 pr-4 font-medium">Méthode</th>
                          <th className="py-2 font-medium">Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {patient.identity_map.map((entry: IdentityMapEntry) => (
                          <tr key={`${entry.source_system}-${entry.source_patient_id}`}
                              className="border-b border-gray-100">
                            <td className="py-2 pr-4 text-gray-800">{entry.source_system}</td>
                            <td className="py-2 pr-4 text-gray-600">{entry.source_patient_id}</td>
                            <td className="py-2 pr-4">
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${METHOD_BADGES[entry.match_method] ?? "bg-gray-100 text-gray-600"}`}
                              >
                                {METHOD_LABELS[entry.match_method] ?? entry.match_method}
                              </span>
                            </td>
                            <td className="py-2 text-gray-600">
                              {(entry.match_score * 100).toFixed(1)} %
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              <hr className="border-gray-200" />

              {/* Consentements par finalité */}
              <div>
                <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-800 mb-3">
                  <ShieldCheck className="w-4 h-4" />
                  Consentements par finalité
                </h3>
                <div className="flex flex-wrap gap-2">
                  {CONSENT_PURPOSES.map((purpose) => {
                    const consent = latestConsent(purpose, patient.consents);
                    return (
                      <span
                        key={purpose}
                        className={`text-xs px-2 py-1 rounded ${
                          consent?.granted
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {PURPOSE_LABELS[purpose]} : {consent && !consent.granted ? "refusé" : consent?.granted ? "accordé" : "non renseigné"}
                      </span>
                    );
                  })}
                </div>
                <p className="text-xs text-gray-500 mt-3">
                  Dernier avis de chaque finalité (l'historique complet est conservé dans la
                  table `consent`). Le dossier n'est consultable que pour une finalité accordée.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}