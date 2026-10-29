#!/usr/bin/env python3
"""Erzeugt aus plaene/<datum>_<schwerpunkt>.yaml das PDF für den Co-Trainer.

Aufruf:
  python3 scripts/plan_pdf.py plaene/2026-11-05_umschalten.yaml

Prüft den Plan gegen den Trainingsrahmen (6 Teile, 120 min, Lauf-ABC 10, Abschlussspiel >= 20)
und bricht bei Verstößen ab. Das PDF ist so gebaut, dass niemand ein Video schauen muss:
Deckblatt mit Zeitplan aller 6 Teile, danach je Übung eine Seite.
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepInFrame, KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)
from svglib.svglib import svg2rlg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from datenbank import ROOT, UEBUNGEN  # noqa: E402
from diagramm import diagramme, svg_namen  # noqa: E402

from datenbank import historie  # noqa: E402
from rahmen import (BEGINN, GESAMT_MIN, MATERIAL, MATERIAL_KATEGORIEN, PHASE_ZU_TEIL, PLATZ,  # noqa: E402
                    TAGE, TEILE, WOCHENTAGE)

# ---------- Stil ----------
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("DV", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B", str(FONT_DIR / "DejaVuSans-Bold.ttf")))

GRUEN = colors.HexColor("#1f6f2b")
HELL = colors.HexColor("#e8f3ea")
GRAU = colors.HexColor("#4b5563")

S = {
    "titel": ParagraphStyle("titel", fontName="DV-B", fontSize=22, leading=27, textColor=GRUEN, spaceAfter=2),
    "unter": ParagraphStyle("unter", fontName="DV", fontSize=12, leading=15, textColor=GRAU, spaceAfter=8),
    "h1": ParagraphStyle("h1", fontName="DV-B", fontSize=17, leading=21, textColor=GRUEN, spaceAfter=2),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=13, leading=16, textColor=GRUEN, spaceBefore=8, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="DV-B", fontSize=11, leading=14, spaceBefore=6, spaceAfter=2),
    "text": ParagraphStyle("text", fontName="DV", fontSize=10.5, leading=13.5),
    "klein": ParagraphStyle("klein", fontName="DV", fontSize=9.5, leading=12, textColor=GRAU),
    "zelle": ParagraphStyle("zelle", fontName="DV", fontSize=10, leading=12.5),
    "zelle_b": ParagraphStyle("zelle_b", fontName="DV-B", fontSize=10, leading=12.5),
    "kopf": ParagraphStyle("kopf", fontName="DV-B", fontSize=10, leading=12.5, textColor=colors.white),
    "balken": ParagraphStyle("balken", fontName="DV-B", fontSize=11, leading=14, textColor=colors.white,
                             backColor=GRUEN, borderPadding=(4, 6, 4, 6), spaceAfter=8),
}


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def P(t, stil="text"):
    return Paragraph(esc(t), S[stil])


def titel_neu(name, neu, stil="h1"):
    marke = ' <font color="#c2410c">[NEU]</font>' if neu else ""
    return Paragraph(esc(name) + marke, S[stil])


def liste(punkte, nummeriert=False):
    punkte = punkte if isinstance(punkte, list) else [punkte] if punkte else []
    items = [ListItem(P(p), leftIndent=14) for p in punkte]
    if nummeriert:
        return ListFlowable(items, bulletType="1", bulletFontName="DV-B", bulletFontSize=10, leftIndent=16)
    return ListFlowable(items, bulletType="bullet", start="•", bulletFontName="DV", bulletFontSize=10, leftIndent=14)


def grafik(svg: Path, max_b, max_h):
    d = svg2rlg(str(svg))
    f = min(max_b / d.width, max_h / d.height)
    d.width, d.height = d.width * f, d.height * f
    d.scale(f, f)
    d.hAlign = "CENTER"
    return d


def tabelle(daten, breiten, kopf=True):
    t = Table(daten, colWidths=breiten, repeatRows=1 if kopf else 0)
    stil = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c7d7ca")),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if kopf:
        stil += [("BACKGROUND", (0, 0), (-1, 0), GRUEN), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HELL])]
    else:
        stil += [("BACKGROUND", (0, 0), (0, -1), HELL)]
    t.setStyle(TableStyle(stil))
    return t


# ---------- Prüfung gegen den Trainingsrahmen ----------
def pruefe(plan, uebungen):
    fehler, warnungen = [], []
    teile = [e.get("teil") for e in plan["teile"]]
    if teile != TEILE:
        fehler.append(f"Teile müssen genau sein: {', '.join(TEILE)} (ist: {', '.join(map(str, teile))})")
    summe = sum(int(e["dauer_min"]) for e in plan["teile"])
    if summe != GESAMT_MIN:
        fehler.append(f"Summe der Minuten ist {summe}, muss {GESAMT_MIN} sein")
    for e in plan["teile"]:
        if e.get("teil") == "Lauf-ABC" and int(e["dauer_min"]) != 10:
            fehler.append("Lauf-ABC muss 10 min dauern")
        if e.get("teil") == "Abschlussspiel" and int(e["dauer_min"]) < 20:
            fehler.append("Abschlussspiel muss mindestens 20 min dauern")
        if not e.get("aufteilung"):
            fehler.append(f"{e.get('teil')}: Aufteilung für die Spielerzahl fehlt")
        u = uebungen[e["uebung"]]
        phase = PHASE_ZU_TEIL.get(e.get("teil"))
        if phase and phase not in (u.get("phase") or []):
            warnungen.append(f"{e['uebung']}: Phase '{phase}' steht nicht in der Karte")
        for m in u.get("material") or []:
            if not any(w in m.lower() for w in MATERIAL):
                warnungen.append(f"{e['uebung']}: Material '{m}' gehört nicht zum Vereinsmaterial")
        if plan["feldspieler"] < u.get("spieler_min", 0):
            warnungen.append(f"{e['uebung']}: braucht mind. {u['spieler_min']} Feldspieler")
    if plan.get("trainingstag") not in TAGE:
        warnungen.append(f"Trainingstag '{plan.get('trainingstag')}' ist kein regulärer Tag (Di/Do)")
    if "TODO" in yaml.safe_dump(plan, allow_unicode=True):
        fehler.append("Im Plan stehen noch TODOs (ziel/rollen/wechsel ...) – erst ausfüllen")
    datum = dt.date.fromisoformat(str(plan["datum"]))
    for kurz, daten in historie().items():
        frueher = [d for d in daten if 0 < (datum - d).days <= 14]
        if kurz in uebungen and frueher:
            warnungen.append(f"{kurz} war schon am {max(frueher).strftime('%d.%m.')} dran – Abwechslung?")
    return fehler, warnungen


# ---------- Material-Checkliste ----------
def menge(text: str, gruppen: int) -> int | None:
    """'8 Hütchen' -> 8, '2-3 Bälle pro Gruppe' bei 2 Gruppen -> 6, 'Leibchen' -> None."""
    zahlen = re.match(r"\s*(\d+)(?:\s*-\s*(\d+))?", text)
    if not zahlen:
        return None
    n = int(zahlen.group(2) or zahlen.group(1))
    return n * gruppen if "pro gruppe" in text.lower() else n


def checkliste(plan, uebungen):
    """Kategorie -> (Mindestmenge oder None, [Teil-Nummern], [Originaltexte]).

    Mindestmenge = größter Bedarf eines einzelnen Teils (Aufbauten werden nacheinander genutzt)."""
    ergebnis = {}
    for nr, e in enumerate(plan["teile"], 1):
        gruppen = int((e.get("aufteilung") or {}).get("anzahl_gruppen") or 1)
        for m in uebungen[e["uebung"]].get("material") or []:
            for kat, worte in MATERIAL_KATEGORIEN.items():
                if any(w in m.lower() for w in worte):
                    bedarf, teile, texte = ergebnis.setdefault(kat, [None, [], []])
                    n = menge(m, gruppen)
                    if n is not None and (bedarf is None or n > bedarf):
                        ergebnis[kat][0] = n
                    if nr not in teile:
                        teile.append(nr)
                    if m not in texte:
                        texte.append(m)
                    break
    return ergebnis


# ---------- Seiten ----------
def zeitplan(plan):
    t = dt.datetime.strptime(str(plan.get("beginn", BEGINN)), "%H:%M")
    zeilen = []
    for e in plan["teile"]:
        ende = t + dt.timedelta(minutes=int(e["dauer_min"]))
        zeilen.append((t.strftime("%H:%M"), ende.strftime("%H:%M"), e))
        t = ende
    return zeilen


def deckblatt(plan, uebungen, story, breite):
    datum = dt.date.fromisoformat(str(plan["datum"]))
    tag = plan.get("trainingstag", WOCHENTAGE[datum.weekday()])
    charakter, tw_regel = TAGE.get(tag, ("", ""))
    zeilen = zeitplan(plan)

    story.append(P(f"Training {tag}, {datum.strftime('%d.%m.%Y')}", "titel"))
    story.append(P(f"Schwerpunkt: {plan['schwerpunkt']}", "unter"))

    info = [
        ("Datum", f"{tag}, {datum.strftime('%d.%m.%Y')}" + (f" – {charakter}" if charakter else "")),
        ("Schwerpunkt", plan["schwerpunkt"]),
        ("Spieler", f"{plan['feldspieler']} Feldspieler + {plan['torhueter']} Torhüter"),
        ("Zeit", f"{zeilen[0][0]} – {zeilen[-1][1]} Uhr ({GESAMT_MIN} min)"),
        ("Platz", plan.get("platz", PLATZ)),
    ]
    if plan["torhueter"] and tw_regel:
        info.append(("Torhüter", tw_regel))
    if plan.get("ziel"):
        info.append(("Ziel", plan["ziel"]))
    story.append(tabelle([[P(k, "zelle_b"), P(v, "zelle")] for k, v in info],
                         [34 * mm, breite - 34 * mm], kopf=False))

    story.append(P("Zeitplan", "h2"))
    daten = [[P(h, "kopf") for h in ("Zeit", "Teil", "Übung", "Min", "Int.")]]
    for nr, (von, bis, e) in enumerate(zeilen, 1):
        u = uebungen[e["uebung"]]
        daten.append([P(f"{von}–{bis}", "zelle"), P(f"{nr}. {e['teil']}", "zelle_b"),
                      titel_neu(u["name"], e.get("neu"), "zelle"), P(str(e["dauer_min"]), "zelle"),
                      P("●" * int(u.get("intensitaet") or 0), "zelle")])
    story.append(tabelle(daten, [29 * mm, 41 * mm, breite - 108 * mm, 12 * mm, 26 * mm]))
    story.append(P("Int. = Intensität 1–5", "klein"))
    if any(e.get("neu") for e in plan["teile"]):
        story.append(Spacer(1, 3))
        story.append(P("[NEU] = eigene Übung, noch nicht im Training getestet.", "klein"))

    story.append(P("Material-Checkliste", "h2"))
    daten = [[P(h, "kopf") for h in ("", "Material", "mind.", "für Teil", "Details")]]
    for kat, (bedarf, teile, texte) in checkliste(plan, uebungen).items():
        daten.append([P("☐", "zelle_b"), P(kat, "zelle_b"), P(str(bedarf) if bedarf else "✓", "zelle"),
                      P(", ".join(map(str, teile)), "zelle"), P(" · ".join(texte), "klein")])
    story.append(tabelle(daten, [8 * mm, 36 * mm, 15 * mm, 20 * mm, breite - 79 * mm]))
    if plan.get("hinweise"):
        story.append(P("Hinweise", "h2"))
        story.append(liste(plan["hinweise"]))


def uebungsseite(nr, von, bis, e, u, haupt_story, breite, hoehe, kopf=None):
    """Eine Seite pro Übung – wird zu lang, wird alles gleichmäßig verkleinert.

    Ohne `aufteilung` (Katalog) stehen Spielerzahl und die Varianten für andere Spielerzahlen drin."""
    story = []
    story.append(P(kopf or f"{nr}. {e['teil']}   ·   {von}–{bis} Uhr   ·   {e['dauer_min']} min", "balken"))
    story.append(titel_neu(u["name"], e.get("neu")))
    story.append(P(f"Intensität {u.get('intensitaet', '–')}/5   ·   {', '.join(u.get('schwerpunkte') or [])}", "klein"))
    story.append(Spacer(1, 5))

    ordner = UEBUNGEN / e["uebung"]
    svgs = [ordner / n for n in svg_namen(len(diagramme(u))) if (ordner / n).exists()]
    if len(svgs) == 1:
        story.append(grafik(svgs[0], breite, 110 * mm))
    elif svgs:  # mehrere Phasen: je zwei nebeneinander
        b = (breite - 4 * mm) / 2
        bilder = [grafik(s, b, 80 * mm) for s in svgs]
        reihen = [bilder[i:i + 2] + [""] * (2 - len(bilder[i:i + 2])) for i in range(0, len(bilder), 2)]
        t = Table(reihen, colWidths=[b + 2 * mm, b + 2 * mm])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        story.append(t)

    a = e.get("aufteilung") or {}
    story.append(P("Aufbau und Aufteilung heute" if a else "Aufbau", "h3"))
    aufbau = [[P("Feld", "zelle_b"), P(u.get("feldgroesse", "–"), "zelle")],
              [P("Material", "zelle_b"), P(", ".join(u.get("material") or []), "zelle")],
              [P("Dauer", "zelle_b"), P(f"{e['dauer_min']} min", "zelle")]]
    if not a:
        aufbau.append([P("Spieler", "zelle_b"),
                       P(f"{u.get('spieler_min')}–{u.get('spieler_max')} Feldspieler, Torhüter: {u.get('torhueter')}", "zelle")])
        for v in (u.get("varianten") or {}).get("spielerzahl") or []:
            aufbau.append([P("Spielerzahl", "zelle_b"), P(v, "zelle")])
    for key, label in (("gruppen", "Teams / Gruppen"), ("rollen", "Rollen"), ("wechsel", "Wechsel"),
                       ("torhueter", "Torhüter")):
        if a.get(key):
            aufbau.append([P(label, "zelle_b"), P(a[key], "zelle")])
    story.append(tabelle(aufbau, [32 * mm, breite - 32 * mm], kopf=False))

    story += [P("Ablauf", "h3"), liste(u.get("ablauf"), nummeriert=True)]
    if u.get("regeln"):
        story += [P("Regeln", "h3"), liste(u["regeln"])]
    story += [P("Coachingpunkte", "h3"), liste(u.get("coachingpunkte"))]
    var = u.get("varianten") or {}
    zeilen = []
    if var.get("leichter"):
        zeilen.append(f"Leichter: {'; '.join(var['leichter'])}")
    if var.get("schwerer"):
        zeilen.append(f"Schwerer: {'; '.join(var['schwerer'])}")
    if zeilen:
        story += [P("Varianten", "h3"), liste(zeilen)]

    unten = []
    if e.get("hinweis"):
        unten.append(P(f"Hinweis: {e['hinweis']}", "zelle_b"))
    notizen = [f for f in u.get("feedback") or [] if f.get("notiz")]
    if notizen:
        unten.append(P(f"Erfahrung vom {notizen[-1]['datum']}: {notizen[-1]['notiz']}", "klein"))
    if unten:
        story.append(Spacer(1, 6))
        story.append(KeepTogether(unten))
    haupt_story.append(PageBreak())
    haupt_story.append(KeepInFrame(breite, hoehe, story, mode="shrink"))


def platzkarte(plan, uebungen, haupt_story, breite, hoehe):
    """Letzte Seite: alle 6 Teile kompakt auf einem Blatt – zum Mitnehmen auf den Platz."""
    datum = dt.date.fromisoformat(str(plan["datum"]))
    story = [P(f"Platzkarte – {plan.get('trainingstag', '')} {datum.strftime('%d.%m.')} – {plan['schwerpunkt']} – "
               f"{plan['feldspieler']}+{plan['torhueter']}", "balken")]
    b = (breite - 6 * mm) / 2
    zellen = []
    for nr, (von, bis, e) in enumerate(zeitplan(plan), 1):
        u = uebungen[e["uebung"]]
        inhalt = [Paragraph(f"<b>{nr}. {esc(e['teil'])}</b>  {von}–{bis} ({e['dauer_min']}')", S["zelle"]),
                  titel_neu(u["name"], e.get("neu"), "zelle_b")]
        svg = UEBUNGEN / e["uebung"] / "diagramm.svg"
        if svg.exists():
            inhalt.append(grafik(svg, b - 4 * mm, 52 * mm))
        a = e.get("aufteilung") or {}
        if a.get("gruppen"):
            inhalt.append(P(f"Gruppen: {a['gruppen']}", "klein"))
        for c in (u.get("coachingpunkte") or [])[:2]:
            inhalt.append(P(f"• {c}", "klein"))
        zellen.append(inhalt)
    reihen = [zellen[i:i + 2] for i in range(0, len(zellen), 2)]
    t = Table(reihen, colWidths=[b + 3 * mm, b + 3 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.6, GRUEN),
                           ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c7d7ca"))]))
    story.append(t)
    haupt_story.append(PageBreak())
    haupt_story.append(KeepInFrame(breite, hoehe, story, mode="shrink"))


def fusszeile(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 8)
    canvas.setFillColor(GRAU)
    canvas.drawString(15 * mm, 9 * mm, doc.title)
    canvas.drawRightString(A4[0] - 15 * mm, 9 * mm, f"Seite {doc.page}")
    canvas.restoreState()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    a = ap.parse_args()
    pfad = Path(a.plan).resolve()
    plan = yaml.safe_load(pfad.read_text())

    uebungen = {}
    for e in plan["teile"]:
        p = UEBUNGEN / str(e.get("uebung")) / "uebung.yaml"
        if not p.exists():
            sys.exit(f"Übung '{e.get('uebung')}' ({e.get('teil')}) nicht in der Datenbank")
        uebungen[e["uebung"]] = yaml.safe_load(p.read_text())

    fehler, warnungen = pruefe(plan, uebungen)
    for w in warnungen:
        print(f"Warnung: {w}", file=sys.stderr)
    if fehler:
        for f in fehler:
            print(f"FEHLER: {f}", file=sys.stderr)
        sys.exit(1)

    ziel = pfad.with_suffix(".pdf")
    doc = SimpleDocTemplate(str(ziel), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=13 * mm, bottomMargin=15 * mm,
                            title=f"Training {plan['datum']} – {plan['schwerpunkt']}", author="Trainerteam")
    breite = A4[0] - 30 * mm
    hoehe = A4[1] - 28 * mm - 12  # Rahmenhöhe abzüglich Innenabstand
    story = []
    deckblatt(plan, uebungen, story, breite)
    for nr, (von, bis, e) in enumerate(zeitplan(plan), 1):
        uebungsseite(nr, von, bis, e, uebungen[e["uebung"]], story, breite, hoehe)
    platzkarte(plan, uebungen, story, breite, hoehe)
    doc.build(story, onFirstPage=fusszeile, onLaterPages=fusszeile)
    print(ziel.relative_to(ROOT) if ziel.is_relative_to(ROOT) else ziel)


if __name__ == "__main__":
    main()
