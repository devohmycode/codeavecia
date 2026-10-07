# Tâches — CodeAvecIA

Plan d'implémentation de [PRD.md](PRD.md), découpé selon ses jalons (§11). Les identifiants entre crochets renvoient
aux exigences du PRD.

**Légende** : `[x]` fait · `[ ]` à faire · 👤 action à faire par le propriétaire du projet (achat, compte, réglage dans un
tableau de bord) · ❓ dépend d'une question ouverte du PRD (§13).

---

## M0 — Fondations

**Critère de fin** : `codeavecia.fr` affiche une page en HTTPS.

- [x] Créer le dépôt privé `devohmycode/codeavecia`
- [x] Rédiger le PRD (`docs/PRD.md`)
- [x] Initialiser le projet Astro dans `site/` : page d'accueil provisoire, page 404, gabarit de base
- [x] En-têtes de sécurité (CSP, HSTS…) et `noindex` des prévisualisations `*.pages.dev` dans `site/public/_headers`
- [x] `.gitignore` (secrets, `media/`), `.env.example`, `README.md`
- [x] Commande `npm run preview:cf` pour tester la CSP en local
- [ ] 👤 Acheter `codeavecia.fr` et `codeavecia.com` chez OVH
- [ ] 👤 Relier le dépôt à Cloudflare Pages (preset Astro, root `site`, build `npm run build`, sortie `dist`)
- [ ] 👤 Ajouter les deux domaines dans Cloudflare et pointer leurs serveurs DNS OVH vers Cloudflare
- [ ] 👤 Ajouter `codeavecia.fr` et `www.codeavecia.fr` en domaines personnalisés du projet Pages
- [ ] Rediriger `codeavecia.com` et `www.codeavecia.fr` vers `https://codeavecia.fr` (règle de redirection
      Cloudflare : le fichier `_redirects` de Pages ne gère pas les redirections entre domaines) [F4.6]
- [ ] Vérifier en ligne : HTTPS, en-têtes de sécurité, `noindex` sur `*.pages.dev`, page 404
- [ ] 👤 Activer Cloudflare Web Analytics sur le projet [§8 Vie privée]

## M1 — Publication

**Critère de fin** : un article HTML généré en local est en ligne par simple `git push`.

### Décisions préalables

- [ ] ❓ Trancher la licence des articles (§13, Q4) — affichée dans le pied de page
- [ ] ❓ Fixer une identité visuelle minimale : logo, couleurs, typographie (§13, Q2)

### Chargement des articles [F1.1 → F1.4]

- [ ] Créer la collection de contenu `articles` avec un *loader* Astro qui lit `src/content/articles/*.html`
- [ ] Extraire les métadonnées du `<head>` : `<title>`, `description`, `cai:date`, `cai:updated`, `cai:tags`,
      `cai:repo`, `cai:video`, `cai:draft` [F1.2, §7]
- [ ] Valider ces métadonnées par un schéma (champs obligatoires, format des dates) ; la construction échoue avec un
      message clair si un article est invalide
- [ ] Déduire l'adresse de l'article du nom du fichier (`mon-article.html` → `/articles/mon-article/`) [F4.5]
- [ ] Ne garder que le contenu de `<article>` (à défaut `<main>`) [F1.3]
- [ ] Nettoyer ce contenu : supprimer `<style>`, `<script>`, `<link>`, attributs `style` et gestionnaires `on*` ;
      liste blanche des éléments et attributs autorisés, extensible aux composants de M2 et M4 [F1.3]
- [ ] Coloration syntaxique des `<pre><code class="language-…">` avec Shiki, thèmes clair et sombre [F1.7]

### Pages [F1.6, F5.4]

- [ ] Gabarit commun : en-tête avec navigation, pied de page (licence, mentions légales), lien d'évitement
- [ ] Gabarit d'article : titre, dates, tags, contenu, lien vers le dépôt associé si `cai:repo`
- [ ] Page d'article `/articles/<slug>/`
- [ ] Archives `/articles/` (tous les articles, du plus récent au plus ancien)
- [ ] Pages de tag `/tags/<tag>/` et index des tags
- [ ] Accueil : derniers articles à la place de la page provisoire
- [ ] Flux RSS `/rss.xml`
- [ ] Pages « À propos » et « Mentions légales »

### Référencement [F4.1 → F4.6]

- [ ] Composant SEO : `<title>`, description, URL canonique sur chaque page [F4.1]
- [ ] Open Graph et Twitter Cards [F4.2]
- [ ] Image de partage générée à la construction pour chaque article (titre + identité visuelle) [F4.2]
- [ ] JSON-LD `Article` sur les articles et `BreadcrumbList` sur toutes les pages internes [F4.3]
- [ ] `sitemap.xml` généré, référencé dans `robots.txt` [F4.4]
- [ ] Fichier `site/public/_redirects` pour les articles renommés [F4.6]

### Présentation et accessibilité [F5.1 → F5.3]

