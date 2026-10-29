# prologue

**Quatre dépôts, expliqués sans jargon.** Le point de départ pour qui découvre ce GitHub :
ce que font les projets de `gnu6dotlive`, ce qu'ils prouvent, et ce qu'ils ne promettent pas.

**Lire en ligne : https://gnu6dotlive.github.io/prologue/** — ou les PDF de [`exports/`](exports/).

- **[gnosix](https://github.com/gnu6dotlive/gnosix)** — environnement de bureau Linux, Rust + Wayland/GPUI, préversion `v26.11-rc1 « Ardoise »`, MIT.
- **[gnostral.rs](https://github.com/gnu6dotlive/gnostral.rs)** — laboratoire d'inférence locale en Rust sur GPU contraint, `v0.8.0`, MIT.
- **[Calix](https://github.com/gnu6dotlive/calix)** — interface native de gestion de paquets pour Arch Linux, Rust + GPUI / Zig, `v0.3.1`, GPL-3.0.
- **[in.gnu6](https://github.com/gnu6dotlive/in.gnu6)** — moteur de scènes et de topologies, `2026.10.0-research`, public sans licence décidée.

Public visé : lecteurs non techniciens (curieux, recruteurs, décideurs, financeurs) qui veulent
comprendre ces projets sans lire le code.

## Un instantané daté : 29 octobre 2026

Ce dossier ne suit pas les projets en continu. Il a été construit et vérifié contre l'état
public des quatre dépôts **le 29 octobre 2026**, puis figé (tag `2026-10-29`). Les projets ont
continué d'avancer depuis : en cas de divergence, les dépôts font foi.

Chaque source citée dans les pages est un lien souligné ; au survol, une fiche la présente.
Les liens vers les quatre dépôts pointent vers le commit public du jour, pas vers la branche
courante — ils montrent ce que la page décrit :

| Dépôt | Commit du 29 octobre 2026 | Version publiée |
| --- | --- | --- |
| gnosix | [`66d801b`](https://github.com/gnu6dotlive/gnosix/tree/66d801b0069808e6a18120ac41477a20466b4d66) | `v26.11-rc1` (préversion, 21 oct.) |
| gnostral.rs | [`38c4134`](https://github.com/gnu6dotlive/gnostral.rs/tree/38c4134a3a398b5b83d34326826362cf4dcc7336) | `v0.8.0` (7 oct.) |
| calix | [`aa42325`](https://github.com/gnu6dotlive/calix/tree/aa423254f89cd233f261fbf19f4705d1d9c94259) | `v0.3.1` (22 oct.) |
| in.gnu6 | [`fec80a7`](https://github.com/gnu6dotlive/in.gnu6/tree/fec80a7ae19de4b5838fe9f84dd271d6924fa753) | `2026.10.0-research` |

## Ouvrir le dossier localement

Aucune installation, aucun serveur :

```
xdg-open index.html
```

Le site est entièrement statique (HTML + CSS + SVG + une fonte embarquée, un petit script
pour les fiches de sources). Il fonctionne depuis le disque, hors ligne, et s'imprime en PDF
(`Ctrl+P` → « Enregistrer au format PDF ») : les animations y sont remplacées par une image fixe.

## Structure

```
.
├── index.html          accueil : les quatre projets, le fil rouge, comment lire
├── gnosix.html         dossier 1 : le bureau
├── gnostral.html       dossier 2 : le moteur
├── calix.html          dossier 3 : le compagnon
├── ingnu6.html         dossier 4 : la scène
├── comprendre.html     vocabulaire, open source, échelle de preuve, glossaire
├── assets/
│   ├── style.css       feuille de style commune (jetons gnosix_DS V3.4.1)
│   ├── sources.js      fiche de source au survol des liens soulignés
│   ├── fonts/          Space Grotesk (OFL-1.1), embarquée pour l'hors-ligne
│   ├── diagrams/
│   │   ├── ecosysteme.svg            les quatre dépôts et leurs liens
│   │   ├── topologie.svg             le fil rouge commun aux quatre projets
│   │   ├── echelle-preuve.svg        la traduction des vocabulaires de statut
│   │   ├── gnosix-surfaces.svg       anatomie d'un écran
│   │   ├── gnosix-wireframe.svg      croquis : cinq surfaces numérotées
│   │   ├── gnosix-plans.svg          les quatre plans d'architecture
│   │   ├── gnostral-probleme.svg     le problème de mémoire et l'astuce MoE
│   │   ├── gnostral-ab.svg           mesure A/B Q-010 : débit, premier mot, mémoire
│   │   ├── gnostral-placement.svg    placement des 48 couches sous pression (Q-011)
│   │   ├── gnostral-comparaisons.svg les trois références d'un même chiffre
│   │   ├── gnostral-boucle.svg       la boucle de preuve en six étapes
│   │   ├── calix-flux.svg            six sources, un seul inventaire
│   │   ├── calix-matrice.svg         six sources × quatre gestes
│   │   ├── calix-privilege.svg       la frontière de privilège (polkit / pkexec)
│   │   ├── gnu6-scene.svg            une scène, plusieurs projecteurs
│   │   └── gnu6-gates.svg            protocole CUDA-05F : 10/10 portes de labo, publication refusée
│   ├── gif/            animations (+ image de repos *-still.png pour l'impression)
│   │   ├── gnosix-appstack.gif       l'AppStack sort du deck, cherche, lance
│   │   ├── gnostral-course.gif       même réponse, deux vitesses, en temps réel
│   │   └── gnu6-scene-projection.gif la scène change, les projections suivent
│   └── shots/          captures réelles
│       ├── calix-browse.png          recherche « ripgrep » (29/10/2026, r5022)
│       ├── calix-installed.png       inventaire, 1 803 paquets (29/10/2026, r5022)
│       └── gnu6-pixi.png             qualification MQ-12, renderer PixiJS
├── tools/
│   ├── make_gifs.py    génère les animations (SVG image par image → rsvg-convert → ffmpeg)
│   └── link_sources.py registre des sources : pose les liens et leurs fiches
├── exports/            les mêmes pages en PDF
├── LICENSE             CC BY 4.0 (contenu) ; la fonte garde sa licence OFL-1.1
└── README.md
```

## Design system

Le site applique `gnosix_DS V3.4.1` tel qu'il est défini dans
`gnosix/docs/diagrams/` : une seule fonte (Space Grotesk), six neutres, trois signaux
(orange `#FF6A00` / `#C95400`, vert `#5F7F52` / `#455F3D`, bleu `#4169E1` / `#2446A8`)
et leurs teintes claires. Aucune teinte n'est inventée hors de ces jetons : quand une
quatrième couleur était nécessaire (le fil rouge), elle est rendue en anthracite, pas en
violet.

## Règle de rédaction

Chaque affirmation factuelle de ce dossier est adossée à un document du dépôt source :

| Sujet | Source |
| --- | --- |
| Périmètre et état de gnosix | `gnosix/docs/status/STATUS.md` |
| Architecture en quatre plans | `gnosix/ARCHITECTURE.md` |
| Licence, build, surfaces | `gnosix/README.md` |
| Résultats mesurés | `gnostral.rs/docs/CAPABILITY_MATRIX.md` |
| Méthode et huit états | `gnostral.rs/docs/ARCHITECTURE.md` |
| Chiffres et limites | `gnostral.rs/README.md` |
| État de Calix, composants, privilège | `calix/README.md` |
| Architecture Calix | `calix/docs/calix-architecture.md` |
| Marque et jetons Calix | `calix/docs/brand.md` |
| Mandat et jalons in.gnu6 | `in.gnu6/CONTRACT.md`, `in.gnu6/QUESTLOG.md` |
| Licence et publication in.gnu6 | `in.gnu6/docs/public/PUBLICATION-READINESS.md` |

Quatre principes ont guidé la rédaction :

1. **Ne pas promouvoir un état en un autre.** Un `QUALIFIED` n'est pas un `PROVEN`, un
   `BOUNDED PASS` n'est pas un produit. Les mots du dépôt sont conservés, puis traduits.
2. **Garder les limites visibles.** Chaque dossier a un encadré « les limites, sans détour ».
3. **Signaler les lectures d'auteur.** La parenté « topologie » entre les quatre dépôts est
   une interprétation, explicitement présentée comme telle dans les légendes.
4. **Ne pas prêter une licence qui n'existe pas.** in.gnu6 est public sans licence OSS
   décidée : le dossier le dit, et ne le présente pas comme réutilisable.

## Relier les sources

```
python3 tools/link_sources.py
```

Le registre du script est la seule liste des sources : projets externes (mistral.rs,
llama.cpp, PixiJS, Hyprland, polkit…), documents des quatre dépôts et reçus de mesure
(Q-010, CUDA-05F…). Le script lie la première mention de chaque source dans chaque section ;
il peut être relancé sans doubler les liens.

## Régénérer les animations

```
python3 tools/make_gifs.py
```

Chaque image est un SVG écrit par le script, avec les mêmes jetons et la même fonte que les
schémas ; `rsvg-convert` la rastérise, `ffmpeg` assemble le GIF. Les chiffres de
`gnostral-course.gif` sont ceux du reçu Q-010 (médianes, réponse de 512 jetons). Les deux
autres animations sont des animations de principe, signalées comme telles.

## Régénérer les captures Calix

Calix se pilote en ligne de commande (`calix-gpui open`, `navigate installed`,
`search ripgrep`, `view table`, `logs hide`) ; la fenêtre est mise en flottant, et `grim` capture
son seul rectangle, pointeur hors de la fenêtre.

## Régénérer les schémas

Les SVG sont écrits à la main, sans dépendance. Pour en vérifier le rendu :

```
rsvg-convert -w 1200 assets/diagrams/ecosysteme.svg -o /tmp/ecosysteme.png
```

Les couleurs suivent `gnosix_DS V3.4.1` : `#F7F3ED` (fond), `#FFFFFF` (cartes),
`#111418` (encre), `#667085` (secondaire), `#A1A6AD` (atténué), `#D7DADF` (filet),
`#E6E8EB` (séparateur), `#FF6A00` / `#C95400` (orange), `#5F7F52` / `#455F3D` (vert),
`#4169E1` / `#2446A8` (bleu).

## Portée

Document de vulgarisation, instantané du 29 octobre 2026. Il ne remplace ni les README, ni les
documents de statut, ni les reçus de mesure des dépôts : il les rend lisibles. En cas de
divergence, les dépôts font foi.

## Licence

Textes, schémas, animations et captures : [CC BY 4.0](LICENSE) — réutilisation libre en
créditant « gnu6dotlive, prologue ». La fonte Space Grotesk est sous OFL-1.1
([`assets/fonts/`](assets/fonts/)). Les projets décrits gardent leurs propres licences ;
in.gnu6 n'en a pas encore, et ce dossier ne lui en prête aucune.
