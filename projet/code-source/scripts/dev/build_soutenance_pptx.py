"""Génère le deck de soutenance M2 MBDS du projet patients (PowerPoint 16:9, 16 x 9 pouces).

Usage :
    python scripts/dev/build_soutenance_pptx.py

Sortie : documents/slide_soutenance/V2soutenance_m2_mmt_alpha.pptx
Dépendances dev (venv local, hors deps du projet) : python-pptx>=0.6.21, Pillow.

Structure des 21 slides alignée sur le deck de référence (documents/references/V2soutenance_m2_hasina.pptx) :
bandeau de logos (ITuniversity, MBDS, Université Côte d'Azur, entreprise) et pied de page
« titre » présenté par … / date sur chaque slide ; contenu = plateforme patients (mémoire
`chapters/`). Les figures proviennent de documents/figures/ (render_mermaid_figures.py), les
logos de documents/image/. Le texte accepte **gras** et `code` en ligne.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

from PIL import Image, ImageChops
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

BASE = Path(__file__).resolve().parents[4]
FIGURES = BASE / "documents" / "figures"
IMAGES = BASE / "documents" / "image"
OUT = BASE / "documents" / "slide_soutenance" / "V2soutenance_m2_mmt_alpha.pptx"

# Canevas 16 x 9 pouces, comme le deck de référence.
W, H = 16.0, 9.0
MARGIN = 0.75

PRIMARY = RGBColor(0x10, 0x6D, 0x8E)
SECOND = RGBColor(0x2F, 0xA8, 0xB5)
GOLD = RGBColor(0xE8, 0xA8, 0x2E)
DARK = RGBColor(0x0B, 0x2E, 0x4F)
TEXT = RGBColor(0x20, 0x30, 0x3C)
MUTED = RGBColor(0x5A, 0x6B, 0x79)
TINT = RGBColor(0xE6, 0xF1, 0xF6)
TINT2 = RGBColor(0xD3, 0xE7, 0xEF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ZEBRA = RGBColor(0xF1, 0xF7, 0xFA)
OK = RGBColor(0x2E, 0x8B, 0x57)
KO = RGBColor(0xC0, 0x39, 0x2B)

FONT = "Calibri"
MONO = "Consolas"
TITLE = "Plateforme Big Data de gouvernance des données patients"
AUTHOR = "RANOMENJANAHARY Manjaka Alpha"
DATE = "Octobre 2026"  # date de soutenance : une seule constante à modifier
FOOTER = "« {0} » présenté par {1}".format(TITLE, AUTHOR)

LOGOS = [IMAGES / "logo-ituniversity.png", IMAGES / "logo-mbds.jpg", IMAGES / "logo-uca.png"]
MMT_LOGO = IMAGES / "mmt-logo.png"

RICH_RE = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")


# --------------------------------------------------------------------------- primitives

def _in(v):
    return Inches(v)


def _solid(shape, color, line=None):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    shape.shadow.inherit = False
    return shape


def _runs(paragraph, text, size, color=TEXT, bold=False, italic=False):
    """Ajoute `text` au paragraphe en interprétant **gras** et `code`."""
    for token in RICH_RE.split(text):
        if not token:
            continue
        r = paragraph.add_run()
        if token.startswith("**") and token.endswith("**"):
            r.text = token[2:-2]
            r.font.bold = True
        elif token.startswith("`") and token.endswith("`"):
            r.text = token[1:-1]
            r.font.bold = bold
            r.font.name = MONO
        else:
            r.text = token
            r.font.bold = bold
        if r.font.name != MONO:
            r.font.name = FONT
        r.font.size = Pt(size * (0.92 if r.font.name == MONO else 1))
        r.font.italic = italic
        r.font.color.rgb = color


def _frame(tf, margin=0.0, anchor=MSO_ANCHOR.TOP):
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, _in(margin))


def text(slide, x, y, w, h, content, size=16, color=TEXT, bold=False, italic=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, gap=6):
    """Zone de texte ; `content` est une chaîne ou une liste de paragraphes."""
    box = slide.shapes.add_textbox(_in(x), _in(y), _in(w), _in(h))
    _frame(box.text_frame, anchor=anchor)
    paras = content if isinstance(content, list) else [content]
    for i, para in enumerate(paras):
        p = box.text_frame.paragraphs[0] if i == 0 else box.text_frame.add_paragraph()
        p.alignment = align
        p.space_after = Pt(gap)
        if para.startswith("•  "):
            para = para[3:]
            _bullet(p, size)
        _runs(p, para, size, color, bold, italic)
    return box


def _bullet(paragraph, size):
    """Vraie puce PowerPoint, avec retrait suspendu des lignes suivantes."""
    ppr = paragraph._p.get_or_add_pPr()
    indent = int(Pt(size) * 1.1)
    ppr.set("marL", str(indent))
    ppr.set("indent", str(-indent))
    bu = ppr.makeelement(qn("a:buChar"), {"char": "•"})
    ppr.append(bu)


def box(slide, x, y, w, h, fill=TINT, radius=0.08, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, _in(x), _in(y), _in(w), _in(h))
    _solid(s, fill, line)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    return s


def card(slide, x, y, w, h, title, body, num=None, title_size=17, body_size=14, fill=TINT):
    """Carte : fond teinté, pastille numérotée optionnelle, titre, puis corps."""
    box(slide, x, y, w, h, fill)
    tx = x + 0.25
    if num is not None:
        badge(slide, x + 0.22, y + 0.22, str(num), 0.5)
        tx = x + 0.9
    text(slide, tx, y + 0.24, x + w - tx - 0.2, 0.5, title, title_size, DARK, bold=True)
    if body:
        text(slide, x + 0.25, y + 0.85, w - 0.45, h - 1.0, body, body_size, TEXT, gap=4)


def badge(slide, x, y, label, d=0.55, fill=PRIMARY, size=16):
    c = slide.shapes.add_shape(MSO_SHAPE.OVAL, _in(x), _in(y), _in(d), _in(d))
    _solid(c, fill)
    tf = c.text_frame
    _frame(tf, anchor=MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _runs(p, label, size, WHITE, bold=True)


def chip(slide, x, y, w, h, label, size=15, fill=TINT2, color=DARK, bold=True):
    s = box(slide, x, y, w, h, fill, radius=0.2)
    tf = s.text_frame
    _frame(tf, 0.12, MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _runs(p, label, size, color, bold=bold)


def band(slide, y, content, size=18, h=0.95, fill=DARK, color=WHITE):
    """Bandeau de message clé, pleine largeur utile."""
    s = box(slide, MARGIN, y, W - 2 * MARGIN, h, fill, radius=0.12)
    tf = s.text_frame
    _frame(tf, 0.3, MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _runs(p, content, size, color)


def arrow(slide, x, y, w, h=0.5, fill=SECOND):
    box(slide, x, y, w, h, fill, shape=MSO_SHAPE.RIGHT_ARROW)


def picture(slide, path, x, y, w=None, h=None):
    """Image dans la boîte (x, y, w, h) en conservant ses proportions, centrée."""
    img = Image.open(path)
    ratio = img.width / img.height
    if w is not None and h is not None:
        if w / h > ratio:
            pw, ph = h * ratio, h
        else:
            pw, ph = w, w / ratio
        x, y = x + (w - pw) / 2, y + (h - ph) / 2
    elif w is not None:
        pw, ph = w, w / ratio
    else:
        pw, ph = h * ratio, h
    slide.shapes.add_picture(str(path), _in(x), _in(y), _in(pw), _in(ph))


def _mmt_logo():
    """Logo MMT recadré sur son contenu (le fichier source a une large marge blanche)."""
    img = Image.open(MMT_LOGO).convert("RGB")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bbox = ImageChops.difference(img, bg).getbbox()
    if bbox:
        pad = 6
        bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0),
                min(bbox[2] + pad, img.width), min(bbox[3] + pad, img.height))
        img = img.crop(bbox)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf, img.width / img.height


MMT_BUF, MMT_RATIO = _mmt_logo()


def mmt(slide, x, y, h):
    MMT_BUF.seek(0)
    slide.shapes.add_picture(MMT_BUF, _in(x), _in(y), _in(h * MMT_RATIO), _in(h))


def line(slide, y, color=PRIMARY):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, _in(y), _in(W), _in(y))
    c.line.color.rgb = color
    c.line.width = Pt(1)


def logos(slide, y=0.12, h=0.5, gap=0.9):
    """Bandeau de logos, dans l'ordre du deck de référence ; MMT à droite."""
    x = MARGIN
    for path in LOGOS:
        img = Image.open(path)
        pw = h * img.width / img.height
        picture(slide, path, x, y, h=h)
        x += pw + gap
    mmt(slide, W - MARGIN - (h + 0.1) * MMT_RATIO, y - 0.05, h + 0.1)


