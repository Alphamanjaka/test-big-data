"""Exporte les chapitres du mémoire (Markdown) vers un document Word (.docx).

Usage :
    python scripts/dev/render_mermaid_figures.py     # une fois : produit les PNG
    python scripts/dev/export_memoire_docx.py [--out documents/memoire_M2_MBDS.docx]

Convertit `chapters/01..09.md` en un unique .docx A4 : pièce liminaire (page de garde,
résumé, abstract, sommaire, listes des tableaux et figures, acronymes), titres,
paragraphes, listes, tableaux, blocs de code, citations, bibliographie et pagination.

La pièce liminaire est numérotée en chiffres romains et le corps repart à 1, comme dans
le modèle de l'établissement. Les listes des tableaux et des figures sont recopiées
depuis les légendes des chapitres : une liste vide est omise plutôt qu'affichée, et
aucune numérotation n'est recomptée à l'export.

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
# Le libellé du diplôme reprend celui de la page de garde de référence, à l'identique :
# toute reformulation serait un écart de forme par rapport au modèle de l'établissement.
DOC_META = {
    "mention": "MASTER de SCIENCES, TECHNOLOGIES, SANTE, mention INFORMATIQUE",
    "specialite": (
        "Spécialité MOBIQUITE, BASES DE DONNEES ET INTEGRATION DE SYSTÈMES (MBDS)"
    ),
    "mois": "Octobre",
    "annee": "2026",
    "titre": "Plateforme Big Data de gestion et de gouvernance des données patients",
    "sous_titre": "Nettoyage, déduplication et contrôle d'accès basé sur le consentement",
    "auteur": "RANOMENJANAHARY Manjaka Alpha",
    "encadrant_pro": "M. Harena Ny Aina Rabemanoela",
    "encadrant_ped": "M. RABENANAHARY Rojo",
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
TABLE_CAPTION_RE = re.compile(r"\*\*Tableau\s+(\d+)\s*[—–-]\s*([^*]+)\*\*")

# Pièces liminaires : le texte est ici, et nulle part ailleurs, pour rester la source unique.
RESUME = (
    "Dans un établissement de santé, les données patients sont réparties entre plusieurs "
    "systèmes d'information, sans référentiel d'identité commun : les mêmes personnes "
    "apparaissent plusieurs fois, et tout usage secondaire devient incertain. Le stage a "
    "porté sur une plateforme de centralisation et de gouvernance de ces données "
    "synthétiques. L'architecture retenue est un lac de données Medallion "
    "(RAW, SILVER, GOLD) sur HDFS, Hive et Spark, complété par un moteur de déduplication "
    "explicable : une voie exacte par clés normalisées, une voie probabiliste par score "
    "pondéré, et aucune fusion sans correspondance justifiée. La gouvernance associe rôles, "
    "contrôle du consentement par finalité, journal d'audit et clés d'API hachées. Sur le "
    "jeu de référence, la déduplication ramène 214 enregistrements à 145 patients, dont 69 "
    "doublons éliminés, soit 32,24 %. La précision atteint 1,000 ; le rappel atteint 0,578 "
    "sur le jeu « easy » mais reste à 0,422 sur le jeu « hard », où 420 faux négatifs sont "
    "assumés et bornés. Ce mémoire expose l'état réel du système : ce qui est "
    "démontré et testé, ce qui reste limité, et les corrections identifiées."
)
MOTS_CLES = (
    "Données de santé, Lac de données, Medallion, Spark, Hive, HDFS, FHIR, "
    "Déduplication, MPI, Consentement, Gouvernance, RGPD"
)
ABSTRACT = (
    "Patient data in a healthcare institution is spread across several information systems "
    "with no shared identity reference: the same person appears several times, weakening "
    "any secondary use. This internship built a platform to centralise and govern such "
    "synthetic data. The architecture is a Medallion data lake (RAW, SILVER, "
    "GOLD) on HDFS, Hive and Spark, completed by an explainable deduplication engine: an "
    "exact path based on normalised keys, a probabilistic path based on a weighted score, "
    "no merge without a justified match. Governance combines roles, purpose-by-purpose "
    "consent, access auditing and hashed API keys. Deduplication reduces 214 records to 145 "
    "patients, removing 69 duplicates (32.24%). "
    "Precision reaches 1.000; recall reaches 0.578 on the “easy” set but 0.422 on the "
    "“hard” set, where 420 false negatives are accepted and bounded. This thesis reports the "
    "system's state: what is demonstrated and tested, what remains limited, and the "
    "identified corrections."
)
KEYWORDS = (
    "Healthcare data, Data lake, Medallion, Spark, Hive, HDFS, FHIR, Deduplication, "
    "Master Patient Index, Consent, Governance, GDPR"
)

# Acronymes réellement employés dans les chapitres, avec leur développé. L'ordre suit la
# progression du texte (socle technique, puis santé, puis concepts étudiés).
ACRONYMES = [
    ("API", "Application Programming Interface — interface de programmation d'applications"),
    ("CI", "Continuous Integration — intégration continue"),
    ("CIN", "Carte d'Identité Nationale (Madagascar)"),
    ("CNIL", "Commission Nationale de l'Informatique et des Libertés"),
    ("DMP", "Data Management Platform — plateforme de gestion des données de référence"),
    ("ELT", "Extract, Load, Transform — extraction, chargement, transformation"),
    ("EM", "Expectation-Maximisation — algorithme d'estimation de paramètres"),
    ("EMPI", "Enterprise Master Patient Index — référentiel d'identité d'entreprise"),
    ("ER", "Entity Resolution — résolution d'entités, rapprochement d'enregistrements"),
    ("ETL", "Extract, Transform, Load — extraction, transformation, chargement"),
    ("FHIR", "Fast Healthcare Interoperability Resources — format d'échange de données de santé"),
    ("FN", "Faux Négatif — paire de patients identiques non détectée"),
    ("FP", "Faux Positif — paire de patients différents fusionnés à tort"),
    ("HDFS", "Hadoop Distributed File System — système de fichiers distribué"),
    ("MAVIS", "système d'information métier de l'établissement, répliqué localement pour le PoC"),
    ("MBDS", "Mobilité, Bases de Données et Intégration de Systèmes — spécialité du Master 2"),
    ("MDM", "Master Data Management — gestion des données de référence"),
    ("MMT", "Madagascar Medical Technology — établissement d'accueil du stage"),
    ("MPI", "Master Patient Index — index maître des patients"),
    ("MVP", "Minimum Viable Product — produit viable minimal"),
    ("NLP", "Natural Language Processing — traitement automatique du langage"),
    ("REST", "Representational State Transfer — style d'architecture d'API"),
    ("RGPD", "Règlement Général sur la Protection des Données"),
    ("RMA", "reporting périodique d'activité de l'établissement : diagnostics, "
            "morbidité–mortalité, laboratoire, paludisme"),
    ("SHA-256", "Secure Hash Algorithm 256 bits — empreinte de hachage"),
    ("SQL", "Structured Query Language — langage de requête"),
    ("VM", "Machine Virtuelle"),
]


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


def add_centered(doc: Document, text: str, size: float, bold: bool = False,
                 italic: bool = False, space_after: float = 0) -> None:
    """Paragraphe centré, typé comme une ligne de page de garde ou de titre liminaire."""
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(space_after)
    run = paragraph.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return paragraph


def add_cover(doc: Document) -> None:
    """Page de garde, sur le modèle de l'établissement (métadonnées dans DOC_META).

    L'ordre reprend la page de garde de référence : titre, « par », nom de l'auteur,
    « Mémoire présenté » suivi du libellé exact du diplôme, encadrement, mois et année,
    puis mention de copyright. Aucune ligne « service » n'est produite : l'établissement
    ne la demande pas et le modèle de référence ne la comporte pas.
    """
    for _ in range(2):
        doc.add_paragraph()
    add_centered(doc, DOC_META["titre"], 18, bold=True)
    add_centered(doc, DOC_META["sous_titre"], 12, italic=True, space_after=18)
    add_centered(doc, "par", 12)
    add_centered(doc, DOC_META["auteur"], 13, bold=True, space_after=18)

    add_centered(doc, "Mémoire présenté", 12)
    diploma = doc.add_paragraph()
    diploma.alignment = WD_ALIGN_PARAGRAPH.CENTER
    diploma.paragraph_format.space_after = Pt(18)
    first = diploma.add_run(DOC_META["mention"])
    first.bold = True
    first.font.size = Pt(12)
    diploma.add_run().add_break()
    second = diploma.add_run(DOC_META["specialite"])
    second.bold = True
    second.font.size = Pt(12)

    for label, key in [
        ("Encadrant professionnel", "encadrant_pro"),
        ("Encadrant pédagogique", "encadrant_ped"),
        ("Entreprise d'accueil", "entreprise"),
    ]:
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lead = paragraph.add_run("{0} : ".format(label))
        lead.font.size = Pt(12)
        value = paragraph.add_run(DOC_META[key])
        value.font.size = Pt(12)
        value.bold = True

    for _ in range(2):
        doc.add_paragraph()
    add_centered(doc, "{0}, {1}".format(DOC_META["mois"], DOC_META["annee"]), 12, bold=True)
    add_centered(
        doc,
        "© {0}, {1}".format(DOC_META["auteur"], DOC_META["annee"]),
        10,
        italic=True,
    )
    doc.add_page_break()


def add_liminaire_title(doc: Document, text: str) -> None:
    """Titre d'une section liminaire (résumé, abstract, listes, acronymes)."""
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    run.bold = True
    run.font.size = Pt(16)
    paragraph.paragraph_format.space_after = Pt(12)


