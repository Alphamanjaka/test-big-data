"""Rend les figures dessinées en HTML/CSS/SVG (documents/figures/src/*.html) en PNG.

Usage :
    python scripts/dev/render_html_figures.py [--scale 2] [nom ...]

Chaque source déclare sa taille dans sa feuille de style (`html, body { width: …px;
height: …px; }`) ; la capture est faite par le Chrome ou l'Edge du poste en mode
headless, à l'échelle demandée (2 par défaut, soit une image nette à 16 cm imprimés).
Rien n'est installé ni téléchargé. Sortie : documents/figures/<nom>.png.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC_DIR = ROOT / "documents" / "figures" / "src"
OUT_DIR = ROOT / "documents" / "figures"
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]
SIZE = re.compile(r"html,\s*body\s*\{[^}]*?width:\s*(\d+)px;[^}]*?height:\s*(\d+)px", re.S)


def find_browser() -> str:
    for candidate in BROWSERS:
        if Path(candidate).exists():
            return candidate
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("Aucun navigateur Chrome/Edge trouvé pour le rendu headless.")


def render(browser: str, src: Path, scale: float) -> Path:
    m = SIZE.search(src.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit(f"{src.name} : taille « html, body {{ width; height }} » introuvable.")
    width, height = m.groups()
    out = OUT_DIR / f"{src.stem}.png"
    subprocess.run([
        browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--default-background-color=ffffffff",
        f"--force-device-scale-factor={scale}",
        f"--window-size={width},{height}",
        f"--screenshot={out}",
        src.resolve().as_uri(),
    ], check=True, capture_output=True, timeout=120)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*", help="noms des sources sans extension (défaut : toutes)")
    ap.add_argument("--scale", type=float, default=2.0)
    args = ap.parse_args(argv)
    sources = sorted(SRC_DIR.glob("*.html"))
    if args.names:
        sources = [s for s in sources if s.stem in args.names]
    if not sources:
        sys.exit("Aucune source HTML à rendre.")
    browser = find_browser()
    for src in sources:
        out = render(browser, src, args.scale)
        print(f"{src.name} -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
