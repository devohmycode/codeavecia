# Atelier vidéo CodeAvecIA

Outil local, jamais déployé : transforme une capture d'écran du poste en vidéo montée, commentée et
sous-titrée, en 16:9 et en 9:16, puis écrit la fiche vidéo lue par le site. Spécifications : PRD §6.

## Installation

Prérequis : Windows, GPU NVIDIA, [uv](https://docs.astral.sh/uv/), ffmpeg 7 ou plus récent (avec `ddagrab` et
`h264_nvenc`), Node.js 22, LM Studio (commentaire local) et VoiceStudio (voix locale).

```sh
cd studio
uv sync                      # environnement Python (.venv)
cd montage && npm install    # Remotion ; fait automatiquement au premier rendu sinon
```

Ensuite, toutes les commandes se lancent depuis `studio/` avec `uv run studio …`.

## Utilisation

```sh
uv run studio connecteurs                 # état de LM Studio, Claude, VoiceStudio, voix Windows
uv run studio nouveau ma-video --titre "Mon titre"
# compléter studio/projets/ma-video/projet.yaml, surtout `contexte`
uv run studio capture ma-video            # Ctrl+C pour arrêter (ou capture.duree)
uv run studio tout ma-video               # toutes les étapes suivantes
```

`tout` s'arrête après le dérushage tant que les coupes ne sont pas validées : relire
`projets/ma-video/coupes.yaml`, passer `valide: true`, puis relancer `tout`. L'option `--auto` (ou
`derushage.validation: auto`) valide les coupes proposées sans relecture.

| Commande | Étape | Produit |
|---|---|---|
| `capture` | S1 | `media/<projet>/rush.mp4` et `capture.json` (curseur, clics, fenêtres actives) |
| `transcrire` | S2 | `media/<projet>/transcription.json`, `.srt`, `.vtt` |
| `derusher` | S3 | `projets/<projet>/coupes.yaml` (à valider), puis `rush-coupe.mp4` et `timeline.json` |
| `commenter` | S4 | `projets/<projet>/commentaire.yaml` : chapitres et répliques, éditables |
| `voix` | S5 | `media/<projet>/voix/*.wav` et `voix.json` (placement sans chevauchement) |
| `monter` | S8 | `media/<projet>/props.json` : sous-titres, zooms, cadrage vertical |
| `rendre` | S9 | `media/<projet>/rendus/<projet>-16x9.mp4` et `-9x16.mp4` |
| `exporter` | S11 | `contenus/videos/<projet>.json`, la fiche lue par le site |

Chaque étape ne refait que ce qui a changé. Les fichiers de `projets/<projet>/` sont des décisions éditables et
versionnées ; tout le reste vit dans `media/`, exclu de git. Pour refaire une étape malgré tout : `--force`.

## Réglages de `projet.yaml`

| Section | Réglage | Rôle |
|---|---|---|
| `capture` | `source` : `ecran`, `zone` (`zone: [x, y, l, h]`) ou `fenetre` (`fenetre: "titre partiel"`) | Ce qui est filmé (écran principal uniquement) |
| | `micro` : `aucun`, `auto` ou nom exact | Voix enregistrée pendant la capture |
| `derushage` | `seuil`, `marge`, `silence_db` | Un temps mort = silence **et** image figée pendant au moins `seuil` secondes |
| `commentaire` | `connecteur` : `lmstudio` ou `claude` | Qui écrit la voix off (Claude est payant : confirmation demandée, ou `--oui`) |
| | `images` | Nombre d'images de la vidéo montrées au modèle (0 pour aucune) |
| | `mots_par_seconde` | Débit de lecture visé |
| `voix` | `connecteur` : `voicestudio` ou `windows` ; `voix` ; `vitesse` | Synthèse de la voix off |
| `montage` | `volume_original`, `sous_titres`, `zooms`, `facteur_zoom`, `musique` | Mixage et habillage |
| `rendu` | `formats` : `paysage`, `vertical` | Formats produits |

## Ce que le modèle sait de la vidéo

Pour écrire le commentaire, le modèle reçoit : le `contexte` du projet, le journal des fenêtres actives et des
clics, la transcription de la voix enregistrée et, s'il sait lire les images, quelques images de la vidéo.
Il ne voit pas la vidéo en continu : plus le `contexte` est précis, meilleur est le commentaire. Le résultat est
un brouillon à relire dans `commentaire.yaml`.

Les titres de fenêtres peuvent contenir des informations personnelles : ils restent dans `media/`, mais sont
envoyés au modèle choisi (local avec LM Studio, à Anthropic avec Claude).

## Services

| Service | Adresse par défaut | Variable `.env` |
|---|---|---|
| LM Studio | `http://127.0.0.1:1234/v1` (serveur lancé automatiquement) | `LMSTUDIO_URL`, `LMSTUDIO_MODELE`, `LMSTUDIO_CONTEXTE` |
| VoiceStudio | `http://127.0.0.1:3900` (application ouverte) | `VOICESTUDIO_URL`, `VOICESTUDIO_CLE` |
| Claude | API Anthropic, modèle `claude-opus-5-5` | `ANTHROPIC_API_KEY` (ou `ant auth login`) |

Les tâches GPU (transcription, voix, rendu) passent une par une par un verrou commun (`media/.gpu.lock`) ;
LM Studio décharge son modèle après le commentaire pour rendre la mémoire vidéo.

## Limites connues

- Capture de l'écran principal uniquement.
- Remotion encode le rendu final avec le processeur (H.264) : NVENC sert à la capture et au découpage.
- Remotion est gratuit pour un particulier ou une entreprise de 3 personnes au plus ; au-delà, une licence est
  nécessaire.
