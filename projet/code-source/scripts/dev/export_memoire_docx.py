"""Exporte les chapitres du mémoire (Markdown) vers un document Word (.docx).

Usage :
    python scripts/dev/render_mermaid_figures.py     # une fois : produit les PNG
    python scripts/dev/export_memoire_docx.py [--out documents/memoire_M2_MBDS.docx]

Convertit `chapters/01..09.md` en un unique .docx A4 : page de garde, sommaire,
titres, paragraphes, listes, tableaux, blocs de code, citations, bibliographie et
pagination « Page X / Y ».

Les diagrammes Mermaid sont insérés comme images (`documents/figures/fig-<N>.png`),
produites par `render_mermaid_figures.py`. Le manifeste indique la taille naturelle
de chaque image : la figure est placée dans le texte si elle reste lisible à la
largeur de la colonne, sinon sur une page paysage dédiée, pour que les libellés
restent au moins à 9 points. Si une image manque, l'exporteur conserve le bloc de
code et affiche un avertissement : aucune figure n'est perdue en silence.
La numérotation des figures est lue dans la légende Markdown (Figure N), pas dans
un compteur, pour que le rendu et le texte ne puissent pas diverger.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[4]
CHAPTERS_DIR = ROOT / "chapters"
FIGURES_DIR = ROOT / "documents" / "figures"
MANIFEST = FIGURES_DIR / "manifest.json"
BIBLIOGRAPHY = ROOT / "references" / "bibliographie.md"

# Page de garde : métadonnées du mémoire (à modifier ici, en un seul endroit).
DOC_META = {
    "diplome": "Mémoire de stage — Master 2 MBDS (spécialité Big Data)",
    "session": "Session septembre 2026",
    "titre": "Plateforme Big Data de gestion et de gouvernance des données patients",
    "sous_titre": "Nettoyage, déduplication et contrôle d'accès basé sur le consentement",
    "auteur": "RANOMENJANAHARY Manjaka Alpha",
    "encadrant_pro": "RABEMANOELA Harena",
    "encadrant_ped": "RABENANAHARY Rojo",
    "entreprise": "Madagascar Medical Technology (MMT)",
}

# Mise en page : A4, marges et regles de placement des figures.
A4_PORTRAIT_CM = (21.0, 29.7)
MARGIN_PORTRAIT_CM = 2.5
MARGIN_LANDSCAPE_CM = 1.5
TEXT_WIDTH_PORTRAIT_CM = A4_PORTRAIT_CM[0] - 2 * MARGIN_PORTRAIT_CM
TEXT_WIDTH_LANDSCAPE_CM = A4_PORTRAIT_CM[1] - 2 * MARGIN_LANDSCAPE_CM
MAX_HEIGHT_PORTRAIT_CM = 18.0
MAX_HEIGHT_LANDSCAPE_CM = 15.0
INLINE_MIN_PT = 9.0
DIAGRAM_FONT_PX = 16
PT_PER_CM = 28.35

CAPTION_RE = re.compile(r"^>\s*\*\*Figure\s+(\d+)\b")


def add_runs(paragraph, text: str) -> None:
    """Applique **gras** et `code` inline dans un paragraphe."""
    pattern = re.compile(r"(\*\*.*?\*\*|`[^`]*`)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            paragraph.add_run(text[pos : match.start()])
        token = match.group(1)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        else:
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9)
        pos = match.end()
    if pos < len(text):
        paragraph.add_run(text[pos:])


def parse_table(lines: list[str]) -> str:
    """Supprime la ligne de séparation éventuelle d'un tableau markdown."""
    if len(lines) >= 2 and re.match(r"^\|[\s:\-|]*\|$", lines[1]):
        return "\n".join([lines[0]] + lines[2:])
    return "\n".join(lines)


def add_field(paragraph, instruction: str) -> None:
    """Insère un champ Word calculé (PAGE, NUMPAGES, TOC)."""
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    run_begin = paragraph.add_run()
    run_begin._r.append(begin)
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " {} ".format(instruction)
    run_instr = paragraph.add_run()
    run_instr._r.append(instr)
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run_end = paragraph.add_run()
    run_end._r.append(end)


def add_code_block(doc: Document, code_lines: list[str]) -> None:
    """Bloc de code indenté, police à chasse fixe."""
    for line in code_lines:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Pt(18)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(line)
        run.font.name = "Consolas"
        run.font.size = Pt(8)


def load_manifest() -> dict:
    """Dimensions naturelles des figures, indexées par numéro."""
    if not MANIFEST.exists():
        return {}
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {int(entry["number"]): entry for entry in data.get("figures", [])}


def font_pt(width_cm: float, width_px: int) -> float:
    """Taille de police effective en points pour une largeur d'impression donnée."""
    if not width_px:
        return 0.0
    return width_cm * DIAGRAM_FONT_PX / width_px * PT_PER_CM


