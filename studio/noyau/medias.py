"""Appels à ffmpeg / ffprobe et petits utilitaires de fichiers."""

import json
import subprocess
from pathlib import Path

from .erreurs import ErreurStudio


def executer(commande: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Lance une commande ; en cas d'échec, lève une ErreurStudio avec la fin de sa sortie d'erreur."""
    try:
        resultat = subprocess.run(
            commande, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
    except FileNotFoundError as e:
        raise ErreurStudio(f"Programme introuvable : {commande[0]}") from e
    if resultat.returncode != 0:
        fin = "\n".join((resultat.stderr or resultat.stdout).strip().splitlines()[-15:])
        raise ErreurStudio(f"Échec de {Path(commande[0]).name} (code {resultat.returncode}) :\n{fin}")
    return resultat


def sonder(fichier: Path) -> dict:
    sortie = executer(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(fichier)]
    ).stdout
    return json.loads(sortie)


def duree(fichier: Path) -> float:
    return float(sonder(fichier)["format"]["duration"])


def a_audio(fichier: Path) -> bool:
    return any(f["codec_type"] == "audio" for f in sonder(fichier)["streams"])


def dimensions(fichier: Path) -> tuple[int, int]:
    video = next(f for f in sonder(fichier)["streams"] if f["codec_type"] == "video")
    return int(video["width"]), int(video["height"])


def a_jour(sortie: Path, *entrees: Path) -> bool:
    """Vrai si `sortie` existe et n'est plus ancienne qu'aucune des entrées existantes."""
    if not sortie.exists():
        return False
    date = sortie.stat().st_mtime
    return all(not e.exists() or e.stat().st_mtime <= date for e in entrees)


def ecrire_json(fichier: Path, donnees) -> None:
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(json.dumps(donnees, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def lire_json(fichier: Path):
    return json.loads(fichier.read_text(encoding="utf-8"))
