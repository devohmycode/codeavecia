# PRD — CodeAvecIA

| | |
|---|---|
| **Produit** | codeavecia — site éditorial sur le développement assisté par IA, et son atelier vidéo |
| **Domaines visés** | `codeavecia.fr` (principal), `codeavecia.com` (redirection) |
| **Version du document** | 0.1 — brouillon initial |
| **Date** | 7 octobre 2026 |
| **Statut** | À valider |

---

## 1. Contexte et vision

Le développement logiciel bascule vers le code assisté par IA : agents de code, serveurs MCP, génération de projets
entiers à partir de prompts. Le contenu francophone sérieux et pratique sur ce sujet reste rare et dispersé.

**Vision** : devenir une référence francophone sur le code assisté par IA, en montrant le travail réel —
articles, dépôts de code consultables et vidéos de sessions de développement — plutôt que des promesses.

Le projet repose sur deux briques dans un même dépôt :

1. **Le site** (`site/`) — public, statique, rapide, optimisé pour le référencement.
2. **L'atelier vidéo** (`studio/`) — outil local, jamais déployé, qui transforme des captures d'écran du poste
   de travail en vidéos montées et commentées, publiées sur YouTube et intégrées au site.

## 2. Objectifs

| # | Objectif | Mesure de réussite |
|---|---|---|
| O1 | Publier un article en déposant un fichier HTML généré en local, sans étape manuelle | Article en ligne en moins de 5 min après `git push` |
| O2 | Montrer le code réel des dépôts GitHub et des Gists dans les pages | Code visible dans le HTML servi, donc indexable |
| O3 | Bien se positionner sur les requêtes francophones « coder avec l'IA » | Score Lighthouse SEO = 100, performance ≥ 95 ; trafic organique mesurable dès M+3 |
| O4 | Produire une vidéo de démonstration à partir d'une capture d'écran avec peu de travail manuel | Capture de 10 min → vidéo montée, sous-titrée et commentée en moins d'une heure de travail |
| O5 | Faire fonctionner le site sans coût d'hébergement ni maintenance serveur | 0 € d'hébergement pour le site ; seules les API d'IA sont payantes, à l'usage |

## 3. Hors périmètre (version 1)

- Comptes utilisateurs, espace membre, contenu payant.
- Commentaires et forum (envisagés plus tard, hébergés sur le VPS).
- Interface d'administration web : la publication passe par git.
- Édition en ligne des articles.
- Version anglaise du site.
- Hébergement des fichiers vidéo sur le site : les vidéos vivent sur YouTube.
- Exécution de l'atelier vidéo sur un serveur : il a besoin du GPU local.

## 4. Public cible

| Persona | Besoin | Ce que le site lui apporte |
|---|---|---|
| **Développeur curieux** | Comprendre comment intégrer l'IA à son quotidien | Tutoriels pas à pas, code réel, vidéos de sessions |
| **Développeur confirmé** | Aller plus loin : agents, MCP, automatisation | Articles techniques, dépôts complets à explorer |
| **Créateur non développeur** | Construire des outils avec l'IA sans être expert | Démonstrations vidéo, exemples reproductibles |

Langue : français.

## 5. Exigences fonctionnelles — le site

### F1 — Publication d'articles HTML

