"""S4 — Commentaire : un LLM écrit la voix off, calée sur la timeline de la capture dérushée.

Le résultat (commentaire.yaml) est versionné et éditable : il n'est régénéré qu'avec --force.
"""

import datetime as dt
import subprocess

import yaml

import connecteurs
from noyau.erreurs import ErreurStudio
from noyau.medias import lire_json
from noyau.projet import ProjetCharge
from noyau.timeline import Timeline

SCHEMA = {
    "type": "object",
    "properties": {
        "chapitres": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"debut": {"type": "number"}, "titre": {"type": "string"}},
                "required": ["debut", "titre"],
                "additionalProperties": False,
            },
        },
        "repliques": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"debut": {"type": "number"}, "texte": {"type": "string"}},
                "required": ["debut", "texte"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["chapitres", "repliques"],
    "additionalProperties": False,
}

SYSTEME = """\
Tu écris la voix off de vidéos de démonstration pour CodeAvecIA, un site francophone sur le développement \
assisté par IA. Public : développeurs et créateurs francophones. Ton : clair, concret, chaleureux, sans \
superlatifs marketing. Tu vouvoies le spectateur.

Règles :
- Le commentaire accompagne ce qui se passe à l'écran, au bon moment. N'invente pas de détails : appuie-toi \
uniquement sur le contexte, le journal des fenêtres, la transcription et, s'il y en a, les images horodatées \
extraites de la vidéo.
- Chaque réplique fait 1 à 3 phrases de texte brut, à lire à voix haute : pas de markdown, d'emoji, de liste \
ni d'URL.
- Débit : au plus {mps} mots par seconde. Une réplique de N mots dure N/{mps} secondes ; elle doit se terminer \
au moins 0,5 seconde avant le `debut` de la réplique suivante, et avant la fin de la vidéo.
- Laisse respirer la vidéo : le commentaire ne la couvre pas en entier.
- `debut` est exprimé en secondes depuis le début de la vidéo, en ordre croissant.
- Chapitres : 1 à 6, le premier à 0, titres de moins de 50 caractères.
"""


def _contexte(p: ProjetCharge) -> str:
    timeline = Timeline([tuple(g) for g in lire_json(p.timeline)["gardes"]])
    capture = lire_json(p.journal_capture) if p.journal_capture.exists() else {}
    transcription = lire_json(p.transcription) if p.transcription.exists() else {"segments": []}

    fenetres = []
    for t, titre in capture.get("fenetres", []):
        tc = timeline.vers_coupe(max(0.0, t))
        if tc is not None and titre:
            fenetres.append(f"- {tc:.1f} s : {titre}")
    clics = [tc for t, *_ in capture.get("clics", []) if (tc := timeline.vers_coupe(t)) is not None]
    paroles = []
    for s in transcription["segments"]:
        debut, fin = timeline.vers_coupe(s["debut"]), timeline.vers_coupe(s["fin"])
        if debut is not None or fin is not None:
            paroles.append(f"- [{(debut if debut is not None else fin):.1f}–{(fin if fin is not None else debut):.1f} s] {s['texte']}")

    cfg = p.config
    return "\n".join(
        [
            f"Titre : {cfg.titre}",
            f"Durée de la vidéo : {timeline.duree:.1f} s",
            "",
            "Contexte fourni par l'auteur :",
            cfg.contexte.strip() or "(aucun)",
            "",
            "Journal des fenêtres actives (temps de la vidéo) :",
            *(fenetres or ["(non disponible)"]),
            "",
            f"Clics de souris : {len(clics)}" + (f" (à {', '.join(f'{c:.1f} s' for c in clics[:30])})" if clics else ""),
            "",
            "Transcription de la voix enregistrée pendant la capture :",
            *(paroles or ["(aucune)"]),
        ]
    ), timeline.duree


def _images(p: ProjetCharge, nombre: int, duree: float) -> list[tuple[str, bytes]]:
    """Images régulièrement espacées de la vidéo dérushée, en JPEG de 1280 px de large."""
    images = []
    for i in range(nombre):
        t = duree * (i + 0.5) / nombre
        jpeg = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(p.rush_coupe),
             "-frames:v", "1", "-vf", "scale=1280:-2", "-q:v", "4", "-f", "image2pipe", "-vcodec", "mjpeg", "-"],
            capture_output=True,
        ).stdout
        if jpeg:
            images.append((f"Image de la vidéo à {t:.1f} s :", jpeg))
    return images


def _nettoyer(reponse: dict, duree: float) -> dict:
    repliques = sorted(
        ({"debut": round(max(0.0, float(r["debut"])), 2), "texte": " ".join(r["texte"].split())} for r in reponse["repliques"]),
        key=lambda r: r["debut"],
    )
    repliques = [r for r in repliques if r["texte"] and r["debut"] < duree]
    chapitres = sorted(
        ({"debut": round(max(0.0, float(c["debut"])), 2), "titre": c["titre"].strip()} for c in reponse["chapitres"]),
        key=lambda c: c["debut"],
    )
    chapitres = [c for c in chapitres if c["titre"] and c["debut"] < duree]
    if not chapitres or chapitres[0]["debut"] > 0:
        chapitres.insert(0, {"debut": 0.0, "titre": "Introduction"})
    return {"chapitres": chapitres, "repliques": repliques}


def lancer(p: ProjetCharge, *, force: bool = False, oui: bool = False) -> None:
    cfg = p.config.commentaire
    if not cfg.actif:
        print("[commentaire] désactivé dans projet.yaml")
        return
    if p.commentaire.exists() and not force:
        if p.timeline.exists() and p.timeline.stat().st_mtime > p.commentaire.stat().st_mtime:
            print("[commentaire] attention : les coupes ont changé depuis l'écriture du commentaire ; --force pour le réécrire")
        else:
            print(f"[commentaire] déjà écrit : {p.commentaire} (modifiez-le, ou --force pour le régénérer)")
        return

    connecteur = connecteurs.texte(cfg.connecteur, cfg.modele)
    systeme = SYSTEME.format(mps=str(cfg.mots_par_seconde).replace(".", ","))
    utilisateur, duree = _contexte(p)
    images = []
    if cfg.images:
        if connecteur.voit_images():
            images = _images(p, cfg.images, duree)
        else:
            print(f"[commentaire] le modèle de {connecteur.nom} ne lit pas les images : commentaire écrit sans les voir")
    if not connecteur.local:
        cout = connecteur.cout_estime(systeme + utilisateur, len(images))
        if not oui and input(f"[commentaire] {connecteur.nom} est payant (≈ {cout:.3f} $). Continuer ? [o/N] ").strip().lower() not in ("o", "oui"):
            raise ErreurStudio("Génération du commentaire annulée.")

    try:
        reponse = _nettoyer(connecteur.generer_json(systeme, utilisateur, SCHEMA, images), duree)
    finally:
        connecteur.liberer()  # rend la mémoire vidéo avant la synthèse vocale
    entete = (
        f"# Commentaire écrit par {connecteur.nom} le {dt.date.today().isoformat()} pour une vidéo de {duree:.1f} s.\n"
        "# Modifiez librement les textes et les temps (secondes de la vidéo dérushée), puis relancez `studio voix`.\n"
    )
    p.commentaire.write_text(entete + yaml.safe_dump(reponse, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    print(f"[commentaire] {len(reponse['repliques'])} répliques, {len(reponse['chapitres'])} chapitres → {p.commentaire}")
