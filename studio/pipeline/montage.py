"""S8 — Montage : assemble les données de la vidéo (props.json) que la composition Remotion met en images.

Calcule les sous-titres, les zooms sur les clics, la trajectoire lissée du curseur (cadrage vertical)
et prépare le dossier public servi à Remotion.
"""

import os
import re
import shutil
from pathlib import Path

import yaml

from noyau.erreurs import ErreurStudio
from noyau.medias import dimensions, duree, ecrire_json, lire_json
from noyau.projet import ProjetCharge
from noyau.timeline import Timeline

LONGUEUR_SOUS_TITRE = 84  # caractères, soit deux lignes
REGROUPEMENT_CLICS = 2.5  # secondes : des clics plus proches forment un seul zoom
AVANT_ZOOM, APRES_ZOOM = 0.6, 2.0


def _decouper(texte: str) -> list[str]:
    """Découpe un texte en morceaux d'au plus LONGUEUR_SOUS_TITRE caractères, de préférence en fin de phrase."""
    morceaux, courant = [], ""
    for mot in texte.split():
        if courant and len(courant) + 1 + len(mot) > LONGUEUR_SOUS_TITRE:
            morceaux.append(courant)
            courant = mot
        else:
            courant = f"{courant} {mot}".strip()
            if re.search(r"[.!?…]$", mot) and len(courant) > LONGUEUR_SOUS_TITRE / 2:
                morceaux.append(courant)
                courant = ""
    if courant:
        morceaux.append(courant)
    return morceaux


def _sous_titres_commentaire(voix: list[dict]) -> list[dict]:
    resultat = []
    for clip in voix:
        morceaux = _decouper(clip["texte"])
        total = sum(len(m) for m in morceaux)
        t = clip["debut"]
        for m in morceaux:
            fin = t + clip["duree"] * len(m) / total
            resultat.append({"debut": round(t, 3), "fin": round(fin, 3), "texte": m})
            t = fin
    return resultat


def _sous_titres_transcription(p: ProjetCharge, timeline: Timeline) -> list[dict]:
    if not p.transcription.exists():
        return []
    resultat, courant = [], None
    for s in lire_json(p.transcription)["segments"]:
        for m in s["mots"]:
            debut, fin = timeline.vers_coupe(m["debut"]), timeline.vers_coupe(m["fin"])
            if debut is None or fin is None:
                continue
            if courant and (len(courant["texte"]) + len(m["mot"]) + 1 > LONGUEUR_SOUS_TITRE or debut - courant["fin"] > 0.8):
                resultat.append(courant)
                courant = None
            if courant:
                courant["texte"] += " " + m["mot"]
                courant["fin"] = round(fin, 3)
            else:
                courant = {"debut": round(debut, 3), "fin": round(fin, 3), "texte": m["mot"]}
    if courant:
        resultat.append(courant)
    return resultat


def _zooms(capture: dict, timeline: Timeline, duree_video: float) -> list[dict]:
    largeur, hauteur = capture["region"][2], capture["region"][3]
    clics = [
        (tc, x / largeur, y / hauteur)
        for t, x, y in capture.get("clics", [])
        if 0 <= x < largeur and 0 <= y < hauteur and (tc := timeline.vers_coupe(t)) is not None
    ]
    groupes: list[list[tuple[float, float, float]]] = []
    for clic in sorted(clics):
        if groupes and clic[0] - groupes[-1][-1][0] <= REGROUPEMENT_CLICS:
            groupes[-1].append(clic)
        else:
            groupes.append([clic])
    zooms = []
    for g in groupes:
        debut, fin = max(0.0, g[0][0] - AVANT_ZOOM), min(duree_video, g[-1][0] + APRES_ZOOM)
        x, y = sum(c[1] for c in g) / len(g), sum(c[2] for c in g) / len(g)
        if zooms and debut < zooms[-1]["fin"]:  # deux zooms qui se touchent n'en font qu'un
            zooms[-1]["fin"] = round(fin, 3)
        else:
            zooms.append({"debut": round(debut, 3), "fin": round(fin, 3), "x": round(x, 3), "y": round(y, 3)})
    return zooms


