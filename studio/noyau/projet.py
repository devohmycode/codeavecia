"""Schéma et chargement de `projets/<slug>/projet.yaml`, et emplacement des fichiers d'un projet.

Le dossier du projet (versionné) ne contient que des décisions éditables à la main : projet.yaml, coupes.yaml,
commentaire.yaml. Les fichiers lourds ou recalculables vont dans media/<slug>/, exclu de git (PRD ST4).
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .config import CONTENUS_VIDEOS, MEDIA, PROJETS
from .erreurs import ErreurStudio

SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class _Section(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Capture(_Section):
    source: Literal["ecran", "zone", "fenetre"] = "ecran"
    zone: tuple[int, int, int, int] | None = None  # x, y, largeur, hauteur (pixels de l'écran principal)
    fenetre: str | None = None  # partie du titre de la fenêtre à capturer
    fps: int = Field(30, ge=10, le=60)
    micro: str = "aucun"  # "aucun", "auto" ou nom exact du périphérique audio DirectShow
    duree: float | None = Field(None, gt=0)  # secondes ; absent = arrêt par Ctrl+C


class Transcription(_Section):
    modele: str = "large-v3-turbo"
    langue: str = "fr"


class Derushage(_Section):
    seuil: float = Field(1.5, gt=0)  # durée minimale d'un temps mort (s)
    marge: float = Field(0.3, ge=0)  # temps conservé de part et d'autre d'une coupe (s)
    silence_db: float = -35
    validation: Literal["manuelle", "auto"] = "manuelle"


class Commentaire(_Section):
    actif: bool = True
    connecteur: Literal["lmstudio", "claude"] = "lmstudio"
    modele: str | None = None
    mots_par_seconde: float = Field(2.3, gt=0.5, le=4)
    images: int = Field(8, ge=0, le=24)  # images de la vidéo montrées au modèle (s'il sait les lire)


class Voix(_Section):
    connecteur: Literal["voicestudio", "windows"] = "voicestudio"
    voix: str = "default"
    vitesse: float = Field(1.0, ge=0.5, le=2.0)


class Montage(_Section):
    volume_original: float = Field(0.0, ge=0, le=1)  # 0 = son de la capture coupé
    sous_titres: Literal["commentaire", "transcription", "aucun"] = "commentaire"
    zooms: bool = True
    facteur_zoom: float = Field(1.6, ge=1, le=3)
    musique: str | None = None  # chemin d'un fichier audio, relatif au dossier du projet
    volume_musique: float = Field(0.1, ge=0, le=1)


class Rendu(_Section):
    formats: list[Literal["paysage", "vertical"]] = ["paysage", "vertical"]


class Projet(_Section):
    titre: str
    description: str = ""
    date: dt.date | None = None
    tags: list[str] = []
    article: str | None = None
    repo: str | None = None
    contexte: str = ""  # ce que montre la vidéo : aide l'IA à écrire le commentaire
    capture: Capture = Capture()
    transcription: Transcription = Transcription()
    derushage: Derushage = Derushage()
    commentaire: Commentaire = Commentaire()
    voix: Voix = Voix()
    montage: Montage = Montage()
    rendu: Rendu = Rendu()


@dataclass
class ProjetCharge:
    slug: str
    config: Projet
    dossier: Path
    media: Path

    # Dans le dossier du projet (versionné, éditable)
    @property
    def fichier_config(self) -> Path:
        return self.dossier / "projet.yaml"

    @property
    def coupes(self) -> Path:
        return self.dossier / "coupes.yaml"

    @property
    def commentaire(self) -> Path:
        return self.dossier / "commentaire.yaml"

    # Dans media/<slug>/ (exclu de git)
    @property
    def rush(self) -> Path:
        return self.media / "rush.mp4"

    @property
    def journal_capture(self) -> Path:
        return self.media / "capture.json"

    @property
    def transcription(self) -> Path:
        return self.media / "transcription.json"

    @property
    def timeline(self) -> Path:
        return self.media / "timeline.json"

    @property
    def rush_coupe(self) -> Path:
        return self.media / "rush-coupe.mp4"

    @property
    def dossier_voix(self) -> Path:
        return self.media / "voix"

    @property
    def placement_voix(self) -> Path:
        return self.media / "voix.json"

    @property
    def public(self) -> Path:
        """Dossier servi à Remotion : liens vers la vidéo dérushée, les voix et la musique."""
        return self.media / "public"

    @property
    def props(self) -> Path:
        return self.media / "props.json"

    @property
    def rendus(self) -> Path:
        return self.media / "rendus"

    # Pour le site (versionné)
    @property
    def fiche(self) -> Path:
        return CONTENUS_VIDEOS / f"{self.slug}.json"


def verifier_slug(slug: str) -> None:
    if not SLUG.match(slug):
        raise ErreurStudio(f"Nom de projet invalide « {slug} » : minuscules, chiffres et tirets uniquement.")


def charger(slug: str) -> ProjetCharge:
    verifier_slug(slug)
    dossier = PROJETS / slug
    fichier = dossier / "projet.yaml"
    if not fichier.exists():
        raise ErreurStudio(f"Projet introuvable : {fichier}. Créez-le avec `studio nouveau {slug}`.")
    try:
        brut = yaml.safe_load(fichier.read_text(encoding="utf-8")) or {}
        config = Projet.model_validate(brut)
    except yaml.YAMLError as e:
        raise ErreurStudio(f"{fichier} n'est pas un YAML valide :\n{e}") from e
    except ValidationError as e:
        lignes = [f"  - {'.'.join(map(str, err['loc']))} : {err['msg']}" for err in e.errors()]
        raise ErreurStudio(f"{fichier} contient des erreurs :\n" + "\n".join(lignes)) from e
    media = MEDIA / slug
    media.mkdir(parents=True, exist_ok=True)
    return ProjetCharge(slug=slug, config=config, dossier=dossier, media=media)


MODELE = """\
# Projet vidéo de l'atelier CodeAvecIA — voir studio/README.md pour chaque option.
titre: "{titre}"
description: ""
tags: []
# article: slug-d-un-article     # article du site lié à la vidéo
# repo: devohmycode/un-depot     # dépôt GitHub montré dans la vidéo

# Ce que montre la vidéo et ce qu'elle doit transmettre : sert à l'IA pour écrire le commentaire.
contexte: |
  À compléter.

capture:
  source: ecran        # ecran | zone | fenetre
  # zone: [0, 0, 1920, 1080]
  # fenetre: "Visual Studio Code"
  fps: 30
  micro: aucun         # aucun | auto | nom exact du micro
  # duree: 60          # secondes ; sinon arrêt par Ctrl+C

derushage:
  seuil: 1.5
  validation: manuelle # manuelle : relire coupes.yaml avant le montage

commentaire:
  connecteur: lmstudio # lmstudio (local) | claude (payant)

voix:
  connecteur: voicestudio  # voicestudio (local, application ouverte) | windows (voix système)
  voix: default

montage:
  volume_original: 0   # 0 = son de la capture coupé ; 1 = conservé
  sous_titres: commentaire
  zooms: true
"""


def creer(slug: str, titre: str) -> Path:
    verifier_slug(slug)
    fichier = PROJETS / slug / "projet.yaml"
    if fichier.exists():
        raise ErreurStudio(f"Le projet existe déjà : {fichier}")
    fichier.parent.mkdir(parents=True)
    fichier.write_text(MODELE.format(titre=titre.replace('"', '\\"')), encoding="utf-8")
    return fichier
