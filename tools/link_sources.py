#!/usr/bin/env python3
"""Relie chaque source citée dans les pages à son dépôt, avec une fiche au survol.

Le registre ci-dessous est la seule liste des sources. Le script :

  - retire les liens qu'il a lui-même posés (classe « src »), puis les repose :
    il peut donc être relancé autant de fois que nécessaire ;
  - lie la première mention de chaque source dans chaque <section> de <main>,
    hors titres, liens existants, étiquettes et boutons ;
  - écrit de vrais <a href> : le lien marche sans JavaScript et dans le PDF.
    assets/sources.js ne fait qu'afficher la fiche (titre, description, adresse).

Les quatre dépôts du dossier sont liés au commit du jour de l'instantané (DATE) :
le lien montre ce que la page décrit, même quand le dépôt a avancé depuis.

Usage : python3 tools/link_sources.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index.html", "gnosix.html", "gnostral.html", "calix.html", "ingnu6.html", "comprendre.html",
         "en/index.html", "en/gnosix.html", "en/gnostral.html", "en/calix.html", "en/ingnu6.html", "en/glossary.html",
         "methode.html", "verifier.html", "chronologie.html", "en/method.html", "en/verify.html", "en/timeline.html"]

DATE = {"fr": "29 octobre 2026", "en": "October 29, 2026"}
LANG = "fr"
GH = "https://github.com/gnu6dotlive"
PIN = {  # dernier commit public de chaque dépôt au jour de l'instantané
    "gnosix": "66d801b0069808e6a18120ac41477a20466b4d66",
    "gnostral.rs": "38c4134a3a398b5b83d34326826362cf4dcc7336",
    "calix": "aa423254f89cd233f261fbf19f4705d1d9c94259",
    "in.gnu6": "fec80a7ae19de4b5838fe9f84dd271d6924fa753",
}


def blob(repo: str, path: str) -> str:
    kind = "tree" if path.endswith("/") else "blob"
    return f"{GH}/{repo}/{kind}/{PIN[repo]}/{path.rstrip('/')}"


def pinned(repo: str) -> str:
    return f"{GH}/{repo}/tree/{PIN[repo]}"


# --- sources externes : (identifiant, motifs, titre, description, adresse)
EXTERNAL = [
    ("mistralrs", ["mistral.rs"], "mistral.rs", "Moteur d'inférence de grands modèles de langage, écrit en Rust. gnostral.rs le modifie ; il ne le remplace pas.", "https://github.com/EricLBuehler/mistral.rs"),
    ("llamacpp", ["llama.cpp"], "llama.cpp", "Moteur d'inférence en C/C++, très répandu. C'est la référence de comparaison du dossier gnostral.", "https://github.com/ggml-org/llama.cpp"),
    ("candle", ["Candle"], "Candle", "Cadre d'apprentissage automatique minimaliste en Rust, par Hugging Face.", "https://github.com/huggingface/candle"),
    ("vllm", ["vLLM"], "vLLM", "Moteur de service d'inférence à haut débit, pensé pour les centres de données.", "https://github.com/vllm-project/vllm"),
    ("qwen", ["Qwen"], "Qwen", "Famille de modèles de langage ouverts de l'équipe Qwen (Alibaba). Les modèles mesurés dans le dossier en font partie.", "https://github.com/QwenLM"),
    ("mistralai", ["Mistral AI"], "Mistral AI", "Entreprise qui conçoit les modèles Mistral. Aucun lien avec le moteur mistral.rs.", "https://github.com/mistralai"),
    ("pixijs", ["PixiJS"], "PixiJS", "Moteur de rendu 2D pour le navigateur (WebGL). C'est le renderer de référence d'in.gnu6.", "https://github.com/pixijs/pixijs"),
    ("hyprland", ["Hyprland"], "Hyprland", "Compositeur Wayland, celui sur lequel gnosix dessine son bureau.", "https://github.com/hyprwm/Hyprland"),
    ("gpui", ["GPUI"], "GPUI", "Bibliothèque d'interface accélérée par le GPU, issue de l'éditeur Zed. Socle commun de gnosix et Calix.", "https://github.com/zed-industries/zed/tree/main/crates/gpui"),
    ("wppresentation", ["wp_presentation"], "wp_presentation", "Protocole Wayland qui indique quand une image a réellement été présentée à l'écran.", "https://gitlab.freedesktop.org/wayland/wayland-protocols/-/tree/main/stable/presentation-time"),
    ("wayland", ["Wayland"], "Wayland", "Le protocole d'affichage moderne de Linux, entre les applications et le compositeur.", "https://gitlab.freedesktop.org/wayland/wayland"),
    ("vulkan", ["Vulkan"], "Vulkan", "API graphique et de calcul ouverte, maintenue par le Khronos Group.", "https://github.com/KhronosGroup/Vulkan-Docs"),
    ("cuda", ["CUDA"], "CUDA", "Plateforme de calcul parallèle de NVIDIA pour ses cartes graphiques.", "https://developer.nvidia.com/cuda-toolkit"),
    ("pkexec", ["pkexec"], "pkexec", "Commande de polkit qui exécute une action autorisée avec les droits d'administrateur.", "https://github.com/polkit-org/polkit"),
    ("polkit", ["polkit"], "polkit", "Le système d'autorisations de Linux : il décide qui peut faire quelle action privilégiée.", "https://github.com/polkit-org/polkit"),
    ("libalpm", ["libalpm", "ALPM", "pacman"], "pacman · libalpm", "Le gestionnaire de paquets d'Arch Linux et sa bibliothèque (ALPM).", "https://gitlab.archlinux.org/pacman/pacman"),
    ("aur", ["AUR"], "AUR", "Arch User Repository : des recettes de paquets écrites par la communauté, compilées chez soi.", "https://aur.archlinux.org"),
    ("flatpak", ["Flatpak", "flatpak"], "Flatpak", "Format d'application isolée du système, distribuée avec ses dépendances.", "https://github.com/flatpak/flatpak"),
    ("appimage", ["AppImage", "AppImages"], "AppImage", "Une application entière dans un seul fichier exécutable, sans installation.", "https://github.com/AppImage"),
    ("cargo", ["Cargo"], "Cargo", "Le gestionnaire de paquets et de compilation du langage Rust.", "https://github.com/rust-lang/cargo"),
    ("npm", ["NPM", "npm"], "npm", "Le gestionnaire de paquets de l'écosystème JavaScript.", "https://github.com/npm/cli"),
    ("zig", ["Zig"], "Zig", "Langage système compact ; le moteur de paquets de Calix est écrit en Zig.", "https://codeberg.org/ziglang/zig"),
    ("rust", ["Rust"], "Rust", "Langage système sûr pour la mémoire, celui de gnosix, gnostral.rs et Calix.", "https://github.com/rust-lang/rust"),
    ("typescript", ["TypeScript"], "TypeScript", "JavaScript typé, par Microsoft. Le noyau d'in.gnu6 est écrit en TypeScript.", "https://github.com/microsoft/TypeScript"),
    ("nodejs", ["Node.js"], "Node.js", "Environnement d'exécution JavaScript hors navigateur.", "https://github.com/nodejs/node"),
    ("logind", ["logind"], "systemd-logind", "Le service de systemd qui gère les sessions : verrouiller, suspendre, éteindre.", "https://github.com/systemd/systemd"),
    ("mpris", ["MPRIS"], "MPRIS", "Spécification freedesktop pour piloter les lecteurs multimédias.", "https://specifications.freedesktop.org/mpris-spec/latest/"),
    ("pam", ["PAM"], "Linux PAM", "Modules d'authentification de Linux ; l'écran de verrouillage s'en sert.", "https://github.com/linux-pam/linux-pam"),
    ("tabler", ["Tabler"], "Tabler Icons", "Jeu d'icônes libre (MIT), dessinées au trait.", "https://github.com/tabler/tabler-icons"),
    ("arch", ["Arch Linux"], "Arch Linux", "Distribution Linux minimaliste, en publication continue.", "https://archlinux.org"),
]

# --- documents des quatre dépôts, liés au commit du jour, par page
DOCS = {
    "gnosix.html": ("gnosix", [
        ("docs/status/STATUS.md", "État publié de gnosix : chaque surface et son niveau de preuve."),
        ("ARCHITECTURE.md", "Architecture de gnosix : les quatre plans et leurs frontières."),
        ("README.md", "Présentation du dépôt gnosix."),
    ]),
    "gnostral.html": ("gnostral.rs", [
        ("docs/CAPABILITY_MATRIX.md", "Matrice publique des capacités, avec leurs limites."),
        ("docs/ARCHITECTURE.md", "Architecture et méthode : les huit états de la vérité."),
        ("README.md", "Présentation du dépôt gnostral.rs et ses chiffres mesurés."),
    ]),
    "calix.html": ("calix", [
        ("docs/calix-architecture.md", "Architecture de Calix : interface, moteur, service, notifications."),
        ("docs/brand.md", "Marque et jetons visuels de Calix."),
        ("README.md", "Présentation du dépôt Calix, avec son tableau d'état."),
    ]),
    "ingnu6.html": ("in.gnu6", [
        ("docs/public/PUBLICATION-READINESS.md", "Ce que la publication d'in.gnu6 autorise, et ce qu'elle n'autorise pas."),
        ("docs/evidence/assets/", "Captures et pièces des dossiers de qualification."),
        ("CONTRACT.md", "Le contrat d'in.gnu6 : ce que la scène possède, ce que les renderers n'ont pas le droit de faire."),
        ("QUESTLOG.md", "Le journal des jalons, ratifiés ou ouverts."),
        ("README.md", "Présentation du dépôt in.gnu6."),
    ]),
}

# --- jalons et protocoles cités en texte, liés à leur reçu
MILESTONES = {
    "gnostral.html": ("gnostral.rs", [
        ("Q-010", "evidence/runs/q010-hotpath-ssd-ab-audit-20261010.json", "Reçu d'audit Q-010 : la mesure A/B appariée, réponse par réponse."),
        ("Q-011", "evidence/runs/q011-rtx3070-placement-observation-20261010.json", "Reçu Q-011 : placement des couches sous pression mémoire."),
        ("Q-012", "evidence/runs/gnostral-q012-native-three-families-20261010.json", "Reçu Q-012 : un moteur, trois familles de modèles."),
        ("Q-013-C", "evidence/runs/gnostral-q013c-real-dense-single-server-20261010.json", "Reçu Q-013-C : le cycle de vie d'un vrai processus dense."),
    ]),
    "verifier.html": ("gnostral.rs", [
        ("Q-010", "evidence/runs/q010-hotpath-ssd-ab-audit-20261010.json", "Reçu d'audit Q-010 : la mesure A/B appariée, réponse par réponse."),
    ]),
    "ingnu6.html": ("in.gnu6", [
        ("CUDA-05F", "docs/agent-results/blobin-next-01/CUDA-05F.md", "Rapport CUDA-05F : protocole, portes, essais négatifs conservés, limites."),
        ("MQ-12", "docs/evidence/mq-12-pixi-browser-2026-10-07.md", "Dossier de qualification MQ-12 : le renderer navigateur de référence."),
    ]),
}

# --- les fiches en anglais (pages /en/) : texte français → texte anglais
EN = {
    "Moteur d'inférence de grands modèles de langage, écrit en Rust. gnostral.rs le modifie ; il ne le remplace pas.": "A large-language-model inference engine written in Rust. gnostral.rs modifies it; it does not replace it.",
    "Moteur d'inférence en C/C++, très répandu. C'est la référence de comparaison du dossier gnostral.": "A widely used inference engine in C/C++. It is the comparison reference in the gnostral dossier.",
    "Cadre d'apprentissage automatique minimaliste en Rust, par Hugging Face.": "A minimalist machine-learning framework in Rust, by Hugging Face.",
    "Moteur de service d'inférence à haut débit, pensé pour les centres de données.": "A high-throughput inference serving engine, designed for datacenters.",
    "Famille de modèles de langage ouverts de l'équipe Qwen (Alibaba). Les modèles mesurés dans le dossier en font partie.": "A family of open language models from the Qwen team (Alibaba). The models measured in the dossier belong to it.",
    "Entreprise qui conçoit les modèles Mistral. Aucun lien avec le moteur mistral.rs.": "The company that designs the Mistral models. Unrelated to the mistral.rs engine.",
    "Moteur de rendu 2D pour le navigateur (WebGL). C'est le renderer de référence d'in.gnu6.": "A 2D rendering engine for the browser (WebGL). It is in.gnu6's reference renderer.",
    "Compositeur Wayland, celui sur lequel gnosix dessine son bureau.": "A Wayland compositor — the one gnosix draws its desktop on.",
    "Bibliothèque d'interface accélérée par le GPU, issue de l'éditeur Zed. Socle commun de gnosix et Calix.": "A GPU-accelerated interface library from the Zed editor. The shared foundation of gnosix and Calix.",
    "Protocole Wayland qui indique quand une image a réellement été présentée à l'écran.": "A Wayland protocol that tells when a frame was actually presented on screen.",
    "Le protocole d'affichage moderne de Linux, entre les applications et le compositeur.": "Linux's modern display protocol, between applications and the compositor.",
    "API graphique et de calcul ouverte, maintenue par le Khronos Group.": "An open graphics and compute API, maintained by the Khronos Group.",
    "Plateforme de calcul parallèle de NVIDIA pour ses cartes graphiques.": "NVIDIA's parallel computing platform for its graphics cards.",
    "Commande de polkit qui exécute une action autorisée avec les droits d'administrateur.": "The polkit command that runs an authorised action with administrator rights.",
    "Le système d'autorisations de Linux : il décide qui peut faire quelle action privilégiée.": "Linux's authorisation system: it decides who may perform which privileged action.",
    "Le gestionnaire de paquets d'Arch Linux et sa bibliothèque (ALPM).": "Arch Linux's package manager and its library (ALPM).",
    "Arch User Repository : des recettes de paquets écrites par la communauté, compilées chez soi.": "Arch User Repository: package recipes written by the community, built on your own machine.",
    "Format d'application isolée du système, distribuée avec ses dépendances.": "An application format sandboxed from the system, shipped with its dependencies.",
    "Une application entière dans un seul fichier exécutable, sans installation.": "A whole application in a single executable file, with no installation.",
    "Le gestionnaire de paquets et de compilation du langage Rust.": "The package manager and build tool of the Rust language.",
    "Le gestionnaire de paquets de l'écosystème JavaScript.": "The package manager of the JavaScript ecosystem.",
    "Langage système compact ; le moteur de paquets de Calix est écrit en Zig.": "A compact systems language; Calix's package engine is written in Zig.",
    "Langage système sûr pour la mémoire, celui de gnosix, gnostral.rs et Calix.": "A memory-safe systems language — that of gnosix, gnostral.rs and Calix.",
    "JavaScript typé, par Microsoft. Le noyau d'in.gnu6 est écrit en TypeScript.": "Typed JavaScript, by Microsoft. in.gnu6's core is written in TypeScript.",
    "Environnement d'exécution JavaScript hors navigateur.": "A JavaScript runtime outside the browser.",
    "Le service de systemd qui gère les sessions : verrouiller, suspendre, éteindre.": "The systemd service that manages sessions: lock, suspend, power off.",
    "Spécification freedesktop pour piloter les lecteurs multimédias.": "A freedesktop specification for controlling media players.",
    "Modules d'authentification de Linux ; l'écran de verrouillage s'en sert.": "Linux's authentication modules; the lock screen uses them.",
    "Jeu d'icônes libre (MIT), dessinées au trait.": "A free icon set (MIT), drawn as strokes.",
    "Distribution Linux minimaliste, en publication continue.": "A minimalist, rolling-release Linux distribution.",
    "État publié de gnosix : chaque surface et son niveau de preuve.": "gnosix's published status: each surface and its level of proof.",
    "Architecture de gnosix : les quatre plans et leurs frontières.": "gnosix's architecture: the four planes and their boundaries.",
    "Présentation du dépôt gnosix.": "Overview of the gnosix repository.",
    "Matrice publique des capacités, avec leurs limites.": "The public capability matrix, with its limits.",
    "Architecture et méthode : les huit états de la vérité.": "Architecture and method: the eight states of truth.",
    "Présentation du dépôt gnostral.rs et ses chiffres mesurés.": "Overview of the gnostral.rs repository and its measured figures.",
    "Architecture de Calix : interface, moteur, service, notifications.": "Calix's architecture: interface, engine, service, notifications.",
    "Marque et jetons visuels de Calix.": "Calix's brand and visual tokens.",
    "Présentation du dépôt Calix, avec son tableau d'état.": "Overview of the Calix repository, with its status table.",
    "Ce que la publication d'in.gnu6 autorise, et ce qu'elle n'autorise pas.": "What publishing in.gnu6 allows, and what it does not.",
    "Captures et pièces des dossiers de qualification.": "Screenshots and exhibits from the qualification records.",
    "Le contrat d'in.gnu6 : ce que la scène possède, ce que les renderers n'ont pas le droit de faire.": "in.gnu6's contract: what the scene owns, what renderers are not allowed to do.",
    "Le journal des jalons, ratifiés ou ouverts.": "The milestone log, ratified or open.",
    "Présentation du dépôt in.gnu6.": "Overview of the in.gnu6 repository.",
    "Reçu d'audit Q-010 : la mesure A/B appariée, réponse par réponse.": "Q-010 audit receipt: the paired A/B measurement, answer by answer.",
    "Reçu Q-011 : placement des couches sous pression mémoire.": "Q-011 receipt: layer placement under memory pressure.",
    "Reçu Q-012 : un moteur, trois familles de modèles.": "Q-012 receipt: one engine, three model families.",
    "Reçu Q-013-C : le cycle de vie d'un vrai processus dense.": "Q-013-C receipt: the lifecycle of a real dense process.",
    "Rapport CUDA-05F : protocole, portes, essais négatifs conservés, limites.": "CUDA-05F report: protocol, gates, negative runs kept, limits.",
    "Dossier de qualification MQ-12 : le renderer navigateur de référence.": "MQ-12 qualification record: the reference browser renderer.",
    "Environnement de bureau Linux en Rust.": "A Linux desktop environment in Rust.",
    "Laboratoire d'inférence locale en Rust sur GPU contraint.": "A lab for local inference in Rust on a constrained GPU.",
    "Gestion de paquets native pour Arch Linux.": "Native package management for Arch Linux.",
    "Moteur de scènes et de topologies.": "A scene and topology engine.",
}

# noms de dépôts écrits en <code> (accueil, glossaire)
REPOS = {"gnosix": "gnosix", "gnu6dotlive/gnosix": "gnosix", "gnostral.rs": "gnostral.rs",
         "gnu6dotlive/gnostral.rs": "gnostral.rs", "calix": "calix", "in.gnu6": "in.gnu6"}
REPO_DESC = {"gnosix": "Environnement de bureau Linux en Rust.",
             "gnostral.rs": "Laboratoire d'inférence locale en Rust sur GPU contraint.",
             "calix": "Gestion de paquets native pour Arch Linux.",
             "in.gnu6": "Moteur de scènes et de topologies."}

SKIP_TAGS = {"a", "h1", "h2", "h3", "h4", "title", "script", "style", "nav", "header", "footer", "button", "summary"}
SKIP_CLASSES = {"tag", "label", "kicker", "btn"}
VOID = {"img", "meta", "link", "br", "hr", "input", "source", "wbr"}


def L(s: str) -> str:
    """Le texte de la fiche dans la langue de la page."""
    if LANG != "en":
        return s
    if s not in EN:
        raise KeyError(f"fiche sans traduction anglaise : {s}")
    return EN[s]


def stamp(href: str, repo: str) -> str:
    when = "as of" if LANG == "en" else "état au"
    return f"{short(href)} · commit {PIN[repo][:7]} · {when} {DATE[LANG]}"


def anchor(sid, href, title, desc, meta, inner):
    desc = L(desc)
    attrs = (f'class="src" data-src="{sid}" href="{html.escape(href)}" '
             f'data-title="{html.escape(title)}" data-desc="{html.escape(desc)}" data-meta="{html.escape(meta)}"')
    return f"<a {attrs}>{inner}</a>"


def host(url: str) -> str:
    return re.sub(r"^https?://", "", url).split("/")[0]


def short(url: str) -> str:
    u = re.sub(r"^https?://", "", url).rstrip("/")
    u = re.sub(r"/(blob|tree)/[0-9a-f]{40}", "", u)
    return u


def build_rules(page):
    rules = []  # (id, regex, href, title, desc, meta)
    for repo_page, (repo, docs) in MILESTONES.items():
        if repo_page != page:
            continue
        for label, path, desc in docs:
            href = blob(repo, path)
            meta = stamp(href, repo)
            rules.append((f"ms-{label}", re.compile(rf"(?<![\w-]){re.escape(label)}(?![\w-])"), href, f"{repo} · {label}", desc, meta))
    for sid, pats, title, desc, url in EXTERNAL:
        alt = "|".join(re.escape(p) for p in sorted(pats, key=len, reverse=True))
        rx = re.compile(rf"(?<![\w./-])(?:{alt})(?![\w-]|\.\w)")
        rules.append((sid, rx, url, title, desc, short(url)))
    return rules


def link_code(segment, page, done):
    """Lie les <code>chemin</code> et <code>dépôt</code> du segment."""
    def repl(m):
        txt = html.unescape(m.group(1))
        if page in DOCS:
            repo, docs = DOCS[page]
            for path, desc in docs:
                if txt == path and f"doc-{path}" not in done:
                    done.add(f"doc-{path}")
                    href = blob(repo, path)
                    return anchor(f"doc-{path}", href, f"{repo} · {path}", desc, stamp(href, repo), m.group(0))
        if txt in REPOS and f"repo-{txt}" not in done:
            repo = REPOS[txt]
            done.add(f"repo-{txt}")
            href = pinned(repo)
            return anchor(f"repo-{repo}", href, f"gnu6dotlive/{repo}", REPO_DESC[repo], stamp(href, repo), m.group(0))
        return m.group(0)
    # jamais de lien dans un lien existant
    parts = re.split(r"(<a\b.*?</a>)", segment, flags=re.S)
    return "".join(p if p.startswith("<a") else re.sub(r"<code>([^<]+)</code>", repl, p) for p in parts)


def link_page(src: str, page: str) -> str:
    # retirer les liens posés par une passe précédente
    src = re.sub(r'<a class="src"[^>]*>(.*?)</a>', r"\1", src, flags=re.S)
    a, b = re.search(r"<main[^>]*>", src).start(), src.index("</main>")
    body = src[a:b]
    rules = build_rules(page)
    out, stack, done = [], [], set()
    for tok in re.split(r"(<[^>]+>)", body):
        if not tok:
            continue
        if tok.startswith("<"):
            m = re.match(r"<\s*(/)?\s*([a-zA-Z0-9]+)", tok)
            if m:
                closing, name = m.group(1), m.group(2).lower()
                if closing:
                    while stack:
                        top = stack.pop()
                        if top[0] == name:
                            break
                    if name == "section":
                        done = set()
                elif name not in VOID and not tok.endswith("/>"):
                    cls = set(re.findall(r'class="([^"]*)"', tok)[0].split()) if 'class="' in tok else set()
                    stack.append((name, cls))
            out.append(tok)
            continue
        if any(n in SKIP_TAGS for n, _ in stack):
            out.append(tok)
            continue
        # dans une étiquette (« Q-010 »), seuls les jalons se lient à leur reçu
        in_label = any(c & SKIP_CLASSES for _, c in stack)
        in_code = any(n == "code" for n, _ in stack)
        if in_code:
            out.append(tok)
            continue
        # une seule passe par motif : on remplace la première occurrence encore libre
        pieces = [tok]
        for sid, rx, href, title, desc, meta in rules:
            if sid in done or (in_label and not sid.startswith("ms-")):
                continue
            for i, piece in enumerate(pieces):
                if piece.startswith("<a "):
                    continue
                m = rx.search(piece)
                if m:
                    done.add(sid)
                    pieces[i:i + 1] = [piece[:m.start()], anchor(sid, href, title, desc, meta, m.group(0)), piece[m.end():]]
                    break
        out.append("".join(pieces))
    body = "".join(out)
    # les <code> : un second passage sur le texte reconstitué, section par section
    parts = re.split(r"(<section\b[^>]*>)", body)
    body = "".join(link_code(p, page, set()) if not p.startswith("<section") else p for p in parts)
    src = src[:a] + body + src[b:]
    # le pied de page cite les documents sources de la page
    f0 = src.find('<footer class="site-footer">')
    if f0 != -1:
        f1 = src.index("</footer>", f0)
        src = src[:f0] + link_code(src[f0:f1], page, set()) + src[f1:]
    return src


def ensure_script(src: str, prefix: str) -> str:
    tag = f'<script src="{prefix}assets/sources.js" defer></script>'
    if tag not in src:
        css = f'<link rel="stylesheet" href="{prefix}assets/style.css">'
        src = src.replace(css, css + "\n" + tag, 1)
    return src


def main():
    global LANG
    total = 0
    for page in PAGES:
        p = ROOT / page
        LANG = "en" if page.startswith("en/") else "fr"
        key = page.removeprefix("en/")
        key = {"glossary.html": "comprendre.html", "method.html": "methode.html",
               "verify.html": "verifier.html", "timeline.html": "chronologie.html"}.get(key, key)
        s = p.read_text(encoding="utf-8")
        s = ensure_script(link_page(s, key), "../" if LANG == "en" else "")
        p.write_text(s, encoding="utf-8")
        n = s.count('class="src"')
        total += n
        print(f"{page:16} {n:3} liens")
    print(f"total            {total:3}")


if __name__ == "__main__":
    main()
