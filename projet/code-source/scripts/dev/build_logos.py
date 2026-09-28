"""Normalise les logos d'outils (documents/icon/) en PNG homogènes pour le rapport.

Usage :
    python scripts/dev/build_logos.py

Les logos d'origine ont des formats (png, jpg, webp, avif, svg) et des proportions très
différents. Chacun est rendu par le Chrome ou l'Edge du poste (headless) dans un cadre
identique de 400 × 140 px CSS, centré et contenu sans déformation, à l'échelle 3 : le
tableau des outils les affiche tous à la même hauteur. Les icônes monochromes de
Simple Icons (CC0) sont colorées avec la couleur de marque officielle.

Sortie : documents/figures/logos/<id>.png, lus par build_rapport_stage_docx.py
(syntaxe `logo:<id>` dans une cellule de tableau).
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from render_html_figures import find_browser

ROOT = Path(__file__).resolve().parents[4]
ICON_DIR = ROOT / "documents" / "icon"
OUT_DIR = ROOT / "documents" / "figures" / "logos"
BOX_W, BOX_H, SCALE = 400, 140, 3

# id -> (fichier source dans documents/icon, couleur de marque pour une icône monochrome)
# Agrandissement facultatif (ZOOM) pour les images livrées avec de larges marges blanches.
LOGOS = {
    "vscode":     ("vscode.svg", "#007ACC"),
    "python":     ("pythoned.png", None),
    "nodejs":     ("nodejs.svg", "#5FA04E"),
    "git":        ("git.svg", "#F03C2E"),
    "vagrant":    ("vagrant-logo.webp", None),
    "virtualbox": ("virtualbox.svg", "#2F61B4"),
    "ubuntu":     ("ubuntu.svg", "#E95420"),
    "laragon":    ("laragon.svg", "#0E83CD"),
    "hadoop":     ("Hadoop_logo.svg.png", None),
    "hive":       ("Apache_Hive_logo.svg.png", None),
    "spark":      ("Apache_Spark_logo.svg.png", None),
    "openjdk":    ("openjdk.svg", "#437291"),
    "postgresql": ("postgresql.png", None),
    "pandas":     ("pandas.svg", "#150458"),
    "rapidfuzz":  ("rapidfuzz.svg", None),
    "fhir":       ("hl7_fhir.png", None),
    "fastapi":    ("fastapi.svg", "#009688"),
    "flask":      ("thumbnail.avif", None),
    "nextjs":     ("nextjs-logo.png", None),
    "tailwind":   ("tailwindcss-logo.png", None),
    "d3":         ("Logo_D3.svg.png", None),
    "typescript": ("typescript.webp", None),
    "pytest":     ("pytest.svg", "#0A9EDC"),
    "mermaid":    ("mermaid.svg", "#FF3670"),
}


ZOOM = {"flask": 1.7, "tailwind": 2.1, "fhir": 1.5, "postgresql": 1.25, "typescript": 1.5}


def logo_markup(source: Path, color: str | None) -> str:
    if color and source.suffix == ".svg":
        svg = source.read_text(encoding="utf-8")
        svg = re.sub(r"<title>.*?</title>", "", svg)
        svg = svg.replace("<svg ", f'<svg fill="{color}" ', 1)
        return svg
    return f'<img src="{source.resolve().as_uri()}">'


def page(markup: str, zoom: float = 1.0) -> str:
    return f"""<!doctype html><meta charset="utf-8"><style>
html, body {{ margin: 0; width: {BOX_W}px; height: {BOX_H}px; background: #fff; }}
body {{ display: flex; align-items: center; justify-content: center; }}
img, svg {{ max-width: {BOX_W - 16}px; max-height: {BOX_H - 16}px; object-fit: contain; }}
svg {{ height: {BOX_H - 24}px; width: auto; }}
img {{ transform: scale({zoom}); }}
</style>{markup}"""


def main():
    browser = find_browser()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing = []
    with tempfile.TemporaryDirectory() as tmp:
        for key, (name, color) in LOGOS.items():
            source = ICON_DIR / name
            if not source.exists():
                missing.append(name)
                continue
            html = Path(tmp) / f"{key}.html"
            html.write_text(page(logo_markup(source, color), ZOOM.get(key, 1.0)), encoding="utf-8")
            out = OUT_DIR / f"{key}.png"
            subprocess.run([
                browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--default-background-color=ffffffff", f"--force-device-scale-factor={SCALE}",
                f"--window-size={BOX_W},{BOX_H}", f"--screenshot={out}", html.as_uri(),
            ], check=True, capture_output=True, timeout=120)
            print(f"{key:<11} <- {name}")
    if missing:
        raise SystemExit("Logos introuvables dans documents/icon : " + ", ".join(missing))


if __name__ == "__main__":
    main()