def footer(slide):
    line(slide, H - 0.55)
    text(slide, 0.3, H - 0.45, 12.0, 0.3, FOOTER, 11, PRIMARY)
    text(slide, W - 3.3, H - 0.45, 3.0, 0.3, DATE, 11, PRIMARY, align=PP_ALIGN.RIGHT)


def new_slide(prs, title=None, subtitle=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    logos(s)
    line(s, 0.78)
    if title:
        text(s, MARGIN, 0.95, W - 2 * MARGIN, 0.75, title, 32, PRIMARY)
    if subtitle:
        text(s, MARGIN, 1.7, W - 2 * MARGIN, 0.5, subtitle, 20, MUTED)
    footer(s)
    return s


def table(slide, x, y, w, headers, rows, col_w=None, size=14, head_size=15, row_h=0.5,
          center_from=None):
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), _in(x), _in(y), _in(w),
                                   _in(row_h * (len(rows) + 1)))
    tbl = shape.table
    if col_w:
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = _in(cw)
    for ri in range(len(rows) + 1):
        tbl.rows[ri].height = _in(row_h)
    for ci, htext in enumerate(headers):
        _cell(tbl.cell(0, ci), htext, head_size, WHITE, PRIMARY, bold=True,
              center=center_from is not None and ci >= center_from)
    for ri, row in enumerate(rows, start=1):
        for ci, value in enumerate(row):
            _cell(tbl.cell(ri, ci), value, size, TEXT, ZEBRA if ri % 2 == 0 else WHITE,
                  center=center_from is not None and ci >= center_from)
    return tbl


