"""File d'attente GPU : une seule tâche GPU à la fois sur le poste (PRD ST2, 8 Go de mémoire vidéo)."""

from collections.abc import Iterator
from contextlib import contextmanager

from filelock import FileLock, Timeout

from .config import MEDIA


@contextmanager
def tache_gpu(nom: str) -> Iterator[None]:
    """Réserve le GPU pour `nom` ; attend si un autre processus de l'atelier l'utilise."""
    MEDIA.mkdir(parents=True, exist_ok=True)
    verrou = FileLock(MEDIA / ".gpu.lock")
    try:
        verrou.acquire(timeout=0)
    except Timeout:
        print(f"[gpu] GPU occupé par une autre tâche de l'atelier, « {nom} » attend son tour…")
        verrou.acquire()
    try:
        yield
    finally:
        verrou.release()
