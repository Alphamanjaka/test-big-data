"""Génère le deck de soutenance M2 MBDS, version refondue (PowerPoint 16:9, 13,33 × 7,5 pouces).

Usage :
    python scripts/dev/build_soutenance_deck.py

Sortie : documents/slide_soutenance/Soutenance_M2_MBDS_RANOMENJANAHARY.pptx
(l'ancien deck V2soutenance_m2_mmt_alpha.pptx et son générateur ont été retirés le 28/09/2026 ; voir l'historique Git).

Plan : celui du deck de référence (titre, entreprise, question, contexte, objectifs, plan,
état de l'art, existant, solution, fonctionnalités, résultats, démonstration, perspectives,
conclusion, merci), en 20 slides pour 15 à 20 minutes. Chaque slide porte un titre
affirmatif, un seul message et un visuel natif (formes, tableau ou graphique modifiables).
Style aligné sur le rapport : bleu marine dominant, fond blanc, Calibri. Bandeau des logos de
l'établissement et pied de page sur chaque slide, comme dans la référence.

Tous les chiffres sont ceux du rapport (données synthétiques) ; les notes de présentation de
chaque slide donnent le message à dire. Une capture déposée dans documents/captures/ (C07)
remplace le cadre réservé de la slide de démonstration.
"""

from __future__ import annotations

import re
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from pptx_anim import add_entrance, add_transition

ROOT = Path(__file__).resolve().parents[4]
IMAGES = ROOT / "documents" / "image"
FIGURES = ROOT / "documents" / "figures"
LOGOS_DIR = FIGURES / "logos"
CAPTURES = ROOT / "documents" / "captures"
OUT = ROOT / "documents" / "slide_soutenance" / "Soutenance_M2_MBDS_RANOMENJANAHARY.pptx"

W, H = 13.333, 7.5
MX = 0.6                      # marge horizontale
TOP = 1.55                    # début de la zone de contenu
BOTTOM = 6.85                 # fin de la zone de contenu (pied de page en dessous)

