#!/usr/bin/env python3
"""Hängt Feedback an eine Übung an (Kommentare/Formatierung der YAML bleiben erhalten).

Die Übung darf ungefähr benannt sein ("Rondo 5v2", "rondo"). Bei mehreren Treffern
wird nichts gespeichert, sondern die Kandidaten werden aufgelistet (Exit-Code 3).

Aufruf:
  python3 scripts/feedback.py <übung> --bewertung 4 --notiz "Lief gut, Feld war zu klein"
  python3 scripts/feedback.py <kurzname> --bewertung 2 --datum 2026-10-28
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from datenbank import finde

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("uebung", help="Kurzname oder ungefährer Name")
    ap.add_argument("--bewertung", type=int, choices=range(1, 6))
    ap.add_argument("--notiz", default="")
    ap.add_argument("--datum", default=dt.date.today().isoformat())
    a = ap.parse_args()
    if a.bewertung is None and not a.notiz:
        ap.error("--bewertung und/oder --notiz angeben")

    treffer = finde(a.uebung)
    if not treffer:
        sys.exit(f"Keine Übung passt zu '{a.uebung}'")
    if len(treffer) > 1:
        print(f"Mehrdeutig: '{a.uebung}' passt zu")
        for u in treffer:
            print(f"  {u['_kurz']}  ({u['name']})")
        sys.exit(3)
    pfad = ROOT / "uebungen" / treffer[0]["_kurz"] / "uebung.yaml"
    y = YAML()
    y.preserve_quotes = True
    y.width = 120
    y.indent(mapping=2, sequence=4, offset=2)
    data = y.load(pfad.read_text())

    eintrag = CommentedMap()
    eintrag["datum"] = a.datum
    if a.bewertung is not None:
        eintrag["bewertung"] = a.bewertung
    if a.notiz:
        eintrag["notiz"] = a.notiz
    fb = data.get("feedback")
    if not isinstance(fb, list) or not fb:
        fb = CommentedSeq()
        data["feedback"] = fb
    fb.append(eintrag)
    with pfad.open("w") as f:
        y.dump(data, f)

    werte = [e["bewertung"] for e in fb if e.get("bewertung")]
    schnitt = f"{sum(werte) / len(werte):.1f}" if werte else "–"
    print(f"{data['name']} [{pfad.parent.name}]: Feedback gespeichert ({len(fb)} Einträge, Schnitt {schnitt}/5)")


if __name__ == "__main__":
    main()
