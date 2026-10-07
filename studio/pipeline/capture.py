"""S1 — Capture de l'écran (ffmpeg ddagrab + encodage NVENC) et journal du curseur, des clics et des fenêtres.

Le journal sert ensuite aux zooms (S8), au cadrage vertical (S8) et au contexte du commentaire (S4).
Limite : seul l'écran principal est capturé.
"""

import ctypes
import ctypes.wintypes as wt
import datetime as dt
import re
import subprocess
import threading
import time

from noyau.erreurs import ErreurStudio
from noyau.medias import ecrire_json, executer
from noyau.projet import ProjetCharge

user32 = ctypes.windll.user32
FREQUENCE_JOURNAL = 20  # échantillons de curseur par seconde


def _activer_dpi() -> None:
    """Coordonnées en pixels physiques, comme celles de l'image capturée."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except OSError:
        user32.SetProcessDPIAware()


def _taille_ecran() -> tuple[int, int]:
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def _titre(hwnd) -> str:
    longueur = user32.GetWindowTextLengthW(hwnd)
    tampon = ctypes.create_unicode_buffer(longueur + 1)
    user32.GetWindowTextW(hwnd, tampon, longueur + 1)
    return tampon.value


def _rect_fenetre(partie_titre: str) -> tuple[int, int, int, int]:
    trouvees = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def enumerer(hwnd, _):
        if user32.IsWindowVisible(hwnd) and partie_titre.lower() in _titre(hwnd).lower():
            trouvees.append(hwnd)
        return True

    user32.EnumWindows(enumerer, 0)
    if not trouvees:
        raise ErreurStudio(f"Aucune fenêtre visible dont le titre contient « {partie_titre} ».")
    rect = wt.RECT()
    # Bords réels de la fenêtre, sans l'ombre portée (DWMWA_EXTENDED_FRAME_BOUNDS = 9)
    if ctypes.windll.dwmapi.DwmGetWindowAttribute(trouvees[0], 9, ctypes.byref(rect), ctypes.sizeof(rect)):
        user32.GetWindowRect(trouvees[0], ctypes.byref(rect))
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def _region(p: ProjetCharge) -> tuple[int, int, int, int]:
    cfg = p.config.capture
    largeur_ecran, hauteur_ecran = _taille_ecran()
    if cfg.source == "ecran":
        x, y, l, h = 0, 0, largeur_ecran, hauteur_ecran
    elif cfg.source == "zone":
        if not cfg.zone:
            raise ErreurStudio("capture.source vaut « zone » mais capture.zone est absent.")
        x, y, l, h = cfg.zone
    else:
        if not cfg.fenetre:
            raise ErreurStudio("capture.source vaut « fenetre » mais capture.fenetre est absent.")
        x, y, l, h = _rect_fenetre(cfg.fenetre)
    x, y = max(0, x), max(0, y)
    l, h = min(l, largeur_ecran - x), min(h, hauteur_ecran - y)
    l, h = l - l % 2, h - h % 2  # NVENC exige des dimensions paires
    if l < 64 or h < 64:
        raise ErreurStudio(f"Zone de capture trop petite ou hors de l'écran principal : {x},{y} {l}×{h}.")
    return x, y, l, h


def _micro(reglage: str) -> str | None:
    if reglage == "aucun":
        return None
    if reglage != "auto":
        return reglage
    sortie = subprocess.run(
        ["ffmpeg", "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stderr
    micros = re.findall(r'"([^"]+)" \(audio\)', sortie)
    if not micros:
        raise ErreurStudio("Aucun micro détecté (capture.micro: auto). Mettez « aucun » ou le nom exact.")
    return micros[0]


class _Journal(threading.Thread):
    """Échantillonne le curseur, les clics gauches et le titre de la fenêtre active."""

    def __init__(self):
        super().__init__(daemon=True)
        self.arret = threading.Event()
        self.curseur: list[tuple[float, int, int]] = []
        self.clics: list[tuple[float, int, int]] = []
        self.fenetres: list[tuple[float, str]] = []

    def run(self):
        point = wt.POINT()
        appuye = False
        dernier_titre = None
        while not self.arret.is_set():
            t = time.perf_counter()
            user32.GetCursorPos(ctypes.byref(point))
            self.curseur.append((t, point.x, point.y))
            bouton = bool(user32.GetAsyncKeyState(0x01) & 0x8000)
            if bouton and not appuye:
                self.clics.append((t, point.x, point.y))
            appuye = bouton
            titre = _titre(user32.GetForegroundWindow())
            if titre != dernier_titre:
                self.fenetres.append((t, titre))
                dernier_titre = titre
            self.arret.wait(1 / FREQUENCE_JOURNAL)


def lancer(p: ProjetCharge, *, duree: float | None = None, force: bool = False) -> None:
    if p.rush.exists() and not force:
        raise ErreurStudio(f"Une capture existe déjà ({p.rush}). Relancez avec --force pour la remplacer.")
    executer(["ffmpeg", "-hide_banner", "-version"])
    _activer_dpi()
    cfg = p.config.capture
    duree = duree or cfg.duree
    x, y, l, h = _region(p)
    largeur_ecran, hauteur_ecran = _taille_ecran()
    source = f"ddagrab=output_idx=0:framerate={cfg.fps}:draw_mouse=1"
    if (x, y, l, h) != (0, 0, largeur_ecran, hauteur_ecran):
        source += f":offset_x={x}:offset_y={y}:video_size={l}x{h}"
    micro = _micro(cfg.micro)

    commande = ["ffmpeg", "-hide_banner", "-y", "-f", "lavfi", "-i", source]
    if micro:
        commande += ["-f", "dshow", "-i", f"audio={micro}"]
    commande += ["-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "19"]
    if micro:
        commande += ["-c:a", "aac", "-b:a", "160k"]
    if duree:
        commande += ["-t", str(duree)]
    commande.append(str(p.rush))

    print(f"[capture] zone {x},{y} {l}×{h} à {cfg.fps} i/s, micro : {micro or 'aucun'}")
    print(f"[capture] {'durée : ' + str(duree) + ' s' if duree else 'arrêt : Ctrl+C'}")
    journal = _Journal()
    journal.start()
    processus = subprocess.Popen(commande, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    # Instant de la première image : ffmpeg met un moment à démarrer, le journal doit s'y caler.
    debut_video: list[float] = []
    fin_stderr: list[str] = []

    def lire_stderr():
        tampon = b""
        while octet := processus.stderr.read(1):
            if octet in b"\r\n":
                ligne = tampon.decode("utf-8", "replace")
                tampon = b""
                fin_stderr[:] = (fin_stderr + [ligne])[-20:]
                m = re.search(r"frame=\s*(\d+)", ligne)
                if m and not debut_video and int(m.group(1)) > 0:
                    debut_video.append(time.perf_counter() - int(m.group(1)) / cfg.fps)
            else:
                tampon += octet

    lecteur = threading.Thread(target=lire_stderr, daemon=True)
    lecteur.start()
    try:
        processus.wait()
    except KeyboardInterrupt:
        try:
            processus.stdin.write(b"q")
            processus.stdin.flush()
        except OSError:
            pass  # ffmpeg a déjà reçu Ctrl+C et termine proprement le fichier
        processus.wait()
    journal.arret.set()
    journal.join()
    lecteur.join(timeout=2)

    if processus.returncode not in (0, 255) or not p.rush.exists():
        raise ErreurStudio("Échec de la capture ffmpeg :\n" + "\n".join(fin_stderr[-10:]))
    t0 = debut_video[0] if debut_video else journal.curseur[0][0]

    def relatif(t: float) -> float:
        return round(t - t0, 3)

    ecrire_json(
        p.journal_capture,
        {
            "date": dt.datetime.now().isoformat(timespec="seconds"),
            "region": [x, y, l, h],
            "fps": cfg.fps,
            "micro": micro,
            "curseur": [[relatif(t), cx - x, cy - y] for t, cx, cy in journal.curseur if t >= t0],
            "clics": [[relatif(t), cx - x, cy - y] for t, cx, cy in journal.clics if t >= t0],
            "fenetres": [[max(0.0, relatif(t)), titre] for t, titre in journal.fenetres],
        },
    )
    print(f"[capture] terminé : {p.rush}")
