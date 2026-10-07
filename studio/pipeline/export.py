"""S11 — Export site : écrit la fiche vidéo lue par le site (contenus/videos/<slug>.json, PRD §7)."""

import datetime as dt

import yaml

from noyau.erreurs import ErreurStudio
from noyau.medias import ecrire_json, lire_json
from noyau.projet import ProjetCharge
from noyau.timeline import Timeline


def lancer(p: ProjetCharge) -> None:
    if not p.props.exists():
        raise ErreurStudio(f"props.json absent : lancez d'abord `studio monter {p.slug}`.")
    cfg = p.config
    props = lire_json(p.props)
    existante = lire_json(p.fiche) if p.fiche.exists() else {}
    commentaire = yaml.safe_load(p.commentaire.read_text(encoding="utf-8")) if p.commentaire.exists() else {}

    # Transcription de la bande-son finale : voix off, plus la voix d'origine si elle est conservée.
    transcription = [
        {"debut": c["debut"], "fin": round(c["debut"] + c["duree"], 3), "texte": c["texte"]}
        for c in lire_json(p.placement_voix)
    ]
    if cfg.montage.volume_original > 0 and p.transcription.exists():
        timeline = Timeline([tuple(g) for g in lire_json(p.timeline)["gardes"]])
        for s in lire_json(p.transcription)["segments"]:
            debut, fin = timeline.vers_coupe(s["debut"]), timeline.vers_coupe(s["fin"])
            if debut is not None and fin is not None:
                transcription.append({"debut": round(debut, 3), "fin": round(fin, 3), "texte": s["texte"]})
    transcription.sort(key=lambda s: s["debut"])

    fiche = {
        "youtubeId": existante.get("youtubeId", ""),  # renseigné à la publication (M4)
        "titre": cfg.titre,
        "description": cfg.description,
        "date": (cfg.date or dt.date.today()).isoformat(),
        "duree": round(props["dureeTotale"]),
        "chapitres": [{"debut": c["debut"], "titre": c["titre"]} for c in (commentaire or {}).get("chapitres", [])],
        "transcription": transcription,
        "tags": cfg.tags,
        "article": cfg.article,
        "repo": cfg.repo,
    }
    ecrire_json(p.fiche, fiche)
    print(f"[export] fiche vidéo → {p.fiche}")
