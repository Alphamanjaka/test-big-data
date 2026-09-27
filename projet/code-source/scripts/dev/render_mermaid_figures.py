"""Rend les diagrammes Mermaid du mémoire en images PNG.

Usage :
    python scripts/dev/render_mermaid_figures.py [--scale 3]

Lecture : les blocs mermaid des chapitres sont la source unique de vérité. Le
numéro de figure est lu dans la légende qui suit le bloc (une ligne de la forme
« > **Figure N — ...** ») ; en son absence, il est attribué dans l'ordre de lecture.

Rendu : deux passes par diagramme. La première rend un SVG avec une fenêtre très
large pour mesurer la taille naturelle (une fenêtre trop étroite tronque le
diagramme). La seconde produit le PNG, dans la fenêtre mesurée, avec la
configuration la plus lisible : les diagrammes très allongés (plus de 5 fois plus
larges que hauts) voient leurs libellés resserrés.

mermaid-cli est appelé via npx : rien n'est installé dans le dépôt (aucun
node_modules). Un fichier de configuration puppeteer pointant vers le Chrome ou
l'Edge du poste est généré à la volée : aucun Chromium n'est téléchargé.

Sorties : documents/figures/fig-<N>.png et documents/figures/manifest.json
(dimensions en pixels, configuration utilisée), lu par l'exporteur DOCX pour
décider de la taille et de l'orientation de la page qui accueille la figure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[4]
CHAPTERS_DIR = ROOT / "chapters"
FIGURES_DIR = ROOT / "documents" / "figures"
MANIFEST = FIGURES_DIR / "manifest.json"

FENCE = chr(96) * 3
CAPTION_RE = re.compile(r"^>\s*\*\*Figure\s+(\d+)\b")
MERMAID_CLI = "@mermaid-js/mermaid-cli@11"
FONT_PX = 16  # taille de police Mermaid par défaut, sert au calcul de lisibilité
WIDE_RATIO = 5.0  # au-dela de ce rapport largeur/hauteur, on resserre les libelles
VIEWPORT_MEASURE = 6000  # fenetre de mesure : largement au-dessus de toute largeur
VIEWPORT_MARGIN = 300  # marge de securite pour la fenetre de rendu finale

CONFIGS = {
    "compact": {
        "wrappingWidth": 200,
        "nodeSpacing": 30,
        "rankSpacing": 40,
        "padding": 8,
    },
    "serre": {
        "wrappingWidth": 150,
        "nodeSpacing": 20,
        "rankSpacing": 25,
        "padding": 6,
    },
}

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def find_browser() -> Optional[str]:
    """Retourne un navigateur utilisable par puppeteer, ou None."""
    override = os.environ.get("MERMAID_BROWSER")
    if override:
        return override if Path(override).exists() else None
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    for name in ("chrome", "google-chrome", "chromium", "chrome.exe", "msedge.exe"):
        found = shutil.which(name)
        if found:
            return found
    return None


def iter_diagrams() -> Iterator[Tuple[Path, int, int, List[str]]]:
    """Yield (chapitre, numéro de ligne, numéro de figure, lignes mermaid)."""
    counter = 0
    for chapter in sorted(CHAPTERS_DIR.glob("0*.md")):
        lines = chapter.read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith(FENCE):
                language = lines[i].strip()[3:].strip()
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith(FENCE):
                    j += 1
                if language == "mermaid":
                    counter += 1
                    number = counter
                    k = j + 1
                    while k < len(lines) and not lines[k].strip():
                        k += 1
                    if k < len(lines):
                        match = CAPTION_RE.match(lines[k].strip())
                        if match:
                            number = int(match.group(1))
                    yield chapter, i + 1, number, lines[i + 1 : j]
                i = j + 1
            else:
                i += 1


def write_puppeteer_config(directory: Path, browser: Optional[str]) -> Path:
    """Ecrit la configuration puppeteer (navigateur du poste, pas de download)."""
    config = {"args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if browser:
        config["executablePath"] = browser
    path = directory / "puppeteer.json"
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def write_mermaid_config(directory: Path, name: str) -> Path:
    """Ecrit la configuration mermaid-cli (theme + espacement des noeuds)."""
    path = directory / "mermaid-{0}.json".format(name)
    config = {
        "theme": "neutral",
        "themeVariables": {"fontSize": "{0}px".format(FONT_PX)},
        "flowchart": dict(CONFIGS[name]),
    }
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def call_mermaid(
    npx: str,
    mmd: Path,
    out: Path,
    config: Path,
    browser: Path,
    width: int,
    scale: int,
) -> Tuple[bool, str]:
    done = subprocess.run(
        [
            npx, "-y", MERMAID_CLI,
            "-i", str(mmd),
            "-o", str(out),
            "-p", str(browser),
            "-c", str(config),
            "-b", "white",
            "-w", str(width),
            "-s", str(scale),
        ],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        return False, (done.stderr or done.stdout or "erreur inconnue").strip()[-300:]
    return True, ""


def natural_size(svg: Path) -> Tuple[int, int]:
    """Lit la taille naturelle du diagramme dans le viewBox du SVG."""
    head = svg.read_text(encoding="utf-8")[:2000]
    view = re.search(r'viewBox="[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)"', head)
    if not view:
        return 0, 0
    return int(round(float(view.group(1)))), int(round(float(view.group(2))))


def readable(width_cm: float, width_px: int) -> float:
    """Taille de police effective, en points, pour une largeur d'impression donnee."""
    if width_px <= 0:
        return 0.0
    return width_cm * FONT_PX / width_px * 28.35