def _cell(cell, value, size, color, fill, bold=False, center=False):
    cell.fill.solid()
    cell.fill.fore_color.rgb = fill
    cell.margin_left = cell.margin_right = _in(0.1)
    cell.margin_top = cell.margin_bottom = _in(0.05)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = cell.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
    if value in ("✔", "◐", "✖"):
        tone = {"✔": OK, "◐": GOLD, "✖": KO}[value]
        _runs(p, value, size + 2, tone, bold=True)
    else:
        _runs(p, value, size, color, bold)


# --------------------------------------------------------------------------- slides

def s01_cover(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    logos(s, y=0.45, h=0.7, gap=1.2)
    text(s, 1.0, 2.2, 14.0, 1.1, "Plateforme Big Data de gestion et de gouvernance",
         44, PRIMARY, italic=True, align=PP_ALIGN.CENTER)
    text(s, 1.0, 3.15, 14.0, 1.1, "des données patients", 44, PRIMARY, italic=True,
         align=PP_ALIGN.CENTER)
    text(s, 1.0, 4.35, 14.0, 0.5,
         "Nettoyage · Déduplication explicable · Contrôle d'accès par consentement",
         22, DARK, align=PP_ALIGN.CENTER)
    text(s, 1.0, 5.6, 14.0, 0.45, DATE, 20, TEXT, italic=True, align=PP_ALIGN.CENTER)
    text(s, 1.0, 6.2, 14.0, 0.45, "Présenté par : **{0}**".format(AUTHOR), 20, TEXT,
         align=PP_ALIGN.CENTER)
    text(s, 1.0, 7.0, 14.0, 0.8,
         ["Encadrant professionnel : M. Harena Ny Aina Rabemanoela  ·  "
          "Encadrant pédagogique : M. RABENANAHARY Rojo",
          "Madagascar Medical Technology (MMT) — Master MBDS"],
         15, MUTED, align=PP_ALIGN.CENTER, gap=2)


def s02_entreprise(prs):
    s = new_slide(prs, "Présentation de l'entreprise")
    chip(s, 0.75, 2.0, 2.9, 1.1, "Ingénierie biomédicale", 16)
    chip(s, 3.95, 2.0, 2.9, 1.1, "Madagascar", 16)
    chip(s, 7.15, 2.0, 2.2, 1.1, "2009", 18)
    chip(s, 3.1, 3.55, 4.4, 0.9, "Madagascar Medical Technology", 17, PRIMARY, WHITE)
    text(s, 0.75, 4.9, 8.6, 0.45, "**Domaines d'activité**", 18, DARK)
    text(s, 0.95, 5.4, 8.4, 2.4, [
        "•  Distribution et maintenance de matériels biomédicaux",
        "•  Fourniture de consommables",
        "•  Gestion de stock des établissements partenaires",
        "•  Business Partner **Siemens Healthineers** (branche sud-africaine)",
    ], 16, gap=6)
    box(s, 10.0, 1.95, 5.25, 3.3, WHITE, line=TINT2)
    mmt(s, 10.0 + (5.25 - 2.9 * MMT_RATIO) / 2, 2.15, 2.9)
    card(s, 10.0, 5.5, 5.25, 2.35, "Département R&D (depuis 2024)",
         ["Systèmes d'information médicale, infrastructures et réseaux informatiques.",
          "**Lieu du stage**, du 6 juillet à fin octobre 2026."], body_size=15)


def s03_question(prs):
    s = new_slide(prs, "Question")
    chip(s, 3.3, 2.1, 4.2, 0.85, "Plusieurs systèmes", 17)
    chip(s, 8.5, 2.1, 4.2, 0.85, "Un même patient", 17)
    band(s, 3.35, "**Comment savoir qu'il s'agit du même patient — et qui a le droit de lire "
                  "ses données, pour quelle finalité ?**", 20, 1.0, TINT2, DARK)
    code = box(s, 2.3, 4.85, 11.4, 1.9, RGBColor(0xF4, 0xF8, 0xFA), line=TINT2)
    _frame(code.text_frame, 0.35, MSO_ANCHOR.MIDDLE)
    for i, ln in enumerate(["Pharmacie     →  Jean Rakoto   ·  CIN 101 02404 5  ·  1990-01-10",
                            "Consultation  →  Rakoto Jean   ·  101024045        ·  10/01/1990",
                            "Imagerie      →  J. RAKOTO     ·  101024045        ·  1990/01/10"]):
        p = code.text_frame.paragraphs[0] if i == 0 else code.text_frame.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = ln
        r.font.name = MONO
        r.font.size = Pt(18)
        r.font.color.rgb = TEXT
    text(s, 2.3, 7.0, 11.4, 0.5, "Trois fiches, trois formats… **une seule personne** "
         "(cas de référence du projet).", 16, MUTED, italic=True, align=PP_ALIGN.CENTER)


def s04_contexte(prs):
    s = new_slide(prs, "Contexte et problématique")
    items = [
        ("Dispersion", "Chaque service tient son propre registre, sans identifiant commun."),
        ("Hétérogénéité", "Genre `H/F`, `male/female`, `Homme/femme` ; dates et CIN aux formats divergents."),
        ("Processus manuel", "Recoupements lents, erreurs humaines, aucune trace des décisions."),
        ("Absence de gouvernance", "Ni rôles, ni consentement par finalité, ni audit d'accès."),
    ]
    for i, (t, b) in enumerate(items):
        card(s, 0.75 + (i % 2) * 3.65, 1.95 + (i // 2) * 2.35, 3.45, 2.15, t, [b], body_size=15)
    picture(s, FIGURES / "fig-1.png", 8.2, 1.95, 7.05, 4.5)
    band(s, 6.85, "**Problématique** : intégrer, nettoyer, dédupliquer et centraliser ces données, "
                  "en gardant la traçabilité des identités et en gouvernant l'accès par le "
                  "consentement du patient.", 16, 1.1)


def s05_objectifs(prs):
    s = new_slide(prs, "Objectifs du projet")
    items = [
        ("Centraliser", "Data Lake Medallion : zones **RAW → SILVER → GOLD** sur HDFS / Hive / Spark."),
        ("Normaliser", "Modèle canonique `CanonicalPatient` + pivot **FHIR** (genre, dates, CIN)."),
        ("Dédupliquer", "Master patient + identity map : chaque fusion justifiée par **score et méthode**."),
        ("Gouverner", "Rôles, **consentement par finalité**, audit de chaque accès, clés API hachées."),
    ]
    for i, (t, b) in enumerate(items):
        card(s, 0.75 + i * 3.7, 2.2, 3.45, 3.0, t, [b], num=i + 1, title_size=19, body_size=17)
    band(s, 5.8, "Données **exclusivement synthétiques** — aucune donnée réelle de patient "
                 "n'est manipulée.", 18, 0.95, TINT2, DARK)


def s06_plan(prs):
    s = new_slide(prs, "Plan")
    parts = [
        ("État de l'art", "notions, critères, solutions du domaine"),
        ("Étude de l'existant", "les systèmes de MMT : points forts, limites"),
        ("Solution proposée", "architecture Medallion + moteur de déduplication + gouvernance"),
        ("Fonctionnalités principales", "cas d'utilisation et résultats mesurés"),
        ("Démonstration", "tests, évaluation ground-truth, pipeline de bout en bout"),
    ]
    for i, (t, sub) in enumerate(parts):
        y = 2.0 + i * 1.18
        badge(s, 4.2, y, str(i + 1), 0.75, size=20)
        text(s, 5.25, y + 0.02, 8.0, 0.45, t, 22, DARK, bold=True)
        text(s, 5.25, y + 0.48, 8.0, 0.4, sub, 15, MUTED)


def s07_etat_art(prs):
    s = new_slide(prs, "État de l'art", "Six solutions du domaine, étudiées sur documentation")
    table(s, 0.75, 2.4, 14.5, ("Solution", "Famille", "Points forts", "Limites ici"), [
        ("**InterSystems EMPI**", "MPI santé", "identité déterministe + probabiliste, PIX/PDQ",
         "propriétaire, référentiel externe"),
        ("**Talend MDM**", "MDM / ETL", "match & survivorship, golden record",
         "suite lourde, pas de FHIR natif"),
        ("**Azure Health Data Services**", "Cloud santé", "FHIR managé, dé-identification",
         "cloud : contraire à l'hébergement interne"),
        ("**HAPI FHIR**", "Open source", "serveur FHIR de référence, `$match`",
         "ni rapprochement, ni gouvernance"),
        ("**Splink**", "Open source", "Fellegi–Sunter à l'échelle (EM, Spark)",
         "poids EM peu lisibles"),
        ("**Apache Atlas**", "Open source", "catalogue, lineage, classification",
         "métadonnées, pas de contrôle d'accès"),
    ], col_w=(3.6, 2.2, 4.5, 4.2), size=14, row_h=0.62)
    text(s, 0.75, 7.25, 14.5, 0.4, "Capacités **annoncées** par la documentation : aucun "
         "produit n'a été installé ni mesuré.", 14, MUTED, italic=True)


def s08_criteres(prs):
    s = new_slide(prs, "État de l'art", "Critères de comparaison")
    table(s, 0.75, 2.35, 14.5,
          ("Critère", "EMPI", "Talend", "Azure", "HAPI", "Splink", "Atlas", "Projet"), [
              ("Déduplication explicable", "✔", "✔", "✖", "✖", "◐", "✖", "✔"),
              ("Interopérabilité FHIR", "◐", "✖", "✔", "✔", "✖", "✖", "✔"),
              ("Gouvernance rôle + consentement + audit", "◐", "◐", "✔", "✖", "✖", "◐", "✔"),
              ("Montée en charge Big Data", "◐", "✔", "✔", "✖", "✔", "✔", "✔"),
              ("Hébergement interne", "✔", "✔", "✖", "✔", "✔", "✔", "✔"),
              ("Faisabilité VM 8 Go / Python 3.8", "✖", "✖", "✖", "✖", "◐", "✖", "✔"),
          ], col_w=(5.0, 1.35, 1.35, 1.35, 1.35, 1.35, 1.35, 1.4), size=15, row_h=0.6,
          center_from=1)
    band(s, 6.85, "**Aucun produit ne coche les six cases** dans les contraintes du stage → "
                  "une chaîne sur mesure, adossée aux standards.", 17, 0.9)


def s09_choix(prs):
    s = new_slide(prs, "État de l'art",
                  "Trois briques retenues, chacune introduite par un besoin")
    items = [
        ("Apache Spark · HDFS · Hive", "Stockage et traitement répartis ; Data Lake Medallion "
         "RAW → SILVER → GOLD. Il vient **après** le besoin."),
        ("Entity Resolution · RapidFuzz", "Fellegi–Sunter : passe exacte puis probabiliste, "
         "score pondéré lisible, seuil **0,80**."),
        ("FHIR · FastAPI · PostgreSQL", "Pivot d'échange standard ; API qui applique rôle, "
         "finalité et consentement ; base de référence."),
    ]
    for i, (t, b) in enumerate(items):
        card(s, 0.75 + i * 4.9, 2.45, 4.6, 2.9, t, [b], num=i + 1, body_size=17)
    band(s, 5.9, "**Choix technologique** : RapidFuzz plutôt qu'un NLP lourd (crash sous "
                 "Python 3.8), score explicable plutôt qu'EM, et **parité Pandas = Spark** vérifiée.",
         16, 1.2, TINT2, DARK)


def s10_existant_modules(prs):
    s = new_slide(prs, "Étude de l'existant", "Les systèmes d'information en place")
    items = [
        ("MAVIS", ["Odoo + module de gestion hospitalière", "PostgreSQL **distant** (tunnel SSH)",
                   "1 260 tables détectées, **11 retenues**", "réplique locale : 73 090 lignes"]),
        ("MMT_DB", ["GNU Health (dossier médical)", "PostgreSQL local",
                    "9 tables, **60 271 lignes**", "3 tables extraites"]),
        ("CLINIQUE", ["Base SQLite d'une clinique", "patients, visites, diagnostics, observations",
                      "**54 582 lignes**", "déjà alignée sur FHIR"]),
        ("Sources de démonstration", ["pharmacy · consultation · imaging (CSV)",
                                      "générateur synthétique, graine 42",
                                      "**76 / 76 / 62** au run de référence"]),
    ]
    for i, (t, b) in enumerate(items):
        card(s, 0.75 + i * 3.7, 2.4, 3.45, 3.6, t, ["•  " + x for x in b], title_size=19,
             body_size=16)
    text(s, 0.75, 6.4, 14.5, 0.5, "Chaque logiciel est **complet dans son périmètre** — aucun "
         "n'est conçu pour être le référentiel d'identité de l'établissement.", 16, MUTED,
         align=PP_ALIGN.CENTER)


def s11_points_forts(prs):
    s = new_slide(prs, "Étude de l'existant", "Points forts")
    stats = [
        ("9 791 / 9 791", "jointure `hms_patient` ↔ `res_partner` vérifiée ligne à ligne"),
        ("0", "violation de clé étrangère dans CLINIQUE"),
        ("5", "clés étrangères GNU Health découvertes automatiquement"),
    ]
    for i, (big, lbl) in enumerate(stats):
        x = 0.75 + i * 4.9
        box(s, x, 2.45, 4.6, 2.6)
        text(s, x, 2.75, 4.6, 1.0, big, 44, PRIMARY, bold=True, align=PP_ALIGN.CENTER)
        text(s, x + 0.3, 3.95, 4.0, 1.0, lbl, 15, TEXT, align=PP_ALIGN.CENTER)
    band(s, 5.6, "Chaque base est **intègre avec elle-même** : le défi n'est pas la qualité "
                 "d'une base, c'est l'**absence de pont entre elles**.", 18, 1.2, TINT2, DARK)


def s12_limites(prs):
    s = new_slide(prs, "Étude de l'existant", "Limitations identifiées")
    items = ["Aucun identifiant patient transversal", "Aucune normalisation commune",
             "Aucun rapprochement d'identité", "Aucune gouvernance des accès",
             "Aucun espace de rejeu", "Recoupements entièrement manuels"]
    for i, t in enumerate(items):
        chip(s, 0.75 + (i % 2) * 7.35, 2.5 + (i // 2) * 1.35, 7.15, 1.0, t, 18, TINT, DARK)
    text(s, 0.75, 6.75, 14.5, 0.8, "Mesure du problème : le PoC d'origine comptait **24 872 "
         "marqueurs de doublon** sans référentiel patient ni fusion justifiée.", 16, MUTED,
         italic=True, align=PP_ALIGN.CENTER)


def s13_architecture(prs):
    s = new_slide(prs, "Solution proposée", "Architecture du système — trois niveaux, une logique")
    rows = [
        ("HDFS · Hive · Spark", "Data Lake Medallion RAW → SILVER → GOLD (VM 8 Go)"),
        ("Moteur `engine/`", "déduplication Pandas + Spark, parité stricte"),
        ("PostgreSQL central", "masters, identity map, consentements, audit"),
        ("API FastAPI", "rôle + finalité + consentement, refus 403 journalisé"),
        ("Flask · Next.js", "indicateurs et interface de pilotage (optionnelle)"),
    ]
    for i, (t, b) in enumerate(rows):
        y = 2.4 + i * 1.02
        badge(s, 0.75, y + 0.08, str(i + 1), 0.6, size=17)
        text(s, 1.55, y, 5.5, 0.42, t, 18, DARK, bold=True)
        text(s, 1.55, y + 0.42, 5.5, 0.45, b, 14, TEXT)
    picture(s, FIGURES / "fig-4.png", 7.3, 2.25, 7.95, 5.6)


def s14_fonctionnalites(prs):
    s = new_slide(prs, "Fonctionnalités principales")
    items = [
        ("Centralisation", "Les sources arrivent **telles quelles** dans RAW (parquet HDFS, tables Hive)."),
        ("Normalisation", "Un champ → un format : genre `M/F`, dates ISO, CIN ; aucune valeur devinée."),
        ("Déduplication explicable", "`master_patient_id` + méthode + score + explication."),
        ("Consentement par finalité", "Finalité obligatoire ; non consentie → **403** + motif en audit."),
        ("Pilotage du pipeline", "Reprise après échec, ingestion incrémentale, planification cron."),
    ]
    pos = [(0.75, 1.95), (5.65, 1.95), (10.55, 1.95), (3.2, 4.85), (8.1, 4.85)]
    for (t, b), (x, y) in zip(items, pos):
        card(s, x, y, 4.7, 2.65, t, [b], title_size=19, body_size=17)


def s15_cas(prs):
    s = new_slide(prs, "Cas d'utilisation", "Quatre étapes, huit cas d'utilisation")
    steps = [
        ("Intégrer", "CU1 ingérer\nCU2 normaliser"),
        ("Dédupliquer", "CU3 décider qui est\nle même patient"),
        ("Gouverner", "CU4 consentement en GOLD\nCU5 interroger l'API"),
        ("Exploiter", "CU6 vues · CU7 planifier\nCU8 dossier patient"),
    ]
    for i, (t, b) in enumerate(steps):
        x = 0.75 + i * 3.75
        box(s, x, 2.45, 3.1, 2.6, TINT)
        badge(s, x + 1.25, 2.05, str(i + 1), 0.6, size=17)
        text(s, x, 2.85, 3.1, 0.5, t, 20, DARK, bold=True, align=PP_ALIGN.CENTER)
        text(s, x + 0.15, 3.5, 2.8, 1.4, b.split("\n"), 14, TEXT, align=PP_ALIGN.CENTER, gap=2)
        if i < 3:
            arrow(s, x + 3.17, 3.5, 0.5, 0.45)
    band(s, 5.6, "Cas limite : un **refus de consentement** n'est jamais silencieux — il renvoie "
                 "un **403** et reste consultable dans le journal d'audit.", 16, 1.0, TINT2, DARK)
    text(s, 0.75, 6.85, 14.5, 0.5, "Évaluation transverse : générateur synthétique + vérité "
         "terrain jamais fournie à l'algorithme.", 15, MUTED, italic=True, align=PP_ALIGN.CENTER)


def s16_resultats(prs):
    s = new_slide(prs, "Cas d'utilisation", "Résultats mesurés au run de référence (07/09/2026)")
    stats = [("214", "lignes SILVER\n76 + 76 + 62"), ("145", "patients maîtres"),
             ("69", "doublons liés\n214 − 69 = 145"), ("32,24 %", "taux de doublons\n`mocked: false`")]
    for i, (big, lbl) in enumerate(stats):
        x = 0.75 + i * 3.7
        box(s, x, 2.4, 3.45, 2.9)
        text(s, x, 2.7, 3.45, 1.0, big, 48, PRIMARY, bold=True, align=PP_ALIGN.CENTER)
        text(s, x + 0.2, 3.9, 3.05, 1.2, lbl.split("\n"), 15, TEXT, align=PP_ALIGN.CENTER, gap=2)
    chip(s, 0.75, 5.8, 4.6, 0.9, "Pipeline **5 étapes** · run **4/4**", 16)
    chip(s, 5.7, 5.8, 4.6, 0.9, "Tests : **102/102**", 16)
    chip(s, 10.65, 5.8, 4.6, 0.9, "API d'indicateurs : **3/3**", 16)
    text(s, 0.75, 7.0, 14.5, 0.45, "Sources CSV synthétiques ; GOLD certifie l'identité, pas "
         "encore les événements de soin (`patient_events_gold` vide).", 14, MUTED, italic=True,
         align=PP_ALIGN.CENTER)


def s17_avant_apres(prs):
    s = new_slide(prs, "Cas d'utilisation", "Avant / après")
    box(s, 0.75, 2.4, 6.2, 2.9, TINT)
    text(s, 0.75, 2.6, 6.2, 0.5, "Avant", 22, KO, bold=True, align=PP_ALIGN.CENTER)
    text(s, 1.1, 3.25, 5.5, 2.0, ["•  Recoupement manuel entre services",
                                  "•  Erreurs humaines, décisions sans trace",
                                  "•  Accès sans finalité ni audit"], 16, gap=6)
    arrow(s, 7.2, 3.5, 1.6, 0.7, PRIMARY)
    box(s, 9.05, 2.4, 6.2, 2.9, TINT)
    text(s, 9.05, 2.6, 6.2, 0.5, "Après", 22, OK, bold=True, align=PP_ALIGN.CENTER)
    text(s, 9.4, 3.25, 5.5, 2.0, ["•  Pipeline automatisé de bout en bout",
                                  "•  Chaque fusion expliquée (score, méthode)",
                                  "•  Chaque accès contrôlé et audité"], 16, gap=6)
    stats = [("1,000", "précision · 0 faux positif\neasy · medium · hard"),
             ("0,422", "rappel sur le jeu « hard »\n(0,287 avant la clé CIN)"),
             ("TP = 307", "décisions identiques\nPandas = Spark")]
    for i, (big, lbl) in enumerate(stats):
        x = 0.75 + i * 4.9
        text(s, x, 5.65, 4.6, 0.8, big, 36, PRIMARY, bold=True, align=PP_ALIGN.CENTER)
        text(s, x, 6.45, 4.6, 0.9, lbl.split("\n"), 14, TEXT, align=PP_ALIGN.CENTER, gap=1)


def s18_demo(prs):
    s = new_slide(prs, "Démonstration", "Vidéo enregistrée (3 min 30) — aucun point de défaillance le jour J")
    table(s, 2.0, 2.5, 12.0, ("Plan", "Contenu filmé", "Durée"), [
        ("1", "`pytest projet/code-source/tests` — moteur, gouvernance, planification **102/102**", "0:45"),
        ("2", "Évaluation « hard » : précision / rappel / F1 (précision 1,000)", "0:45"),
        ("3", "`run_pipeline.sh` de bout en bout : RAW → SILVER → GOLD (5 étapes)", "1:00"),
        ("4", "Tableau de bord `/dashboard` : zones Medallion, planification cron, fraîcheur", "0:30"),
        ("Repli", "Compteurs figés : 214 · 145 · 69 · 32,24 %", "0:30"),
    ], col_w=(1.4, 9.1, 1.5), size=16, head_size=16, row_h=0.6)
    text(s, 2.0, 6.55, 12.0, 0.5, "Données synthétiques, graine fixe : la démonstration est "
         "rejouable à l'identique.", 15, MUTED, italic=True, align=PP_ALIGN.CENTER)


def s19_perspectives(prs):
    s = new_slide(prs, "Perspectives")
    items = ["Enrichir le mapping FHIR → `patient_events_gold`",
             "Peupler le consentement en base centrale",
             "Calibrer seuil et poids sur la vérité terrain",
             "Générateur de « faux jumeaux » (cas adversarial)",
             "Tests déployés et intégration continue",
             "Passage à l'échelle sur les volumes réels"]
    for i, t in enumerate(items):
        chip(s, 0.75 + (i % 2) * 7.35, 2.2 + (i // 2) * 1.4, 7.15, 1.05, t, 17, TINT, DARK)
    band(s, 6.55, "Et avant toute mise en production : vérifier le **droit malgache** des "
                  "données de santé.", 16, 0.9, TINT2, DARK)


def s20_conclusion(prs):
    s = new_slide(prs, "Conclusion")
    items = ["**Centraliser** un patient dispersé entre plusieurs systèmes",
             "**Normaliser** vers un modèle canonique + pivot FHIR",
             "**Dédupliquer** sans jamais fusionner à tort (précision 1,000)",
             "**Gouverner** par consentement : finalité, refus 403, audit"]
    for i, t in enumerate(items):
        chip(s, 0.75 + (i % 2) * 7.35, 2.2 + (i // 2) * 1.4, 7.15, 1.05, t, 17, TINT, DARK,
             bold=False)
    band(s, 5.3, "Une démarche progressive — **MVP → Spark → Big Data** — où chaque "
                 "technologie répond à un besoin, et chaque résultat se vérifie dans le dépôt.",
         18, 1.3)


def s21_merci(prs):
    s = new_slide(prs)
    text(s, 0, 3.6, W, 1.0, "Merci", 54, PRIMARY, align=PP_ALIGN.CENTER)
    text(s, 0, 4.75, W, 0.5, "Vos questions", 22, MUTED, italic=True, align=PP_ALIGN.CENTER)


def build():
    prs = Presentation()
    prs.slide_width = _in(W)
    prs.slide_height = _in(H)
    for fn in (s01_cover, s02_entreprise, s03_question, s04_contexte, s05_objectifs, s06_plan,
               s07_etat_art, s08_criteres, s09_choix, s10_existant_modules, s11_points_forts,
               s12_limites, s13_architecture, s14_fonctionnalites, s15_cas, s16_resultats,
               s17_avant_apres, s18_demo, s19_perspectives, s20_conclusion, s21_merci):
        fn(prs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print("OK  {0}".format(OUT))
    print("Slides : {0}".format(len(prs.slides)))


if __name__ == "__main__":
    build()