def add_justified(doc: Document, text: str, size: float = 12, space_after: float = 6) -> None:
    """Paragraphe de texte courant justifié, avec retrait de première ligne."""
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.first_line_indent = Cm(0.75)
    run = paragraph.add_run(text)
    run.font.size = Pt(size)
    run.font.name = "Times New Roman"
    run.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")


def add_abstract(doc: Document, title: str, text: str, keywords_label: str,
                 keywords: str) -> None:
    """Section liminaire : texte justifié, puis ligne de mots-clés en gras."""
    add_liminaire_title(doc, title)
    add_justified(doc, text, space_after=10)
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    lead = paragraph.add_run("{0} : ".format(keywords_label))
    lead.bold = True
    lead.font.size = Pt(12)
    body = paragraph.add_run(keywords)
    body.font.size = Pt(12)
    doc.add_page_break()


def add_acronymes(doc: Document) -> None:
    """Liste des acronymes en tableau à deux colonnes, comme dans le modèle de référence."""
    add_liminaire_title(doc, "Acronymes")
    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for sigle, developpe in ACRONYMES:
        cells = table.add_row().cells
        for cell, text, bold in [
            (cells[0], sigle, True),
            (cells[1], developpe, False),
        ]:
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run(text)
            run.bold = bold
            run.font.size = Pt(10)
    doc.add_page_break()