- [ ] Vérifier le rendu mobile de toutes les pages [F5.1]
- [ ] Thème clair et sombre sur toutes les pages, coloration du code comprise [F5.2]
- [ ] Contrôle d'accessibilité WCAG 2.2 AA : contrastes, ordre de focus, titres, textes alternatifs [F5.3]

### Outillage auteur [F1.10]

- [ ] `docs/PROMPT-ARTICLE.md` : gabarit de prompt qui impose à l'IA le format HTML du §7 [F1.10]
- [ ] Un article d'exemple complet, conforme au format, dans `docs/`

### Validation du jalon

- [ ] Publier un premier vrai article généré en local ; mesurer le délai entre `git push` et la mise en ligne
      (objectif < 5 min) [O1]
- [ ] Lighthouse mobile sur l'accueil et sur un article : SEO = 100, performance ≥ 95 [O3, §8]

## M2 — GitHub

**Critère de fin** : un article affiche un fichier, un README et un Gist, indexables.

### Accès à l'API GitHub [F2.6, F2.7]

- [ ] 👤 Créer un token GitHub à granularité fine, en lecture seule sur les dépôts publics [§8 Sécurité]
- [ ] 👤 Déclarer `GITHUB_TOKEN` dans les variables d'environnement Cloudflare Pages (production et prévisualisation)
- [ ] Module `site/src/lib/github.ts` : client de l'API REST, authentifié par `GITHUB_TOKEN`
- [ ] Cache des réponses entre deux constructions, avec requêtes conditionnelles (`ETag`) [§8 Construction]
- [ ] Refuser tout dépôt privé, sauf ceux d'une liste blanche explicite (vide par défaut) [F2.7]
- [ ] Message d'erreur clair à la construction si un dépôt, un fichier ou un Gist est introuvable

### Composants [F2.1 → F2.3, F2.5, F2.8]

- [ ] `GithubRepo` : carte du dépôt (nom, description, langage, étoiles, licence, dernière mise à jour, lien) [F2.1]
- [ ] `GithubFile` : fichier d'un dépôt par chemin et branche ou commit, avec sélection de lignes, coloré par
      Shiki [F2.2]
- [ ] `GithubReadme` : README rendu en HTML, nettoyé comme un article [F2.3]
- [ ] `Gist` : un fichier ou tous les fichiers d'un Gist, colorés par Shiki [F2.5]
- [ ] Mention de la source et de la licence sous chaque extrait de code tiers [F2.8]
- [ ] JSON-LD `SoftwareSourceCode` sur les pages qui affichent du code [F4.3]

### Intégration dans les articles

- [ ] Remplacer, à la construction, les éléments `<github-repo>`, `<github-file>`, `<github-readme>` et `<gist>`
      des articles par le rendu des composants
- [ ] Ajouter ces éléments à la liste blanche du nettoyage [F1.3]
- [ ] Documenter leur syntaxe dans `docs/PROMPT-ARTICLE.md`

### Projets [F2.10]

- [ ] Liste des dépôts mis en avant (fichier de configuration)
- [ ] Page `/projets/` [F2.10]
- [ ] Page `/projets/<repo>/` : carte et README [F4.5]

### Validation du jalon

- [ ] Article de démonstration avec un fichier, un README et un Gist ; vérifier que le code est présent dans le
      HTML servi [O2]
- [ ] Durée de construction < 3 min [§8 Construction]

## M3 — Atelier vidéo, version minimale

**Critère de fin** : une capture de 1 min devient une vidéo commentée et sous-titrée.

### Fondations de l'atelier

- [ ] ❓ Déterminer comment piloter VoiceStudio : API locale, ligne de commande ou aucune (§13, Q1) — conditionne S5
- [ ] Structure `studio/` : `projets/`, `pipeline/`, `connecteurs/`, `montage/` [§10]
- [ ] Point d'entrée en ligne de commande : `studio <étape> <projet>` et `studio tout <projet>`
- [ ] Schéma de `projet.yaml` (sources, coupes, script, voix, plan de montage) avec validation
- [ ] Interface commune des connecteurs (entrées, sorties, coût estimé, disponibilité) [ST1]
- [ ] File d'attente GPU : une seule tâche GPU à la fois [ST2]
- [ ] Lecture des clés et adresses depuis `.env` [ST5] ; fichiers produits dans `media/<projet>/` [ST4]

### Étapes du pipeline

- [ ] **S1 Capture** : écran entier, fenêtre ou zone, avec le micro ; ffmpeg `ddagrab` + `h264_nvenc` ;
      enregistrement des positions du curseur (pour les zooms de S8)
- [ ] **S2 Transcription** : faster-whisper sur GPU, français, horodatage par mot ; export JSON, SRT et VTT
- [ ] **S3 Dérushage** : détection des silences et temps morts (audio + transcription) ; coupes proposées dans
      `projet.yaml`, à valider avant montage