| ID | Exigence | Priorité |
|---|---|---|
| F1.1 | Un article est un **fichier HTML autonome**, généré en local par l'IA et lisible tel quel dans un navigateur. | Must |
| F1.2 | Les métadonnées sont lues dans le `<head>` du fichier : `<title>`, `<meta name="description">`, date de publication, tags, dépôt GitHub associé, vidéo associée (format exact en §7). | Must |
| F1.3 | Seul le contenu de `<article>` (à défaut, `<main>`) est repris. Le site applique son propre gabarit et ignore les `<style>` et `<script>` de l'article, sauf composants autorisés (F2, F3). | Must |
| F1.4 | La publication se fait par dépôt du fichier dans `site/src/content/articles/` puis `git push`. | Must |
| F1.5 | Un article peut être marqué brouillon (`draft`) : il est alors visible sur l'URL de prévisualisation de sa branche, mais absent de la production. | Should |
| F1.6 | Pages générées automatiquement : accueil (derniers articles), page par tag, archives, flux RSS. | Must |
| F1.7 | Coloration syntaxique des blocs `<pre><code class="language-…">` au moment de la construction (Shiki). | Must |
| F1.8 | Bouton « copier » sur chaque bloc de code. | Should |
| F1.9 | Temps de lecture estimé et table des matières générée à partir des titres. | Could |
| F1.10 | Un **gabarit de prompt** fourni dans `docs/` indique à l'IA le format HTML attendu. | Must |
| F1.11 | Un script de validation vérifie un article avant publication : métadonnées obligatoires, liens internes, images. | Should |

### F2 — Visualisation de dépôts GitHub et de Gists

