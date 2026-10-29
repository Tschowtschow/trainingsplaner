#!/usr/bin/env python3
"""Prüft alle (oder die genannten) Übungskarten auf Vollständigkeit und gültige Werte.

Aufruf:
  python3 scripts/pruefen.py            # alle
  python3 scripts/pruefen.py <kurzname>
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PHASEN = {"Lauf-ABC", "Erweitertes Aufwärmen", "Hauptteil", "Schlussteil", "Abschlussspiel"}
PFLICHT = ["name", "schwerpunkte", "phase", "spieler_min", "spieler_max", "torhueter", "feldgroesse",
           "material", "dauer_min", "intensitaet", "ablauf", "regeln", "coachingpunkte", "varianten",
           "quelle", "feedback", "diagramm"]
OBJEKTE = {"spieler", "torhueter", "huetchen", "stange", "dummy", "ring", "ball", "balldepot",
           "leiter", "tor", "minitor", "text"}
PFEILE = {"pass", "lauf", "dribbling", "schuss", "flanke"}


def pruefe(p: Path):
    fehler = []
    try:
        u = yaml.safe_load(p.read_text())
    except yaml.YAMLError as e:
        return [f"YAML kaputt: {e}"]
    for k in PFLICHT:
        if k not in u:
            fehler.append(f"Feld fehlt: {k}")
    for ph in u.get("phase") or []:
        if ph not in PHASEN:
            fehler.append(f"unbekannte Phase '{ph}' (erlaubt: {', '.join(sorted(PHASEN))})")
    if u.get("torhueter") not in ("ja", "nein", "optional"):
        fehler.append("torhueter muss ja/nein/optional sein")
    if not isinstance(u.get("intensitaet"), int) or not 1 <= u["intensitaet"] <= 5:
        fehler.append("intensitaet muss 1-5 sein")
    if isinstance(u.get("spieler_min"), int) and isinstance(u.get("spieler_max"), int) \
            and u["spieler_min"] > u["spieler_max"]:
        fehler.append("spieler_min > spieler_max")
    for k in ("ablauf", "regeln", "coachingpunkte", "material"):
        for eintrag in u.get(k) or []:
            if not isinstance(eintrag, str):
                fehler.append(f"{k}: Eintrag ist kein Text (Doppelpunkt? -> in Anführungszeichen setzen): {eintrag}")
    for f in u.get("feedback") or []:
        if f.get("bewertung") is not None and f["bewertung"] not in range(1, 6):
            fehler.append(f"Feedback-Bewertung {f['bewertung']} nicht 1-5")
    d = u.get("diagramm") or {}
    if d:
        if not {"laenge", "breite"} <= set(d.get("feld", {})):
            fehler.append("diagramm.feld braucht laenge und breite")
        for o in d.get("objekte") or []:
            if o.get("typ") not in OBJEKTE:
                fehler.append(f"unbekannter Objekttyp {o.get('typ')}")
            if "x" not in o or "y" not in o:
                fehler.append(f"Objekt ohne x/y: {o}")
        for pf in d.get("pfeile") or []:
            if pf.get("typ", "pass") not in PFEILE:
                fehler.append(f"unbekannter Pfeiltyp {pf.get('typ')}")
    if not (p.parent / "diagramm.svg").exists():
        fehler.append("diagramm.svg fehlt (scripts/diagramm.py laufen lassen)")
    return fehler


def main():
    namen = sys.argv[1:]
    pfade = [ROOT / "uebungen" / n / "uebung.yaml" for n in namen] if namen \
        else sorted((ROOT / "uebungen").glob("*/uebung.yaml"))
    ok = True
    for p in pfade:
        f = pruefe(p)
        if f:
            ok = False
            print(f"✗ {p.parent.name}")
            for x in f:
                print(f"    - {x}")
        else:
            print(f"✓ {p.parent.name}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
