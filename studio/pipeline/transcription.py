"""S2 — Transcription de la capture avec faster-whisper sur GPU, horodatée au mot."""

import importlib.util
import os
from pathlib import Path

from noyau.gpu import tache_gpu
from noyau.medias import a_audio, a_jour, ecrire_json
from noyau.projet import ProjetCharge


def _rendre_cuda_visible() -> None:
    """Windows : expose à CTranslate2 les DLL cuBLAS et cuDNN des paquets pip nvidia-*."""
    for paquet in ("nvidia.cublas", "nvidia.cudnn"):
        try:
            spec = importlib.util.find_spec(paquet)
        except ModuleNotFoundError:
            continue
        for dossier in (spec.submodule_search_locations or []) if spec else []:
            binaires = Path(dossier) / "bin"
            if binaires.is_dir():
                os.add_dll_directory(str(binaires))
                os.environ["PATH"] = str(binaires) + os.pathsep + os.environ["PATH"]


def transcrire_fichier(fichier: Path, modele: str, langue: str) -> dict:
    _rendre_cuda_visible()
    from faster_whisper import WhisperModel

    with tache_gpu("transcription"):
        try:
            whisper = WhisperModel(modele, device="cuda", compute_type="float16")
            segments, _ = whisper.transcribe(str(fichier), language=langue, word_timestamps=True, vad_filter=True)
            segments = list(segments)
            appareil = "cuda"
        except RuntimeError as e:
            print(f"[transcription] GPU indisponible ({e}) : repli sur le processeur, plus lent.")
            whisper = WhisperModel(modele, device="cpu", compute_type="int8")
            segments, _ = whisper.transcribe(str(fichier), language=langue, word_timestamps=True, vad_filter=True)
            segments = list(segments)
            appareil = "cpu"
    return {
        "modele": modele,
        "langue": langue,
        "appareil": appareil,
        "segments": [
            {
                "debut": round(s.start, 3),
                "fin": round(s.end, 3),
                "texte": s.text.strip(),
                "mots": [{"debut": round(m.start, 3), "fin": round(m.end, 3), "mot": m.word.strip()} for m in s.words or []],
            }
            for s in segments
        ],
    }


def _horodatage(t: float, separateur: str) -> str:
    ms = round(t * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}{separateur}{ms:03}"


def ecrire_sous_titres(segments: list[dict], base: Path) -> None:
    """Exporte les segments en SRT et en WebVTT à côté de `base`."""
    srt = [f"{i}\n{_horodatage(s['debut'], ',')} --> {_horodatage(s['fin'], ',')}\n{s['texte']}\n" for i, s in enumerate(segments, 1)]
    vtt = ["WEBVTT\n"] + [f"{_horodatage(s['debut'], '.')} --> {_horodatage(s['fin'], '.')}\n{s['texte']}\n" for s in segments]
    base.with_suffix(".srt").write_text("\n".join(srt), encoding="utf-8")
    base.with_suffix(".vtt").write_text("\n".join(vtt), encoding="utf-8")


def lancer(p: ProjetCharge, *, force: bool = False) -> None:
    if not force and a_jour(p.transcription, p.rush):
        print("[transcription] déjà à jour")
        return
    if not a_audio(p.rush):
        ecrire_json(p.transcription, {"segments": []})
        print("[transcription] la capture n'a pas de piste audio : rien à transcrire")
        return
    cfg = p.config.transcription
    print(f"[transcription] modèle {cfg.modele} (téléchargé au premier usage)…")
    donnees = transcrire_fichier(p.rush, cfg.modele, cfg.langue)
    ecrire_json(p.transcription, donnees)
    ecrire_sous_titres(donnees["segments"], p.transcription)
    print(f"[transcription] {len(donnees['segments'])} segments ({donnees['appareil']}) → {p.transcription}")
