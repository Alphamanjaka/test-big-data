"""Animations et transitions PowerPoint pour python-pptx, qui ne les gère pas nativement.

Le modèle suit celui du volet « Animation » de PowerPoint :
    slide  → une liste de CLICS ;
    clic   → une liste d'ÉTAPES jouées l'une après l'autre (« après la précédente ») ;
    étape  → un GROUPE de formes animées ensemble (« avec la précédente »).

    clicks = [
        [[carte1_fond, carte1_valeur, carte1_libelle], [carte2...], [carte3...]],   # clic 1
        [[titre_liste, liste]],                                                    # clic 2
    ]
    add_entrance(slide, clicks, effect="fade")
    add_transition(slide, "fade")

Le XML produit (<p:timing>, <p:bldLst>, <p:transition>) est celui qu'écrit PowerPoint pour
les mêmes réglages : l'animation reste modifiable dans le volet Animation.
"""

from __future__ import annotations

from lxml import etree
from pptx.oxml.ns import qn

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"

# effet -> (presetID, presetSubtype, fragment XML du comportement ; {spid} et {dur} remplacés)
EFFECTS = {
    # Fondu
    "fade": (10, 0, '<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{id}" dur="{dur}"/>'
                    '<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'),
    # Balayage depuis la gauche
    "wipe": (22, 8, '<p:animEffect transition="in" filter="wipe(left)"><p:cBhvr><p:cTn id="{id}" dur="{dur}"/>'
                    '<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'),
    # Zoom (apparition en grossissant)
    "zoom": (53, 16, '<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{id}" dur="{dur}"/>'
                     '<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'
                     '<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{id2}" dur="{dur}" fill="hold"/>'
                     '<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>ppt_w</p:attrName>'
                     '</p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:fltVal val="0"/></p:val></p:tav>'
                     '<p:tav tm="100000"><p:val><p:strVal val="#ppt_w"/></p:val></p:tav></p:tavLst></p:anim>'
                     '<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{id3}" dur="{dur}" fill="hold"/>'
                     '<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>ppt_h</p:attrName>'
                     '</p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:fltVal val="0"/></p:val></p:tav>'
                     '<p:tav tm="100000"><p:val><p:strVal val="#ppt_h"/></p:val></p:tav></p:tavLst></p:anim>'),
}


class _Ids:
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return self.n


def _effect_par(ids, spid, node_type, effect, dur, delay=0):
    preset, subtype, behaviour = EFFECTS[effect]
    ctn = ids()
    set_id = ids()
    ids_b = {"id": ids(), "id2": ids(), "id3": ids()}
    return (
        f'<p:par><p:cTn id="{ctn}" presetID="{preset}" presetClass="entr" presetSubtype="{subtype}" '
        f'fill="hold" grpId="0" nodeType="{node_type}"><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst>'
        f'<p:childTnLst>'
        f'<p:set><p:cBhvr><p:cTn id="{set_id}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/>'
        f'</p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst>'
        f'<p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/>'
        f'</p:to></p:set>'
        + behaviour.format(spid=spid, dur=dur, **ids_b)
        + '</p:childTnLst></p:cTn></p:par>'
    )


def add_entrance(slide, clicks, effect="fade", dur=500, gap=150):
    """Ajoute les animations d'entrée ; `clicks` : liste de clics → étapes → formes."""
    ids = _Ids()
    root_id, seq_id = ids(), ids()
    click_xml = []
    animated = []
    for steps in clicks:
        click_id = ids()
        step_xml = []
        t = 0
        for k, group in enumerate(steps):
            step_id = ids()
            effects = []
            for j, shape in enumerate(group):
                if j == 0:
                    node = "clickEffect" if k == 0 else "afterEffect"
                else:
                    node = "withEffect"
                effects.append(_effect_par(ids, shape.shape_id, node, effect, dur))
                animated.append(shape)
            step_xml.append(f'<p:par><p:cTn id="{step_id}" fill="hold"><p:stCondLst><p:cond delay="{t}"/>'
                            f'</p:stCondLst><p:childTnLst>{"".join(effects)}</p:childTnLst></p:cTn></p:par>')
            t += dur + gap
        click_xml.append(f'<p:par><p:cTn id="{click_id}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
                         f'</p:stCondLst><p:childTnLst>{"".join(step_xml)}</p:childTnLst></p:cTn></p:par>')

    # Formes porteuses de texte : PowerPoint les déclare dans la liste de construction.
    bld = "".join(
        '<p:bldP spid="%d" grpId="0" animBg="1"/>' % s.shape_id
        for s in animated if getattr(s, "has_text_frame", False) and s.has_text_frame
    )
    xml = (
        f'<p:timing xmlns:p="{P_NS}"><p:tnLst><p:par>'
        f'<p:cTn id="{root_id}" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
        f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{seq_id}" dur="indefinite" nodeType="mainSeq">'
        f'<p:childTnLst>{"".join(click_xml)}</p:childTnLst></p:cTn>'
        f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        f'</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst>'
        + (f'<p:bldLst>{bld}</p:bldLst>' if bld else '')
        + '</p:timing>'
    )
    _insert(slide, etree.fromstring(xml), "timing")


def add_transition(slide, kind="fade", speed="med"):
    """Transition d'entrée de la slide (fondu par défaut)."""
    xml = f'<p:transition xmlns:p="{P_NS}" spd="{speed}"><p:{kind}/></p:transition>'
    _insert(slide, etree.fromstring(xml), "transition")


def _insert(slide, element, tag):
    """Place l'élément dans l'ordre imposé par le schéma : cSld, clrMapOvr, transition, timing, extLst."""
    sld = slide._element
    old = sld.find(qn(f"p:{tag}"))
    if old is not None:
        sld.remove(old)
    order = ["cSld", "clrMapOvr", "transition", "timing", "extLst"]
    after = [qn(f"p:{t}") for t in order[: order.index(tag)]]
    anchor = None
    for child in sld:
        if child.tag in after:
            anchor = child
    if anchor is None:
        sld.insert(0, element)
    else:
        anchor.addnext(element)