- [ ] **S4 Commentaire** : connecteur LM Studio (API compatible OpenAI) ; voix off calée sur la timeline ;
      Claude en alternative
- [ ] **S5 Voix** : connecteur de voix locale (VoiceStudio, ou modèle de voix dans ComfyUI à défaut)
- [ ] **S8 Montage** : composition Remotion générée depuis `projet.yaml` — rushes coupés, voix off, sous-titres,
      zooms sur le curseur, musique
- [ ] **S9 Rendu** : 1080p 16:9 et format vertical 9:16 ; encodage NVENC
- [ ] **S11 Export site** : fiche `contenus/videos/<slug>.json` au format du §7 (`youtubeId` vide jusqu'à M4)

### Validation du jalon

- [ ] Projet de démonstration : capture de 1 min → vidéo commentée et sous-titrée, en 16:9 et 9:16
- [ ] Relancer le même projet produit la même vidéo (§6, reproductibilité)

## M4 — Vidéos sur le site

**Critère de fin** : une vidéo publiée sur YouTube a sa page sur le site, avec transcription.

### Publication YouTube [S10]

- [ ] ❓ Fixer le nom de la chaîne YouTube (§13, Q3)
- [ ] 👤 Créer le projet Google Cloud, activer l'API YouTube Data v3 et créer les identifiants OAuth
- [ ] Connecteur YouTube : envoi de la vidéo (titre, description, chapitres, sous-titres, miniature) [S10]
- [ ] Écrire l'identifiant YouTube obtenu dans la fiche vidéo

### Pages vidéo [F3.1 → F3.5]

- [ ] Collection de contenu `videos` lisant `contenus/videos/*.json`, avec schéma [F3.3]
- [ ] Lecteur YouTube en mode façade (`youtube-nocookie.com`), sans script tant qu'on ne clique pas [F3.2]
- [ ] Autoriser le lecteur dans la CSP de `_headers` (`frame-src https://www.youtube-nocookie.com`) et vérifier avec
      `npm run preview:cf`
- [ ] Page `/videos/<slug>/` : lecteur, description, chapitres, transcription complète [F3.1, F4.5]
- [ ] Page `/videos/` listant les vidéos [F3.5]
- [ ] Liens croisés article ↔ vidéo (`cai:video` et champ `article`) [F3.4]
- [ ] JSON-LD `VideoObject` [F4.3]

### Validation du jalon

- [ ] Publier la vidéo de démonstration de M3 sur YouTube et vérifier sa page sur le site

## M5 — Atelier enrichi

**Critère de fin** : une vidéo intègre des plans générés et une miniature Canva.

- [ ] Garde-fou des coûts : estimation, confirmation avant tout appel payant, journal des dépenses [ST3]
- [ ] 👤 Créer les comptes et clés API : ElevenLabs, Runway, Higgsfield, Canva ; les renseigner dans `.env`
- [ ] Connecteur ComfyUI : exécution de workflows par l'API locale, récupération des images et clips [S6]
- [ ] Connecteurs Runway et Higgsfield pour les plans vidéo trop lourds pour 8 Go de mémoire vidéo [S6]
- [ ] Connecteur ElevenLabs comme voix alternative [S5] ; clonage limité à la voix du propriétaire [ST6]
- [ ] Connecteur Canva : miniature et visuels à l'identité du site [S7]
- [ ] Gabarits Remotion : intro, outro, cartons [S7]
- [ ] Insertion des plans générés dans le plan de montage de `projet.yaml` [S6, S8]
- [ ] Validation : vidéo avec plans générés et miniature Canva

## M6 — Compléments

- [ ] Explorateur de dépôt : arborescence navigable et fichiers sur `/projets/<repo>/` [F2.4]
- [ ] Recherche interne avec Pagefind [F4.7]
- [ ] Bouton « copier » sur les blocs de code [F1.8]
- [ ] Temps de lecture et table des matières [F1.9]
- [ ] Script de validation d'un article : métadonnées, liens internes, images [F1.11]
- [ ] ❓ Services sur le VPS : statistiques Umami, commentaires (§13, Q6)

## Hors jalon — à planifier

- [ ] Brouillons visibles sur les prévisualisations de branche, absents de la production [F1.5]
- [ ] Reconstruction automatique quand un dépôt suivi change (webhook GitHub → déclencheur Cloudflare) [F2.9]
- [ ] ❓ Inscription à une newsletter (§13, Q5) [F4.8]
- [ ] Vérification automatique des pull requests : construction du site et validation des articles (GitHub Actions)
      [§8 Maintenabilité]
- [ ] Mises à jour des dépendances avec Dependabot [§8 Maintenabilité]
- [ ] Détection de secrets avant commit et dans la CI (gitleaks) [§8 Sécurité, §12]
- [ ] Mesure Lighthouse automatique à chaque déploiement [O3]
- [ ] ❓ Fixer le rythme de publication et la stratégie de monétisation (§13, Q7 et Q8)
