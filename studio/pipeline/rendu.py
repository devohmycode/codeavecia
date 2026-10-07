"""S9 — Rendu : met en images la composition Remotion, en 16:9 (Paysage) et en 9:16 (Vertical).

Remotion encode en H.264 avec le processeur : l'accélération matérielle qu'il propose ne couvre pas NVENC
sous Windows. NVENC sert à la capture (S1) et au découpage (S3).
"""

import shutil
import subprocess

from noyau.config import MONTAGE
from noyau.erreurs import ErreurStudio
from noyau.gpu import tache_gpu
from noyau.medias import duree
from noyau.projet import ProjetCharge

COMPOSITIONS = {"paysage": ("Paysage", "16x9"), "vertical": ("Vertical", "9x16")}


def _npx() -> str:
    npx = shutil.which("npx")
    if not npx:
        raise ErreurStudio("npx introuvable : installez Node.js 22 ou plus récent.")
    return npx


def _installer_montage() -> None:
    if (MONTAGE / "node_modules" / "remotion").exists():
        return
    print("[rendu] première utilisation : installation de Remotion (npm install)…")
    resultat = subprocess.run([shutil.which("npm") or "npm", "install"], cwd=MONTAGE)
    if resultat.returncode != 0:
        raise ErreurStudio("Échec de `npm install` dans studio/montage.")


def lancer(p: ProjetCharge, *, formats: list[str] | None = None) -> list:
    if not p.props.exists():
        raise ErreurStudio(f"props.json absent : lancez d'abord `studio monter {p.slug}`.")
    _installer_montage()
    p.rendus.mkdir(parents=True, exist_ok=True)
    sorties = []
    for nom in formats or p.config.rendu.formats:
        composition, suffixe = COMPOSITIONS[nom]
        sortie = p.rendus / f"{p.slug}-{suffixe}.mp4"
        commande = [
            _npx(), "remotion", "render", "src/index.ts", composition, str(sortie),
            f"--props={p.props}", f"--public-dir={p.public}",
            "--codec=h264", "--crf=20", "--log=warn",
        ]
        print(f"[rendu] {composition} → {sortie}")
        with tache_gpu(f"rendu {nom}"):
            resultat = subprocess.run(commande, cwd=MONTAGE)
        if resultat.returncode != 0 or not sortie.exists():
            raise ErreurStudio(f"Échec du rendu Remotion ({composition}).")
        print(f"[rendu] {composition} terminé : {duree(sortie):.1f} s")
        sorties.append(sortie)
    return sorties
