"""Chemins du dépôt et variables d'environnement (fichier .env à la racine, PRD ST5)."""

import os
from pathlib import Path

from dotenv import load_dotenv

STUDIO = Path(__file__).resolve().parent.parent
RACINE = STUDIO.parent
PROJETS = STUDIO / "projets"
MONTAGE = STUDIO / "montage"
MEDIA = RACINE / "media"
CONTENUS_VIDEOS = RACINE / "contenus" / "videos"

load_dotenv(RACINE / ".env")


def env(nom: str, defaut: str | None = None) -> str | None:
    """Valeur d'une variable d'environnement ; une valeur vide compte comme absente."""
    valeur = os.environ.get(nom)
    return valeur if valeur else defaut