NAVY = RGBColor(0x1F, 0x38, 0x64)
BLUE = RGBColor(0x2E, 0x55, 0x97)
SKY = RGBColor(0x8E, 0xAA, 0xDB)
TINT = RGBColor(0xF1, 0xF4, 0xF9)
TINT2 = RGBColor(0xE2, 0xE9, 0xF3)
AMBER = RGBColor(0xC7, 0x84, 0x00)
AMBER_T = RGBColor(0xFB, 0xF1, 0xDC)
INK = RGBColor(0x1D, 0x24, 0x33)
MUTED = RGBColor(0x5B, 0x64, 0x75)
LINE = RGBColor(0xC9, 0xD2, 0xE0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
OK = RGBColor(0x2E, 0x7D, 0x4F)
OK_T = RGBColor(0xE5, 0xF3, 0xEA)
KO = RGBColor(0xB3, 0x26, 0x1E)
KO_T = RGBColor(0xFB, 0xE7, 0xE5)
RAW_C, SILVER_C, GOLD_C = RGBColor(0x8A, 0x6F, 0x55), RGBColor(0x6F, 0x7B, 0x8C), RGBColor(0xB8, 0x86, 0x0B)

FONT = "Calibri"
MONO = "Consolas"
TITLE = "Plateforme Big Data de gestion et de gouvernance des données patients"
SUBTITLE = "Nettoyage, déduplication et contrôle d'accès basé sur le consentement"
AUTHOR = "RANOMENJANAHARY Manjaka Alpha"
DATE = "Octobre 2026"
FOOTER = f"« Plateforme Big Data de gouvernance des données patients » présenté par {AUTHOR}"
INSTITUTION_LOGOS = [IMAGES / "logo-ituniversity.png", IMAGES / "logo-mbds.jpg", IMAGES / "logo-uca.png"]
MMT_LOGO = IMAGES / "mmt-logo.png"


# --------------------------------------------------------------------------- primitives

class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width = Inches(W)
        self.prs.slide_height = Inches(H)
        self.blank = self.prs.slide_layouts[6]
        self.total = 20
        self.n = 0

    # -- texte --------------------------------------------------------------------------
    @staticmethod
    def runs(paragraph, text, size, color=INK, bold=False, font=FONT, italic=False):
        """Ajoute `text` au paragraphe ; **gras**, `code` et *italique* reconnus."""
        for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)", text):
            if not part:
                continue
            r = paragraph.add_run()
            f = r.font
            f.size = Pt(size)
            f.color.rgb = color
            f.bold = bold
            f.italic = italic
            f.name = font
            if part.startswith("**"):
                r.text = part[2:-2]
                f.bold = True
            elif part.startswith("`"):
                r.text = part[1:-1]
                f.name = MONO
                f.size = Pt(size - 1)
            elif part.startswith("*"):
                r.text = part[1:-1]
                f.italic = True
            else:
                r.text = part

    def text(self, slide, x, y, w, h, lines, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, font=FONT, spacing=None, italic=False, bullets=False):
        """Zone de texte ; `lines` : une chaîne ou une liste de paragraphes."""
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.02)
        tf.margin_top = tf.margin_bottom = Inches(0.02)
        tf.vertical_anchor = anchor
        for i, line in enumerate([lines] if isinstance(lines, str) else lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            if spacing:
                p.space_after = Pt(spacing)
            if bullets:
                self._bullet(p)
            self.runs(p, line, size, color, bold, font, italic)
        return tb

    @staticmethod
    def _bullet(p):
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(Inches(0.25)))
        pPr.set("indent", str(-Inches(0.22)))
        bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
        clr = pPr.makeelement(qn("a:buClr"), {})
        srgb = clr.makeelement(qn("a:srgbClr"), {"val": "2E5597"})
        clr.append(srgb)
        pPr.append(clr)
        pPr.append(bu)

    # -- formes -------------------------------------------------------------------------
    def box(self, slide, x, y, w, h, fill=TINT, line=None, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
        s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
            s.adjustments[0] = radius
        if fill is None:
            s.fill.background()
        else:
            s.fill.solid()
            s.fill.fore_color.rgb = fill
        if line is None:
            s.line.fill.background()
        else:
            s.line.color.rgb = line
            s.line.width = Pt(1.25)
        s.shadow.inherit = False
        s.text_frame.margin_left = s.text_frame.margin_right = Inches(0.12)
        return s

    def label_box(self, slide, x, y, w, h, lines, size=15, fill=TINT, color=INK, bold=False,
                  align=PP_ALIGN.CENTER, line=None, radius=0.08):
        s = self.box(slide, x, y, w, h, fill=fill, line=line, radius=radius)
        tf = s.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for i, t in enumerate([lines] if isinstance(lines, str) else lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            self.runs(p, t, size, color, bold)
        return s

    def circle(self, slide, x, y, d, label, fill=NAVY, size=16):
        s = self.box(slide, x, y, d, d, fill=fill, shape=MSO_SHAPE.OVAL)
        tf = s.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        self.runs(p, label, size, WHITE, True)
        return s

    def arrow(self, slide, x1, y1, x2, y2, color=BLUE, width=2.25):
        c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        c.line.color.rgb = color
        c.line.width = Pt(width)
        ln = c.line._get_or_add_ln()
        ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
        return c

    def chevron(self, slide, x, y, w, h, color=BLUE):
        s = self.box(slide, x, y, w, h, fill=color, shape=MSO_SHAPE.RIGHT_ARROW)
        return s

    def picture(self, slide, path, x, y, w=None, h=None):
        kw = {}
        if w:
            kw["width"] = Inches(w)
        if h:
            kw["height"] = Inches(h)
        return slide.shapes.add_picture(str(path), Inches(x), Inches(y), **kw)

    def stat(self, slide, x, y, w, value, label, color=NAVY, vsize=46, lsize=14, fill=TINT, h=1.65):
        self.box(slide, x, y, w, h, fill=fill)
        self.text(slide, x + 0.1, y + 0.12, w - 0.2, 0.85, value, size=vsize, color=color, bold=True,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        dark = fill in (NAVY, BLUE)
        self.text(slide, x + 0.15, y + 0.98, w - 0.3, h - 1.05, label, size=lsize,
                  color=TINT2 if dark else MUTED, align=PP_ALIGN.CENTER)

    # -- gabarit de slide ---------------------------------------------------------------
    def chrome(self, slide, dark=False):
        """Logos de l'établissement (gauche), logo MMT (droite), pied de page et numéro."""
        x = MX
        for logo in INSTITUTION_LOGOS:
            pic = self.picture(slide, logo, x, 0.28, h=0.42)
            x += pic.width / 914400 + 0.35
        self.picture(slide, MMT_LOGO, W - MX - 0.55, 0.2, h=0.6)
        color = SKY if dark else MUTED
        self.text(slide, MX, 7.05, 9.5, 0.3, FOOTER, size=9, color=color)
        self.text(slide, W - MX - 3.0, 7.05, 3.0, 0.3, f"{DATE}   ·   {self.n} / {self.total}", size=9,
                  color=color, align=PP_ALIGN.RIGHT)

    def slide(self, kicker, title, notes):
        self.n += 1
        s = self.prs.slides.add_slide(self.blank)
        self.chrome(s)
        self.text(s, MX, 0.86, 8.0, 0.3, kicker.upper(), size=12, color=AMBER, bold=True)
        self.text(s, MX, 1.08, W - 2 * MX, 0.6, title, size=28, color=NAVY, bold=True)
        s.notes_slide.notes_text_frame.text = notes
        return s

    # -- animation ---------------------------------------------------------------------
    @staticmethod
    def mark(slide):
        """Repère avant la création d'un groupe de formes à animer ensemble."""
        return len(slide.shapes)

    @staticmethod
    def since(slide, mark):
        """Formes créées depuis `mark` : un groupe pour add_entrance."""
        return list(slide.shapes)[mark:]

    def check_geometry(self):
        """PowerPoint refuse d'ouvrir un fichier contenant une forme de taille nulle ou négative,
        ou qui sort du canevas : on échoue ici avec la slide fautive plutôt que d'écrire un
        fichier corrompu."""
        sw, sh = self.prs.slide_width, self.prs.slide_height
        for n, slide in enumerate(self.prs.slides, 1):
            for shape in slide.shapes:
                x, y, w, h = shape.left, shape.top, shape.width, shape.height
                if w < 0 or h < 0 or (w == 0 and h == 0):
                    raise SystemExit(f"Slide {n} : forme « {shape.name} » de taille invalide ({w}, {h}).")
                if x < 0 or y < 0 or x + w > sw + 10 or y + h > sh + 10:
                    raise SystemExit(f"Slide {n} : forme « {shape.name} » hors du canevas.")

    def save(self, out: Path):
        self.check_geometry()
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.prs.save(str(out))
        except PermissionError:
            raise SystemExit(f"Impossible d'écrire {out.name} : le fichier est probablement ouvert "
                             "dans PowerPoint. Fermez-le puis relancez.")


# --------------------------------------------------------------------------- slides

def s01_title(d: Deck):
    d.n += 1
    s = d.prs.slides.add_slide(d.blank)
    x = MX
    for logo in INSTITUTION_LOGOS:
        pic = d.picture(s, logo, x, 0.45, h=0.62)
        x += pic.width / 914400 + 0.5
    d.picture(s, MMT_LOGO, W - MX - 0.85, 0.3, h=0.95)
    d.box(s, 0, 1.75, W, 3.05, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
    d.text(s, MX + 0.2, 2.05, W - 2 * MX - 0.4, 0.4, "SOUTENANCE DE STAGE — MASTER MBDS", size=14,
           color=SKY, bold=True)
    d.text(s, MX + 0.2, 2.5, W - 2 * MX - 0.4, 1.4, TITLE, size=38, color=WHITE, bold=True)
    d.text(s, MX + 0.2, 3.95, W - 2 * MX - 0.4, 0.5, SUBTITLE, size=19, color=TINT2, italic=True)
    d.text(s, MX, 5.15, 7.5, 0.4, f"Présenté par **{AUTHOR}**", size=18, color=INK)
    d.text(s, MX, 5.6, 7.5, 0.9, [
        "Encadrant professionnel : M. Harena Ny Aina RABEMANOELA (MMT)",
        "Encadrant pédagogique : M. Rojo RABENANAHARY (MBDS)",
    ], size=14, color=MUTED, spacing=2)
    d.text(s, W - MX - 4.5, 5.15, 4.5, 0.4, DATE, size=18, color=NAVY, bold=True, align=PP_ALIGN.RIGHT)
    d.text(s, W - MX - 4.5, 5.6, 4.5, 0.9, ["Madagascar Medical Technology", "Département Recherche et Développement"],
           size=14, color=MUTED, align=PP_ALIGN.RIGHT, spacing=2)
    s.notes_slide.notes_text_frame.text = (
        "Bonjour. Je présente mon stage de Master MBDS réalisé chez Madagascar Medical Technology : la "
        "conception d'une plateforme Big Data qui centralise des données patients, reconnaît les doublons de "
        "façon explicable et contrôle chaque accès selon le consentement du patient. Toutes les données "
        "manipulées sont synthétiques.")


def s02_company(d: Deck):
    s = d.slide("Présentation de l'entreprise", "MMT, partenaire technologique des établissements de santé",
                "MMT a été créée en 2009. Elle distribue et maintient du matériel biomédical, fournit des "
                "consommables et gère des stocks. Elle est Business Partner de Siemens Healthineers. Depuis 2024, "
                "son département R&D gère les systèmes d'information médicale : c'est là que j'ai fait mon stage, "
                "du 6 juillet à fin octobre 2026.")
    stats = []
    for i, (v, l) in enumerate([("2009", "création de l'entreprise à Madagascar"),
                                ("Siemens", "Business Partner de Siemens Healthineers"),
                                ("R&D", "département créé en 2024 : systèmes d'information médicale")]):
        m = d.mark(s)
        d.stat(s, MX + i * 2.72, TOP + 0.2, 2.5, v, l, vsize=36 if i else 44, lsize=13, h=1.75)
        stats.append(d.since(s, m))
    m = d.mark(s)
    d.text(s, MX, TOP + 2.3, 8.0, 0.4, "Domaines d'activité", size=17, color=NAVY, bold=True)
    d.text(s, MX, TOP + 2.75, 8.0, 2.2, [
        "Distribution et maintenance de matériels biomédicaux",
        "Fourniture de consommables médicaux",
        "Gestion de stock des établissements partenaires",
        "Systèmes d'information médicale, infrastructures et réseaux",
    ], size=16, bullets=True, spacing=6)
    activities = d.since(s, m)
    m = d.mark(s)
    d.box(s, 9.0, TOP + 0.2, W - MX - 9.0, 4.95, fill=TINT)
    d.picture(s, MMT_LOGO, 9.0 + (W - MX - 9.0 - 1.9) / 2, TOP + 0.5, h=1.9)
    d.text(s, 9.25, TOP + 2.65, W - MX - 9.5, 2.4, [
        "**Le stage**",
        "Département Recherche et Développement",
        "6 juillet → fin octobre 2026 (4 mois)",
        "Encadrant : M. Harena Ny Aina RABEMANOELA",
    ], size=14, color=INK, spacing=5)
    internship = d.since(s, m)
    # Clic 1 : les trois chiffres l'un après l'autre ; clic 2 : activités ; clic 3 : le stage.
    add_entrance(s, [stats, [activities], [internship]], effect="fade")
    add_transition(s, "fade")


def s03_question(d: Deck):
    s = d.slide("Question", "Trois fiches, trois formats… une seule personne ?",
                "Voici le point de départ. Le même patient apparaît dans trois systèmes : Jean Rakoto en "
                "pharmacie, Rakoto Jean en consultation, J. RAKOTO en imagerie, avec des dates et des CIN écrits "
                "différemment. Aucun système ne sait qu'il s'agit de la même personne. Et une seconde question "
                "suit immédiatement : qui a le droit de lire son dossier, et pour quoi faire ?")
    recs = [("Pharmacie", "Jean Rakoto", "101 02404 5 · 1990-01-10"),
            ("Consultation", "Rakoto Jean", "101024045 · 10/01/1990"),
            ("Imagerie", "J. RAKOTO", "101024045 · 1990/01/10")]
    for i, (src, name, meta) in enumerate(recs):
        y = TOP + 0.25 + i * 1.3
        d.box(s, MX, y, 4.6, 1.1, fill=WHITE, line=LINE)
        d.text(s, MX + 0.25, y + 0.1, 4.1, 0.3, src.upper(), size=12, color=BLUE, bold=True)
        d.text(s, MX + 0.25, y + 0.38, 4.1, 0.35, name, size=19, color=INK, bold=True, font=MONO)
        d.text(s, MX + 0.25, y + 0.72, 4.1, 0.3, meta, size=13, color=MUTED, font=MONO)
        d.arrow(s, MX + 4.7, y + 0.55, 6.15, TOP + 1.85, color=SKY, width=2)
    d.circle(s, 6.2, TOP + 1.25, 1.2, "?", fill=AMBER, size=44)
    d.box(s, 7.8, TOP + 0.25, W - MX - 7.8, 3.7, fill=NAVY)
    d.text(s, 8.1, TOP + 0.5, W - MX - 8.4, 3.2, [
        "Comment savoir qu'il s'agit du **même patient** ?",
        "",
        "Et **qui a le droit** de lire ses données, **pour quelle finalité** ?",
    ], size=22, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    d.text(s, MX, TOP + 4.35, W - 2 * MX, 0.4,
           "Cas de référence du projet — données fictives.", size=13, color=MUTED, italic=True)


def s04_context(d: Deck):
    s = d.slide("Contexte et problématique", "Des systèmes complets… mais qui ne se parlent pas",
                "Trois problèmes concrets : la dispersion, puisque les données d'un patient sont réparties "
                "entre plusieurs bases ; l'hétérogénéité, puisque identifiants, libellés et formats diffèrent ; "
                "et l'absence de gouvernance : rien ne dit qui accède à quoi, ni pourquoi. D'où la problématique.")
    items = [("1", "Dispersion", "Les données d'un patient sont réparties entre plusieurs bases, sans vue globale."),
             ("2", "Hétérogénéité", "Identifiants, libellés et formats diffèrent : le genre s'écrit `H/F`, `male/female` ou `Homme/femme`."),
             ("3", "Absence de gouvernance", "Aucun contrôle de qui accède à quelle donnée, ni pour quelle finalité.")]
    cw = (W - 2 * MX - 2 * 0.35) / 3
    for i, (n, t, desc) in enumerate(items):
        x = MX + i * (cw + 0.35)
        d.box(s, x, TOP + 0.2, cw, 2.55, fill=TINT)
        d.circle(s, x + 0.3, TOP + 0.45, 0.6, n)
        d.text(s, x + 1.05, TOP + 0.5, cw - 1.2, 0.5, t, size=20, color=NAVY, bold=True)
        d.text(s, x + 0.3, TOP + 1.25, cw - 0.55, 1.4, desc, size=15)
    d.box(s, MX, TOP + 3.1, W - 2 * MX, 1.95, fill=NAVY)
    d.text(s, MX + 0.4, TOP + 3.25, 3.0, 0.35, "PROBLÉMATIQUE", size=13, color=SKY, bold=True)
    d.text(s, MX + 0.4, TOP + 3.62, W - 2 * MX - 0.8, 1.35,
           "Comment concevoir une plateforme capable d'**intégrer, nettoyer, dédupliquer et centraliser** "
           "des données patients hétérogènes, tout en assurant la **traçabilité des identités** et la "
           "**gouvernance des accès** basée sur le consentement du patient ?",
           size=19, color=WHITE)


def s05_objectives(d: Deck):
    s = d.slide("Objectifs du projet", "Six objectifs, deux contraintes non négociables",
                "Le cahier des charges fixe six objectifs : centraliser, nettoyer, dédupliquer de façon "
                "explicable, gouverner les accès, visualiser et évaluer. Deux contraintes encadrent tout le "
                "travail : les données restent sur les machines de l'établissement, et seules des données "
                "synthétiques sont utilisées.")
    objs = [("Centraliser", "lac de données Medallion RAW → SILVER → GOLD"),
            ("Nettoyer", "modèle canonique et schéma pivot FHIR"),
            ("Dédupliquer", "patient maître, score, méthode et explication"),
            ("Gouverner", "rôles, consentement par finalité, audit"),
            ("Visualiser", "vues de déduplication et de consentement"),
            ("Évaluer", "précision, rappel, F1 sur vérité terrain")]
    cw, ch = (W - 2 * MX - 2 * 0.3) / 3, 1.45
    for i, (t, desc) in enumerate(objs):
        x = MX + (i % 3) * (cw + 0.3)
        y = TOP + 0.15 + (i // 3) * (ch + 0.25)
        d.box(s, x, y, cw, ch, fill=TINT)
        d.circle(s, x + 0.25, y + 0.35, 0.65, str(i + 1))
        d.text(s, x + 1.1, y + 0.2, cw - 1.25, 0.45, t, size=20, color=NAVY, bold=True)
        d.text(s, x + 1.1, y + 0.66, cw - 1.25, 0.75, desc, size=14, color=INK)
    y = TOP + 3.7
    for i, t in enumerate(["**Hébergement interne** : aucune donnée ne quitte l'établissement",
                           "**Données exclusivement synthétiques** : aucune donnée réelle de patient"]):
        cw2 = (W - 2 * MX - 0.3) / 2
        d.label_box(s, MX + i * (cw2 + 0.3), y, cw2, 0.95, t, size=16, fill=AMBER_T, color=INK)


def s06_plan(d: Deck):
    s = d.slide("Plan", "Déroulé de la présentation",
                "Je présente d'abord l'état de l'art et l'existant, puis la solution et ses fonctionnalités, "
                "les résultats mesurés, une démonstration, et enfin les limites et perspectives.")
    parts = [("État de l'art", "notions clés, solutions du marché"),
             ("Étude de l'existant", "trois systèmes, leurs limites"),
             ("Solution proposée", "démarche en trois niveaux, architecture"),
             ("Fonctionnalités et résultats", "déduplication, gouvernance, évaluation"),
             ("Démonstration et perspectives", "démo, limites, suite du projet")]
    cw = (W - 2 * MX - 4 * 0.25) / 5
    for i, (t, desc) in enumerate(parts):
        x = MX + i * (cw + 0.25)
        d.box(s, x, TOP + 0.9, cw, 3.1, fill=TINT)
        d.circle(s, x + (cw - 0.95) / 2, TOP + 0.4, 0.95, str(i + 1), size=26)
        d.text(s, x + 0.2, TOP + 1.65, cw - 0.4, 0.95, t, size=19, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        d.text(s, x + 0.2, TOP + 2.65, cw - 0.4, 1.2, desc, size=14, color=MUTED, align=PP_ALIGN.CENTER)


def s07_notions(d: Deck):
    s = d.slide("État de l'art", "Quatre notions structurent la solution",
                "Quatre notions reviennent partout. L'ELT : on charge le brut d'abord, on transforme ensuite. "
                "Le modèle Medallion : trois zones de qualité croissante, rejouables. Le Master Patient Index : "
                "l'annuaire qui reconnaît le même patient et lui donne un identifiant unique. Et le consentement "
                "par finalité : le patient autorise un usage précis, jamais un accès global ; sans avis, c'est un refus.")
    img = FIGURES / "notions_cles.png"
    h = BOTTOM - TOP - 0.05
    w = h * 3000 / 2300
    d.picture(s, img, (W - w) / 2, TOP, h=h)


def s08_market(d: Deck):
    s = d.slide("État de l'art", "Aucune solution du marché ne coche les six critères",
                "J'ai comparé six solutions sur six critères, sur la base de leur documentation — aucune n'a été "
                "installée. Les plus complètes sur l'identité, EMPI et Talend, sont lourdes, sous licence, et "
                "Azure est un service cloud, incompatible avec l'hébergement interne. D'où le choix d'une chaîne "
                "sur mesure, adossée aux standards : Fellegi-Sunter, FHIR, Medallion.")
    header = ["Critère", "EMPI", "Talend", "Azure", "HAPI", "Splink", "Atlas", "Stage"]
    rows = [("Déduplication explicable", "✔", "✔", "✖", "✖", "◐", "✖", "✔"),
            ("Interopérabilité FHIR", "◐", "✖", "✔", "✔", "✖", "✖", "✔"),
            ("Rôle, consentement, audit", "◐", "◐", "✔", "✖", "✖", "◐", "✔"),
            ("Montée en charge Big Data", "◐", "✔", "✔", "✖", "✔", "✔", "✔"),
            ("Hébergement interne", "✔", "✔", "✖", "✔", "✔", "✔", "✔"),
            ("VM 8 Go et Python 3.8", "✖", "✖", "✖", "✖", "◐", "✖", "✔")]
    tw, th = W - 2 * MX, 3.9
    gt = s.shapes.add_table(len(rows) + 1, len(header), Inches(MX), Inches(TOP + 0.1), Inches(tw), Inches(th))
    tbl = gt.table
    tbl.columns[0].width = Inches(3.7)
    for j in range(1, len(header)):
        tbl.columns[j].width = Inches((tw - 3.7) / (len(header) - 1))
    colors = {"✔": OK, "✖": KO, "◐": AMBER}
    for i, row in enumerate([header] + list(rows)):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.1)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if i == 0:
                cell.fill.fore_color.rgb = NAVY if j < len(header) - 1 else AMBER
            elif j == len(header) - 1:
                cell.fill.fore_color.rgb = AMBER_T
            else:
                cell.fill.fore_color.rgb = TINT if i % 2 else WHITE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            if i == 0:
                d.runs(p, val, 15, WHITE, True)
            elif j == 0:
                d.runs(p, val, 15, INK, True)
            else:
                d.runs(p, val, 20, colors[val], True)
    d.text(s, MX, TOP + 4.2, W - 2 * MX, 0.4,
           "✔ capacité annoncée   ◐ partielle   ✖ absente — comparaison documentaire, aucun produit installé.",
           size=13, color=MUTED, italic=True)
    d.label_box(s, MX, TOP + 4.65, W - 2 * MX, 0.6,
                "Décision : une **chaîne sur mesure adossée aux standards** (Fellegi-Sunter, FHIR, Medallion)",
                size=17, fill=TINT2, color=NAVY)


def s09_existing(d: Deck):
    s = d.slide("Étude de l'existant", "Trois systèmes riches, cohérents… et isolés",
                "Trois systèmes ont été capturés. MAVIS, un ERP Odoo avec module hospitalier : 1 260 tables sur le "
                "nœud distant, 11 retenues. MMT_DB, sous GNU Health : 60 271 lignes. CLINIQUE, en SQLite : 54 582 "
                "lignes et aucune violation de clé. Chaque base est cohérente avec elle-même ; ce qui manque, "
                "c'est le pont entre elles.")
    systems = [("MAVIS", "Odoo + module hospitalier · PostgreSQL distant",
                [("73 090", "lignes en réplique locale"), ("1 260", "tables détectées, 11 retenues")]),
               ("MMT_DB", "GNU Health · PostgreSQL local",
                [("60 271", "lignes dans 9 tables"), ("5", "clés étrangères découvertes")]),
               ("CLINIQUE", "SQLite",
                [("54 582", "lignes dans 4 tables"), ("0", "violation de clé étrangère")])]
    cw = (W - 2 * MX - 2 * 0.35) / 3
    for i, (name, socle, stats) in enumerate(systems):
        x = MX + i * (cw + 0.35)
        d.box(s, x, TOP + 0.15, cw, 4.05, fill=TINT)
        d.text(s, x + 0.3, TOP + 0.3, cw - 0.6, 0.5, name, size=24, color=NAVY, bold=True)
        d.text(s, x + 0.3, TOP + 0.82, cw - 0.6, 0.5, socle, size=13, color=MUTED)
        for k, (v, l) in enumerate(stats):
            y = TOP + 1.45 + k * 1.3
            d.text(s, x + 0.3, y, cw - 0.6, 0.65, v, size=36, color=BLUE, bold=True)
            d.text(s, x + 0.3, y + 0.66, cw - 0.6, 0.4, l, size=14, color=INK)
    d.label_box(s, MX, TOP + 4.45, W - 2 * MX, 0.8,
                "Chaque base est **cohérente avec elle-même** : ce qui manque, c'est **le pont entre elles**.",
                size=18, fill=NAVY, color=WHITE)


def s10_limits(d: Deck):
    s = d.slide("Étude de l'existant", "Cinq manques à combler",
                "L'analyse fait ressortir cinq manques : pas d'identifiant transversal, le CIN manque pour un quart "
                "des patients ; pas de normalisation commune ; pas de rapprochement d'identités ; pas de "
                "gouvernance ; pas d'espace de rejeu. Le premier prototype comptait 24 872 marqueurs de doublon "
                "sans référentiel ni justification : on détectait, on n'expliquait pas.")
    items = ["**Aucun identifiant transversal** — le CIN manque pour ~25 % des patients",
             "**Aucune normalisation commune** — ni schéma pivot, ni formats partagés",
             "**Aucun rapprochement d'identités** explicable",
             "**Aucune gouvernance** — ni rôles, ni consentement, ni journal d'accès",
             "**Aucun espace de rejeu** — une erreur de traitement ne se rejoue pas"]
    for i, t in enumerate(items):
        y = TOP + 0.15 + i * 0.98
        d.box(s, MX, y, 7.6, 0.82, fill=TINT)
        d.circle(s, MX + 0.18, y + 0.14, 0.54, str(i + 1), size=15)
        d.text(s, MX + 0.9, y + 0.08, 6.55, 0.7, t, size=16, anchor=MSO_ANCHOR.MIDDLE)
    x = MX + 8.0
    d.box(s, x, TOP + 0.15, W - MX - x, 4.75, fill=NAVY)
    d.text(s, x + 0.35, TOP + 0.55, W - MX - x - 0.7, 1.1, "24 872", size=60, color=WHITE, bold=True,
           align=PP_ALIGN.CENTER)
    d.text(s, x + 0.35, TOP + 1.75, W - MX - x - 0.7, 1.2,
           "marqueurs de doublon dans le premier prototype (run du 24/08/2026)", size=17, color=TINT2,
           align=PP_ALIGN.CENTER)
    d.text(s, x + 0.35, TOP + 3.2, W - MX - x - 0.7, 1.4,
           "… sans référentiel patient ni justification des fusions", size=18, color=WHITE, bold=True,
           align=PP_ALIGN.CENTER)


def s11_approach(d: Deck):
    s = d.slide("Solution proposée", "Une démarche en trois niveaux : chaque technologie répond à un besoin",
                "Je n'ai pas commencé par le Big Data. Niveau 1 : un MVP Pandas et PostgreSQL pour résoudre le "
                "problème métier. Niveau 2 : le même moteur porté en Spark, avec des résultats strictement "
                "identiques. Niveau 3 : le lac de données Medallion sur HDFS, Hive et Spark. Deux garde-fous "
                "transverses : on valide sur une vérité terrain avant de passer à l'échelle, et la gouvernance "
                "s'appuie sur la zone GOLD.")
    levels = [("Niveau 1", "MVP", "CSV · Pandas · PostgreSQL", "résoudre le problème métier au plus simple"),
              ("Niveau 2", "Spark", "même moteur en PySpark", "changer d'échelle **sans changer la logique**"),
              ("Niveau 3", "Big Data", "HDFS · Hive · Spark", "lac Medallion rejouable et planifiable")]
    gap = 0.55
    cw = (W - 2 * MX - 2 * gap) / 3
    for i, (lvl, name, tech, why) in enumerate(levels):
        x = MX + i * (cw + gap)
        d.box(s, x, TOP + 0.15, cw, 2.9, fill=TINT if i < 2 else NAVY)
        dark = i == 2
        d.text(s, x + 0.3, TOP + 0.3, cw - 0.6, 0.35, lvl.upper(), size=13, color=AMBER if dark else BLUE, bold=True)
        d.text(s, x + 0.3, TOP + 0.65, cw - 0.6, 0.6, name, size=30, color=WHITE if dark else NAVY, bold=True)
        d.text(s, x + 0.3, TOP + 1.35, cw - 0.6, 0.5, tech, size=15, color=TINT2 if dark else MUTED, font=FONT)
        d.text(s, x + 0.3, TOP + 1.9, cw - 0.6, 1.0, why, size=16, color=WHITE if dark else INK)
        if i < 2:
            d.chevron(s, x + cw + 0.08, TOP + 1.3, gap - 0.16, 0.6, color=AMBER)
    for i, (t, desc) in enumerate([("Validation", "vérité terrain avant le passage à l'échelle"),
                                   ("Gouvernance", "consentement, audit et API sur la zone GOLD")]):
        y = TOP + 3.35 + i * 0.95
        d.label_box(s, MX, y, 2.6, 0.78, t, size=17, fill=AMBER_T, color=INK, bold=True)
        d.text(s, MX + 2.85, y, W - 2 * MX - 2.85, 0.78, desc, size=17, anchor=MSO_ANCHOR.MIDDLE)
    d.text(s, MX, TOP + 5.05, W - 2 * MX, 0.3, "Deux étapes transverses : on ne passe à l'échelle, et on n'ouvre "
           "les accès, qu'une fois la preuve établie.", size=13, color=MUTED, italic=True)


def s12_architecture(d: Deck):
    s = d.slide("Solution proposée", "Architecture : de la source à l'API gouvernée",
                "Le chemin d'une donnée : les sources sont copiées telles quelles dans la zone RAW, sur HDFS. "
                "Le mapping FHIR produit la zone SILVER, où le moteur de déduplication rattache chaque ligne à "
                "son patient maître. La zone GOLD porte les agrégats et le consentement. PostgreSQL conserve "
                "l'état de référence : patients maîtres, consentements, audit. L'API de gouvernance est le seul "
                "point d'accès, et chaque appel est journalisé. Le tout tourne sur une VM de 8 Go, en outils libres.")
    y0 = TOP + 0.3
    # Sources
    d.text(s, MX, y0 - 0.05, 2.1, 0.3, "SOURCES", size=12, color=BLUE, bold=True)
    for i, t in enumerate(["Pharmacie", "Consultation", "Imagerie"]):
        d.label_box(s, MX, y0 + 0.3 + i * 0.72, 2.1, 0.58, t, size=14, fill=WHITE, line=LINE)
    zones = [("RAW", "brut, inchangé", RAW_C), ("SILVER", "FHIR normalisé\n+ patient maître", SILVER_C),
             ("GOLD", "agrégats\n+ consentement", GOLD_C)]
    zx, zw, zg = MX + 2.75, 1.95, 0.45
    d.text(s, zx, y0 - 0.05, 3 * zw + 2 * zg, 0.3, "LAC DE DONNÉES — HDFS · HIVE · SPARK", size=12, color=BLUE,
           bold=True)
    for i, (name, desc, col) in enumerate(zones):
        x = zx + i * (zw + zg)
        b = d.box(s, x, y0 + 0.3, zw, 2.02, fill=WHITE, line=col)
        b.line.width = Pt(2.5)
        d.text(s, x + 0.1, y0 + 0.45, zw - 0.2, 0.5, name, size=22, color=col, bold=True, align=PP_ALIGN.CENTER)
        d.text(s, x + 0.1, y0 + 1.0, zw - 0.2, 1.2, desc.split("\n"), size=13, color=INK, align=PP_ALIGN.CENTER)
        if i < 2:
            d.arrow(s, x + zw + 0.05, y0 + 1.3, x + zw + zg - 0.05, y0 + 1.3)
    d.arrow(s, MX + 2.15, y0 + 1.3, zx - 0.05, y0 + 1.3)
    # Moteur sous SILVER
    mx = zx + zw + zg
    d.label_box(s, mx - 0.25, y0 + 2.75, zw + 0.5, 0.85, ["**Moteur de déduplication**", "exact + probabiliste"],
                size=13, fill=AMBER_T)
    d.arrow(s, mx + zw / 2, y0 + 2.7, mx + zw / 2, y0 + 2.37, color=AMBER)
    # API et PostgreSQL
    ax = zx + 3 * zw + 2 * zg + 0.5
    aw = W - MX - ax
    d.label_box(s, ax, y0 + 0.3, aw, 1.15, ["**API de gouvernance**", "rôle · finalité · consentement"],
                size=14, fill=NAVY, color=WHITE)
    d.arrow(s, zx + 3 * zw + 2 * zg + 0.05, y0 + 0.87, ax - 0.05, y0 + 0.87)
    d.label_box(s, ax, y0 + 1.75, aw, 1.15, ["**PostgreSQL**", "patients maîtres · consentements · audit"],
                size=14, fill=TINT2)
    d.arrow(s, ax + aw / 2, y0 + 1.72, ax + aw / 2, y0 + 1.48)
    d.label_box(s, ax, y0 + 3.2, aw, 0.62, "Journal d'audit de chaque appel", size=13, fill=WHITE, line=LINE)
    d.arrow(s, ax + aw / 2, y0 + 2.93, ax + aw / 2, y0 + 3.17)
    # Logos des outils
    ly = TOP + 4.35
    d.text(s, MX, ly + 0.2, 2.2, 0.4, "Outils libres :", size=14, color=MUTED, bold=True)
    keys = ["hadoop", "hive", "spark", "python", "pandas", "rapidfuzz", "postgresql", "fastapi", "vagrant"]
    lw = (W - MX - (MX + 2.1)) / len(keys)
    for i, k in enumerate(keys):
        p = LOGOS_DIR / f"{k}.png"
        if p.exists():
            d.picture(s, p, MX + 2.1 + i * lw + 0.05, ly, w=lw - 0.1)


def s13_dedup(d: Deck):
    s = d.slide("Fonctionnalités principales", "Déduplication explicable : jamais de fusion sans justification",
                "Le moteur compare seulement des candidats plausibles grâce au blocking. Première passe : "
                "rapprochement exact sur le nom normalisé, la date de naissance et le CIN. Sinon, un score pondéré : "
                "le nom compte pour moitié, la date pour 0,3, le CIN et la ville pour 0,1 chacun. Au-dessus de 0,80, "
                "on fusionne ; en dessous, on crée un nouveau patient maître. Chaque décision porte sa méthode, son "
                "score et son explication. Les poids sont dans un fichier de configuration.")
    steps = [("Blocking", "ne comparer que les candidats : préfixe du nom, date, CIN"),
             ("Passe exacte", "nom normalisé + naissance + CIN identiques → score 1,0"),
             ("Passe probabiliste", "score pondéré ≥ 0,80 → fusion ; sinon nouveau patient maître")]
    for i, (t, desc) in enumerate(steps):
        y = TOP + 0.15 + i * 1.12
        d.circle(s, MX, y + 0.12, 0.66, str(i + 1), size=18)
        d.text(s, MX + 0.85, y + 0.02, 5.2, 0.42, t, size=19, color=NAVY, bold=True)
        d.text(s, MX + 0.85, y + 0.45, 5.2, 0.6, desc, size=15)
    d.label_box(s, MX, TOP + 3.6, 6.1, 1.55, [
        "Chaque décision porte **méthode · score · explication**",
        "`exact` · `probabilistic` · `new_master`",
    ], size=16, fill=NAVY, color=WHITE)
    # Barre du score pondéré
    x0, bw = 7.3, W - MX - 7.3
    d.text(s, x0, TOP + 0.15, bw, 0.4, "Composition du score de similarité", size=17, color=NAVY, bold=True)
    parts = [("Nom", 0.5, NAVY), ("Naissance", 0.3, BLUE), ("CIN", 0.1, SKY), ("Ville", 0.1, TINT2)]
    x = x0
    for name, wgt, col in parts:
        seg = bw * wgt
        b = d.box(s, x, TOP + 0.75, seg, 0.9, fill=col, shape=MSO_SHAPE.RECTANGLE)
        dark = col in (NAVY, BLUE)
        d.text(s, x, TOP + 0.8, seg, 0.8, [name, f"{wgt:.1f}".replace(".", ",")], size=13 if wgt < 0.2 else 15,
               color=WHITE if dark else INK, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += seg
    tx = x0 + bw * 0.8
    d.arrow(s, tx, TOP + 2.3, tx, TOP + 1.7, color=AMBER, width=2.5)
    d.text(s, tx - 1.6, TOP + 2.3, 3.2, 0.45, "seuil de fusion : 0,80", size=16, color=AMBER, bold=True,
           align=PP_ALIGN.CENTER)
    # Exemple
    d.box(s, x0, TOP + 3.0, bw, 2.15, fill=TINT)
    d.text(s, x0 + 0.3, TOP + 3.12, bw - 0.6, 0.35, "EXEMPLE — CAS DE RÉFÉRENCE", size=12, color=BLUE, bold=True)
    d.text(s, x0 + 0.3, TOP + 3.5, bw - 0.6, 1.6, [
        "**Jean Rakoto** : 3 fiches → **PAT-0102**, méthode *exacte* (CIN identique après normalisation)",
        "**Nirina** : rattachée par méthode *probabiliste*, score ≥ 0,80",
    ], size=15, spacing=6)


def s14_governance(d: Deck):
    s = d.slide("Fonctionnalités principales", "Gouvernance : qui demande, pourquoi, et la trace de chaque accès",
                "Trois contrôles, dans cet ordre. Qui : la clé d'API est résolue en utilisateur et en rôle ; clé "
                "inconnue, 401 ; rôle insuffisant, 403. Pourquoi : la finalité est obligatoire, dans une liste "
                "fermée ; finalité inconnue, 422 ; finalité non consentie, 403, même pour un utilisateur autorisé. "
                "Trace : chaque appel, accepté ou refusé, est journalisé avec la finalité et le motif du refus.")
    steps = [("Qui ?", "clé d'API → utilisateur → rôle", ["**401** clé absente ou inconnue", "**403** rôle insuffisant"]),
             ("Pourquoi ?", "finalité déclarée → consentement du patient",
              ["**422** finalité absente ou inconnue", "**403** finalité non consentie"]),
             ("Trace", "chaque appel journalisé", ["finalité demandée", "motif du refus"])]
    cw, gap = 3.7, 0.5
    for i, (t, sub, codes) in enumerate(steps):
        x = MX + i * (cw + gap)
        d.box(s, x, TOP + 0.15, cw, 2.75, fill=TINT)
        d.circle(s, x + 0.25, TOP + 0.35, 0.62, str(i + 1), size=17)
        d.text(s, x + 1.05, TOP + 0.35, cw - 1.2, 0.6, t, size=24, color=NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        d.text(s, x + 0.3, TOP + 1.1, cw - 0.6, 0.6, sub, size=15, color=INK)
        d.text(s, x + 0.3, TOP + 1.75, cw - 0.6, 1.1, codes, size=15, color=MUTED, bullets=True, spacing=3)
        if i < 2:
            d.chevron(s, x + cw + 0.08, TOP + 1.25, gap - 0.16, 0.55, color=AMBER)
    # Exemple de refus
    y = TOP + 3.2
    d.box(s, MX, y, W - 2 * MX, 1.95, fill=NAVY)
    d.text(s, MX + 0.35, y + 0.15, 6.0, 0.35, "EXEMPLE DE REFUS", size=12, color=AMBER, bold=True)
    d.text(s, MX + 0.35, y + 0.52, W - 2 * MX - 0.7, 1.35, [
        "GET /patients/PAT-0102?purpose=analytics",
        "→ 403  « consentement non accorde pour la finalite analytics »",
        "→ access_audit : purpose = analytics · refusal_reason enregistré",
    ], size=16, color=WHITE, font=MONO, spacing=4)


def s15_results(d: Deck):
    s = d.slide("Cas d'utilisation", "Sur le jeu de démonstration : 214 fiches ramenées à 145 patients",
                "Le run de référence du 7 septembre 2026, sur les trois sources synthétiques : 214 lignes en zone "
                "SILVER, 145 patients maîtres, 69 doublons rattachés, soit 32,24 % de doublons. La cohérence se "
                "vérifie par un simple comptage : 214 moins 69 égale 145. Le pipeline a réussi toutes ses étapes, "
                "et la suite de tests passe à 102 sur 102.")
    d.stat(s, MX, TOP + 0.2, 3.3, "214", "fiches dans la zone SILVER\n(76 + 76 + 62)", vsize=60, lsize=15, h=2.3)
    d.chevron(s, MX + 3.45, TOP + 1.0, 0.8, 0.7, color=AMBER)
    d.stat(s, MX + 4.4, TOP + 0.2, 3.3, "145", "patients maîtres distincts", vsize=60, lsize=15, h=2.3,
           fill=NAVY, color=WHITE)
    rx = MX + 8.1
    for i, (v, l) in enumerate([("69", "doublons rattachés"), ("32,24 %", "taux de doublons")]):
        d.stat(s, rx, TOP + 0.2 + i * 1.2, W - MX - rx, v, l, vsize=30, lsize=13, h=1.1)
    y = TOP + 2.95
    items = [("214 − 69 = 145", "cohérence vérifiée par comptage sur le lac"),
             ("4 / 4", "étapes du pipeline réussies (run du 07/09/2026)"),
             ("102 / 102", "tests automatisés réussis (moteur, gouvernance, planification)")]
    for i, (v, l) in enumerate(items):
        yy = y + i * 0.75
        d.text(s, MX, yy, 3.3, 0.65, v, size=22, color=NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        d.text(s, MX + 3.4, yy, W - 2 * MX - 3.4, 0.65, l, size=16, anchor=MSO_ANCHOR.MIDDLE)
    d.text(s, MX, TOP + 5.15, W - 2 * MX, 0.3, "Sources CSV synthétiques (graine 42) — aucune donnée réelle.",
           size=12, color=MUTED, italic=True)


def s16_evaluation(d: Deck):
    s = d.slide("Cas d'utilisation", "Évaluation sur vérité terrain : zéro fusion à tort",
                "Pour mesurer la qualité, il faut connaître la vérité : un générateur produit 500 patients et leurs "
                "variantes, avec 10, 30 ou 50 % de variations. La précision est de 1,000 sur les trois niveaux : "
                "aucune fusion à tort, c'est la propriété essentielle en santé. Le rappel baisse sur le jeu difficile, "
                "0,422 : c'est le prix d'un seuil prudent, assumé. Le CIN l'a fait passer de 0,287 à 0,422. Pandas "
                "et Spark donnent exactement les mêmes résultats.")
    data = CategoryChartData()
    data.categories = ["Facile (10 %)", "Moyen (30 %)", "Difficile (50 %)"]
    data.add_series("Précision", (1.0, 1.0, 1.0))
    data.add_series("Rappel", (1.0, 0.884, 0.422))
    data.add_series("F1", (1.0, 0.939, 0.594))
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(MX), Inches(TOP + 0.05),
                            Inches(7.6), Inches(5.2), data)
    ch = gf.chart
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.TOP
    ch.legend.include_in_layout = False
    ch.legend.font.size = Pt(14)
    ch.legend.font.color.rgb = INK
    values = {"Précision": (1.0, 1.0, 1.0), "Rappel": (1.0, 0.884, 0.422), "F1": (1.0, 0.939, 0.594)}
    for ser, col in zip(ch.series, (NAVY, AMBER, SKY)):
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = col
        # Étiquettes écrites en toutes lettres : la virgule décimale ne dépend pas de la
        # langue de PowerPoint sur le poste qui projette.
        for k, v in enumerate(values[ser.name]):
            dl = ser.points[k].data_label
            dl.position = XL_LABEL_POSITION.OUTSIDE_END
            dl.text_frame.text = f"{v:.3f}".replace(".", ",")
            run = dl.text_frame.paragraphs[0].runs[0]
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = INK
    ch.plots[0].gap_width = 60
    va = ch.value_axis
    va.maximum_scale = 1.1
    va.minimum_scale = 0
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = TINT2
    va.visible = False               # valeurs déjà portées par les étiquettes
    ca = ch.category_axis
    ca.tick_labels.font.size = Pt(14)
    ca.tick_labels.font.color.rgb = INK
    rx = MX + 8.0
    rw = W - MX - rx
    d.stat(s, rx, TOP + 0.15, rw, "0", "faux positif sur les trois niveaux", vsize=54, lsize=15, h=1.7,
           fill=NAVY, color=WHITE)
    d.box(s, rx, TOP + 2.05, rw, 1.45, fill=TINT)
    d.text(s, rx + 0.25, TOP + 2.15, rw - 0.5, 1.3, [
        "**Parité Pandas = Spark**",
        "VP 307 · FP 0 · FN 420 dans les deux implémentations",
    ], size=15, spacing=4)
    d.box(s, rx, TOP + 3.7, rw, 1.55, fill=AMBER_T)
    d.text(s, rx + 0.25, TOP + 3.8, rw - 0.5, 1.4, [
        "**Rappel difficile : 0,287 → 0,422**",
        "grâce au CIN dans la clé exacte, sans aucun faux positif",
    ], size=15, spacing=4)


def s17_demo(d: Deck):
    s = d.slide("Démonstration", "Démonstration : la chaîne de bout en bout",
                "Vidéo enregistrée de 3 minutes 30, pour ne dépendre ni du réseau ni de la VM le jour J. "
                "On y voit les tests, l'évaluation sur le jeu difficile, un run du pipeline jusqu'à la zone GOLD, "
                "puis le tableau de bord. Si la vidéo ne se lance pas, je présente les compteurs figés.")
    fx, fw, fh = MX, 7.4, 4.9
    cap = CAPTURES / "C07_pipeline.png"
    if cap.exists():
        d.box(s, fx, TOP + 0.15, fw, fh, fill=WHITE, line=LINE)
        from pptx.util import Emu as _E  # noqa: F401
        pic = d.picture(s, cap, fx + 0.1, TOP + 0.25, w=fw - 0.2)
        if pic.height / 914400 > fh - 0.2:
            ratio = (fh - 0.2) / (pic.height / 914400)
            pic.height = int(pic.height * ratio)
            pic.width = int(pic.width * ratio)
    else:
        b = d.box(s, fx, TOP + 0.15, fw, fh, fill=TINT, line=SKY)
        b.line.dash_style = 4
        d.circle(s, fx + fw / 2 - 0.55, TOP + 1.5, 1.1, "▶", fill=NAVY, size=28)
        d.text(s, fx + 0.4, TOP + 2.85, fw - 0.8, 1.6, [
            "**Vidéo de démonstration — 3 min 30**",
            "Emplacement réservé : insérer la vidéo ici,",
            "ou déposer documents/captures/C07_pipeline.png",
        ], size=15, color=MUTED, align=PP_ALIGN.CENTER, spacing=4)
    rx = fx + fw + 0.4
    rw = W - MX - rx
    steps = [("0:45", "Tests automatisés : 102 / 102"),
             ("0:45", "Évaluation, jeu difficile : précision 1,000"),
             ("1:00", "Pipeline RAW → SILVER → GOLD"),
             ("0:30", "Tableau de bord : zones, dernier run, planification"),
             ("0:30", "Repli : compteurs figés 214 · 145 · 69")]
    for i, (t, desc) in enumerate(steps):
        y = TOP + 0.15 + i * 0.99
        d.label_box(s, rx, y, 1.0, 0.8, t, size=15, fill=NAVY if i < 4 else TINT2,
                    color=WHITE if i < 4 else INK, bold=True)
        d.text(s, rx + 1.15, y, rw - 1.15, 0.8, desc, size=15, anchor=MSO_ANCHOR.MIDDLE,
               color=INK if i < 4 else MUTED)


def s18_perspectives(d: Deck):
    s = d.slide("Perspectives", "Limites assumées et suite du projet",
                "Je préfère nommer les limites. Le rappel sur le jeu difficile est de 0,422. La table GOLD des "
                "événements est vide, car les consultations ne sont pas encore rattachées au patient. La base "
                "centrale de consentements n'a pas été peuplée : la mécanique est testée, la donnée manque. Et la "
                "plateforme n'est pas déployée. La suite : compléter le mapping FHIR, peupler les consentements, "
                "calibrer le seuil, puis intégration continue et passage à l'échelle. Avant toute production : "
                "vérifier le droit malgache des données de santé.")
    cw = (W - 2 * MX - 0.4) / 2
    d.box(s, MX, TOP + 0.15, cw, 4.35, fill=KO_T)
    d.text(s, MX + 0.35, TOP + 0.3, cw - 0.7, 0.45, "Limites assumées", size=21, color=KO, bold=True)
    d.text(s, MX + 0.35, TOP + 0.9, cw - 0.7, 3.5, [
        "Rappel de **0,422** sur le jeu difficile (seuil prudent)",
        "Table GOLD des **événements vide** : rattachement FHIR à compléter",
        "Base de consentements **non peuplée** : mécanique testée, donnée absente",
        "Plateforme **non déployée** : prototype reproductible sur VM",
    ], size=16, bullets=True, spacing=10)
    x = MX + cw + 0.4
    d.box(s, x, TOP + 0.15, cw, 4.35, fill=OK_T)
    d.text(s, x + 0.35, TOP + 0.3, cw - 0.7, 0.45, "Perspectives", size=21, color=OK, bold=True)
    d.text(s, x + 0.35, TOP + 0.9, cw - 0.7, 3.5, [
        "**Court terme** : mapping FHIR, consentements peuplés, calibrage du seuil",
        "**Moyen terme** : intégration continue, blocking partitionné, volumes réels",
        "**Long terme** : catalogue de métadonnées, autres entités (médecins, médicaments)",
    ], size=16, bullets=True, spacing=10)
    d.label_box(s, MX, TOP + 4.75, W - 2 * MX, 0.6,
                "Avant toute mise en production : vérifier le **droit malgache** des données de santé",
                size=16, fill=AMBER_T)


def s19_conclusion(d: Deck):
    s = d.slide("Conclusion", "La plateforme répond à la problématique, preuves à l'appui",
                "Pour conclure : la plateforme centralise dans un lac Medallion, normalise avec un modèle canonique "
                "et FHIR, déduplique sans jamais fusionner à tort, et gouverne chaque accès par le consentement, "
                "avec un audit. La démarche progressive a tenu : changer d'échelle n'a pas changé la logique. "
                "Et chaque résultat se vérifie dans le dépôt.")
    items = [("Centraliser", "lac Medallion RAW → SILVER → GOLD", "214 fiches intégrées"),
             ("Normaliser", "modèle canonique + pivot FHIR", "4 entités FHIR"),
             ("Dédupliquer", "exact + probabiliste, explicable", "précision 1,000"),
             ("Gouverner", "rôle · finalité · consentement · audit", "401 · 403 · 422 testés")]
    cw = (W - 2 * MX - 3 * 0.3) / 4
    for i, (t, how, proof) in enumerate(items):
        x = MX + i * (cw + 0.3)
        d.box(s, x, TOP + 0.15, cw, 3.25, fill=TINT)
        d.circle(s, x + (cw - 0.8) / 2, TOP + 0.35, 0.8, "✓", fill=OK, size=24)
        d.text(s, x + 0.2, TOP + 1.3, cw - 0.4, 0.5, t, size=21, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        d.text(s, x + 0.2, TOP + 1.85, cw - 0.4, 0.8, how, size=14, align=PP_ALIGN.CENTER)
        d.text(s, x + 0.2, TOP + 2.7, cw - 0.4, 0.5, proof, size=16, color=BLUE, bold=True, align=PP_ALIGN.CENTER)
    d.label_box(s, MX, TOP + 3.75, W - 2 * MX, 1.35, [
        "Une démarche progressive — **MVP → Spark → Big Data** — où chaque technologie répond à un besoin,",
        "et où **chaque résultat se vérifie** dans le dépôt.",
    ], size=18, fill=NAVY, color=WHITE)


def s20_thanks(d: Deck):
    d.n += 1
    s = d.prs.slides.add_slide(d.blank)
    d.box(s, 0, 0, W, H, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
    d.text(s, MX, 2.3, W - 2 * MX, 1.2, "Merci pour votre attention", size=48, color=WHITE, bold=True,
           align=PP_ALIGN.CENTER)
    d.text(s, MX, 3.55, W - 2 * MX, 0.6, "Questions et échanges", size=24, color=SKY, align=PP_ALIGN.CENTER)
    d.text(s, MX, 5.2, W - 2 * MX, 0.9, [AUTHOR, f"Master MBDS · Madagascar Medical Technology · {DATE}"],
           size=16, color=TINT2, align=PP_ALIGN.CENTER, spacing=3)
    s.notes_slide.notes_text_frame.text = "Merci pour votre attention. Je suis prêt à répondre à vos questions."


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Génère le deck de soutenance.")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    d = Deck()
    for build in (s01_title, s02_company, s03_question, s04_context, s05_objectives, s06_plan, s07_notions,
                  s08_market, s09_existing, s10_limits, s11_approach, s12_architecture, s13_dedup,
                  s14_governance, s15_results, s16_evaluation, s17_demo, s18_perspectives, s19_conclusion,
                  s20_thanks):
        build(d)
    assert d.n == d.total, f"{d.n} slides pour un total annoncé de {d.total}"
    d.save(args.out)
    print(f"{args.out} : {d.n} slides")


if __name__ == "__main__":
    main()
