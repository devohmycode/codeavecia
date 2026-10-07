"""LM Studio : LLM local, servi par une API compatible OpenAI (http://127.0.0.1:1234/v1 par défaut)."""

import base64
import json
import re
import shutil
import subprocess
from pathlib import Path

import httpx

from noyau.config import env
from noyau.erreurs import ErreurStudio

from .base import ConnecteurTexte


def _lms() -> str | None:
    trouve = shutil.which("lms")
    if trouve:
        return trouve
    defaut = Path.home() / ".lmstudio" / "bin" / "lms.exe"
    return str(defaut) if defaut.exists() else None


class LMStudio(ConnecteurTexte):
    nom = "lmstudio"

    def __init__(self, modele: str | None = None):
        self.url = env("LMSTUDIO_URL", "http://127.0.0.1:1234/v1").rstrip("/")
        self.modele = modele or env("LMSTUDIO_MODELE")

    def _modeles(self) -> list[str]:
        reponse = httpx.get(f"{self.url}/models", timeout=5)
        reponse.raise_for_status()
        return [m["id"] for m in reponse.json()["data"]]

    def disponible(self) -> tuple[bool, str]:
        try:
            modeles = [m for m in self._modeles() if "embed" not in m]
        except httpx.HTTPError:
            if _lms():
                return False, "serveur arrêté ; il sera lancé automatiquement (`lms server start`)"
            return False, f"serveur injoignable sur {self.url}"
        return bool(modeles), f"modèles : {', '.join(modeles) or 'aucun'}"

    def _demarrer(self) -> None:
        try:
            self._modeles()
            return
        except httpx.HTTPError:
            pass
        lms = _lms()
        if not lms:
            raise ErreurStudio(f"LM Studio injoignable sur {self.url} et commande `lms` introuvable.")
        print("[lmstudio] démarrage du serveur local…")
        subprocess.run([lms, "server", "start"], capture_output=True, check=False)
        try:
            self._modeles()
        except httpx.HTTPError as e:
            raise ErreurStudio("Le serveur LM Studio n'a pas démarré. Ouvrez LM Studio et réessayez.") from e

    def _choisir_modele(self) -> str:
        if self.modele:
            return self.modele
        modeles = [m for m in self._modeles() if "embed" not in m]
        if not modeles:
            raise ErreurStudio("Aucun modèle de langage téléchargé dans LM Studio.")
        return modeles[0]

    def _info(self, modele: str) -> dict:
        """Fiche du modèle dans l'API native de LM Studio (type « vlm » = lit les images, état de chargement)."""
        try:
            reponse = httpx.get(f"{self.url.removesuffix('/v1')}/api/v0/models/{modele}", timeout=5)
            reponse.raise_for_status()
            return reponse.json()
        except httpx.HTTPError:
            return {}

    def voit_images(self) -> bool:
        self._demarrer()
        return self._info(self._choisir_modele()).get("type") == "vlm"

    def _charger(self, modele: str) -> None:
        """Charge le modèle avec un contexte assez long pour le journal et les images (le défaut est trop court)."""
        if self._info(modele).get("state") == "loaded":
            return
        lms = _lms()
        if not lms:
            return  # LM Studio chargera le modèle à la demande, avec son contexte par défaut
        contexte = env("LMSTUDIO_CONTEXTE", "16384")
        print(f"[lmstudio] chargement de {modele} (contexte {contexte} jetons)…")
        subprocess.run([lms, "load", modele, "--context-length", contexte, "--yes"], capture_output=True, check=False)

    def generer_json(self, systeme: str, utilisateur: str, schema: dict, images=()) -> dict:
        self._demarrer()
        modele = self._choisir_modele()
        self._charger(modele)
        contenu: str | list = utilisateur
        if images:
            contenu = [{"type": "text", "text": utilisateur}]
            for legende, jpeg in images:
                contenu.append({"type": "text", "text": legende})
                url = "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()
                contenu.append({"type": "image_url", "image_url": {"url": url}})
        print(f"[lmstudio] génération avec {modele} ({len(images)} images)…")
        corps = {
            "model": modele,
            "messages": [{"role": "system", "content": systeme}, {"role": "user", "content": contenu}],
            "temperature": 0.4,
            "max_tokens": 12000,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "reponse", "strict": True, "schema": schema},
            },
        }
        try:
            reponse = httpx.post(f"{self.url}/chat/completions", json=corps, timeout=900)
            reponse.raise_for_status()
        except httpx.HTTPError as e:
            raise ErreurStudio(f"Échec de l'appel à LM Studio : {e}") from e
        contenu = reponse.json()["choices"][0]["message"]["content"] or ""
        contenu = re.sub(r"<think>.*?</think>", "", contenu, flags=re.DOTALL).strip()
        try:
            return json.loads(contenu)
        except json.JSONDecodeError as e:
            raise ErreurStudio(f"Réponse de LM Studio illisible en JSON :\n{contenu[:500]}") from e

    def liberer(self) -> None:
        lms = _lms()
        if lms:
            subprocess.run([lms, "unload", "--all"], capture_output=True, check=False)
