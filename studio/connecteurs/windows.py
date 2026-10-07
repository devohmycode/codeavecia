"""Voix système de Windows (SAPI) : voix de secours, sans installation, de qualité modeste."""

import os
import subprocess
import sys
from pathlib import Path

from noyau.erreurs import ErreurStudio

from .base import ConnecteurVoix

# Le texte et les paramètres passent par des variables d'environnement : aucun échappement à gérer.
SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($env:STUDIO_VOIX -ne 'default') { $s.SelectVoice($env:STUDIO_VOIX) }
else {
  $v = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like "$($env:STUDIO_LANGUE)*" } | Select-Object -First 1
  if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }
}
$s.Rate = [int]$env:STUDIO_DEBIT
$s.SetOutputToWaveFile($env:STUDIO_SORTIE)
$s.Speak($env:STUDIO_TEXTE)
$s.Dispose()
"""


class VoixWindows(ConnecteurVoix):
    nom = "windows"

    def disponible(self) -> tuple[bool, str]:
        if sys.platform != "win32":
            return False, "Windows uniquement"
        return True, "voix SAPI installées (Hortense, Julie, Paul…)"

    def synthetiser(self, texte: str, sortie: Path, *, voix: str, langue: str, vitesse: float) -> None:
        debit = max(-10, min(10, round((vitesse - 1) * 10)))
        environnement = os.environ | {
            "STUDIO_TEXTE": texte,
            "STUDIO_SORTIE": str(sortie),
            "STUDIO_VOIX": voix,
            "STUDIO_LANGUE": langue,
            "STUDIO_DEBIT": str(debit),
        }
        resultat = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", SCRIPT],
            env=environnement,
            capture_output=True,
            text=True,
        )
        if resultat.returncode != 0 or not sortie.exists():
            raise ErreurStudio(f"Échec de la voix Windows : {resultat.stderr.strip()[:300]}")