def fit_width(text_width_cm: float, max_height_cm: float, width_px: int, height_px: int) -> float:
    """Largeur d'impression tenant dans la colonne sans dépasser la hauteur max."""
    if not width_px or not height_px:
        return text_width_cm
    return min(text_width_cm, max_height_cm * width_px / float(height_px))


def set_page(section, landscape: bool) -> None:
    """Format A4, marges et orientation."""
    width, height = A4_PORTRAIT_CM
    margin = MARGIN_LANDSCAPE_CM if landscape else MARGIN_PORTRAIT_CM
    if landscape:
        width, height = height, width
        section.orientation = WD_ORIENT.LANDSCAPE
    else:
        section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(width)
    section.page_height = Cm(height)
    section.left_margin = Cm(margin)
    section.right_margin = Cm(margin)
    section.top_margin = Cm(margin)
    section.bottom_margin = Cm(margin)


def add_figure_image(doc: Document, image: Path, width_cm: float, caption: str) -> None:
    """Insère l'image centrée, puis sa légende centrée en petit corps."""
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run().add_picture(str(image), width=Cm(width_cm))
    if caption:
        legend = doc.add_paragraph()
        legend.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(legend, caption)
        for run in legend.runs:
            run.italic = True
            run.font.size = Pt(9)


def add_figure(doc: Document, number: int, caption: str, entry) -> None:
    """Insère une figure : dans le texte si lisible, sinon sur une page paysage."""
    image = FIGURES_DIR / "fig-{0}.png".format(number)
    width_px = int(entry.get("width_px", 0)) if entry else 0
    height_px = int(entry.get("height_px", 0)) if entry else 0

    inline_width = fit_width(
        TEXT_WIDTH_PORTRAIT_CM, MAX_HEIGHT_PORTRAIT_CM, width_px, height_px
    )
    if font_pt(inline_width, width_px) >= INLINE_MIN_PT:
        add_figure_image(doc, image, inline_width, caption)
        return

    # Figure trop large pour la colonne : page paysage dédiée, puis retour portrait.
    landscape_width = fit_width(
        TEXT_WIDTH_LANDSCAPE_CM, MAX_HEIGHT_LANDSCAPE_CM, width_px, height_px
    )
    if not width_px:
        print(
            "  [avertissement] figure {0} : dimensions inconnues (manifeste absent ?), "
            "page paysage par défaut".format(number)
        )
    set_page(doc.add_section(WD_SECTION.NEW_PAGE), landscape=True)
    add_figure_image(doc, image, landscape_width, caption)
    set_page(doc.add_section(WD_SECTION.NEW_PAGE), landscape=False)


def add_markdown(doc: Document, md: str, manifest: dict, figure_number: int = 0) -> int:
    """Convertit du Markdown en Word. Retourne le prochain numéro de figure."""
    lines = md.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            code_start = i
            language = stripped[3:].strip()
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                i += 1
            code_lines = lines[code_start + 1 : i]
            if i < n:
                i += 1
            if language != "mermaid":
                add_code_block(doc, code_lines)
                continue

            # Légende éventuelle : ligne(s) « > **Figure N — ...** » après le bloc.
            figure_number += 1
            j = i
            while j < n and not lines[j].strip():
                j += 1
            caption_lines = []
            if j < n and CAPTION_RE.match(lines[j].strip()):
                match = CAPTION_RE.match(lines[j].strip())
                if match:
                    figure_number = int(match.group(1))
                while j < n and lines[j].strip().startswith(">"):
                    caption_lines.append(lines[j].strip())
                    j += 1
            caption = " ".join(item[1:].strip() for item in caption_lines).strip()
            if FIGURES_DIR.joinpath("fig-{0}.png".format(figure_number)).exists():
                add_figure(doc, figure_number, caption, manifest.get(figure_number))
            else:
                print(
                    "  [avertissement] figure {0} : image introuvable -> bloc de code conservé".format(
                        figure_number
                    )
                )
                add_code_block(doc, code_lines)
            i = j
            continue

        if stripped.startswith("|"):
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            table_md = parse_table(table_lines)
            t_rows = [
                [cell.strip() for cell in row.strip("|").split("|")]
                for row in table_md.splitlines()
            ]
            if not t_rows:
                continue
            ncols = max(len(r) for r in t_rows)
            table = doc.add_table(rows=len(t_rows), cols=ncols)
            table.style = "Table Grid"
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for r_idx, row in enumerate(t_rows):
                for c_idx in range(ncols):
                    cell = row[c_idx] if c_idx < len(row) else ""
                    para = table.cell(r_idx, c_idx).paragraphs[0]
                    add_runs(para, cell)
                    if r_idx == 0:
                        for run in para.runs:
                            run.bold = True
            doc.add_paragraph()
            continue

        if stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=1)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=2)
        elif stripped.startswith("### "):
            doc.add_heading(stripped[4:], level=3)
        elif stripped.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            add_runs(p, stripped[2:])
            for run in p.runs:
                if run.text.strip():
                    run.italic = True
        elif re.match(r"^\d+\.\s+", stripped):
            p = doc.add_paragraph()
            add_runs(p, stripped)
            p.paragraph_format.left_indent = Pt(18)
        elif stripped.startswith("- "):
            p = doc.add_paragraph()
            add_runs(p, "• " + stripped[2:])
            p.paragraph_format.left_indent = Pt(18)
        elif re.match(r"^  [^ ]", line):
            # Ligne de continuation indentée de deux espaces (bibliographie).
            p = doc.add_paragraph()
            add_runs(p, stripped)
            p.paragraph_format.left_indent = Pt(30)
        elif stripped == "---":
            p = doc.add_paragraph()
            p.add_run("―" * 40)
            p.paragraph_format.space_after = Pt(6)
        elif stripped == "":
            pass
        else:
            p = doc.add_paragraph()
            add_runs(p, stripped)
        i += 1
    return figure_number


