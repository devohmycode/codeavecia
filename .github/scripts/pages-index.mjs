// Génère <dossier>/index.html : la liste des pages .html du dossier, avec leur <title>.
// Usage : node .github/scripts/pages-index.mjs <dossier>
// Si le dossier contient déjà un index.html écrit à la main, il est conservé.
import { readdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const dir = process.argv[2] ?? "pages";
const out = join(dir, "index.html");
if (existsSync(out)) process.exit(0);

const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

const items = readdirSync(dir)
  .filter((f) => f.endsWith(".html"))
  .sort()
  .map((f) => {
    const html = readFileSync(join(dir, f), "utf8");
    const title = html.match(/<title>([^<]*)<\/title>/i)?.[1].trim() || f;
    const lang = html.match(/<html[^>]*\slang=["']?([a-z-]+)/i)?.[1] ?? "";
    return `<li><a href="${encodeURI(f)}">${esc(title)}</a>${lang ? ` <span>${esc(lang)}</span>` : ""}</li>`;
  });

writeFileSync(
  out,
  `<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>Pages CodeAvecIA</title>
<style>
:root{color-scheme:light dark;--fg:#1a1a1a;--muted:#6b6b6b;--bg:#fafaf9;--link:#0b57d0}
@media (prefers-color-scheme:dark){:root{--fg:#ececec;--muted:#9a9a9a;--bg:#161616;--link:#8ab4f8}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,sans-serif}
main{max-width:40rem;margin:0 auto;padding:3rem 1rem}
h1{font-size:1.4rem;margin:0 0 1.5rem}
ul{list-style:none;padding:0;margin:0}
li{padding:.5rem 0;border-bottom:1px solid color-mix(in srgb,var(--fg) 12%,transparent)}
a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
span{color:var(--muted);font-size:.8rem;text-transform:uppercase;margin-left:.4rem}
</style>
</head>
<body><main>
<h1>Pages</h1>
<ul>
${items.join("\n")}
</ul>
</main></body>
</html>
`,
);
console.log(`${out} : ${items.length} page(s)`);
