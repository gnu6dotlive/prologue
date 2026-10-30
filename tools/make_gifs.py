#!/usr/bin/env python3
"""Génère les trois animations du site, image par image, en SVG.

Chaque image est un SVG écrit ici (mêmes jetons gnosix_DS V3.4.1 et même fonte que
les schémas de assets/diagrams/), rastérisé par rsvg-convert, puis assemblé en GIF
par ffmpeg avec une palette calculée sur l'ensemble de l'animation.

  gnosix-appstack.gif      l'AppStack sort du deck par extrusion, cherche, lance
  gnostral-course.gif      même réponse, deux vitesses, au rythme mesuré (Q-010)
  gnu6-scene-projection.gif la scène change, deux projections suivent ; un renderer
                            qui tente de déplacer un objet est refusé

Pour chaque GIF, une image de repos (<nom>-still.png) sert à l'impression.

Règles de mouvement : pas de fondu d'opacité ; les objets bougent entiers ; un bord
mobile ne tranche jamais un contenu immobile ; une surface sort de son module comme
une seule forme.

Deux langues : les GIF français dans assets/gif/, les anglais dans assets/gif/en/.
Tout texte passe par text(), qui le traduit via EN quand LANG vaut « en ».

Deux thèmes : chaque image passe aussi par darken() (tools/dark_theme.py) pour la
version sombre, dans un sous-dossier dark/. Un écran ou une scène dessinés gardent
leurs couleurs (data-keep="1") : on montre le produit tel qu'il est. L'image de repos
ne sert qu'à l'impression, qui reste claire : elle n'existe qu'en clair.

Usage : python3 tools/make_gifs.py [fr|en …] [--theme light|dark]
        (dépend de rsvg-convert et ffmpeg)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dark_theme import darken  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "gif"

W, H = 1200, 675
LANG = "fr"
THEME = "light"

EN = {
    # gnosix
    "GNOSIX · LE DECK ET SON APPSTACK": "GNOSIX · THE DECK AND ITS APPSTACK",
    "L'AppStack sort du deck — il ne se pose pas dessus": "The AppStack grows out of the deck — not on top of it",
    "Ouvrir l'AppStack, dans le deck": "Open the AppStack, in the deck",
    "Chercher dans le catalogue": "Search the catalogue",
    "Lancer : l'autorité décide": "Launch: the authority decides",
    "L'application rejoint le deck": "The application joins the deck",
    "autorité de lancement · accordée": "launch authority · granted",
    "Rechercher une application": "Search for an application",
    "RÉCENTS": "RECENT",
    "↵ Entrée": "↵ Enter",
    "Fichiers": "Files", "Paramètres": "Settings", "Musique": "Music",
    "Calculatrice": "Calculator", "Calendrier": "Calendar", "Capture d'écran": "Camera",
    "Animation de principe, d'après gnosix/docs/status/STATUS.md (« The Deck and the AppStack », QUALIFIED). Ni capture, ni durées réelles.":
        "An illustration of the principle, based on gnosix/docs/status/STATUS.md (“The Deck and the AppStack”, QUALIFIED). Not a capture, not real timings.",
    # gnostral
    "GNOSTRAL.RS · Q-010 · TEMPS RÉEL": "GNOSTRAL.RS · Q-010 · REAL TIME",
    "Même question, même réponse, deux vitesses": "Same question, same answer, two speeds",
    "SANS CORRECTIF": "WITHOUT THE PATCH",
    "AVEC CORRECTIF": "WITH THE PATCH",
    "lecture de la question": "reading the question",
    "question lue": "question read",
    "réponse complète": "answer complete",
    "texte identique octet pour octet à celui du haut — 6 paires sur 6": "text identical byte for byte to the one above — 6 pairs out of 6",
    "Rythmes médians mesurés, réponse de 512 jetons — gnostral.rs/evidence/runs/q010-hotpath-ssd-ab-audit-20261010.json. Le décodage est lissé à son débit médian.":
        "Measured median rates, 512-token answer — gnostral.rs/evidence/runs/q010-hotpath-ssd-ab-audit-20261010.json. Decoding is smoothed to its median rate.",
    # in.gnu6
    "IN.GNU6 · UNE SCÈNE, DEUX PROJECTIONS": "IN.GNU6 · ONE SCENE, TWO PROJECTIONS",
    "La scène change, les projections suivent — jamais l'inverse": "The scene changes, the projections follow — never the reverse",
    "LA SCÈNE · CE QUI EXISTE": "THE SCENE · WHAT EXISTS",
    "DERNIER FAIT": "LATEST FACT",
    "aucun changement — requête de renderer refusée": "no change — renderer request refused",
    "n2 · position modifiée par la scène": "n2 · position changed by the scene",
    "relation n2 → n3 (était n2 → n1)": "relation n2 → n3 (was n2 → n1)",
    "relation n2 → n1 rétablie": "relation n2 → n1 restored",
    "n2 · position rétablie": "n2 · position restored",
    "scène stable": "scene stable",
    "PROJECTION 1 · NAVIGATEUR": "PROJECTION 1 · BROWSER",
    "PixiJS : des cartes": "PixiJS: cards",
    "PROJECTION 2 · AUTRE RENDERER": "PROJECTION 2 · ANOTHER RENDERER",
    "même scène, autre dessin": "same scene, another drawing",
    "✕ refusé": "✕ refused",
    "déplacer un objet appartient à la scène": "moving an object belongs to the scene",
    "Animation de principe, d'après in.gnu6/CONTRACT.md : un renderer observe et dessine ; il ne renomme, ne déplace, n'invente rien.":
        "An illustration of the principle, based on in.gnu6/CONTRACT.md: a renderer observes and draws; it renames, moves and invents nothing.",
}


def tr(s: str) -> str:
    return EN.get(s, s) if LANG == "en" else s


def num(x: float, decimals: int) -> str:
    """8,90 en français, 8.90 en anglais ; séparateur de milliers espace ou virgule."""
    out = f"{x:,.{decimals}f}"
    if LANG == "en":
        return out
    return out.replace(",", "\u202f").replace(".", ",").replace("\u202f", " ")
FONT = "'Space Grotesk', sans-serif"

SHELL = "#F7F3ED"
WHITE = "#FFFFFF"
INK = "#111418"
SLATE = "#667085"
MUTED = "#A1A6AD"
HAIRLINE = "#D7DADF"
QUIET = "#E6E8EB"
ORANGE = "#FF6A00"
ORANGE700 = "#C95400"
ORANGE100 = "#FFE5D2"
GREEN = "#5F7F52"
GREEN700 = "#455F3D"
GREEN100 = "#E8EFE5"
BLUE = "#4169E1"
BLUE700 = "#2446A8"
BLUE100 = "#E8EDFF"


# ---------- temps et courbes ----------

def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, x))


def seg(t: float, a: float, b: float) -> float:
    """Progression linéaire de t dans [a, b], bornée à [0, 1]."""
    return clamp((t - a) / (b - a))


def ease(p: float) -> float:
    """Entrée et sortie douces (cubique)."""
    return 4 * p * p * p if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_out(p: float) -> float:
    return 1 - (1 - p) ** 3


def ease_out_back(p: float) -> float:
    c1, c3 = 1.4, 2.4
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def lerp(a: float, b: float, p: float) -> float:
    return a + (b - a) * p


# ---------- primitives SVG ----------

def text(x, y, s, size=13, weight=400, fill=INK, anchor="start", spacing=None, extra=""):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    s = tr(s).replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}{extra}>{s}</text>')


def rect(x, y, w, h, fill, rx=0, stroke=None, sw=1, extra=""):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" rx="{rx}" fill="{fill}"{st}{extra}/>'


def header(eyebrow, title, step=None):
    out = [rect(0, 0, W, H, SHELL),
           text(48, 46, eyebrow, 12, 600, SLATE, spacing=2.4),
           text(48, 84, title, 28, 700, INK)]
    if step:
        n, label = step
        out.append(rect(W - 48 - 300, 56, 300, 34, WHITE, 17, HAIRLINE))
        out.append(f'<circle cx="{W - 48 - 282}" cy="73" r="10" fill="{INK}"/>')
        out.append(text(W - 48 - 282, 77.5, str(n), 11, 700, WHITE, "middle"))
        out.append(text(W - 48 - 264, 78, label, 13.5, 500, INK))
    return out


def cursor(x, y, pressed=False):
    s = 0.92 if pressed else 1.0
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s})">'
            f'<path d="M0 0 L0 22 L6 16.5 L10.5 26 L14 24.4 L9.6 15 L17 15 Z" '
            f'fill="{INK}" stroke="{WHITE}" stroke-width="1.6" stroke-linejoin="round"/></g>')


def svg(parts):
    body = "\n".join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}">\n{body}\n</svg>\n')


# ---------- 1. gnosix : l'AppStack sort du deck ----------

CARD, GAP, PAD = 52, 12, 12
SCREEN = (48, 112, 1104, 528)          # x, y, w, h
DECK_BOTTOM = SCREEN[1] + SCREEN[3] - 14
DECK_TOP = DECK_BOTTOM - (PAD + CARD + 16)
PANEL_TOP = DECK_TOP - 300

APPS = [  # (nom, couleur du glyphe, forme)
    ("Fichiers", BLUE, "folder"),
    ("Terminal", INK, "term"),
    ("Paramètres", SLATE, "gear"),
    ("Musique", GREEN, "note"),
    ("Notes", ORANGE700, "lines"),
]
CALIX = ("Calix", BLUE700, "cube")
RECENTS = ["Fichiers", "Terminal", "Calix", "Paramètres", "Musique"]
CATALOGUE = {
    "c": ["Calix", "Calculatrice", "Calendrier", "Capture d'écran"],
    "ca": ["Calix", "Calculatrice", "Calendrier", "Capture d'écran"],
    "cal": ["Calix", "Calculatrice", "Calendrier"],
    "cali": ["Calix"],
}
GLYPH_COLOR = {"Fichiers": BLUE, "Terminal": INK, "Calix": BLUE700, "Paramètres": SLATE,
               "Musique": GREEN, "Calculatrice": ORANGE700, "Calendrier": GREEN700,
               "Capture d'écran": MUTED}
ROW_KIND = {"Fichiers": "folder", "Terminal": "term", "Calix": "cube", "Paramètres": "gear",
            "Musique": "note", "Calculatrice": "lines", "Calendrier": "lines", "Capture d'écran": "term"}


def glyph(kind, cx, cy, color):
    if kind == "grid":
        return "".join(rect(cx - 13 + i * 10, cy - 13 + j * 10, 6, 6, WHITE, 1.5)
                       for i in range(3) for j in range(3))
    if kind == "folder":
        return (rect(cx - 13, cy - 9, 26, 19, color, 3) + rect(cx - 13, cy - 12, 11, 5, color, 2))
    if kind == "term":
        return (rect(cx - 14, cy - 11, 28, 22, color, 4)
                + f'<path d="M{cx-8} {cy-4} L{cx-3} {cy} L{cx-8} {cy+4}" stroke="{WHITE}" stroke-width="2" fill="none" stroke-linecap="round"/>'
                + rect(cx - 1, cy + 3, 8, 2, WHITE, 1))
    if kind == "gear":
        return (f'<circle cx="{cx}" cy="{cy}" r="11" fill="none" stroke="{color}" stroke-width="5" stroke-dasharray="4 3.2"/>'
                f'<circle cx="{cx}" cy="{cy}" r="4" fill="{color}"/>')
    if kind == "note":
        return (f'<circle cx="{cx-5}" cy="{cy+7}" r="5" fill="{color}"/>'
                + rect(cx - 1, cy - 12, 3, 20, color) + rect(cx - 1, cy - 12, 11, 4, color, 1))
    if kind == "lines":
        return "".join(rect(cx - 12, cy - 9 + k * 7, 24 - (k == 2) * 8, 3.5, color, 1.5) for k in range(3))
    if kind == "cube":
        return (f'<path d="M{cx} {cy-13} L{cx+12} {cy-6} L{cx+12} {cy+7} L{cx} {cy+14} L{cx-12} {cy+7} L{cx-12} {cy-6} Z" fill="{color}"/>'
                f'<path d="M{cx-12} {cy-6} L{cx} {cy+1} L{cx+12} {cy-6} M{cx} {cy+1} L{cx} {cy+14}" stroke="{WHITE}" stroke-width="1.6" fill="none"/>')
    return ""


def deck_width(n_slots: float) -> float:
    return 2 * PAD + n_slots * CARD + (n_slots - 1) * GAP


def gnosix_frame(t: float) -> str:
    sx, sy, sw, sh = SCREEN
    # --- étapes
    if t < 1.55:
        step = (1, "Ouvrir l'AppStack, dans le deck")
    elif t < 2.95:
        step = (2, "Chercher dans le catalogue")
    elif t < 3.6:
        step = (3, "Lancer : l'autorité décide")
    else:
        step = (4, "L'application rejoint le deck")
    p = header("GNOSIX · LE DECK ET SON APPSTACK",
               "L'AppStack sort du deck — il ne se pose pas dessus", step)

    # --- écran et barre (bords immobiles) : le produit, dans ses couleurs, quel que soit le thème
    p.append('<g data-keep="1">')
    p.append(f'<clipPath id="scr"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="16"/></clipPath>')
    p.append(rect(sx, sy, sw, sh, QUIET, 16, HAIRLINE))
    p.append(f'<g clip-path="url(#scr)">')
    # fenêtre de fond, immobile, pour donner l'échelle d'un vrai bureau
    p.append(rect(sx + 70, sy + 74, 430, 250, WHITE, 12, HAIRLINE))
    p.append(rect(sx + 70, sy + 74, 430, 30, "#FAF8F5", 12))
    p.append(rect(sx + 70, sy + 92, 430, 12, "#FAF8F5"))
    for k, wv in enumerate((300, 340, 220, 280)):
        p.append(rect(sx + 94, sy + 128 + k * 26, wv, 9, QUIET, 4))
    p.append(rect(sx + 640, sy + 104, 360, 190, WHITE, 12, HAIRLINE))
    for k, wv in enumerate((180, 260, 210)):
        p.append(rect(sx + 664, sy + 136 + k * 26, wv, 9, QUIET, 4))
    # barre
    p.append(rect(sx, sy, sw, 36, INK))
    for k in range(4):
        p.append(rect(sx + 20 + k * 22, sy + 13, 14, 10, ORANGE if k == 1 else "#3A3F46", 3))
    p.append(text(sx + sw / 2, sy + 23.5, "14:32", 13, 600, WHITE, "middle"))
    for k in range(3):
        p.append(rect(sx + sw - 28 - k * 24, sy + 13, 14, 10, "#3A3F46", 3))
    if 3.55 <= t < 5.2:
        cw = 268
        cx0 = sx + sw - 120 - cw
        p.append(rect(cx0, sy + 7, cw, 22, GREEN100, 11))
        p.append(f'<circle cx="{cx0 + 14}" cy="{sy + 18}" r="4" fill="{GREEN}"/>')
        p.append(text(cx0 + 26, sy + 22.5, "autorité de lancement · accordée", 12, 600, GREEN700))
    p.append("</g>")

    # --- deck : nombre d'emplacements (6, puis 7 quand Calix arrive)
    grow = ease(seg(t, 3.6, 3.95)) - ease(seg(t, 5.75, 6.05))
    slots = 6 + grow
    dw = deck_width(slots)
    dx = sx + sw / 2 - dw / 2

    # --- extrusion : le bord haut du deck monte, une seule forme
    up = ease_out(seg(t, 1.05, 1.5)) - ease(seg(t, 3.1, 3.55))
    top = lerp(DECK_TOP, PANEL_TOP, up)
    p.append(rect(dx, top, dw, DECK_BOTTOM - top, INK, 20))

    # contenu de l'AppStack : présent seulement quand la forme est déployée
    if 1.55 <= t < 3.1:
        query = ""
        for at, q in ((1.9, "c"), (2.15, "ca"), (2.4, "cal"), (2.65, "cali")):
            if t >= at:
                query = q
        rows = CATALOGUE.get(query, RECENTS)
        fx, fy, fw = dx + PAD, top + 16, dw - 2 * PAD
        p.append(rect(fx, fy, fw, 38, WHITE, 10))
        p.append(f'<circle cx="{fx + 20}" cy="{fy + 18}" r="6.5" fill="none" stroke="{SLATE}" stroke-width="2"/>')
        p.append(f'<path d="M{fx + 25} {fy + 23} L{fx + 30} {fy + 28}" stroke="{SLATE}" stroke-width="2" stroke-linecap="round"/>')
        if query:
            p.append(text(fx + 38, fy + 24.5, query, 15, 500, INK))
            qx = fx + 38 + sum({"c": 8.0, "a": 8.4, "l": 3.7, "i": 3.7}.get(ch, 8.0) for ch in query)
        else:
            p.append(text(fx + 38, fy + 24.5, "Rechercher une application", 14, 400, MUTED))
            qx = fx + 37
        if int(t * 4) % 2 == 0 or query:
            p.append(rect(qx + 1, fy + 10, 2, 18, ORANGE))
        found = (f"{len(rows)} RESULT{'S' if len(rows) > 1 else ''}" if LANG == "en"
                 else f"{len(rows)} RÉSULTAT{'S' if len(rows) > 1 else ''}")
        p.append(text(fx + 4, fy + 64, "RÉCENTS" if not query else found,
                      10.5, 600, MUTED, spacing=1.6))
        enter = t >= 2.9
        for k, name in enumerate(rows):
            ry = fy + 76 + k * 40
            if k == 0 and query:
                p.append(rect(fx, ry, fw, 34, ORANGE700 if enter else "#2A2F36", 8))
            p.append(rect(fx + 6, ry + 3, 28, 28, WHITE, 7))
            gx, gy = fx + 20, ry + 17
            p.append(f'<g transform="translate({gx:.1f},{gy:.1f}) scale(0.62) translate({-gx:.1f},{-gy:.1f})">'
                     + glyph(ROW_KIND.get(name, "lines"), gx, gy, GLYPH_COLOR.get(name, SLATE)) + "</g>")
            p.append(text(fx + 44, ry + 22, name, 14, 500, WHITE))
            if k == 0 and query:
                p.append(text(fx + fw - 12, ry + 22, "↵ Entrée", 12, 600, WHITE if enter else MUTED, "end"))

    # cartes du deck (glissent entières quand le deck se recentre)
    cy = DECK_BOTTOM - 16 - CARD
    press = 3 if 0.9 <= t < 1.05 else 0
    cards = [("AppStack", ORANGE, "grid")] + APPS
    for i, (name, col, kind) in enumerate(cards):
        x = dx + PAD + i * (CARD + GAP)
        if i == 0:
            p.append(rect(x, cy + press, CARD, CARD, ORANGE, 12))
            p.append(glyph("grid", x + CARD / 2, cy + press + CARD / 2, WHITE))
        else:
            p.append(rect(x, cy, CARD, CARD, WHITE, 12))
            p.append(glyph(kind, x + CARD / 2, cy + CARD / 2, col))
        if name in ("Fichiers", "Terminal"):
            p.append(f'<circle cx="{x + CARD / 2}" cy="{DECK_BOTTOM - 8}" r="2.6" fill="{MUTED}"/>')
    # Calix : entre dans l'emplacement libéré, puis en ressort
    s_in = ease_out_back(seg(t, 3.9, 4.25)) if t < 5.4 else 1 - ease(seg(t, 5.4, 5.75))
    if 3.9 <= t < 5.75 and s_in > 0.02:
        x = dx + PAD + 6 * (CARD + GAP)
        c = (x + CARD / 2, cy + CARD / 2)
        p.append(f'<g transform="translate({c[0]:.1f},{c[1]:.1f}) scale({s_in:.3f}) translate({-c[0]:.1f},{-c[1]:.1f})">')
        p.append(rect(x, cy, CARD, CARD, WHITE, 12))
        p.append(glyph("cube", c[0], c[1], BLUE700))
        p.append("</g>")
        if 4.25 <= t < 5.4:
            p.append(f'<circle cx="{c[0]}" cy="{DECK_BOTTOM - 8}" r="2.6" fill="{ORANGE}"/>')

    # curseur
    ax, ay = dx + PAD + CARD / 2 + 4, cy + CARD / 2 + 6
    hx, hy = sx + 820, sy + 380
    if t < 0.9:
        q = ease(seg(t, 0.25, 0.9))
        cx_, cy_ = lerp(hx, ax, q), lerp(hy, ay, q)
    elif t < 5.4:
        cx_, cy_ = ax, ay + (press if t < 1.05 else 0)
    else:
        q = ease(seg(t, 5.4, 6.2))
        cx_, cy_ = lerp(ax, hx, q), lerp(ay, hy, q)
    p.append(cursor(cx_, cy_, pressed=0.9 <= t < 1.05))
    p.append("</g>")

    p.append(text(48, H - 14, "Animation de principe, d'après gnosix/docs/status/STATUS.md (« The Deck and the AppStack », QUALIFIED). "
                  "Ni capture, ni durées réelles.", 11, 400, MUTED))
    return svg(p)


# ---------- 2. gnostral : même réponse, deux vitesses ----------

PREFILL = {"base": 7.248, "cand": 2.676}       # s, médianes, réponse de 512 jetons
TPS = {"base": 9.506482, "cand": 20.179588}     # jetons/s, médianes
TOKENS = 209                                    # jetons générés par cette réponse


def token_widths(n=TOKENS):
    seq, v = [], 7
    for _ in range(n):
        v = (v * 1103515245 + 12345) % 2**31
        seq.append(8 + (v >> 16) % 24)
    return seq


WIDTHS = token_widths()


def lane(p, y, key, label, color, tint, t):
    x0, w, h = 48, 1104, 250
    p.append(rect(x0, y, w, h, WHITE, 12, HAIRLINE))
    p.append(rect(x0, y, 4, h, color, 2))
    p.append(text(x0 + 28, y + 34, label, 12, 700, color, spacing=1.8))
    pre, tps = PREFILL[key], TPS[key]
    n = 0 if t < pre else min(TOKENS, int((t - pre) * tps))
    done = n >= TOKENS
    p.append(text(x0 + w - 28, y + 38, f"{n}", 30, 700, INK, "end"))
    p.append(text(x0 + w - 28, y + 58, f"/ {TOKENS} {'tokens' if LANG == 'en' else 'jetons'}", 12, 500, SLATE, "end"))
    if LANG == "en":
        line = f"prefill {num(pre * 1000, 0)} ms · then {num(tps, 2)} tokens/s"
    else:
        line = f"pré-remplissage {num(pre * 1000, 0)} ms · puis {num(tps, 2)} jetons/s"
    p.append(text(x0 + 28, y + 58, line, 13, 400, SLATE))
    # barre de pré-remplissage : la question est lue avant le premier mot
    bx, by, bw = x0 + 28, y + 76, 520
    fill = clamp(t / pre)
    p.append(rect(bx, by, bw, 8, QUIET, 4))
    p.append(rect(bx, by, bw * fill, 8, tint, 4))
    p.append(text(bx + bw + 14, by + 8.5, "lecture de la question" if fill < 1 else "question lue",
                  12, 500, SLATE if fill < 1 else color))
    # jetons : mêmes largeurs dans les deux couloirs, c'est le même texte
    tx, ty, maxw, rowh = x0 + 28, y + 108, w - 56, 15
    cx, row = tx, 0
    for i in range(n):
        tw = WIDTHS[i]
        if cx + tw > tx + maxw:
            cx, row = tx, row + 1
        p.append(rect(cx, ty + row * rowh, tw, 9, color, 3))
        cx += tw + 5
    if 0 < n < TOKENS and t >= pre:
        if cx + 6 > tx + maxw:
            cx, row = tx, row + 1
        p.append(rect(cx, ty + row * rowh - 2, 3, 13, ORANGE))
    if done:
        p.append(rect(x0 + w - 236, y + 212, 208, 26, GREEN100, 13))
        p.append(text(x0 + w - 132, y + 229.5, "réponse complète", 12.5, 600, GREEN700, "middle"))


GN_END = PREFILL["cand"] + TOKENS / TPS["cand"]      # ≈ 13,03 s
GN_TOTAL = GN_END + 2.2


def gnostral_frame(t: float) -> str:
    p = header("GNOSTRAL.RS · Q-010 · TEMPS RÉEL",
               "Même question, même réponse, deux vitesses")
    p.append(rect(W - 48 - 150, 56, 150, 34, INK, 17))
    p.append(text(W - 48 - 75, 78, f"t = {num(min(t, GN_END + 2.2), 1)} s", 14, 700, WHITE, "middle"))
    lane(p, 110, "base", "SANS CORRECTIF", SLATE, MUTED, t)
    lane(p, 374, "cand", "AVEC CORRECTIF", ORANGE700, ORANGE, t)
    if t >= GN_END:
        p.append(rect(48 + 28, 374 + 212, 520, 26, BLUE100, 13))
        p.append(text(48 + 44, 374 + 229.5, "texte identique octet pour octet à celui du haut — 6 paires sur 6",
                      12.5, 600, BLUE700))
    p.append(text(48, H - 14, "Rythmes médians mesurés, réponse de 512 jetons — gnostral.rs/evidence/runs/q010-hotpath-ssd-ab-audit-20261010.json. "
                  "Le décodage est lissé à son débit médian.", 11, 400, MUTED))
    return svg(p)


# ---------- 3. in.gnu6 : une scène, deux projections ----------

NODES = {"n1": (0.18, 0.22), "n2": (0.58, 0.16), "n3": (0.84, 0.56), "n4": (0.30, 0.72), "n5": (0.68, 0.88)}
N2_MOVED = (0.46, 0.50)
EDGES = [("n1", "n4"), ("n4", "n5"), ("n3", "n5")]


def scene_state(t):
    move = ease(seg(t, 0.6, 2.0)) - ease(seg(t, 6.3, 7.7))
    swap = seg(t, 2.0, 2.9) - seg(t, 5.4, 6.3)
    pos = dict(NODES)
    pos["n2"] = (lerp(NODES["n2"][0], N2_MOVED[0], move), lerp(NODES["n2"][1], N2_MOVED[1], move))
    # l'extrémité de la relation n2 → n1 glisse vers n3, entière
    a, b, c = pos["n1"], pos["n2"], pos["n3"]
    if swap < 0.5:   # la relation se replie sur n2…
        q = ease(swap * 2)
        end = (lerp(a[0], b[0], q), lerp(a[1], b[1], q))
    else:            # …puis se déploie vers n3
        q = ease(swap * 2 - 1)
        end = (lerp(b[0], c[0], q), lerp(b[1], c[1], q))
    return pos, end, move, swap


def gnu6_frame(t: float) -> str:
    p = header("IN.GNU6 · UNE SCÈNE, DEUX PROJECTIONS",
               "La scène change, les projections suivent — jamais l'inverse")
    pos, end, move, swap = scene_state(t)

    # -- la scène : un objet sombre, dans ses couleurs, quel que soit le thème
    p.append('<g data-keep="1">')
    X, Y, Wd, Hd = 48, 116, 400, 474
    p.append(rect(X, Y, Wd, Hd, INK, 14, extra=' data-dark-stroke="#323A40"'))
    p.append(text(X + 24, Y + 34, "LA SCÈNE · CE QUI EXISTE", 11, 600, MUTED, spacing=1.8))
    ix, iy, iw, ih = X + 40, Y + 70, Wd - 80, Hd - 170

    def sp(q):
        return ix + q[0] * iw, iy + q[1] * ih

    for a, b in EDGES:
        (x1, y1), (x2, y2) = sp(pos[a]), sp(pos[b])
        p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{SLATE}" stroke-width="2"/>')
    (x1, y1), (x2, y2) = sp(pos["n2"]), sp(end)
    p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{ORANGE}" stroke-width="2.5"/>')
    for k, q in pos.items():
        x, y = sp(q)
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="17" fill="{WHITE}"/>')
        p.append(text(x, y + 4.5, k, 12, 700, INK, "middle"))
    # journal : le dernier fait enregistré par la scène
    if 3.8 <= t < 5.4:
        log, col = "aucun changement — requête de renderer refusée", ORANGE
    elif move > 0.01 and swap < 0.01 and t < 3.0:
        log, col = "n2 · position modifiée par la scène", WHITE
    elif t < 3.8 and swap > 0.01:
        log, col = "relation n2 → n3 (était n2 → n1)", WHITE
    elif 5.4 <= t < 6.3:
        log, col = "relation n2 → n1 rétablie", WHITE
    elif 6.3 <= t < 7.7:
        log, col = "n2 · position rétablie", WHITE
    else:
        log, col = "scène stable", MUTED
    p.append(rect(X + 20, Y + Hd - 76, Wd - 40, 56, "#22262C", 10))
    p.append(text(X + 36, Y + Hd - 52, "DERNIER FAIT", 10, 600, MUTED, spacing=1.6))
    p.append(text(X + 36, Y + Hd - 32, log, 13, 500, col))

    p.append("</g>")

    # -- les deux projections
    def projection(px, color, tint, title, sub, style):
        pw, ph = 330, 474
        p.append(rect(px, Y, pw, ph, WHITE, 14, HAIRLINE))
        p.append(rect(px, Y, pw, 4, color, 2))
        p.append(text(px + 22, Y + 34, title, 11, 700, color, spacing=1.6))
        p.append(text(px + 22, Y + 54, sub, 12, 400, SLATE))
        jx, jy, jw, jh = px + 40, Y + 100, pw - 80, ph - 170

        def pp(q):
            if style == "cards":
                return jx + q[0] * jw, jy + q[1] * jh
            # projection oblique : même faits, autre géométrie de dessin
            return jx + q[0] * jw * 0.86 + q[1] * 30, jy + 40 + q[1] * jh * 0.62

        if style == "dots":
            for k in range(5):
                gy = jy + 40 + k * jh * 0.62 / 4
                p.append(f'<line x1="{jx}" y1="{gy:.1f}" x2="{jx + jw}" y2="{gy:.1f}" stroke="{QUIET}"/>')
        lines = [(pp(pos[a]), pp(pos[b]), MUTED) for a, b in EDGES] + [(pp(pos["n2"]), pp(end), ORANGE)]
        for (x1, y1), (x2, y2), c in lines:
            dash = ' stroke-dasharray="5 4"' if style == "dots" else ""
            p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="2"{dash}/>')
        for k, q in pos.items():
            x, y = pp(q)
            if style == "cards":
                p.append(rect(x - 24, y - 16, 48, 32, tint, 8, color, 1.5))
                p.append(text(x, y + 4.5, k, 12, 700, color, "middle"))
            else:
                p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{color}"/>')
                p.append(text(x + 13, y - 9, k, 11, 600, color))
        return pp

    projection(472, BLUE700, BLUE100, "PROJECTION 1 · NAVIGATEUR", "PixiJS : des cartes", "cards")
    pp2 = projection(822, GREEN700, GREEN100, "PROJECTION 2 · AUTRE RENDERER", "même scène, autre dessin", "dots")

    # flèches « observe » de la scène vers les projections
    for ax in (452, 802):
        p.append(f'<path d="M{ax - 4} {Y + 237} L{ax + 12} {Y + 237}" stroke="{MUTED}" stroke-width="2"/>')
        p.append(f'<path d="M{ax + 12} {Y + 232} L{ax + 18} {Y + 237} L{ax + 12} {Y + 242} Z" fill="{MUTED}"/>')

    # tentative de déplacement depuis la projection 2 : refusée, n4 ne bouge pas
    tx, ty = pp2(pos["n4"])
    hx, hy = 1080, 560
    if 3.3 <= t < 5.4:
        if t < 3.8:
            q = ease(seg(t, 3.3, 3.8))
            cx_, cy_ = lerp(hx, tx, q), lerp(hy, ty, q)
        elif t < 4.8:
            q = ease(seg(t, 3.85, 4.6))
            cx_, cy_ = tx + 80 * q, ty - 10 * q
        else:
            q = ease(seg(t, 4.8, 5.35))
            cx_, cy_ = lerp(tx + 80, hx, q), lerp(ty - 10, hy, q)
        if 3.85 <= t < 4.8:
            p.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{cx_:.1f}" y2="{cy_:.1f}" stroke="{ORANGE}" stroke-width="1.5" stroke-dasharray="3 3"/>')
        p.append(cursor(cx_, cy_, pressed=3.85 <= t < 4.8))
    if 3.9 <= t < 5.6:
        p.append(rect(834, Y + Hd - 62, 306, 44, ORANGE100, 10, ORANGE700))
        p.append(text(852, Y + Hd - 43, "✕ refusé", 12.5, 700, ORANGE700))
        p.append(text(852, Y + Hd - 26, "déplacer un objet appartient à la scène", 12, 400, INK))

    p.append(text(48, H - 14, "Animation de principe, d'après in.gnu6/CONTRACT.md : un renderer observe et dessine ; "
                  "il ne renomme, ne déplace, n'invente rien.", 11, 400, MUTED))
    return svg(p)


# ---------- assemblage ----------

def render(name, frame_fn, duration, fps, still_t):
    work = Path(tempfile.mkdtemp(prefix=f"gif-{name}-"))
    try:
        n = round(duration * fps)
        paint = darken if THEME == "dark" else (lambda s: s)
        for i in range(n):
            (work / f"f{i:04d}.svg").write_text(paint(frame_fn(i / fps)), encoding="utf-8")
        # rsvg-convert en lot : une image PNG par SVG
        svgs = sorted(work.glob("f*.svg"))
        for s in svgs:
            subprocess.run(["rsvg-convert", "-w", str(W), "-o", str(s.with_suffix(".png")), str(s)], check=True)
        palette = work / "palette.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", str(work / "f%04d.png"),
                        "-vf", "palettegen=max_colors=128:stats_mode=full", str(palette)], check=True)
        out = OUT / "en" if LANG == "en" else OUT
        if THEME == "dark":
            out = out / "dark"
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", str(work / "f%04d.png"),
                        "-i", str(palette), "-lavfi", "paletteuse=dither=none", "-loop", "0",
                        str(out / f"{name}.gif")], check=True)
        if THEME == "light":
            still = work / "still.svg"
            still.write_text(frame_fn(still_t), encoding="utf-8")
            subprocess.run(["rsvg-convert", "-w", str(W), "-o", str(out / f"{name}-still.png"), str(still)], check=True)
        size = (out / f"{name}.gif").stat().st_size
        print(f"{LANG}/{THEME}/{name}.gif  {n} images à {fps} i/s  {size / 1024:.0f} Kio")
    finally:
        shutil.rmtree(work)


def main():
    global LANG, THEME
    args = sys.argv[1:]
    themes = ["light", "dark"]
    if "--theme" in args:
        k = args.index("--theme")
        themes = [args[k + 1]]
        del args[k:k + 2]
    langs = args or ["fr", "en"]
    for LANG, THEME in [(lang, theme) for lang in langs for theme in themes]:
        render("gnosix-appstack", gnosix_frame, 6.4, 25, still_t=2.8)
        render("gnostral-course", gnostral_frame, GN_TOTAL, 20, still_t=GN_END + 1.0)
        render("gnu6-scene-projection", gnu6_frame, 8.4, 25, still_t=4.3)


if __name__ == "__main__":
    main()
