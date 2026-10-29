#!/usr/bin/env python3
"""Rechnet Gruppen- und Teamaufteilungen für eine Spielerzahl aus.

Aufruf:
  python3 scripts/aufteilung.py 14 --gruppen 6-7       # Gruppen mit 6 bis 7 Spielern
  python3 scripts/aufteilung.py 15 --teams 2           # zwei Teams (+ Joker bei ungerader Zahl)
  python3 scripts/aufteilung.py 14 --uebung "Rondo 5v2"  # nach gruppengroesse/spieler_max der Karte
"""
import argparse
import math
import sys


def gruppen(n: int, gmin: int, gmax: int) -> list[int] | None:
    """Möglichst gleich große Gruppen mit gmin..gmax Spielern; None, wenn das nicht aufgeht."""
    if n < gmin:
        return None
    k = math.ceil(n / gmax)
    while k <= n // gmin:
        basis, rest = divmod(n, k)
        groessen = [basis + 1] * rest + [basis] * (k - rest)
        if min(groessen) >= gmin and max(groessen) <= gmax:
            return groessen
        k += 1
    return None


def gruppen_text(groessen: list[int]) -> str:
    if len(groessen) == 1:
        return f"1 Gruppe mit {groessen[0]} Spielern"
    if len(set(groessen)) == 1:
        return f"{len(groessen)} Gruppen à {groessen[0]}"
    teile = [f"{groessen.count(g)} x {g}" for g in sorted(set(groessen), reverse=True)]
    return f"{len(groessen)} Gruppen ({' + '.join(teile)})"


def teams(n: int, anzahl: int = 2) -> tuple[list[int], int]:
    """Teamgrößen und Anzahl Joker (Rest, der nicht gleichmäßig aufgeht)."""
    basis, joker = divmod(n, anzahl)
    return [basis] * anzahl, joker


def teams_text(n: int, anzahl: int = 2) -> str:
    groessen, joker = teams(n, anzahl)
    text = " gegen ".join(str(g) for g in groessen)
    if joker:
        text += f" + {joker} Joker" if joker > 1 else " + 1 neutraler Joker"
    return text


def fuer_uebung(u: dict, n: int) -> tuple[str, int]:
    """Vorschlag (Text, Anzahl Gruppen) für eine Übungskarte."""
    gg = u.get("gruppengroesse")
    if gg:
        g = gruppen(n, gg[0], gg[1])
        if g:
            return gruppen_text(g), len(g)
        return f"{n} Spieler passen nicht in Gruppen à {gg[0]}-{gg[1]} – Variante nutzen", 1
    smax = u.get("spieler_max") or n
    if n <= smax:
        return f"alle {n} Feldspieler zusammen", 1
    k = math.ceil(n / smax)
    return gruppen_text(gruppen(n, math.ceil(n / k) - 1, smax) or [n]), k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spieler", type=int)
    ap.add_argument("--gruppen", help="min-max Spieler pro Gruppe, z. B. 6-7")
    ap.add_argument("--teams", type=int)
    ap.add_argument("--uebung")
    a = ap.parse_args()
    if a.gruppen:
        gmin, gmax = (int(x) for x in a.gruppen.split("-"))
        g = gruppen(a.spieler, gmin, gmax)
        print(gruppen_text(g) if g else "geht nicht auf")
    elif a.teams:
        print(teams_text(a.spieler, a.teams))
    elif a.uebung:
        from datenbank import finde
        t = finde(a.uebung)
        if len(t) != 1:
            sys.exit(f"Übung nicht eindeutig: {', '.join(u['_kurz'] for u in t) or 'keine'}")
        print(fuer_uebung(t[0], a.spieler)[0])
    else:
        ap.error("--gruppen, --teams oder --uebung angeben")


if __name__ == "__main__":
    main()