| ID | Exigence | Priorité |
|---|---|---|
| F2.1 | **Carte de dépôt** : nom, description, langage, étoiles, licence, date de dernière mise à jour, lien. | Must |
| F2.2 | **Affichage d'un fichier** d'un dépôt, avec coloration syntaxique, à partir d'un chemin et d'une branche (ou d'un commit). | Must |
| F2.3 | **Affichage du README** d'un dépôt, rendu en HTML. | Must |
| F2.4 | **Explorateur de dépôt** : arborescence navigable et affichage des fichiers, sur une page dédiée par dépôt. | Should |
| F2.5 | **Affichage d'un Gist** (un ou tous ses fichiers), avec coloration syntaxique. | Must |
| F2.6 | Les données GitHub sont récupérées **au moment de la construction du site**, avec un token stocké dans les variables d'environnement de Cloudflare, pour que le code soit présent dans le HTML. | Must |
| F2.7 | Les dépôts privés ne sont jamais exposés, sauf liste blanche explicite. | Must |
| F2.8 | La licence et la source du code tiers sont toujours affichées. | Must |
| F2.9 | Reconstruction automatique quand un dépôt suivi change (webhook GitHub → déclencheur de build Cloudflare). | Could |
| F2.10 | Page « Projets » listant les dépôts mis en avant. | Should |

Usage dans un article : un élément HTML dédié, par exemple
`<github-file repo="devohmycode/mcp-demo" path="src/server.ts" lines="10-42"></github-file>`,
remplacé par le rendu au moment de la construction.

### F3 — Vidéos

| ID | Exigence | Priorité |
|---|---|---|
| F3.1 | Une page par vidéo : lecteur YouTube intégré, description, chapitres, transcription complète. | Must |
| F3.2 | Lecteur intégré en mode « façade » : une simple image tant que l'utilisateur ne clique pas, pour préserver la performance. | Must |
| F3.3 | Les données (transcription, chapitres, sous-titres) sont produites par l'atelier vidéo et versionnées dans `contenus/videos/`. | Must |
| F3.4 | Un article peut être lié à une vidéo, et inversement. | Should |
| F3.5 | Page « Vidéos » listant les vidéos publiées. | Must |

### F4 — Référencement et partage

| ID | Exigence | Priorité |
|---|---|---|
| F4.1 | Balises `<title>`, meta description et URL canonique sur chaque page. | Must |
| F4.2 | Open Graph et Twitter Cards, avec image de partage générée automatiquement (titre + identité visuelle). | Must |
| F4.3 | Données structurées JSON-LD : `Article`, `VideoObject`, `SoftwareSourceCode`, `BreadcrumbList`. | Must |
| F4.4 | `sitemap.xml` et `robots.txt` générés. | Must |
| F4.5 | URL lisibles et stables : `/articles/<slug>/`, `/videos/<slug>/`, `/projets/<repo>/`. | Must |
| F4.6 | Redirections gérées par `_redirects` (renommage d'article, `codeavecia.com` → `codeavecia.fr`). | Must |
| F4.7 | Recherche interne sur le site, sans serveur (Pagefind). | Should |
| F4.8 | Inscription à une newsletter. | Could |

### F5 — Navigation et présentation

| ID | Exigence | Priorité |
|---|---|---|
| F5.1 | Mise en page adaptée au mobile. | Must |
| F5.2 | Thème clair et sombre, qui suit la préférence du système. | Must |
| F5.3 | Accessibilité conforme au niveau AA des WCAG 2.2. | Must |
| F5.4 | Pages : accueil, articles, tags, vidéos, projets, à propos, mentions légales. | Must |

## 6. Exigences fonctionnelles — l'atelier vidéo (`studio/`)

L'atelier tourne uniquement sur le poste local. Il est piloté en ligne de commande et par Claude Code (serveurs MCP).
Chaque vidéo est un **projet** décrit par un fichier `studio/projets/<slug>/projet.yaml` : sources, script,
voix, plan de montage. Relancer un projet avec le même fichier produit la même vidéo.

| ID | Étape | Exigence | Outils pressentis | Priorité |
|---|---|---|---|---|
| S1 | Capture | Enregistrer l'écran (écran entier, fenêtre ou zone) et le micro, avec encodage matériel. | ffmpeg `ddagrab` + `h264_nvenc` ; OBS en option | Must |
| S2 | Transcription | Transcrire l'audio avec horodatage par mot. | faster-whisper sur GPU | Must |
| S3 | Dérushage | Repérer et proposer la coupe des silences et des temps morts. | Analyse audio + transcription | Must |
| S4 | Commentaire | Rédiger une voix off calée sur la timeline, à partir de la transcription et du contexte du projet. | LM Studio (local) ou Claude | Must |
| S5 | Voix | Synthétiser la voix off. | VoiceStudio (local) ; ElevenLabs (API ou MCP) | Must |
| S6 | Plans générés | Générer des images et des plans courts d'illustration. | ComfyUI (local) ; Runway, Higgsfield (API) | Should |
| S7 | Habillage | Produire miniature, intro, outro et cartons à l'identité du site. | Canva (MCP ou API) ; gabarits Remotion | Should |
| S8 | Montage | Assembler rushes, voix, plans, sous-titres, zooms sur le curseur et musique ; synchroniser le tout. | Remotion | Must |
| S9 | Rendu | Exporter en 1080p (16:9) et en format court vertical (9:16). | Remotion + NVENC | Must |
| S10 | Publication | Envoyer sur YouTube (titre, description, chapitres, sous-titres, miniature). | API YouTube Data v3 | Should |
| S11 | Export site | Écrire la fiche vidéo (transcription, chapitres, identifiant YouTube) dans `contenus/videos/`. | Script du pipeline | Must |

Exigences transverses de l'atelier :

- **ST1** — Chaque connecteur (ComfyUI, VoiceStudio, ElevenLabs, Runway, Higgsfield, Canva, LM Studio) suit la
  même interface et peut être remplacé par un autre (par exemple une voix locale à la place d'ElevenLabs).
- **ST2** — Les tâches GPU s'exécutent **une à la fois** (file d'attente), car le GPU n'a que 8 Go de mémoire vidéo.
- **ST3** — Toute étape payante (Runway, Higgsfield, ElevenLabs) affiche une estimation du coût et demande
  confirmation avant de s'exécuter.
- **ST4** — Les fichiers lourds (rushes, rendus, fichiers intermédiaires) vont dans `media/`, exclu de git.
- **ST5** — Les clés d'API sont dans `.env`, exclu de git ; `.env.example` en liste les noms.
- **ST6** — Seule la voix du propriétaire du projet peut être clonée.

## 7. Modèle de contenu

### Article (métadonnées dans le `<head>`)

```html
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Créer son premier serveur MCP</title>
  <meta name="description" content="Un serveur MCP en 50 lignes, pas à pas.">
  <meta name="cai:date" content="2026-10-07">
  <meta name="cai:updated" content="2026-10-12">       <!-- optionnel -->
  <meta name="cai:tags" content="mcp, claude-code">
  <meta name="cai:repo" content="devohmycode/mcp-demo"> <!-- optionnel -->
  <meta name="cai:video" content="premier-serveur-mcp"> <!-- optionnel -->
  <meta name="cai:draft" content="false">               <!-- optionnel -->
</head>
<body>
  <article>
    …contenu repris par le site…
  </article>
</body>
</html>
```

Le nom du fichier donne l'adresse de l'article (`premier-serveur-mcp.html` → `/articles/premier-serveur-mcp/`).

### Vidéo (`contenus/videos/<slug>.json`)

`youtubeId`, `titre`, `description`, `date`, `duree`, `chapitres[]` (début, titre), `transcription` (segments
horodatés), `tags[]`, `article` (slug optionnel), `repo` (optionnel).

## 8. Exigences non fonctionnelles

| Domaine | Exigence |
|---|---|
| Performance | Lighthouse ≥ 95 sur mobile ; aucun JavaScript chargé par défaut sur une page d'article, hors composants interactifs. |
| Disponibilité | Celle du réseau Cloudflare ; le site ne dépend d'aucun serveur à maintenir. |
| Sécurité | Aucun secret dans le dépôt ; token GitHub en lecture seule et limité aux dépôts publics ; en-têtes de sécurité (CSP, HSTS) définis dans `_headers`. |
| Vie privée | Statistiques sans cookies (Cloudflare Web Analytics) ; pas de bandeau cookies nécessaire. |
| Construction | Durée de construction < 3 min ; mise en cache des réponses de l'API GitHub entre deux constructions. |
| Maintenabilité | Dépendances à jour (Renovate ou Dependabot) ; vérification automatique de chaque pull request (construction + validation des articles). |
| Coûts | Hébergement du site : 0 € ; domaines : environ 20 € par an ; API d'IA : à l'usage, avec confirmation avant dépense (ST3). |
| Juridique | Mentions légales ; licence des articles à définir (§13) ; respect des licences du code affiché. |

## 9. Architecture

```
            Poste local (RTX 4060)                                    Cloud
 ┌───────────────────────────────────────────┐
 │  IA locale / Claude Code                  │
 │    └─ article .html ─────────────┐        │
 │                                  ▼        │   git push   ┌──────────────────┐   build   ┌───────────────────┐
 │  studio/ (atelier vidéo)     dépôt git ───┼─────────────►│ GitHub (privé)   │──────────►│ Cloudflare Pages  │
 │    capture → transcription       ▲        │              └──────────────────┘           │  + Functions      │
 │    → voix → montage → rendu      │        │                                             │  codeavecia.fr    │
 │    └─ fiche vidéo ───────────────┘        │                       ▲ API (build)         └───────────────────┘
 │    └─ vidéo ──────────────────────────────┼──► YouTube            │
 │  ComfyUI · VoiceStudio · LM Studio        │                 GitHub API (dépôts, Gists)
 └───────────────────────────────────────────┘
        │ API / MCP : ElevenLabs, Runway, Higgsfield, Canva
                                                   VPS OVH (plus tard) : statistiques Umami, commentaires,
                                                   automatisations — services dynamiques hors du site statique
```

| Composant | Choix | Raison |
|---|---|---|
| Générateur de site | Astro | HTML statique, rapide, collections de contenu, composants React possibles |
| Hébergement | Cloudflare Pages | Gratuit, dépôt privé accepté, bande passante illimitée, Functions, DNS déjà chez Cloudflare |
| Code côté serveur | Cloudflare Pages Functions | Appels authentifiés à l'API GitHub, newsletter, formulaires |
| Dépôt | GitHub `devohmycode/codeavecia`, privé | Versionnement, intégration Cloudflare |
| Montage vidéo | Remotion | Timeline décrite en code, donc reproductible ; React partagé avec le site |
| Transcription | faster-whisper | Rapide sur GPU, horodatage par mot |
| Domaines | OVH (registrar), DNS Cloudflare | Même configuration que familledecker.fr |

## 10. Structure du dépôt

```
codeavecia/
├─ docs/                  PRD, gabarit de prompt pour les articles, décisions d'architecture
├─ site/                  projet Astro → Cloudflare Pages
│  ├─ src/content/articles/
│  ├─ src/components/     GithubRepo, GithubFile, Gist, YouTube…
│  └─ functions/          Cloudflare Pages Functions
├─ studio/                atelier vidéo local, jamais déployé
│  ├─ projets/<slug>/projet.yaml
│  ├─ pipeline/           une étape par script (S1 → S11)
│  ├─ connecteurs/        comfyui, voicestudio, lmstudio, elevenlabs, runway, higgsfield, canva, youtube
│  └─ montage/            compositions Remotion
├─ contenus/videos/       fiches vidéo produites par l'atelier, lues par le site
├─ media/                 rushes et rendus (exclu de git)
└─ .env.example
```

## 11. Jalons

| Jalon | Contenu | Critère de fin |
|---|---|---|
| **M0 — Fondations** | Dépôt, PRD, achat des domaines, projet Astro vide déployé sur Cloudflare Pages | `codeavecia.fr` affiche une page en HTTPS |
| **M1 — Publication** | F1 (Must), F4.1–F4.6, F5, gabarit de prompt | Un article HTML généré en local est en ligne par simple `git push` |
| **M2 — GitHub** | F2.1–F2.3, F2.5–F2.8, page Projets | Un article affiche un fichier, un README et un Gist, indexables |
| **M3 — Atelier, version minimale** | S1, S2, S3, S4, S5 (voix locale), S8, S9, S11 | Une capture de 1 min devient une vidéo commentée et sous-titrée |
| **M4 — Vidéos sur le site** | F3, S10 | Une vidéo publiée sur YouTube a sa page sur le site, avec transcription |
| **M5 — Atelier enrichi** | S6, S7, connecteurs payants, ST3 | Une vidéo intègre des plans générés et une miniature Canva |
| **M6 — Compléments** | F2.4 explorateur, F4.7 recherche, F1.8–F1.11, services sur le VPS | Selon les priorités du moment |

## 12. Risques

| Risque | Impact | Parade |
|---|---|---|
| HTML généré par l'IA incohérent d'un article à l'autre | Mise en forme cassée | Le site ne garde que `<article>` (F1.3) ; gabarit de prompt (F1.10) ; validation (F1.11) |
| Limite de l'API GitHub atteinte pendant la construction | Construction en échec | Token authentifié (5 000 requêtes/h) ; cache entre constructions |
| 8 Go de mémoire vidéo insuffisants pour certains modèles | Génération locale impossible | File GPU (ST2) ; petits modèles quantifiés ; repli sur Runway ou Higgsfield |
| Coûts des API d'IA qui dérivent | Budget dépassé | Estimation et confirmation avant chaque appel payant (ST3) ; journal des dépenses |
| VoiceStudio sans interface de pilotage | S5 non automatisable en local | Vérifier en M3 ; à défaut, ElevenLabs ou modèle de voix dans ComfyUI |
| Évolution des API tierces (Runway, Higgsfield, Canva) | Connecteur cassé | Interface de connecteur commune (ST1) ; connecteurs isolés et remplaçables |
| Fuite d'un secret dans git | Compromission des comptes | `.env` exclu ; détection de secrets en pré-commit et sur GitHub |

## 13. Questions ouvertes

1. **VoiceStudio** : quelle interface de pilotage (API locale, ligne de commande, aucune) ?
2. **Identité visuelle** : logo, couleurs, typographie — à créer ou déjà définies ?
3. **Chaîne YouTube** : nom de la chaîne (CodeAvecIA ?) et lien avec la chaîne CodeLabIA évoquée.
4. **Licence des articles** : tous droits réservés ou Creative Commons (CC BY 4.0) ?
5. **Newsletter** : souhaitée dès le départ ? Avec quel service ?
6. **Commentaires** : utiles en version 1, ou plus tard sur le VPS ?
7. **Rythme de publication** visé (articles et vidéos par mois) ?
8. **Monétisation** : publicité, affiliation, aucune ?