def _curseur_x(capture: dict, timeline: Timeline, fps: int, duree_video: float) -> list[float]:
    """Position horizontale (0–1) du curseur pour chaque image de la vidéo dérushée, lissée sur ~1,5 s."""
    echantillons = capture.get("curseur", [])
    largeur = capture["region"][2]
    nb_images = max(1, int(duree_video * fps))
    if not echantillons:
        return [0.5] * nb_images
    brut, j = [], 0
    for i in range(nb_images):
        t = timeline.vers_source(i / fps)
        while j + 1 < len(echantillons) and echantillons[j + 1][0] <= t:
            j += 1
        brut.append(min(1.0, max(0.0, echantillons[j][1] / largeur)))
    fenetre = int(fps * 1.5)
    for _ in range(2):  # deux moyennes glissantes : mouvement doux, sans à-coups
        cumul = [0.0]
        for v in brut:
            cumul.append(cumul[-1] + v)
        brut = [
            (cumul[min(len(brut), i + fenetre // 2 + 1)] - cumul[max(0, i - fenetre // 2)])
            / (min(len(brut), i + fenetre // 2 + 1) - max(0, i - fenetre // 2))
            for i in range(len(brut))
        ]
    return [round(v, 3) for v in brut]


def _lier(source: Path, cible: Path) -> None:
    """Lien physique (instantané, sans copie) vers `source` ; copie si le lien est impossible."""
    cible.parent.mkdir(parents=True, exist_ok=True)
    if cible.exists():
        cible.unlink()
    try:
        os.link(source, cible)
    except OSError:
        shutil.copyfile(source, cible)


def lancer(p: ProjetCharge) -> None:
    for fichier, etape in ((p.rush_coupe, "derusher"), (p.timeline, "derusher"), (p.placement_voix, "voix")):
        if not fichier.exists():
            raise ErreurStudio(f"{fichier.name} absent : lancez d'abord `studio {etape} {p.slug}`.")
    cfg = p.config.montage
    timeline = Timeline([tuple(g) for g in lire_json(p.timeline)["gardes"]])
    capture = lire_json(p.journal_capture) if p.journal_capture.exists() else {"region": [0, 0, 1, 1]}
    voix = lire_json(p.placement_voix)
    fps = int(capture.get("fps", 30))
    duree_video = duree(p.rush_coupe)
    largeur, hauteur = dimensions(p.rush_coupe)
    fin_voix = max((c["debut"] + c["duree"] for c in voix), default=0.0)

    if p.public.exists():
        shutil.rmtree(p.public)
    _lier(p.rush_coupe, p.public / "video.mp4")
    for clip in voix:
        _lier(p.media / clip["fichier"], p.public / clip["fichier"])
    musique = None
    if cfg.musique:
        source = (p.dossier / cfg.musique).resolve()
        if not source.exists():
            raise ErreurStudio(f"Musique introuvable : {source}")
        musique = f"musique{source.suffix}"
        _lier(source, p.public / musique)

    if cfg.sous_titres == "commentaire":
        sous_titres = _sous_titres_commentaire(voix)
    elif cfg.sous_titres == "transcription":
        sous_titres = _sous_titres_transcription(p, timeline)
    else:
        sous_titres = []

    props = {
        "fps": fps,
        "video": "video.mp4",
        "dureeVideo": round(duree_video, 3),
        "dureeTotale": round(max(duree_video, fin_voix + 1.0), 3),
        "largeurSource": largeur,
        "hauteurSource": hauteur,
        "volumeOriginal": cfg.volume_original,
        "voix": [{"fichier": c["fichier"], "debut": c["debut"], "duree": c["duree"]} for c in voix],
        "sousTitres": sous_titres,
        "zooms": _zooms(capture, timeline, duree_video) if cfg.zooms and "clics" in capture else [],
        "facteurZoom": cfg.facteur_zoom,
        "curseurX": _curseur_x(capture, timeline, fps, duree_video),
        "musique": musique,
        "volumeMusique": cfg.volume_musique,
    }
    ecrire_json(p.props, props)
    chapitres = (yaml.safe_load(p.commentaire.read_text(encoding="utf-8")) or {}).get("chapitres", []) if p.commentaire.exists() else []
    print(
        f"[montage] {props['dureeTotale']:.1f} s, {len(voix)} voix, {len(sous_titres)} sous-titres, "
        f"{len(props['zooms'])} zooms, {len(chapitres)} chapitres → {p.props}"
    )
