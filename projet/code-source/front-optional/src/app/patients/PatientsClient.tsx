"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Users, Search, ChevronLeft, ChevronRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listPatients, type PatientSummary } from "@/lib/api";

const GENDER_LABELS: Record<string, string> = {
  M: "Masculin",
  F: "Féminin",
  "": "Non renseigné",
};

interface Props {
  userName: string;
}

const PAGE_SIZE = 20;

export default function PatientsClient({ userName }: Props) {
  const [items, setItems] = useState<PatientSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (term: string, pageNumber: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await listPatients({
        search: term || undefined,
        page: pageNumber,
        pageSize: PAGE_SIZE,
      });
      setItems(data.items);
      setTotal(data.total);
      setPage(data.page);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "API gouvernance (port 8000) injoignable — vérifiez NEXT_PUBLIC_GOVERNANCE_API_URL / clé API."
      );
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Recherche différée : 350 ms après la frappe, retour à la 1ʳᵉ page.
    const timer = setTimeout(() => load(search, 1), 350);
    return () => clearTimeout(timer);
  }, [search, load]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-blue-600" />
            <span>Patients</span>
          </CardTitle>
          <CardDescription>
            Liste des patients masters ayant consenti à la finalité
            «&nbsp;Accès API&nbsp;» — lecture seule, données fictives.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative max-w-md mb-4">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher par nom, CIN ou identifiant…"
              className="w-full p-2 pl-9 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {loading && <p className="text-sm text-gray-500">Chargement…</p>}

          {!loading && error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-md text-sm">
              {error}
            </div>
          )}

          {!loading && !error && total === 0 && (
            <p className="text-sm text-gray-500">
              Aucun patient trouvé. Un patient apparaît ici uniquement s'il a
              consenti à la finalité déclarée&nbsp;: les autres restent silencieux.
            </p>
          )}

          {!loading && !error && items.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="py-2 pr-4 font-medium">Nom complet</th>
                    <th className="py-2 pr-4 font-medium">Naissance</th>
                    <th className="py-2 pr-4 font-medium">CIN</th>
                    <th className="py-2 pr-4 font-medium">Ville de naissance</th>
                    <th className="py-2 pr-4 font-medium">Genre</th>
                    <th className="py-2 font-medium">Dossier</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((patient) => (
                    <tr key={patient.master_patient_id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 pr-4">
                        <span className="font-medium text-gray-800">{patient.full_name}</span>
                        <span className="text-gray-400 text-xs block">
                          {patient.master_patient_id}
                        </span>
                      </td>
                      <td className="py-2 pr-4 text-gray-600">{patient.birth_date ?? "—"}</td>
                      <td className="py-2 pr-4 text-gray-600">{patient.cin ?? "—"}</td>
                      <td className="py-2 pr-4 text-gray-600">{patient.birth_city ?? "—"}</td>
                      <td className="py-2 pr-4 text-gray-600">
                        {GENDER_LABELS[patient.gender ?? ""] ?? "—"}
                      </td>
                      <td className="py-2">
                        <Link
                          href={`/patients/${encodeURIComponent(patient.master_patient_id)}`}
                          className="text-blue-600 hover:underline"
                        >
                          Ouvrir le dossier
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="flex items-center justify-between mt-4">
                <p className="text-xs text-gray-500">
                  {total} patient(s) · page {page} / {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => load(search, Math.max(1, page - 1))}
                    disabled={page <= 1 || loading}
                    className="flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm disabled:opacity-40 hover:bg-gray-50"
                  >
                    <ChevronLeft className="w-4 h-4" /> Précédent
                  </button>
                  <button
                    onClick={() => load(search, Math.min(totalPages, page + 1))}
                    disabled={page >= totalPages || loading}
                    className="flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm disabled:opacity-40 hover:bg-gray-50"
                  >
                    Suivant <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="text-xs text-gray-400 mt-4">
            Connecté : {userName} — la liste est fournie par l'API gouvernance
            (finalité `api_access`, contrôle de consentement appliqué côté API,
            refus journalisés dans l'audit).
          </div>
        </CardContent>
      </Card>
    </div>
  );
}