# CodeAvecIA

Site francophone sur le développement assisté par IA — articles, code et vidéos — et son atelier vidéo local.

Spécifications : [docs/PRD.md](docs/PRD.md).

| Dossier | Rôle |
|---|---|
| `docs/` | PRD et documentation du projet |
| `site/` | Site Astro, déployé sur Cloudflare Pages (`codeavecia.fr`) |
| `studio/` | Atelier vidéo local, jamais déployé (à venir, jalon M3) |
| `media/` | Rushes et rendus vidéo, exclus de git |
| `pages/` | Pages HTML autonomes, publiées telles quelles sur GitHub Pages |

## Site

```sh
cd site
npm install
npm run dev      # http://localhost:4321
npm run build    # génère site/dist/
npm run preview:cf   # sert site/dist/ avec les en-têtes Cloudflare (CSP) : http://localhost:8788
```

`npm run dev` n'applique pas la politique de sécurité de `site/public/_headers` : avant de publier une page qui
charge un service externe (YouTube, script, police…), la vérifier avec `npm run preview:cf`.

Node.js 22.12 ou plus récent.

## Déploiement

Cloudflare Pages, relié à ce dépôt : chaque `git push` sur `main` met le site en production,
chaque autre branche obtient une URL de prévisualisation.

| Réglage Cloudflare Pages | Valeur |
|---|---|
| Framework preset | Astro |
| Root directory | `site` |
| Build command | `npm run build` |
| Build output directory | `dist` |

## Pages HTML (GitHub Pages)

Pour mettre une page `.html` autonome en ligne sans passer par le site : la déposer dans `pages/`
et pousser sur `main`. Le workflow `.github/workflows/pages.yml` publie le dossier tel quel et génère
un `index.html` qui liste les pages (titre et langue lus dans chaque fichier), sauf si `pages/index.html` existe déjà.

URL : `https://devohmycode.github.io/codeavecia/<fichier>.html`.

Réglage unique : *Settings → Pages → Source : GitHub Actions*.

## Secrets

Copier `.env.example` en `.env` et renseigner les clés. `.env` n'est jamais versionné.
