#!/usr/bin/env python3
"""La navigation des pages : ancres partageables, sommaires, précédent / suivant.

- chaque titre de section (h2) reçoit un identifiant stable et un lien « # » qui
  pointe sur lui : on peut copier l'adresse d'une section et l'envoyer ;
- les quatre dossiers reçoivent un sommaire : une colonne collante sur grand
  écran, un bloc repliable en haut de page ailleurs (assets/nav.js marque la
  section en cours) ;
- chaque page reçoit, en bas, la page précédente et la suivante dans l'ordre de
  lecture : l'accueil, la méthode, les quatre dossiers, puis la vérification,
  la chronologie et le glossaire.

Le script retire ce qu'il a posé avant de le reposer : il peut être relancé.

Usage : python3 tools/navigation.py
"""

from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ORDER = {
    "fr": ["index.html", "methode.html", "gnosix.html", "gnostral.html", "calix.html", "ingnu6.html",
           "verifier.html", "chronologie.html", "comprendre.html"],
    "en": ["en/index.html", "en/method.html", "en/gnosix.html", "en/gnostral.html", "en/calix.html",
           "en/ingnu6.html", "en/verify.html", "en/timeline.html", "en/glossary.html"],
}
DOSSIERS = {"gnosix.html", "gnostral.html", "calix.html", "ingnu6.html"}
WORDS = {
    "fr": dict(toc="Sur cette page", prev="Précédent", next="Suivant", anchor="Lien vers cette section"),
    "en": dict(toc="On this page", prev="Previous", next="Next", anchor="Link to this section"),
}


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", html.unescape(text))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:60] or "section"


def plain(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


def title_of(page: str) -> str:
    s = (ROOT / page).read_text(encoding="utf-8")
    h1 = re.search(r"<h1>(.*?)</h1>", s, flags=re.S)
    return plain(h1.group(1)) if h1 else page


def strip_generated(s: str) -> str:
    s = re.sub(r"\n?<!-- nav:[a-z]+ -->.*?<!-- /nav:[a-z]+ -->", "", s, flags=re.S)
    s = re.sub(r' <a class="anchor"[^>]*>#</a>', "", s)
    s = re.sub(r'<h2 id="[^"]*">', "<h2>", s)
    s = s.replace('<main class="has-toc">', "<main>").replace('<body class="has-toc">', "<body>")
    return s


def process(page: str, lang: str) -> None:
    p = ROOT / page
    s = strip_generated(p.read_text(encoding="utf-8"))
    w = WORDS[lang]
    prefix = "../" if lang == "en" else ""
    name = page.removeprefix("en/")

    # 1. ancres
    seen: dict[str, int] = {}
    heads = []

    def anchor(m):
        inner = m.group(1)
        base = slug(plain(inner))
        seen[base] = seen.get(base, 0) + 1
        ident = base if seen[base] == 1 else f"{base}-{seen[base]}"
        heads.append((ident, plain(inner)))
        return (f'<h2 id="{ident}">{inner} <a class="anchor" href="#{ident}" '
                f'aria-label="{w["anchor"]}">#</a></h2>')
    a, b = s.index("<main>"), s.index("</main>")
    body = re.sub(r"<h2>(.*?)</h2>", anchor, s[a:b], flags=re.S)

    # 2. sommaire des dossiers
    if name in DOSSIERS or name in {"gnosix.html"}:
        items = "\n".join(f'        <li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in heads)
        side = (f'<!-- nav:side -->\n  <aside class="toc-side" aria-label="{w["toc"]}">\n'
                f'    <nav>\n      <p class="toc-title">{w["toc"]}</p>\n      <ol>\n{items}\n      </ol>\n    </nav>\n'
                f'  </aside>\n<!-- /nav:side -->')
        top = (f'<!-- nav:top -->\n  <details class="toc-top">\n    <summary>{w["toc"]}</summary>\n'
               f'    <ol>\n{items}\n    </ol>\n  </details>\n<!-- /nav:top -->')
        body = body.replace("<main>", '<main class="has-toc">\n' + side, 1)
        hero_end = re.search(r'(  <div class="hero prose">.*?\n  </div>\n)', body, flags=re.S)
        if hero_end:
            body = body[:hero_end.end()] + top + "\n" + body[hero_end.end():]

    # 3. précédent / suivant
    order = ORDER[lang]
    k = order.index(page)
    cards = []
    if k > 0:
        prev = order[k - 1]
        cards.append(f'    <a class="pager-prev" href="{prev.removeprefix("en/")}"><span>← {w["prev"]}</span>'
                     f'<b>{html.escape(title_of(prev))}</b></a>')
    if k < len(order) - 1:
        nxt = order[k + 1]
        cards.append(f'    <a class="pager-next" href="{nxt.removeprefix("en/")}"><span>{w["next"]} →</span>'
                     f'<b>{html.escape(title_of(nxt))}</b></a>')
    pager = "<!-- nav:pager -->\n  <nav class=\"pager\" aria-label=\"" + w["prev"] + " / " + w["next"] + "\">\n" \
            + "\n".join(cards) + "\n  </nav>\n<!-- /nav:pager -->\n"
    body = body.rstrip() + "\n\n" + pager

    s = s[:a] + body + s[b:]
    if name in DOSSIERS:
        s = s.replace("<body>", '<body class="has-toc">', 1)
    tag = f'<script src="{prefix}assets/nav.js" defer></script>'
    if tag not in s:
        s = s.replace("</head>", tag + "\n</head>", 1)
    p.write_text(s, encoding="utf-8")
    print(f"{page:18} {len(heads):2} sections{' + sommaire' if name in DOSSIERS else ''}")


def main():
    for lang, pages in ORDER.items():
        for page in pages:
            process(page, lang)


if __name__ == "__main__":
    main()
