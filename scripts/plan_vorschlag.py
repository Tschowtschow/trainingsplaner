#!/usr/bin/env python3
"""Erstellt einen Planentwurf (YAML) nach dem Trainingsrahmen – Ausgangspunkt für jeden Trainingsplan.

Aufruf:
  python3 scripts/plan_vorschlag.py Donnerstag Umschalten 14 2
  python3 scripts/plan_vorschlag.py 2026-11-05 Umschalten 14 2 --nur-anzeigen

Wählt je Teil die am besten passende Übung (Phase, Spielerzahl, Torhüter, Schwerpunkt, Bewertung,
Abwechslung, Tagescharakter, Steigerung Hauptteil 1 -> 2), verteilt die Minuten nach Tag und füllt
`aufteilung.gruppen` und `aufteilung.torhueter` vor. `rollen` und `wechsel` stehen auf TODO und müssen
ergänzt werden – plan_pdf.py bricht ab, solange noch TODO im Plan steht.
Teile ohne passende Übung stehen auf `uebung: FEHLT` -> eigene Übung als Karte anlegen, `neu: true`.
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aufteilung import fuer_uebung, teams_text  # noqa: E402
from datenbank import ROOT, alle, bewertung, historie  # noqa: E402
from rahmen import BEGINN, MINUTEN, PHASE_ZU_TEIL, TAGE, TEILE, WOCHENTAGE  # noqa: E402

TECHNISCH = {"passspiel", "athletik", "koordination", "technik", "torabschluss", "ballkontrolle", "dribbling"}


def datum_und_tag(angabe: str, heute: dt.date | None = None) -> tuple[dt.date, str]:
    heute = heute or dt.date.today()
    if re.match(r"\d{4}-\d{2}-\d{2}$", angabe):
        d = dt.date.fromisoformat(angabe)
        return d, WOCHENTAGE[d.weekday()]
    tag = angabe.strip().capitalize()
    kurz = {"Di": "Dienstag", "Do": "Donnerstag"}
    tag = kurz.get(tag[:2], tag) if tag not in WOCHENTAGE else tag
    if tag not in WOCHENTAGE:
        sys.exit(f"Unbekannter Tag '{angabe}'")
    delta = (WOCHENTAGE.index(tag) - heute.weekday()) % 7
    return heute + dt.timedelta(days=delta), tag


def slug(text: str) -> str:
    t = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def ist_spielform(u) -> bool:
    """Übung mit Gegenspielern (Team B im Diagramm) gilt als spielerisch."""
    d = u.get("diagramm") or []
    for dia in d if isinstance(d, list) else [d]:
        if any(o.get("team") == "b" for o in dia.get("objekte") or []):
            return True
    return False


def ist_neu(u) -> bool:
    return "neu" in str(u.get("quelle", "")).lower() and not u.get("feedback")


def punkte(u, teil, plan, hist, vorher=None) -> float | None:
    """Bewertung einer Übung für einen Teil; None = passt nicht."""
    phase = PHASE_ZU_TEIL[teil]
    if phase not in (u.get("phase") or []):
        return None
    if plan["feldspieler"] < u.get("spieler_min", 0):
        return None
    if u.get("torhueter") == "ja" and plan["torhueter"] == 0:
        return None
    p = 0.0
    tags = {t.lower() for t in u.get("schwerpunkte") or []}
    if plan["schwerpunkt"].lower() in tags:
        p += 1.5 if teil in ("Lauf-ABC", "Erweitertes Aufwärmen") else 4
    schnitt, anzahl = bewertung(u)
    if schnitt is not None:
        p += (schnitt - 3) * 1.5
        if schnitt <= 2:
            p -= 5
    letzte = [d for d in hist.get(u["_kurz"], []) if d < plan["datum"]]
    if letzte:
        tage = (plan["datum"] - max(letzte)).days
        p -= 4 if tage <= 14 else 2 if tage <= 28 else 0
    spielform = ist_spielform(u)
    if plan["trainingstag"] == "Dienstag" and (tags & TECHNISCH or not spielform):
        p += 1
    if plan["trainingstag"] == "Donnerstag" and spielform:
        p += 1
    if vorher is not None:  # Hauptteil 2 soll auf Hauptteil 1 aufbauen
        if (u.get("intensitaet") or 0) >= (vorher.get("intensitaet") or 0):
            p += 1
        if tags & {t.lower() for t in vorher.get("schwerpunkte") or []}:
            p += 1
        if spielform and not ist_spielform(vorher):
            p += 1
    if ist_neu(u):
        p -= 0.5  # Erprobtes leicht bevorzugen
    return p


def tw_text(u, teil, plan) -> str:
    tw = plan["torhueter"]
    if tw == 0:
        return "keine Torhüter dabei"
    separat = plan["trainingstag"] == "Dienstag" and teil in ("Lauf-ABC", "Erweitertes Aufwärmen")
    if separat:
        return "separat mit eigenem TW-Programm"
    if teil == "Lauf-ABC":
        return "laufen mit"
    if u.get("torhueter") == "ja":
        return "TW im Tor" + ("; 2 TW wechseln nach der Hälfte der Zeit" if tw == 2 else "")
    if u.get("torhueter") == "optional":
        return "TW im Tor, falls die Übung mit Tor gespielt wird – sonst als Feldspieler"
    return "spielen als Feldspieler mit"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tag", help="Dienstag/Donnerstag (nächster) oder JJJJ-MM-TT")
    ap.add_argument("schwerpunkt")
    ap.add_argument("feldspieler", type=int)
    ap.add_argument("torhueter", type=int)
    ap.add_argument("--nur-anzeigen", action="store_true", help="nichts speichern")
    ap.add_argument("--heute", help=argparse.SUPPRESS)
    ap.add_argument("--ausgabe", help="Zieldatei statt plaene/<datum>_<schwerpunkt>.yaml")
    a = ap.parse_args()

    heute = dt.date.fromisoformat(a.heute) if a.heute else None
    datum, tag = datum_und_tag(a.tag, heute)
    plan = {"datum": datum, "trainingstag": tag, "schwerpunkt": a.schwerpunkt.strip().capitalize(),
            "feldspieler": a.feldspieler, "torhueter": a.torhueter}
    if tag not in TAGE:
        print(f"Hinweis: {tag} ist kein regulärer Trainingstag – Minuten wie Donnerstag", file=sys.stderr)
    minuten = MINUTEN.get(tag, MINUTEN["Donnerstag"])
    uebungen = list(alle())
    hist = historie()

    # Kandidaten je Teil (Hauptteil-2-Bonus hängt von Hauptteil 1 ab und wird in der Suche addiert)
    kandidaten = {}
    for teil in TEILE:
        liste = [(p, u) for u in uebungen if (p := punkte(u, teil, plan, hist)) is not None]
        kandidaten[teil] = sorted(liste, key=lambda x: -x[0])[:6]

    def aufbau_bonus(u, vorher):
        return (punkte(u, "Hauptteil 2", plan, hist, vorher) or 0) - (punkte(u, "Hauptteil 2", plan, hist) or 0)

    # Beste Gesamtkombination: jede Übung höchstens einmal, ein leerer Teil kostet 10 Punkte
    beste = (float("-inf"), [])

    def suche(i, summe, wahl):
        nonlocal beste
        if i == len(TEILE):
            if summe > beste[0]:
                beste = (summe, list(wahl))
            return
        teil = TEILE[i]
        benutzt = {u["_kurz"] for u in wahl if u}
        for p, u in kandidaten[teil]:
            if u["_kurz"] in benutzt:
                continue
            extra = aufbau_bonus(u, wahl[2]) if teil == "Hauptteil 2" and wahl[2] else 0
            suche(i + 1, summe + p + extra, wahl + [u])
        suche(i + 1, summe - 10, wahl + [None])

    suche(0, 0.0, [])
    gewaehlt = list(zip(TEILE, beste[1]))
    ausgabe = [f"{teil} ({mins} min): " + (", ".join(f"{u['_kurz']} {p:+.1f}" for p, u in kandidaten[teil][:3])
                                            or "KEINE PASSENDE ÜBUNG")
               for teil, mins in zip(TEILE, minuten)]

    zeilen = [
        f"# Entwurf von plan_vorschlag.py – TODOs ergänzen, dann plan_pdf.py",
        f"datum: {datum.isoformat()}",
        f"trainingstag: {tag}",
        f"schwerpunkt: {plan['schwerpunkt']}",
        f"feldspieler: {a.feldspieler}",
        f"torhueter: {a.torhueter}",
        f'beginn: "{BEGINN}"',
        'ziel: "TODO: ein Satz, worum es heute geht"',
        "teile:",
    ]
    for (teil, u), mins in zip(gewaehlt, minuten):
        zeilen.append(f"  - teil: {teil}")
        if u is None:
            zeilen += ["    uebung: FEHLT   # eigene Übung anlegen, neu: true", f"    dauer_min: {mins}",
                       "    neu: true", "    aufteilung:", '      gruppen: "TODO"', '      rollen: "TODO"',
                       '      wechsel: "TODO"', '      torhueter: "TODO"']
            continue
        if ist_spielform(u) and teil in ("Schlussteil 1", "Abschlussspiel"):
            gruppen, anzahl = teams_text(a.feldspieler), 1
        else:
            gruppen, anzahl = fuer_uebung(u, a.feldspieler)
        zeilen += [
            f"    uebung: {u['_kurz']}",
            f"    dauer_min: {mins}",
            f"    neu: {'true' if ist_neu(u) else 'false'}",
            "    aufteilung:",
            f'      gruppen: "{gruppen}"',
            f"      anzahl_gruppen: {anzahl}",
            '      rollen: "TODO"',
            '      wechsel: "TODO"',
            f'      torhueter: "{tw_text(u, teil, plan)}"',
        ]
    text = "\n".join(zeilen) + "\n"

    print("Kandidaten je Teil (Punkte, beste 3):")
    for z in ausgabe:
        print("  " + z)
    print("Auswahl: " + " | ".join(f"{t}: {u['_kurz'] if u else 'FEHLT'}" for t, u in gewaehlt))
    if a.nur_anzeigen:
        print("\n" + text)
        return
    ziel = Path(a.ausgabe).resolve() if a.ausgabe else ROOT / "plaene" / f"{datum.isoformat()}_{slug(plan['schwerpunkt'])}.yaml"
    if ziel.exists():
        sys.exit(f"{ziel.relative_to(ROOT)} existiert schon – nicht überschrieben")
    ziel.write_text(text)
    print(f"\nEntwurf: {ziel}")


if __name__ == "__main__":
    main()
