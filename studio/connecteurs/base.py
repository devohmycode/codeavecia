"""Interface commune des connecteurs (PRD ST1) : chacun peut être remplacé par un autre du même type."""

from abc import ABC, abstractmethod
from pathlib import Path


class Connecteur(ABC):
    nom: str
    local: bool = True  # False : service payant, à confirmer avant chaque appel (PRD ST3)

    @abstractmethod
    def disponible(self) -> tuple[bool, str]:
        """(prêt ?, explication courte pour l'utilisateur)."""

    def cout_estime(self, texte_entree: str, nb_images: int = 0) -> float:
        """Coût estimé en dollars d'un appel portant sur `texte_entree` et `nb_images` images."""
        return 0.0

    def liberer(self) -> None:
        """Rend les ressources (mémoire vidéo…) quand l'étape est terminée."""


Image = tuple[str, bytes]  # (légende, image JPEG)


class ConnecteurTexte(Connecteur):
    def voit_images(self) -> bool:
        """Le modèle accepte-t-il des images en entrée ?"""
        return False

    @abstractmethod
    def generer_json(self, systeme: str, utilisateur: str, schema: dict, images: list[Image] = ()) -> dict:
        """Réponse JSON conforme à `schema` ; `images` n'est transmis que si voit_images() est vrai."""


class ConnecteurVoix(Connecteur):
    @abstractmethod
    def synthetiser(self, texte: str, sortie: Path, *, voix: str, langue: str, vitesse: float) -> None:
        """Écrit la voix lue de `texte` dans le fichier WAV `sortie`."""
