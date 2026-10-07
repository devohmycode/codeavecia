"""Claude (API Anthropic) : alternative payante à LM Studio pour écrire le commentaire."""

import base64
import json
import os
import shutil

import anthropic

from noyau.erreurs import ErreurStudio

from .base import ConnecteurTexte

MODELE = "claude-opus-5-5"
PRIX_ENTREE, PRIX_SORTIE = 4.0, 20.0  # dollars par million de jetons
SORTIE_ESTIMEE = 4000  # jetons de sortie, réflexion comprise


class Claude(ConnecteurTexte):
    nom = "claude"
    local = False

    def __init__(self, modele: str | None = None):
        self.modele = modele or MODELE

    def disponible(self) -> tuple[bool, str]:
        if os.environ.get("ANTHROPIC_API_KEY"):
            return True, f"clé ANTHROPIC_API_KEY présente ; modèle {self.modele}"
        if shutil.which("ant"):
            return True, "profil `ant auth login` (à vérifier avec `ant auth status`)"
        return False, "ni ANTHROPIC_API_KEY ni profil `ant auth login`"

    def cout_estime(self, texte_entree: str, nb_images: int = 0) -> float:
        jetons_entree = len(texte_entree) / 3.5 + nb_images * 1600  # ~1 600 jetons par image de 1280 px
        return (jetons_entree * PRIX_ENTREE + SORTIE_ESTIMEE * PRIX_SORTIE) / 1_000_000

    def voit_images(self) -> bool:
        return True

    def generer_json(self, systeme: str, utilisateur: str, schema: dict, images=()) -> dict:
        contenu: list[dict] = [{"type": "text", "text": utilisateur}]
        for legende, jpeg in images:
            contenu.append({"type": "text", "text": legende})
            contenu.append(
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(jpeg).decode()}}
            )
        client = anthropic.Anthropic()
        try:
            # Repli côté serveur sur un autre modèle si celui-ci refuse la requête.
            reponse = client.beta.messages.create(
                model=self.modele,
                max_tokens=16000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=systeme,
                messages=[{"role": "user", "content": contenu}],
                output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
            )
        except anthropic.AuthenticationError as e:
            raise ErreurStudio("Identifiants Anthropic refusés : vérifiez ANTHROPIC_API_KEY.") from e
        except anthropic.RateLimitError as e:
            raise ErreurStudio("Limite de débit de l'API Anthropic atteinte : réessayez plus tard.") from e
        except anthropic.APIStatusError as e:
            raise ErreurStudio(f"Erreur de l'API Anthropic ({e.status_code}) : {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise ErreurStudio("API Anthropic injoignable.") from e

        if reponse.stop_reason == "refusal":
            raise ErreurStudio("Claude a refusé de produire ce commentaire.")
        if reponse.stop_reason == "max_tokens":
            raise ErreurStudio("Réponse de Claude tronquée (limite de jetons atteinte).")
        texte = next(b.text for b in reponse.content if b.type == "text")
        return json.loads(texte)