def main() -> int:
    parser = argparse.ArgumentParser(description="Rend les diagrammes Mermaid en PNG.")
    parser.add_argument("--scale", type=int, default=3, help="facteur de mise a l'echelle")
    args = parser.parse_args()

    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        print("ERREUR : npx est introuvable (Node.js requis).", file=sys.stderr)
        return 2

    browser_path = find_browser()
    diagrams = list(iter_diagrams())
    if not diagrams:
        print("Aucun diagramme Mermaid trouvé dans {0}".format(CHAPTERS_DIR))
        return 1

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    print("Diagrammes trouvés : {0}".format(len(diagrams)))
    print(
        "Navigateur : {0}".format(
            browser_path or "bundled (Chromium sera téléchargé)"
        )
    )
    print(
        "Moteur : mermaid-cli {0} via npx · échelle {1}\n".format(
            MERMAID_CLI, args.scale
        )
    )

    failures = 0
    entries = []
    with tempfile.TemporaryDirectory(prefix="mermaid_") as tmp:
        workdir = Path(tmp)
        puppeteer = write_puppeteer_config(workdir, browser_path)
        configs = {name: write_mermaid_config(workdir, name) for name in CONFIGS}

        for chapter, line, number, source in diagrams:
            stem = workdir / "fig{0}".format(number)
            mmd = stem.with_suffix(".mmd")
            mmd.write_text("\n".join(source) + "\n", encoding="utf-8")

            def measure(config_name):
                svg = workdir / "measure-{0}.svg".format(number)
                done, reason = call_mermaid(
                    npx, mmd, svg, configs[config_name], puppeteer, VIEWPORT_MEASURE, 1
                )
                if not done:
                    return 0, 0, reason
                width, height = natural_size(svg)
                if width <= 0 or height <= 0:
                    return 0, 0, "taille naturelle illisible"
                return width, height, ""

            # passe 1 : mesure dans la configuration la plus serrée, qui sert de
            # référence au choix ; les diagrammes courts sont remesurés ensuite.
            width_px, height_px, reason = measure("serre")
            if not width_px:
                print(
                    "  ECHEC figure {0}  {1}:{2}  {3}".format(
                        number, chapter.name, line, reason
                    )
                )
                failures += 1
                continue
            name = "serre" if width_px / float(height_px) > WIDE_RATIO else "compact"
            if name != "serre":
                width_px, height_px, reason = measure(name)
                if not width_px:
                    print(
                        "  ECHEC figure {0}  {1}:{2}  {3}".format(
                            number, chapter.name, line, reason
                        )
                    )
                    failures += 1
                    continue
            target = FIGURES_DIR / "fig-{0}.png".format(number)
            viewport = width_px + VIEWPORT_MARGIN
            ok, reason = call_mermaid(
                npx, mmd, target, configs[name], puppeteer, viewport, args.scale
            )
            if not ok or not target.exists() or target.stat().st_size < 1024:
                print(
                    "  ECHEC figure {0}  {1}".format(number, reason or "image absente")
                )
                failures += 1
                continue

            entries.append(
                {
                    "number": number,
                    "file": target.name,
                    "source": "{0}:{1}".format(chapter.name, line),
                    "config": name,
                    "width_px": width_px,
                    "height_px": height_px,
                    "pt_portrait_16cm": round(readable(16.0, width_px), 1),
                    "pt_paysage_26cm": round(readable(26.7, width_px), 1),
                }
            )
            print(
                "  OK   figure {0}  {1}  {2}x{3} px  config {4}  {5}  {6} Ko".format(
                    number,
                    chapter.name,
                    width_px,
                    height_px,
                    name,
                    "{0:.1f} pt à 16 cm / {1:.1f} pt en paysage".format(
                        readable(16.0, width_px), readable(26.7, width_px)
                    ),
                    target.stat().st_size // 1024,
                )
            )

    manifest = {"font_px": FONT_PX, "figures": entries}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("\n{0} image(s) écrite(s) dans {1}".format(len(entries), FIGURES_DIR))
    print("Manifeste : {0}".format(MANIFEST))
    if failures:
        print(
            "{0} échec(s) : le DOCX conservera le bloc de code pour ces figures.".format(
                failures
            )
        )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
