#!/usr/bin/env python3
"""Durchsucht die Übungsdatenbank.

Aufruf (alle Filter optional, kombinierbar):
  python3 scripts/suche.py
  python3 scripts/suche.py --schwerpunkt Torabschluss --phase Hauptteil --spieler 14 --tw 2
  python3 scripts/suche.py --text rondo
  python3 scripts/suche.py --details <übung>        # ungefährer Name reicht
"""
import argparse

import yaml

from datenbank import ROOT, alle, bewertung, finde, historie


def als_liste(v):
    return v if isinstance(v, list) else [v] if v else []


def passt(u, a):
    if a.schwerpunkt and not any(a.schwerpunkt.lower() in s.lower() for s in als_liste(u.get("schwerpunkte"))):
        return False
    if a.phase and not any(a.phase.lower() in s.lower() for s in als_liste(u.get("phase"))):
        return False
    if a.spieler is not None and a.spieler < u.get("spieler_min", 0):
        return False
    if a.tw is not None and a.tw == 0 and u.get("torhueter") == "ja":
        return False
    if a.text and a.text.lower() not in yaml.safe_dump(u, allow_unicode=True).lower():
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schwerpunkt")
    ap.add_argument("--phase")
    ap.add_argument("--spieler", type=int, help="Anzahl Feldspieler")
    ap.add_argument("--tw", type=int, help="Anzahl Torhüter")
    ap.add_argument("--text")
    ap.add_argument("--details")
    a = ap.parse_args()

    if a.details:
        treffer = finde(a.details)
        if len(treffer) != 1:
            print("Treffer:", ", ".join(u["_kurz"] for u in treffer) or "keine")
            return
        print((ROOT / "uebungen" / treffer[0]["_kurz"] / "uebung.yaml").read_text())
        return

    hist = historie()
    treffer = [u for u in alle() if passt(u, a)]
    treffer.sort(key=lambda u: -(bewertung(u)[0] or 0))
    for u in treffer:
        s, n = bewertung(u)
        bew = f"{s:.1f}★ ({n}x)" if s else "neu"
        smax = u.get("spieler_max", "?")
        hinweis = ""
        if a.spieler is not None and isinstance(smax, int) and a.spieler > smax:
            hinweis = "  [mehr Spieler als max → Gruppen/Varianten nutzen]"
        daten = hist.get(u["_kurz"], [])
        geplant = f" | zuletzt geplant {max(daten).strftime('%d.%m.')} ({len(daten)}x)" if daten else ""
        print(f"{u['_kurz']:<32} {u['name']}")
        print(f"    {', '.join(als_liste(u.get('phase')))} | {', '.join(als_liste(u.get('schwerpunkte')))} | "
              f"{u.get('spieler_min')}-{smax} Sp. | TW {u.get('torhueter')} | {u.get('dauer_min')} min | "
              f"Int. {u.get('intensitaet')} | {bew}{geplant}{hinweis}")
        letzte = [f for f in u.get("feedback") or [] if f.get("notiz")]
        if letzte:
            print(f"    letzte Notiz ({letzte[-1]['datum']}): {letzte[-1]['notiz']}")
    print(f"\n{len(treffer)} Übung(en)")


if __name__ == "__main__":
    main()
