"use client";

import { AlertTriangle } from "lucide-react";

/**
 * Bandeau affiché quand les chiffres affichés viennent du jeu de démonstration
 * et non de la zone GOLD. Le backend signale ce repli dans l'enveloppe de
 * réponse (`mocked`), jamais déduit côté interface : c'est la seule façon
 * d'éviter qu'un indicateur de démonstration soit lu comme une mesure réelle.
 */
export default function MockedBanner({
  mocked,
  source = "la zone GOLD",
  className = "",
}: {
  mocked: boolean;
  source?: string;
  className?: string;
}) {
  if (!mocked) return null;

  return (
    <div
      role="status"
      className={`flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 ${className}`}
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" aria-hidden="true" />
      <span>
        <strong className="font-semibold">Données de démonstration.</strong>{" "}
        Les valeurs ci-dessous ne proviennent pas de {source} : ce sont des
        chiffres de substitution, affichés parce que la source n&apos;est pas
        disponible. Ils ne mesurent aucune activité réelle et ne doivent pas être
        repris comme résultats.
      </span>
    </div>
  );
}
