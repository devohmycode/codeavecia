"""Correspondance entre le temps de la capture brute et celui de la capture dérushée."""

from bisect import bisect_right

Intervalle = tuple[float, float]


def complement(duree: float, coupes: list[Intervalle]) -> list[Intervalle]:
    """Passages gardés : la durée totale moins les coupes (triées, fusionnées si elles se chevauchent)."""
    gardes: list[Intervalle] = []
    curseur = 0.0
    for debut, fin in sorted(coupes):
        debut, fin = max(0.0, debut), min(duree, fin)
        if debut > curseur:
            gardes.append((curseur, debut))
        curseur = max(curseur, fin)
    if curseur < duree:
        gardes.append((curseur, duree))
    return gardes


class Timeline:
    def __init__(self, gardes: list[Intervalle]):
        self.gardes = gardes
        self.cumul: list[float] = []  # début de chaque passage gardé dans la vidéo dérushée
        total = 0.0
        for debut, fin in gardes:
            self.cumul.append(total)
            total += fin - debut
        self.duree = total

    def vers_coupe(self, t: float) -> float | None:
        """Temps brut → temps dérushé ; None si l'instant tombe dans une coupe."""
        for (debut, fin), base in zip(self.gardes, self.cumul):
            if debut <= t <= fin:
                return base + t - debut
        return None

    def vers_source(self, t: float) -> float:
        """Temps dérushé → temps brut."""
        i = max(0, bisect_right(self.cumul, t) - 1)
        debut, fin = self.gardes[i]
        return min(fin, debut + t - self.cumul[i])