def add_cover(doc: Document) -> None:
    """Page de garde (métadonnées dans DOC_META)."""
    for _ in range(3):
        doc.add_paragraph()
    for text, size, bold in [
        (DOC_META["diplome"], 16, True),
        (DOC_META["session"], 12, False),
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.font.size = Pt(size)
        run.bold = bold
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(DOC_META["titre"])
    run.font.size = Pt(18)
    run.bold = True
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(DOC_META["sous_titre"])
    run.font.size = Pt(12)
    run.italic = True
    for _ in range(2):
        doc.add_paragraph()
    for label, key in [
        ("Présenté par", "auteur"),
        ("Encadrant professionnel", "encadrant_pro"),
        ("Encadrant pédagogique", "encadrant_ped"),
        ("Entreprise d'accueil", "entreprise"),
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        label_run = p.add_run("{0} : ".format(label))
        label_run.font.size = Pt(12)
        value_run = p.add_run(DOC_META[key])
        value_run.font.size = Pt(12)
        value_run.bold = True
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(DOC_META["session"]).font.size = Pt(12)
    doc.add_page_break()


def add_toc(doc: Document) -> None:
    """Sommaire : champ TOC, rempli par le lecteur à l'ouverture du document."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Sommaire")
    run.bold = True
    run.font.size = Pt(16)
    toc = doc.add_paragraph()
    add_field(toc, 'TOC \\o "1-2" \\h \\z \\u')
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(
        "Si le sommaire reste vide : clic droit dessus puis « Mettre à jour les champs »."
    )
    run.italic = True
    run.font.size = Pt(9)
    doc.add_page_break()


def add_page_footer(doc: Document) -> None:
    """Pied de page « Page X / Y », absent de la page de garde."""
    sections = list(doc.sections)
    for index, section in enumerate(sections):
        if index > 0:
            # Les sections suivantes heritent du pied de page de la premiere.
            section.footer.is_linked_to_previous = True
            section.different_first_page_header_footer = False
            continue
        section.different_first_page_header_footer = True
        paragraph = section.footer.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_field(paragraph, "PAGE")
        paragraph.add_run(" / ")
        add_field(paragraph, "NUMPAGES")
        for run in paragraph.runs:
            run.font.size = Pt(9)


def enable_update_fields(doc: Document) -> None:
    """Demande à Word de recalculer les champs (sommaire) à l'ouverture."""
    settings = doc.settings.element
    existing = settings.find(qn("w:updateFields"))
    if existing is None:
        existing = OxmlElement("w:updateFields")
        settings.append(existing)
    existing.set(qn("w:val"), "true")


def build(out_path: Path) -> None:
    doc = Document()
    set_page(doc.sections[0], landscape=False)
    manifest = load_manifest()

    add_cover(doc)
    add_toc(doc)

    figure_number = 0
    for chapter in sorted(CHAPTERS_DIR.glob("0*.md")):
        figure_number = add_markdown(
            doc, chapter.read_text(encoding="utf-8"), manifest, figure_number
        )
        doc.add_page_break()

    if BIBLIOGRAPHY.exists():
        add_markdown(doc, BIBLIOGRAPHY.read_text(encoding="utf-8"), manifest, figure_number)
    else:
        print("  [avertissement] bibliographie absente : {0}".format(BIBLIOGRAPHY))

    add_page_footer(doc)
    enable_update_fields(doc)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    print("DOCX écrit : {0}".format(out_path.resolve()))
    print(
        "Chapitres : {0} · figures : {1} · bibliographie : {2} · sections : {3}".format(
            len(list(CHAPTERS_DIR.glob("0*.md"))),
            figure_number,
            "oui" if BIBLIOGRAPHY.exists() else "non",
            len(doc.sections),
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporte les chapitres vers un .docx.")
    parser.add_argument(
        "--out",
        default=str(ROOT / "documents" / "memoire_M2_MBDS.docx"),
        help="Chemin de sortie du fichier .docx",
    )
    args = parser.parse_args()
    build(Path(args.out))


if __name__ == "__main__":
    main()
