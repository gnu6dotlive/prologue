#!/usr/bin/env python3
"""Relie chaque page à sa traduction : sélecteur FR · EN, hreflang, aperçu de partage.

Pour chaque paire de pages, le script (re)pose dans <head> les balises canonical,
hreflang et Open Graph de la bonne langue, et dans l'en-tête un sélecteur qui mène à la
même page dans l'autre langue. Il peut être relancé.

Usage : python3 tools/i18n_head.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://gnu6dotlive.github.io/prologue/"
PAIRS = [("index.html", "en/index.html"), ("gnosix.html", "en/gnosix.html"),
         ("gnostral.html", "en/gnostral.html"), ("calix.html", "en/calix.html"),
         ("ingnu6.html", "en/ingnu6.html"), ("comprendre.html", "en/glossary.html")]


def url(page: str) -> str:
    return BASE + ("" if page == "index.html" else "en/" if page == "en/index.html" else page)


def head_block(page: str, fr: str, en: str, title: str, desc: str) -> str:
    lang = "en" if page.startswith("en/") else "fr"
    locale, alt = ("en_US", "fr_CA") if lang == "en" else ("fr_CA", "en_US")
    e = lambda s: html.escape(s, quote=True)
    return "\n".join([
        "<!-- i18n:start -->",
        f'<link rel="canonical" href="{url(page)}">',
        f'<link rel="alternate" hreflang="fr" href="{url(fr)}">',
        f'<link rel="alternate" hreflang="en" href="{url(en)}">',
        f'<link rel="alternate" hreflang="x-default" href="{url(fr)}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="prologue · gnu6dotlive">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{url(page)}">',
        f'<meta property="og:image" content="{BASE}assets/og{"-en" if lang == "en" else ""}.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:locale" content="{locale}">',
        f'<meta property="og:locale:alternate" content="{alt}">',
        '<meta name="twitter:card" content="summary_large_image">',
        "<!-- i18n:end -->",
    ])


def switch(page: str, fr: str, en: str) -> str:
    if page.startswith("en/"):
        target = "../" + fr
        return (f'<a class="lang-switch" href="{target}" hreflang="fr" lang="fr" '
                f'title="Version française">FR</a>')
    return (f'<a class="lang-switch" href="{en}" hreflang="en" lang="en" '
            f'title="English version">EN</a>')


def process(page: str, fr: str, en: str) -> None:
    p = ROOT / page
    s = p.read_text(encoding="utf-8")
    # anciennes balises de partage posées à la main, puis bloc précédent
    s = re.sub(r'\n<meta (property="og:[^"]+"|name="twitter:card")[^>]*>', "", s)
    s = re.sub(r"\n<!-- i18n:start -->.*?<!-- i18n:end -->", "", s, flags=re.S)
    s = re.sub(r'\s*<a class="lang-switch"[^>]*>[^<]*</a>', "", s)
    title = html.unescape(re.search(r"<title>(.*?)</title>", s).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)">', s).group(1))
    m = re.search(r'<meta name="description" content="[^"]*">', s)
    s = s[:m.end()] + "\n" + head_block(page, fr, en, title, desc) + s[m.end():]
    s = s.replace("    </nav>\n  </div>\n</header>",
                  "    </nav>\n    " + switch(page, fr, en) + "\n  </div>\n</header>", 1)
    p.write_text(s, encoding="utf-8")


def main():
    for fr, en in PAIRS:
        process(fr, fr, en)
        process(en, fr, en)
        print(f"{fr:16} ⇄ {en}")


if __name__ == "__main__":
    main()
