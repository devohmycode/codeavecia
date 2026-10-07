"""S5 — Voix : synthétise chaque réplique du commentaire et place les clips sur la timeline sans chevauchement.

Les clips sont mis en cache par empreinte (texte, voix, vitesse, connecteur) : relancer ne resynthétise
que les répliques modifiées.
"""

import hashlib

import yaml

import connecteurs
from noyau.erreurs import ErreurStudio
from noyau.gpu import tache_gpu
from noyau.medias import duree, ecrire_json
from noyau.projet import ProjetCharge

RESPIRATION = 0.3  # silence minimal entre deux répliques (s)


def lancer(p: ProjetCharge, *, force: bool = False) -> None:
    if not p.config.commentaire.actif:
        ecrire_json(p.placement_voix, [])
        print("[voix] commentaire désactivé : aucune voix")
        return
    if not p.commentaire.exists():
        raise ErreurStudio(f"Commentaire absent ({p.commentaire}) : lancez d'abord `studio commenter {p.slug}`.")
    repliques = (yaml.safe_load(p.commentaire.read_text(encoding="utf-8")) or {}).get("repliques") or []

    cfg = p.config.voix
    langue = p.config.transcription.langue
    connecteur = connecteurs.voix(cfg.connecteur)
    p.dossier_voix.mkdir(parents=True, exist_ok=True)

    a_synthetiser = []
    for r in repliques:
        cle = hashlib.sha1(f"{cfg.connecteur}|{cfg.voix}|{cfg.vitesse}|{langue}|{r['texte']}".encode()).hexdigest()[:16]
        r["fichier"] = p.dossier_voix / f"{cle}.wav"
        if force or not r["fichier"].exists():
            a_synthetiser.append(r)

    if a_synthetiser:
        pret, detail = connecteur.disponible()
        if not pret:
            raise ErreurStudio(f"Connecteur de voix « {connecteur.nom} » indisponible : {detail}")
        with tache_gpu("voix"):
            for i, r in enumerate(a_synthetiser, 1):
                print(f"[voix] {i}/{len(a_synthetiser)} : {r['texte'][:60]}…")
                temporaire = r["fichier"].with_suffix(".tmp.wav")
                connecteur.synthetiser(r["texte"], temporaire, voix=cfg.voix, langue=langue, vitesse=cfg.vitesse)
                temporaire.replace(r["fichier"])
        connecteur.liberer()

    placement, fin_precedente = [], 0.0
    for r in sorted(repliques, key=lambda r: float(r["debut"])):
        debut = max(float(r["debut"]), fin_precedente + RESPIRATION if placement else float(r["debut"]))
        longueur = duree(r["fichier"])
        if debut > float(r["debut"]) + 0.05:
            print(f"[voix] réplique décalée de {debut - float(r['debut']):.1f} s pour ne pas chevaucher la précédente")
        placement.append({"debut": round(debut, 3), "duree": round(longueur, 3), "fichier": f"voix/{r['fichier'].name}", "texte": r["texte"]})
        fin_precedente = debut + longueur
    ecrire_json(p.placement_voix, placement)
    print(f"[voix] {len(placement)} clips ({len(a_synthetiser)} synthétisés) → {p.placement_voix}")
