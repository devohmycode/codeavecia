"""Registre des connecteurs : nom dans projet.yaml → implémentation."""

from .base import Connecteur, ConnecteurTexte, ConnecteurVoix


def texte(nom: str, modele: str | None = None) -> ConnecteurTexte:
    if nom == "lmstudio":
        from .lmstudio import LMStudio

        return LMStudio(modele)
    if nom == "claude":
        from .claude import Claude

        return Claude(modele)
    raise ValueError(f"Connecteur de texte inconnu : {nom}")


def voix(nom: str) -> ConnecteurVoix:
    if nom == "voicestudio":
        from .voicestudio import VoiceStudio

        return VoiceStudio()
    if nom == "windows":
        from .windows import VoixWindows

        return VoixWindows()
    raise ValueError(f"Connecteur de voix inconnu : {nom}")


def tous() -> list[Connecteur]:
    return [texte("lmstudio"), texte("claude"), voix("voicestudio"), voix("windows")]
