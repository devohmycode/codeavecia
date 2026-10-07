"""VoiceStudio : synthèse vocale locale (moteur OmniVoice), par son API compatible OpenAI.

L'API n'est disponible que lorsque l'application VoiceStudio est ouverte (port 3900 par défaut).
"""

from pathlib import Path

import httpx

from noyau.config import env
from noyau.erreurs import ErreurStudio

from .base import ConnecteurVoix


class VoiceStudio(ConnecteurVoix):
    nom = "voicestudio"

    def __init__(self):
        self.url = env("VOICESTUDIO_URL", "http://127.0.0.1:3900").rstrip("/")
        cle = env("VOICESTUDIO_CLE")
        self.entetes = {"Authorization": f"Bearer {cle}"} if cle else {}

    def disponible(self) -> tuple[bool, str]:
        try:
            reponse = httpx.get(f"{self.url}/v1/audio/voices", headers=self.entetes, timeout=5)
            reponse.raise_for_status()
        except httpx.HTTPError:
            return False, f"application fermée ou injoignable sur {self.url}"
        donnees = reponse.json()
        voix = donnees.get("voices", donnees.get("data", [])) if isinstance(donnees, dict) else donnees
        # Les alias OpenAI (alloy, ash…) renvoient tous à la voix par défaut : seuls les vrais profils comptent.
        profils = [v.get("voice_id") or v.get("id") for v in voix if isinstance(v, dict) and v.get("type") != "openai_alias"]
        return True, f"voix : default{', ' if profils else ''}{', '.join(map(str, profils[:8]))}"

    def synthetiser(self, texte: str, sortie: Path, *, voix: str, langue: str, vitesse: float) -> None:
        corps = {
            "model": "omnivoice",
            "input": texte,
            "voice": voix,
            "response_format": "wav",
            "speed": vitesse,
            "language": langue,
        }
        try:
            reponse = httpx.post(f"{self.url}/v1/audio/speech", json=corps, headers=self.entetes, timeout=600)
            reponse.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ErreurStudio(f"VoiceStudio a refusé la synthèse ({e.response.status_code}) : {e.response.text[:300]}") from e
        except httpx.HTTPError as e:
            raise ErreurStudio(f"VoiceStudio injoignable sur {self.url} : ouvrez l'application.") from e
        sortie.write_bytes(reponse.content)