def add_listes(doc: Document, figure_captions, table_captions) -> None:
    """Liste des tableaux puis liste des figures.

    Les entrées sont recopiées depuis les légendes des chapitres, jamais recomptées ici :
    la numérotation affichée reste donc celle du texte. La liste des tableaux n'est émise
    que s'il existe au moins une légende de tableau ; à défaut, mieux vaut une section
    absente qu'une section vide.
    """
    if table_captions:
        add_liminaire_title(doc, "Liste des tableaux")
        for numero, titre in table_captions:
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.space_after = Pt(2)
            run = paragraph.add_run("Tableau {0} — {1}".format(numero, titre.strip()))
            run.font.size = Pt(11)
        doc.add_page_break()

    if figure_captions:
        add_liminaire_title(doc, "Liste des figures")
        for numero, titre in figure_captions:
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.space_after = Pt(2)
            run = paragraph.add_run("Figure {0} — {1}".format(numero, titre.strip()))
            run.font.size = Pt(11)
        doc.add_page_break()


def first_sentence(text: str, limit: int = 120) -> str:
    """Première phrase d'une légende, pour les listes liminaires.

    Une légende de figure fait souvent trois lignes ; la recopier entière produirait une
    liste illisible. La première phrase suffit à identifier la figure.
    """
    flat = re.sub(r"\s+", " ", text).strip(" —*")
    match = re.search(r"^(.+?[.!?])(\s|$)", flat)
    sentence = match.group(1) if match else flat
    if len(sentence) > limit:
        cut = sentence[:limit]
        for separator in (";", ",", " : "):
            position = cut.rfind(separator)
            if position > limit * 0.5:
                cut = cut[:position]
                break
        sentence = cut.rstrip(" ,;:") + "…"
    return sentence


def collect_captions() -> "tuple[list, list]":
    """Relit les légendes des chapitres : figures (toujours) et tableaux (si légendés).

    Retourne ([(numéro, titre), ...], [(numéro, titre), ...]). Une légende de figure est
    le bloc `> **Figure N — ...**`, qui peut courir sur plusieurs lignes : les lignes sont
    donc recollées avant d'être nettoyées, faute de quoi la liste afficherait un titre
    coupé au milieu d'un mot. Une légende de tableau est la mention `**Tableau N — ...**`
    placée en tête du tableau concerné.
    """
    figures = []
    tables = []
    for chapter in sorted(CHAPTERS_DIR.glob("0*.md")):
        lines = chapter.read_text(encoding="utf-8").splitlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            start = CAPTION_RE.match(line)
            if start:
                block = [line]
                # Le bloc est clos quand la paire de ** est complète : le compte, et non
                # la simple présence, sinon la lecture s'arrête sur l'astérisque d'ouverture.
                while index + 1 < len(lines) and "".join(block).count("**") < 2:
                    index += 1
                    block.append(lines[index])
                joined = " ".join(re.sub(r"^>\s?", "", part) for part in block)
                joined = re.sub(r"\*\*Figure\s+\d+\s*[—–-]\s*", " ", joined)
                joined = joined.replace("**", " ")
                figures.append((start.group(1), first_sentence(joined)))
            table = TABLE_CAPTION_RE.search(line)
            if table:
                tables.append((table.group(1), first_sentence(table.group(2))))
            index += 1
    return figures, tables


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


