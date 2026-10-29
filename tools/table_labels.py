#!/usr/bin/env python3
"""Recopie l'intitulé de chaque colonne sur ses cellules (attribut data-label).

Sur téléphone, style.css présente chaque ligne de tableau comme une fiche ; la cellule
affiche alors son intitulé au-dessus de sa valeur. Le script peut être relancé.

Usage : python3 tools/table_labels.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index.html", "gnosix.html", "gnostral.html", "calix.html", "ingnu6.html", "comprendre.html",
         "en/index.html", "en/gnosix.html", "en/gnostral.html", "en/calix.html", "en/ingnu6.html", "en/glossary.html"]


def label_table(table: str) -> str:
    heads = [html.unescape(re.sub(r"<[^>]+>", "", h)).strip()
             for h in re.findall(r"<th[^>]*>(.*?)</th>", table, flags=re.S)]
    if not heads:
        return table

    def row(m):
        i = -1

        def cell(c):
            nonlocal i
            i += 1
            attrs = re.sub(r'\s*data-label="[^"]*"', "", c.group(1))
            if i >= len(heads):
                return f"<td{attrs}>"
            return f'<td{attrs} data-label="{html.escape(heads[i], quote=True)}">'
        return re.sub(r"<td([^>]*)>", cell, m.group(0))

    head_end = table.find("</thead>")
    if head_end == -1:
        return table
    return table[:head_end] + re.sub(r"<tr\b.*?</tr>", row, table[head_end:], flags=re.S)


def main():
    for page in PAGES:
        p = ROOT / page
        s = p.read_text(encoding="utf-8")
        s = re.sub(r"<table\b.*?</table>", lambda m: label_table(m.group(0)), s, flags=re.S)
        p.write_text(s, encoding="utf-8")
        print(f"{page:16} {s.count('data-label=')} cellules")


if __name__ == "__main__":
    main()
