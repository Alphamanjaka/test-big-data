"""Génère le deck de soutenance M2 MBDS du projet patients (PowerPoint 16:9).

Usage :
    python scripts/dev/build_soutenance_pptx.py

Sortie : documents/slide_soutenance/V2soutenance_m2_mmt_alpha.pptx
Dépendance dev (venv local, hors deps du projet) : python-pptx>=0.6.21.

Structure des 21 slides alignée sur le deck de référence (V2soutenance_m2_hasina),
contenu = plateforme patients (Mon_Memoire). Les figures projetées proviennent de
documents/figures/ (rendues par render_mermaid_figures.py).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

BASE = Path(__file__).resolve().parents[4]
FIGURES = BASE / "documents" / "figures"
OUT = BASE / "documents" / "slide_soutenance" / "V2soutenance_m2_mmt_alpha.pptx"

PRIMARY = RGBColor(0x10, 0x6D, 0x8E)
SECOND = RGBColor(0x2F, 0xA8, 0xB5)
GOLD = RGBColor(0xE8, 0xA8, 0x2E)
DARK = RGBColor(0x0B, 0x2E, 0x4F)
TEXT = RGBColor(0x20, 0x30, 0x3C)
MUTED = RGBColor(0x5A, 0x6B, 0x79)
BG = RGBColor(0xF0, 0xF6, 0xF9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ZEBRA = RGBColor(0xEA, 0xF2, 0xF6)

FONT = "Calibri"
FOOTER_LEFT = "Madagascar Medical Technology — M2 MBDS"
FOOTER_RIGHT = "RANOMENJANAHARY M. Alpha · Septembre 2026"


def _solid(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def _textbox(slide, x, y, w, h, text, size, color, bold=False, align=PP_ALIGN.LEFT,
             italic=False):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    r.font.name = FONT
    return box


def _new_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _rule(slide, x, y, w, color=GOLD, h=0.06):
    _solid(slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h), color)


def _chip(shape, label, size=16):
    tf = shape.text_frame
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = WHITE
    r.font.name = FONT


def logo_chip(slide, x, y, h=0.42, dark=False):
    chip = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(0.95), Inches(h))
    _solid(chip, DARK if dark else PRIMARY)
    chip.adjustments[0] = 0.25
    _chip(chip, "MMT")
    _textbox(slide, x + Inches(1.12), y + Inches(0.03), Inches(3.4), Inches(h) - Inches(0.06),
             "Madagascar Medical Technology", 11, MUTED)


def footer(slide):
    _rule(slide, 0, Inches(7.18), Inches(13.333), SECOND, Inches(0.03))
    _textbox(slide, Inches(0.6), Inches(7.24), Inches(7.0), Inches(0.22), FOOTER_LEFT, 10, MUTED)
    _textbox(slide, Inches(7.0), Inches(7.24), Inches(5.73), Inches(0.22), FOOTER_RIGHT, 10, MUTED,
             align=PP_ALIGN.RIGHT)


def title_block(slide, section, title):
    _textbox(slide, Inches(0.9), Inches(0.4), Inches(11.5), Inches(0.3),
             section.upper(), 12, SECOND, bold=True)
    _textbox(slide, Inches(0.88), Inches(0.66), Inches(11.8), Inches(0.85), title, 25, DARK, bold=True)
    _rule(slide, Inches(0.92), Inches(1.5), Inches(1.6))


def add_image(slide, fig, x, y, h):
    img = Image.open(FIGURES / fig)
    ratio = img.width / img.height
    slide.shapes.add_picture(str(FIGURES / fig), x, y, height=h, width=int(h * ratio))


def cover(prs):
    s = _new_slide(prs)
    _solid(s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height), BG)
    _solid(s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(0.06), prs.slide_width, Inches(0.14)),
           PRIMARY)
    _rule(s, 0, Inches(0.2), prs.slide_width, GOLD, Inches(0.05))
    logo_chip(s, Inches(0.7), Inches(0.55), dark=True)
    _textbox(s, Inches(0.7), Inches(2.05), Inches(11.9), Inches(0.45),
             "M2 MBDS — Stage · Plateforme Big Data de gestion et de gouvernance des données patients",
             15, SECOND, bold=True)
    _textbox(s, Inches(0.7), Inches(2.6), Inches(11.9), Inches(1.5),
             "Concevoir une plateforme Big Data de gestion et de gouvernance des données patients",
             33, DARK, bold=True)
    _textbox(s, Inches(0.7), Inches(4.2), Inches(11.9), Inches(0.5),
             "Nettoyage · Déduplication explicable · Contrôle d'accès par consentement", 18, TEXT)
    _textbox(s, Inches(0.7), Inches(5.1), Inches(11.9), Inches(0.4),
             "Données exclusivement synthétiques — la confidentialité est un actif de démonstration.",
             13, MUTED, italic=True)
    _textbox(s, Inches(0.7), Inches(6.2), Inches(11.9), Inches(0.45),
             "Présenté par : RANOMENJANAHARY M. Alpha", 16, TEXT, bold=True)
    _textbox(s, Inches(0.7), Inches(6.7), Inches(11.9), Inches(0.4),
             "Madagascar Medical Technology — Septembre 2026", 13, MUTED)


def divider(prs, title, sub=None):
    s = _new_slide(prs)
    _textbox(s, Inches(0.9), Inches(2.55), Inches(11.5), Inches(1.0), title, 37, DARK, bold=True)
    _rule(s, Inches(0.94), Inches(3.7), Inches(1.9), GOLD, Inches(0.07))
    if sub:
        _textbox(s, Inches(0.94), Inches(4.0), Inches(11.3), Inches(0.6), sub, 16, TEXT)
    footer(s)


def bullets(slide, items, x, y, w, h, size=15, color=TEXT, gap=6):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    first = True
    for level, text in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        p.space_after = gap
        if text.startswith("**"):
            end = text.find("**", 2)
            lead, rest = text[2:end], text[end + 2:]
            r = p.add_run()
            r.text = lead
            r.font.bold = True
            r.font.size = Pt(size)
            r.font.color.rgb = color
            r.font.name = FONT
            if rest:
                r = p.add_run()
                r.text = rest
                r.font.size = Pt(size)
                r.font.color.rgb = color
                r.font.name = FONT
        else:
            r = p.add_run()
            r.text = ("•  " if level == 0 else "–  ") + text
            r.font.size = Pt(size)
            r.font.color.rgb = color
            r.font.name = FONT
    return box


def _set_cell(cell, text, size, color=TEXT, bold=False, fill=None):
    if fill is not None:
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill
    cell.margin_left = Inches(0.1)
    cell.margin_right = Inches(0.08)
    cell.margin_top = Inches(0.04)
    cell.margin_bottom = Inches(0.04)
    p = cell.text_frame.paragraphs[0]
    if text.startswith("**"):
        end = text.find("**", 2)
        lead, rest = text[2:end], text[end + 2:]
        r = p.add_run()
        r.text = lead
        r.font.bold = True
        r.font.color.rgb = color
        if rest:
            r = p.add_run()
            r.text = rest
            r.font.color.rgb = color
        for rr in p.runs:
            rr.font.size = Pt(size)
            rr.font.name = FONT
        return
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.name = FONT


def content(prs, section, title, items=None, fig=None, fig_x=None, fig_y=None, fig_h=None,
            body_w=11.6, table=None, table_h=None):
    s = _new_slide(prs)
    title_block(s, section, title)
    if table is not None:
        headers, rows = table
        ncol = len(headers)
        gtbl = s.shapes.add_table(len(rows) + 1, ncol, Inches(0.95), Inches(1.85),
                                  Inches(11.45), Inches(table_h or 0.5 + 0.45 * len(rows))).table
        for c, htext in enumerate(headers):
            _set_cell(gtbl.cell(0, c), htext, 13, WHITE, bold=True, fill=PRIMARY)
        for ri, row in enumerate(rows, start=1):
            fill = ZEBRA if ri % 2 == 0 else WHITE
            for ci, value in enumerate(row):
                _set_cell(gtbl.cell(ri, ci), value, 12, TEXT, fill=fill)
    elif items:
        bullets(s, items, Inches(0.95), Inches(1.9), Inches(body_w), Inches(5.1))
    if fig:
        add_image(s, fig, fig_x, fig_y, fig_h)
    footer(s)
    return s


def code_card(slide, lines, x, y, w, h):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    _solid(card, RGBColor(0xE4, 0xF0, 0xF4))
    card.adjustments[0] = 0.06
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.15)
    first = True
    for line in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = 2
        r = p.add_run()
        r.text = line
        r.font.name = "Consolas"
        r.font.size = Pt(14)
        r.font.color.rgb = TEXT
    return card


def card(slide, title, body, x, y, w, h):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    _solid(shape, BG)
    shape.adjustments[0] = 0.05
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18)
    tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.1)
    tf.margin_bottom = Inches(0.08)
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = title
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = DARK
    r.font.name = FONT
    for chunk in body:
        p = tf.add_paragraph()
        p.space_before = 3
        r = p.add_run()
        r.text = chunk
        r.font.size = Pt(12.5)
        r.font.color.rgb = TEXT
        r.font.name = FONT


def plan_slide(prs):
    s = _new_slide(prs)
    title_block(s, "Sommaire", "Cinq parties")
    names = [
        ("1. État de l'art", "solutions du domaine : MPI, MDM, Data Lake santé, Entity Resolution, FHIR"),
        ("2. Étude de l'existant", "les SI de MMT : points forts, limites"),
        ("3. Solution proposée", "architecture Medallion + moteur de déduplication + gouvernance"),
        ("4. Fonctionnalités principales", "centraliser · normaliser · dédupliquer · consentir · auditer"),
        ("5. Démonstration", "tests, évaluation ground-truth, pipeline bout en bout"),
    ]
    y = Inches(2.1)
    for name, sub in names:
        card(s, name, [sub], Inches(1.0), y, Inches(6.6), Inches(0.78))
        y += Inches(0.95)
    footer(s)


def thankyou(prs):
    s = _new_slide(prs)
    _solid(s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height), BG)
    _textbox(s, Inches(0.9), Inches(2.6), Inches(11.5), Inches(1.0), "Merci — Vos questions",
             38, DARK, bold=True)
    _rule(s, Inches(0.94), Inches(3.6), Inches(1.9), GOLD, Inches(0.07))
    _textbox(s, Inches(0.94), Inches(3.95), Inches(11.3), Inches(0.5),
             "Dépôt unique Mon_Memoire · rapport de stage · mémoire M2 MBDS", 16, TEXT)
    _textbox(s, Inches(0.94), Inches(4.4), Inches(11.3), Inches(0.4),
             "RANOMENJANAHARY M. Alpha — Madagascar Medical Technology", 14, SECOND, bold=True)
    footer(s)


def build():
    prs = Presentation()
    prs.slide_width = 14630400
    prs.slide_height = 8229600

    cover(prs)

    content(
        prs,
        "Contexte du stage",
        "Trois systèmes d'information médicaux indépendants",
        [
            (0, "**MMT** exploite trois SI conçus séparément : **MAVIS** (Odoo/HMS), "
                "**MMT_DB** (GNU Health) et **CLINIQUE** (SQLite)."),
            (0, "**MAVIS** : 1 260 tables détectées sur le nœud distant ; réplique locale de "
                "**73 090 lignes** (jointure patient `partner_id` **9 791 / 9 791**)."),
            (0, "**MMT_DB** : 9 tables extraites (60 271 lignes) ; **CLINIQUE** : 4 tables "
                "(54 582 lignes) — FK découvertes automatiquement."),
            (0, "Chaque base est **intègre avec elle-même** : le défi n'est pas la qualité, "
                "c'est l'absence d'équivalent **entre** les bases."),
            (0, "Jeu de démonstration reproductible : générateur synthétique à **3 sources** "
                "(pharmacy, consultation, imaging), seed 42."),
        ],
    )

    s = content(
        prs,
        "Question",
        "Un même patient, plusieurs systèmes, trois identités",
        [
            (0, "Trois services, trois formats, trois identifiants — et **trois colonnes pour "
                "le même champ**."),
            (1, "`sexe` (pharmacy) · `genre` (consultation) · `sex` (imagerie)"),
        ],
    )
    code_card(s, [
        "Pharmacie     → Jean Rakoto  · CIN 101 02404 5",
        "Consultation  → Rakoto Jean  · CIN 101024045",
        "Imagerie      → J. RAKOTO    · CIN absent",
    ], Inches(0.95), Inches(3.5), Inches(6.9), Inches(1.55))
    bullets(s, [
        (0, "Résultat : **dossier éclaté**, **agrégats faux**, **accès non maîtrisés**."),
        (0, "Qui a accès à quel champ, pour quelle finalité, et qui l'a réellement lu ?"),
    ], Inches(0.95), Inches(5.35), Inches(6.9), Inches(1.4))
    logo_chip(s, Inches(10.6), Inches(6.5))

    content(
        prs,
        "Contexte et problématique",
        "Des données sensibles, dispersées et non gouvernées",
        [
            (0, "**Dispersion** : chaque service tient son propre registre, sans identifiant commun."),
            (0, "**Hétérogénéité** : genres (`H/F`, homme/femme, `sex`), dates (`DD/MM/YYYY`, "
                "`YYYY-MM-DD`), CIN espacé ou compact."),
            (0, "**Processus manuel** : recoupements lents, erreurs humaines, aucune trace."),
            (0, "**Absence de gouvernance** : pas de consentement par finalité, pas d'audit d'accès."),
            (0, "Enjeu sécurité : les données de santé imposent **traçabilité** et **refus possible**."),
        ],
        fig="fig-3.png", fig_x=Inches(8.1), fig_y=Inches(1.9), fig_h=Inches(4.3),
    )

    content(
        prs,
        "Objectifs du projet",
        "Centraliser, dédupliquer, gouverner",
        [
            (0, "**Centraliser** dans un Data Lake (zones RAW → SILVER → GOLD, Medallion)."),
            (0, "**Normaliser** vers un modèle canonique + pivot FHIR (genre, dates, CIN)."),
            (0, "**Dédupliquer de façon explicable** : chaque fusion justifiée par un score "
                "(master patient + identity map)."),
            (0, "**Gouverner les accès** par **consentement purpose-by-purpose** + audit d'accès, "
                "rôles et clés API."),
            (0, "Données **exclusivement synthétiques** — la confidentialité est un actif de "
                "démonstration."),
        ],
    )

    plan_slide(prs)

    content(
        prs,
        "État de l'art",
        "Points forts et limites des solutions du domaine",
        table=(
            ("Solution", "Points forts", "Limites"),
            (
                ("MPI / DMP", "référentiel d'identité maître, vue unique du patient",
                 "ne reconstruit pas l'identité partagée absente"),
                ("MDM", "gouvernance des données de référence",
                 "coûteux, rigide face au changement"),
                ("Data Lake santé", "RAW → SILVER → GOLD, schéma-on-read",
                 "sans curation = marécage de données"),
                ("Fellegi–Sunter (1969)", "cadre probabiliste éprouvé de l'Entity Resolution",
                 "seuils et pondérations à calibrer"),
                ("FHIR", "schéma pivot d'échange standard",
                 "lourd si sources très hétérogènes"),
            ),
        ),
        table_h=3.4,
    )

    content(
        prs,
        "État de l'art",
        "Critères de comparaison",
        [
            (0, "**Normalisation** : un champ vers un format canonique, quelle que soit la source."),
            (0, "**Identité partagée** : reconstruire un master patient absent des sources."),
            (0, "**Explicabilité** : chaque décision de fusion justifiée et traçable (exigence santé)."),
            (0, "**Scalabilité** : passage du MVP (Pandas) à Spark sans changer la logique."),
            (0, "**Gouvernance** : consentement par finalité, audit d'accès, rôles et clés API."),
            (0, "**Coût** : 100 % open source (Hadoop, Spark, Hive, PostgreSQL)."),
        ],
    )

    content(
        prs,
        "État de l'art",
        "Choix technologique : une combinaison synergique",
        [
            (0, "**Apache Spark** — traitement distribué Medallion (RAW → SILVER → GOLD) sur "
                "HDFS/Hive ; il vient **après** le besoin, pas « Big Data pour le Big Data »."),
            (0, "**Entity Resolution** (Fellegi–Sunter + RapidFuzz) — déduplication exacte **et** "
                "probabiliste, explicable, seuil 0,80 déclaré en YAML ; **parité Pandas = Spark**."),
            (0, "**FHIR** — schéma pivot pour normaliser des sources aux formats divergents."),
            (0, "Le ground-truth sert de **validation** (vérité terrain jamais fournie à "
                "l'algorithme)."),
        ],
    )

    content(
        prs,
        "Étude de l'existant",
        "Modules de la plateforme",
        [
            (0, "**Ingestion / Medallion** : RAW → SILVER → GOLD, 4 étapes idempotentes."),
            (0, "**Normalisation** : modèle canonique `CanonicalPatient` + écriture FHIR."),
            (0, "**Déduplication** : blocage → exact → probabiliste → fusion (identity map)."),
            (0, "**Gouvernance** : consentements par finalité (`api_access`, `research`, "
                "`analytics`) et audit d'accès, refus fail-closed."),
            (0, "**Exposition** : API REST gouvernance + API FastAPI à contrôle de consentement, "
                "rôles et clés API hachées."),
        ],
    )

    content(
        prs,
        "Étude de l'existant",
        "Points forts des systèmes en place",
        [
            (0, "Base **intègre avec elle-même** : jointure MAVIS `partner_id` **9 791 / 9 791**."),
            (0, "Volume réel significatif : **1 260 tables**, réplique **73 090 lignes**."),
            (0, "Schéma riche à dériver : 5 FK MMT_DB découvertes automatiquement ; "
                "`PRAGMA foreign_key_check` = 0 violation côté CLINIQUE."),
            (0, "Une **vérité terrain** (`identity_mapping.csv`) existe côté générateur : elle sert "
                "à **évaluer** la déduplication, jamais à la piloter."),
        ],
    )

    content(
        prs,
        "Étude de l'existant",
        "Limitations identifiées",
        [
            (0, "**Bases multiples et non uniformes** : trois SI sans identifiant commun."),
            (0, "**Formats hétérogènes** : genres, dates, CIN divergents entre les tables."),
            (0, "**Processus entièrement manuel** : import et recoupement, erreurs humaines, "
                "temps longs."),
            (0, "**Aucune gouvernance des accès** : impossible de dire qui a lu quoi, et pour "
                "quelle finalité."),
            (0, "Le problème n'est pas la qualité d'une base, c'est **l'absence de pont entre "
                "elles**."),
        ],
    )

    content(
        prs,
        "Solution proposée",
        "Architecture du système",
        [
            (0, "**Medallion** RAW → SILVER → GOLD sur **HDFS/Hive/Spark** (VM 8 Go)."),
            (0, "**Moteur de déduplication** `engine/` (Pandas + Spark) branché en SILVER : "
                "master patient + identity map."),
            (0, "**PostgreSQL central** : masters, consentements, audit, clés API — contrôlé "
                "par l'API FastAPI (finalité obligatoire)."),
            (0, "**API de reporting** Flask `/api/governance/*` (déduplication, consentement) ; "
                "frontend DataViz optionnel."),
        ],
        fig="fig-5.png", fig_x=Inches(8.0), fig_y=Inches(1.9), fig_h=Inches(4.3),
    )

    content(
        prs,
        "Fonctionnalités principales",
        "Du fichier source au consentement vérifié",
        [
            (0, "**Centralisation multi-sources** : les données arrivent telles quelles dans RAW."),
            (0, "**Normalisation automatique** : un champ → un format (genre `M/F`, dates ISO, CIN)."),
            (0, "**Déduplication explicable** : `master_patient_id` + `match_method` + "
                "`match_score` + explication — jamais de fusion arbitraire."),
            (0, "**Consentement purpose-by-purpose** : finalité non consentie → **403** + "
                "`refusal_reason` journalisé."),
            (0, "**Audit d'accès** et rôles (admin / analyst / viewer) + clés API hachées."),
        ],
    )

    content(
        prs,
        "Cas d'utilisation",
        "CU1 → CU3 : le parcours d'une donnée",
        [
            (0, "**CU1 — Ingérer** : les lignes sources arrivent **telles quelles** dans RAW "
                "(schéma-on-read) ; aucune transformation à l'écriture."),
            (0, "**CU2 — Normaliser** : genre, dates et CIN ramenés à un modèle canonique ; un "
                "champ douteux reste **vide**, il ne corrompt pas une clé exacte."),
            (0, "**CU3 — Dédupliquer** : 3 index de blocage (préfixe de nom, naissance, CIN) → "
                "exact puis probabiliste → fusion justifiée."),
            (0, "Cas limite : un **refus de consentement** est journalisé (fail-closed) — on ne "
                "sert jamais ce qu'on n'a pas le droit de lire."),
        ],
    )

    content(
        prs,
        "Cas d'utilisation",
        "Résultats mesurés au run de référence",
        table=(
            ("Mesure", "Valeur vérifiée"),
            (
                ("Pipeline", "RAW → SILVER → GOLD **4/4 vert**"),
                ("SILVER `patient_fhir`", "214 lignes (76 + 76 + 62)"),
                ("Masters / doublons", "**145** masters · **69** doublons · `match_method=exact`"),
                ("Taux de doublons", "**32,24 %** (`mocked: false`, données réelles Hive)"),
                ("API gouvernance", "`test_api.py` **3/3 PASS** sur données réelles"),
            ),
        ),
        table_h=2.6,
    )

    content(
        prs,
        "Cas d'utilisation",
        "Avant / après : de l'humain au moteur",
        [
            (0, "**Avant** : recoupement manuel entre services — lent, erreurs humaines, "
                "**aucune explication conservée**."),
            (0, "**Après** : pipeline automatisé bout en bout, décisions **expliquées** (score, "
                "méthode) et **auditées**."),
            (0, "**Évaluation ground-truth** : **zéro faux positif** sur easy / medium / hard "
                "(Precision 1.000) ; rappel hard relevé à **0.422** grâce à la clé CIN."),
            (0, "**Parité Pandas = Spark** : décisions identiques (TP=307, FP=0, FN=420 sur hard)."),
        ],
    )

    content(
        prs,
        "Démonstration",
        "Vidéo 3:30 enregistrée — aucun point de défaillance le jour J",
        table=(
            ("Plan", "Contenu filmé", "Durée"),
            (
                ("1", "`pytest projet/code-source/tests` — moteur + gouvernance **54/54**", "1:00"),
                ("2", "Évaluation hard : P/R/F1 (Precision 1.000)", "1:00"),
                ("3", "`run_pipeline.sh` bout en bout (RAW → SILVER → GOLD)", "1:30"),
                ("Repli", "compteurs figés : 214 · 145 · 69 · 32,24 %", "0:30"),
            ),
        ),
        table_h=2.6,
    )

    content(
        prs,
        "Perspectives",
        "Après la soutenance",
        [
            (0, "**Enrichir le mapping FHIR** : encounters / conditions / observations → "
                "`patient_events_gold`."),
            (0, "**Calibrer seuil et pondérations** via le ground-truth ; peupler le consentement "
                "central en base."),
            (0, "**Générateur d'homophones** pour solliciter enfin le cas adversariaire des faux "
                "positifs."),
            (0, "**Passage à l'échelle** : volume, intégration continue, export VM."),
            (0, "Le frontend DataViz (optionnel) reste à industrialiser au-delà du PoC."),
        ],
    )

    content(
        prs,
        "Conclusion",
        "Réponse à la problématique",
        [
            (0, "**Centraliser** un même patient dispersé entre plusieurs systèmes."),
            (0, "**Nettoyer et standardiser** vers un modèle canonique + pivot FHIR."),
            (0, "**Dédupliquer de façon explicable** : zéro fusion à tort démontré, rappel calibré."),
            (0, "**Gouverner par consentement** : finalité obligatoire, refus 403, audit d'accès."),
            (0, "Architecture **Big Data** (Medallion) sur données **exclusivement synthétiques**."),
        ],
    )

    thankyou(prs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"OK  {OUT}")
    print(f"Slides : {len(prs.slides._sldIdLst)}")


if __name__ == "__main__":
    build()