def set_page_numbering(section, fmt: str = "decimal", start: int = 1) -> None:
    """Format de numérotation d'une section (`lowerRoman` pour la pièce liminaire).

    L'élément `w:pgNumType` doit respecter l'ordre du schéma `w:sectPr` : inséré
    n'importe où, Word refuse d'ouvrir le fichier. On le place donc avant le premier
    élément d'ordre supérieur, et en dernier recours à la fin.
    """
    order = (
        "w:footnotePr", "w:endnotePr", "w:type", "w:pgSz", "w:pgMar", "w:paperSrc",
        "w:pgBorders", "w:lnNumType", "w:pgNumType", "w:cols", "w:formProt", "w:vAlign",
        "w:noEndnote", "w:titlePg", "w:textDirection", "w:bidi", "w:rtlGutter",
        "w:docGrid", "w:printerSettings", "w:sectPrChange",
    )
    sect_pr = section._sectPr
    existing = sect_pr.find(qn("w:pgNumType"))
    if existing is not None:
        sect_pr.remove(existing)
    element = OxmlElement("w:pgNumType")
    element.set(qn("w:fmt"), fmt)
    element.set(qn("w:start"), str(start))
    index = order.index("w:pgNumType")
    for child in sect_pr:
        tag = "w:{0}".format(child.tag.split("}")[-1])
        if tag in order and order.index(tag) > index:
            child.addprevious(element)
            break
    else:
        sect_pr.append(element)


def clear_page_numbering(section) -> None:
    """Retire `w:pgNumType` : la section continue la numérotation de la précédente.

    Nécessaire parce que `add_section` recopie le `sectPr` courant : sans ce retrait, la
    section du corps portant `start=1`, chaque page paysage créée pour une figure large
    remettrait son compteur à 1.
    """
    sect_pr = section._sectPr
    existing = sect_pr.find(qn("w:pgNumType"))
    if existing is not None:
        sect_pr.remove(existing)


def fill_footer(section) -> None:
    """Pied de page « Page X », sans total, comme dans le modèle de référence.

    Un total était affiché auparavant, mais il devenait faux dès que le corps
    recommençait sa numérotation à 1 après la pièce liminaire. Le choix de masquer ou
    non le numéro sur la première page revient à l'appelant : cette fonction ne touche
    donc pas `different_first_page_header_footer`.
    """
    paragraph = section.footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(paragraph, "PAGE")
    for run in paragraph.runs:
        run.font.size = Pt(9)


def add_page_footer(doc: Document) -> None:
    """Pieds de page : pièce liminaire en chiffres romains, corps en chiffres arabes.

    La page de garde ne porte pas de numéro, et le corps repart à 1 : c'est la
    convention du modèle de l'établissement, repérée sur les deux rapports de référence.
    Les sections paysage de fin de chapitre héritent du pied du corps et surtout ne
    réinitialisent pas le compteur.
    """
    sections = list(doc.sections)
    if not sections:
        return

    front = sections[0]
    set_page_numbering(front, "lowerRoman", 1)
    fill_footer(front)
    front.different_first_page_header_footer = True

    for section in sections[1:]:
        clear_page_numbering(section)
        section.different_first_page_header_footer = False

    if len(sections) > 1:
        body = sections[1]
        body.footer.is_linked_to_previous = False
        fill_footer(body)
        set_page_numbering(body, "decimal", 1)


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

    # --- Pièce liminaire : numérotation romaine, corps en chiffres arabes ---
    add_cover(doc)
    add_abstract(doc, "Résumé", RESUME, "Mots-clés", MOTS_CLES)
    add_abstract(doc, "Abstract", ABSTRACT, "Keywords", KEYWORDS)
    add_toc(doc)
    figure_captions, table_captions = collect_captions()
    add_listes(doc, figure_captions, table_captions)
    add_acronymes(doc)

    body = doc.add_section(WD_SECTION.NEW_PAGE)
    set_page(body, landscape=False)

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
    print(
        "Liminaire : figures listées {0} · tableaux listés {1}{2}".format(
            len(figure_captions),
            len(table_captions),
            "" if table_captions else " (aucune légende de tableau : section omise)",
        )
    )
    print(
        "Résumé : {0} mots · Abstract : {1} mots · Acronymes : {2}".format(
            len(RESUME.split()), len(ABSTRACT.split()), len(ACRONYMES)
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
