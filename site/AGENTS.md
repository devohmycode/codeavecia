## Development

When starting the dev server, use background mode:

```
astro dev --background
```

Manage the background server with `astro dev stop`, `astro dev status`, and `astro dev logs`.

## Politique de sécurité (CSP) — `public/_headers`

En ligne, le navigateur ne charge que les ressources autorisées par la CSP de `public/_headers`. Ce fichier n'est
appliqué que par Cloudflare : `npm run dev` et `npm run preview` l'ignorent, donc un contenu bloqué en production
s'affiche normalement en local.

- Tout service externe ajouté (lecteur YouTube, script, police, iframe, appel `fetch` depuis le navigateur) doit être
  déclaré dans la directive correspondante (`frame-src`, `script-src`, `font-src`, `connect-src`…), dans la même
  modification.
- Vérifier avec `npm run preview:cf`, qui sert `dist/` avec les en-têtes de Cloudflare sur http://localhost:8788,
  puis contrôler la console du navigateur (erreurs « Content Security Policy »).

## Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Using React, Vue, Svelte, or other framework components](https://docs.astro.build/en/guides/framework-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles or using Tailwind](https://docs.astro.build/en/guides/styling/)
- [Supporting multiple languages](https://docs.astro.build/en/guides/internationalization/)
