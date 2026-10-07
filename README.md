# CodeAvecIA

Site francophone sur le développement assisté par IA — articles, code et vidéos — et son atelier vidéo local.

Spécifications : [docs/PRD.md](docs/PRD.md).

| Dossier | Rôle |
|---|---|
| `docs/` | PRD et documentation du projet |
| `site/` | Site Astro, déployé sur Cloudflare Pages (`codeavecia.fr`) |
| `studio/` | Atelier vidéo local, jamais déployé (à venir, jalon M3) |
| `media/` | Rushes et rendus vidéo, exclus de git |

## Site

```sh
cd site
npm install
npm run dev      # http://localhost:4321
npm run build    # génère site/dist/
```

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

## Secrets

Copier `.env.example` en `.env` et renseigner les clés. `.env` n'est jamais versionné.
