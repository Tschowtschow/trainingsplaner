#!/usr/bin/env python3
"""Schreibt UEBUNGEN.md: Übersicht aller Übungen (nach Phase) und aller Pläne – lesbar auf GitHub am Handy.

Aufruf:
  python3 scripts/uebersicht.py           # UEBUNGEN.md neu schreiben
  python3 scripts/uebersicht.py --check   # Exit 1, wenn UEBUNGEN.md veraltet ist (für CI)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from datenbank import ROOT, alle, bewertung, historie, plaene  # noqa: E402
from rahmen import PHASE_ZU_TEIL, TEILE  # noqa: E402

PHASEN = list(dict.fromkeys(PHASE_ZU_TEIL[t] for t in TEILE))


def zelle(t) -> str:
    return str(t).replace("|", "/").replace("\n", " ")


def erzeugen() -> str:
    uebungen = list(alle())
    hist = historie()
    z = ["# Übungen und Pläne", "",
         "_Automatisch erzeugt von `scripts/uebersicht.py` – nicht von Hand bearbeiten._", "",
         f"**{len(uebungen)} Übungen** · Bewertung = Schnitt aus Feedback (Anzahl) · NEU = eigene, ungetestete Übung", ""]
    for phase in PHASEN:
        liste = sorted((u for u in uebungen if phase in (u.get("phase") or [])), key=lambda u: u["name"])
        z += [f"## {phase} ({len(liste)})", ""]
        if not liste:
            z += ["_noch keine_", ""]
            continue
        z += ["| Übung | Schwerpunkte | Spieler | TW | Min | Int. | Bewertung | zuletzt geplant |",
              "|---|---|---|---|---|---|---|---|"]
        for u in liste:
            s, n = bewertung(u)
            neu = " **NEU**" if "neu" in str(u.get("quelle", "")).lower() and not u.get("feedback") else ""
            daten = hist.get(u["_kurz"], [])
            z.append(f"| [{zelle(u['name'])}](uebungen/{u['_kurz']}/uebung.yaml){neu} "
                     f"([Grafik](uebungen/{u['_kurz']}/diagramm.svg)) | {zelle(', '.join(u.get('schwerpunkte') or []))} | "
                     f"{u.get('spieler_min')}–{u.get('spieler_max')} | {u.get('torhueter')} | {u.get('dauer_min')} | "
                     f"{u.get('intensitaet')} | {f'{s:.1f} ({n})' if s else '–'} | "
                     f"{max(daten).strftime('%d.%m.%Y') if daten else '–'} |")
        z.append("")
    z += ["## Pläne", ""]
    alle_plaene = sorted(plaene(mit_tests=True), key=lambda p: str(p["datum"]), reverse=True)
    if not alle_plaene:
        z += ["_noch keine_", ""]
    for p in alle_plaene:
        pdf = Path(p["_datei"]).with_suffix(".pdf").name
        z.append(f"- {p['datum']} ({p.get('trainingstag', '')}) – **{zelle(p['schwerpunkt'])}** – "
                 f"{p['feldspieler']}+{p['torhueter']} – [PDF](plaene/{pdf})" + (" _(Testplan)_" if p.get("test") else ""))
    z += ["", "Übungskatalog (alle Karten als PDF): [katalog/uebungskatalog.pdf](katalog/uebungskatalog.pdf)", ""]
    return "\n".join(z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    ziel = ROOT / "UEBUNGEN.md"
    text = erzeugen()
    if a.check:
        if not ziel.exists() or ziel.read_text() != text:
            sys.exit("UEBUNGEN.md ist veraltet – python3 scripts/uebersicht.py ausführen")
        print("UEBUNGEN.md aktuell")
        return
    ziel.write_text(text)
    print(ziel.relative_to(ROOT))


if __name__ == "__main__":
    main()
