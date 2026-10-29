#!/usr/bin/env python3
"""Übungskatalog als PDF: alle (oder gefilterte) Übungskarten, je eine Seite, mit Inhaltsverzeichnis.

Für den Co-Trainer zum Nachschlagen oder Ausdrucken.

Aufruf:
  python3 scripts/katalog_pdf.py                       # alle -> katalog/uebungskatalog.pdf
  python3 scripts/katalog_pdf.py --phase Hauptteil     # nur Hauptteil-Übungen
  python3 scripts/katalog_pdf.py --schwerpunkt Pressing --ausgabe katalog/pressing.pdf
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate

sys.path.insert(0, str(Path(__file__).resolve().parent))
from datenbank import ROOT, alle, bewertung  # noqa: E402
from plan_pdf import P, fusszeile, tabelle, titel_neu, uebungsseite  # noqa: E402
from rahmen import TEILE, PHASE_ZU_TEIL  # noqa: E402

PHASEN = list(dict.fromkeys(PHASE_ZU_TEIL[t] for t in TEILE))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase")
    ap.add_argument("--schwerpunkt")
    ap.add_argument("--ausgabe", default="katalog/uebungskatalog.pdf")
    a = ap.parse_args()

    uebungen = [u for u in alle()
                if (not a.phase or any(a.phase.lower() in p.lower() for p in u.get("phase") or []))
                and (not a.schwerpunkt or any(a.schwerpunkt.lower() in s.lower() for s in u.get("schwerpunkte") or []))]
    if not uebungen:
        sys.exit("Keine Übungen für diesen Filter")
    # nach erster passender Phase im Trainingsablauf, dann Name
    uebungen.sort(key=lambda u: (min((PHASEN.index(p) for p in u.get("phase") or [] if p in PHASEN), default=99),
                                 u["name"]))

    ziel = ROOT / a.ausgabe
    ziel.parent.mkdir(parents=True, exist_ok=True)
    titel = "Übungskatalog" + (f" – {a.phase}" if a.phase else "") + (f" – {a.schwerpunkt}" if a.schwerpunkt else "")
    doc = SimpleDocTemplate(str(ziel), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=13 * mm, bottomMargin=15 * mm, title=titel, author="Trainerteam")
    breite = A4[0] - 30 * mm
    hoehe = A4[1] - 28 * mm - 12

    story = [P(titel, "titel"), P(f"Stand {dt.date.today().strftime('%d.%m.%Y')} · {len(uebungen)} Übungen", "unter")]
    daten = [[P(h, "kopf") for h in ("S.", "Übung", "Phase", "Spieler", "Bewertung")]]
    for i, u in enumerate(uebungen, 2):
        s, n = bewertung(u)
        neu = "neu" in str(u.get("quelle", "")).lower() and not u.get("feedback")
        daten.append([P(str(i), "zelle"), titel_neu(u["name"], neu, "zelle_b"), P(", ".join(u.get("phase") or []), "zelle"),
                      P(f"{u.get('spieler_min')}–{u.get('spieler_max')}", "zelle"),
                      P(f"{s:.1f} ★ ({n})" if s else "–", "zelle")])
    story.append(tabelle(daten, [10 * mm, breite - 108 * mm, 50 * mm, 20 * mm, 28 * mm]))

    for u in uebungen:
        e = {"uebung": u["_kurz"], "teil": ", ".join(u.get("phase") or []), "dauer_min": u.get("dauer_min"),
             "neu": "neu" in str(u.get("quelle", "")).lower() and not u.get("feedback")}
        kopf = f"{e['teil']}   ·   ca. {u.get('dauer_min')} min   ·   {u['_kurz']}"
        uebungsseite(0, "", "", e, u, story, breite, hoehe, kopf=kopf)
    doc.build(story, onFirstPage=fusszeile, onLaterPages=fusszeile)
    print(ziel.relative_to(ROOT))


if __name__ == "__main__":
    main()
