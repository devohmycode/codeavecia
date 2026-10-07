"""S3 — Dérushage : repère les temps morts (silence ET image figée), les propose dans coupes.yaml,
puis, une fois les coupes validées, produit la capture dérushée et la table de correspondance des temps."""

import datetime as dt
import re
import shutil

import yaml

from noyau.erreurs import ErreurStudio
from noyau.medias import a_audio, a_jour, duree, ecrire_json, executer
from noyau.projet import ProjetCharge
from noyau.timeline import Intervalle, complement


def _intervalles(texte: str, motif_debut: str, motif_fin: str, fin_par_defaut: float) -> list[Intervalle]:
    debuts = [float(x) for x in re.findall(motif_debut + r"\s*([\d.]+)", texte)]
    fins = [float(x) for x in re.findall(motif_fin + r"\s*([\d.]+)", texte)]
    fins += [fin_par_defaut] * (len(debuts) - len(fins))  # un passage encore en cours à la fin du fichier
    return list(zip(debuts, fins))


def _silences(rush, seuil_db: float, duree_min: float, total: float) -> list[Intervalle]:
    sortie = executer(
        ["ffmpeg", "-hide_banner", "-i", str(rush), "-vn", "-af", f"silencedetect=noise={seuil_db}dB:d={duree_min}", "-f", "null", "-"]
    ).stderr
    return _intervalles(sortie, r"silence_start:", r"silence_end:", total)


def _gels(rush, duree_min: float, total: float) -> list[Intervalle]:
    # Analyse en basse définition : un curseur qui clignote ne compte pas comme un mouvement.
    sortie = executer(
        ["ffmpeg", "-hide_banner", "-i", str(rush), "-an", "-vf", f"scale=640:-2,freezedetect=n=0.001:d={duree_min}", "-f", "null", "-"]
    ).stderr
    return _intervalles(sortie, r"freeze_start:", r"freeze_end:", total)


def _intersection(a: list[Intervalle], b: list[Intervalle]) -> list[Intervalle]:
    resultat = []
    for debut_a, fin_a in a:
        for debut_b, fin_b in b:
            debut, fin = max(debut_a, debut_b), min(fin_a, fin_b)
            if fin > debut:
                resultat.append((debut, fin))
    return sorted(resultat)


def proposer(p: ProjetCharge) -> None:
    cfg = p.config.derushage
    total = duree(p.rush)
    gels = _gels(p.rush, cfg.seuil, total)
    if a_audio(p.rush):
        morts = _intersection(_silences(p.rush, cfg.silence_db, cfg.seuil, total), gels)
        raison = "silence et image figée"
    else:
        morts = gels
        raison = "image figée (pas de son)"
    coupes = []
    for debut, fin in morts:
        # Pas de marge au bord de la capture : elle laisserait un fragment de quelques images.
        debut = 0.0 if debut <= 0.05 else debut + cfg.marge
        fin = total if fin >= total - 0.05 else fin - cfg.marge
        if fin - debut >= max(0.5, cfg.seuil - 2 * cfg.marge):
            coupes.append({"debut": round(debut, 2), "fin": round(fin, 2), "raison": raison})
    entete = (
        f"# Coupes proposées par `studio derusher` le {dt.date.today().isoformat()}.\n"
        "# Chaque entrée est un passage SUPPRIMÉ de la capture (secondes de la capture brute).\n"
        "# Modifiez, supprimez ou ajoutez des coupes, puis passez `valide` à true.\n"
    )
    corps = yaml.safe_dump(
        {"valide": False, "duree_source": round(total, 2), "coupes": coupes},
        allow_unicode=True, sort_keys=False, default_flow_style=None,
    )
    p.coupes.write_text(entete + corps, encoding="utf-8")
    retire = sum(c["fin"] - c["debut"] for c in coupes)
    print(f"[dérushage] {len(coupes)} coupes proposées ({retire:.1f} s sur {total:.1f} s) → {p.coupes}")


def _valider(p: ProjetCharge) -> None:
    texte = p.coupes.read_text(encoding="utf-8")
    valide = re.sub(r"(?m)^valide:\s*false\s*$", "valide: true", texte)
    if valide != texte:  # ne pas toucher au fichier sinon : sa date déclencherait un nouveau découpage
        p.coupes.write_text(valide, encoding="utf-8")


def appliquer(p: ProjetCharge) -> None:
    donnees = yaml.safe_load(p.coupes.read_text(encoding="utf-8")) or {}
    total = duree(p.rush)
    try:
        coupes = [(float(c["debut"]), float(c["fin"])) for c in donnees.get("coupes") or []]
    except (KeyError, TypeError, ValueError) as e:
        raise ErreurStudio(f"{p.coupes} : chaque coupe doit avoir un `debut` et une `fin` en secondes.") from e
    gardes = complement(total, coupes)
    if not gardes:
        raise ErreurStudio("Les coupes suppriment toute la capture.")

    if not coupes:
        shutil.copyfile(p.rush, p.rush_coupe)
    else:
        audio = a_audio(p.rush)
        filtres, entrees = [], []
        for i, (debut, fin) in enumerate(gardes):
            filtres.append(f"[0:v]trim=start={debut}:end={fin},setpts=PTS-STARTPTS[v{i}]")
            entrees.append(f"[v{i}]")
            if audio:
                filtres.append(f"[0:a]atrim=start={debut}:end={fin},asetpts=PTS-STARTPTS[a{i}]")
                entrees.append(f"[a{i}]")
        filtres.append(f"{''.join(entrees)}concat=n={len(gardes)}:v=1:a={int(audio)}[v]" + ("[a]" if audio else ""))
        commande = ["ffmpeg", "-hide_banner", "-y", "-i", str(p.rush), "-filter_complex", ";".join(filtres), "-map", "[v]"]
        if audio:
            commande += ["-map", "[a]", "-c:a", "aac", "-b:a", "160k"]
        commande += ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19", str(p.rush_coupe)]
        executer(commande)

    ecrire_json(p.timeline, {"gardes": [[round(a, 3), round(b, 3)] for a, b in gardes], "duree": round(sum(b - a for a, b in gardes), 3)})
    print(f"[dérushage] capture dérushée : {duree(p.rush_coupe):.1f} s → {p.rush_coupe}")


def lancer(p: ProjetCharge, *, auto: bool = False, force: bool = False) -> bool:
    """Renvoie False si les coupes attendent une validation manuelle."""
    if force or not a_jour(p.coupes, p.rush):
        proposer(p)
    if auto or p.config.derushage.validation == "auto":
        _valider(p)
    donnees = yaml.safe_load(p.coupes.read_text(encoding="utf-8")) or {}
    if not donnees.get("valide"):
        print(f"[dérushage] relisez {p.coupes}, passez `valide: true`, puis relancez (ou utilisez --auto).")
        return False
    if force or not a_jour(p.rush_coupe, p.rush, p.coupes) or not p.timeline.exists():
        appliquer(p)
    else:
        print("[dérushage] capture dérushée déjà à jour")
    return True
