// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
	// Domaine de production : sert aux URL canoniques, au sitemap et aux images de partage.
	site: 'https://codeavecia.fr',
	// Les URL publiques se terminent par « / » (PRD F4.5 : /articles/<slug>/).
	trailingSlash: 'always',
});
