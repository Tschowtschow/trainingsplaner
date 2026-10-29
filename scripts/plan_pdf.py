#!/usr/bin/env python3
"""Erzeugt aus plaene/<datum>_<schwerpunkt>.yaml das PDF für den Co-Trainer.

Aufruf:
  python3 scripts/plan_pdf.py plaene/2026-11-03_torabschluss.yaml

Das PDF ist so gebaut, dass niemand ein Video schauen muss:
Seite 1 = Ablauf mit Uhrzeiten, Organisation und Materialliste,
danach je Übung Grafik, Aufbau, Ablauf, Regeln, Coachingpunkte, Varianten.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

import yaml
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, ListFlowable, ListItem, PageBreak,
                                Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parent.parent
UEBUNGEN = ROOT / "uebungen"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("DV", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B", str(FONT_DIR / "DejaVuSans-Bold.ttf")))

GRUEN = colors.HexColor("#1f6f2b")
HELL = colors.HexColor("#e8f3ea")
GRAU = colors.HexColor("#6b7280")

S = {
    "titel": ParagraphStyle("titel", fontName="DV-B", fontSize=20, leading=24, textColor=GRUEN, spaceAfter=4),
    "unter": ParagraphStyle("unter", fontName="DV", fontSize=11, leading=14, textColor=GRAU, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=15, leading=19, textColor=GRUEN, spaceBefore=4, spaceAfter=3),
    "h3": ParagraphStyle("h3", fontName="DV-B", fontSize=10.5, leading=13, spaceBefore=6, spaceAfter=2),
    "text": ParagraphStyle("text", fontName="DV", fontSize=9.5, leading=12.5, alignment=TA_LEFT),
    "klein": ParagraphStyle("klein", fontName="DV", fontSize=8.5, leading=11, textColor=GRAU),
    "zelle": ParagraphStyle("zelle", fontName="DV", fontSize=9, leading=11.5),
    "zelle_b": ParagraphStyle("zelle_b", fontName="DV-B", fontSize=9, leading=11.5),
    "kasten": ParagraphStyle("kasten", fontName="DV", fontSize=9.5, leading=12.5, backColor=HELL,
                             borderPadding=(5, 6, 5, 6), spaceBefore=6, spaceAfter=6),
}

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def P(t, stil="text"):
    return Paragraph(esc(t), S[stil])


def liste(punkte, nummeriert=False):
    punkte = punkte or []
    if isinstance(punkte, str):
        punkte = [punkte]
    items = [ListItem(P(p), leftIndent=12) for p in punkte]
    if nummeriert:
        return ListFlowable(items, bulletType="1", bulletFontName="DV-B", bulletFontSize=9, leftIndent=14)
    return ListFlowable(items, bulletType="bullet", start="•", bulletFontName="DV", bulletFontSize=9, leftIndent=12)


def grafik(svg: Path, max_b, max_h):
    d = svg2rlg(str(svg))
    if d is None:
        return P("(Grafik konnte nicht geladen werden)", "klein")
    f = min(max_b / d.width, max_h / d.height)
    d.width, d.height = d.width * f, d.height * f
    d.scale(f, f)
    return d


def lade_uebung(kurzname):
    pfad = UEBUNGEN / kurzname / "uebung.yaml"
    if not pfad.exists():
        sys.exit(f"Übung '{kurzname}' nicht gefunden ({pfad})")
    return yaml.safe_load(pfad.read_text())


def zeitplan(plan):
    start = dt.datetime.strptime(str(plan.get("beginn", "19:00")), "%H:%M")
    zeilen, t = [], start
    for e in plan["einheiten"]:
        zeilen.append((t.strftime("%H:%M"), e))
        t += dt.timedelta(minutes=int(e["dauer_min"]))
    return zeilen, t


def seite_uebersicht(plan, uebungen, story, breite):
    datum = dt.date.fromisoformat(str(plan["datum"]))
    story.append(P(f"Trainingsplan – {plan['schwerpunkt']}", "titel"))
    story.append(P(f"{plan.get('trainingstag', WOCHENTAGE[datum.weekday()])}, {datum.strftime('%d.%m.%Y')}"
                   f"  ·  {plan.get('mannschaft', 'Herren')}", "unter"))

    zeilen, ende = zeitplan(plan)
    gesamt = sum(int(e["dauer_min"]) for e in plan["einheiten"])
    info = [
        [P("Schwerpunkt", "zelle_b"), P(plan["schwerpunkt"], "zelle"),
         P("Spieler", "zelle_b"), P(f"{plan['feldspieler']} Feldspieler + {plan['torhueter']} TW", "zelle")],
        [P("Zeit", "zelle_b"), P(f"{zeilen[0][0]} – {ende.strftime('%H:%M')} Uhr ({gesamt} min)", "zelle"),
         P("Ort", "zelle_b"), P(plan.get("ort", "–"), "zelle")],
    ]
    t = Table(info, colWidths=[31 * mm, breite / 2 - 31 * mm, 20 * mm, breite / 2 - 20 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HELL), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BOX", (0, 0), (-1, -1), 0.5, GRUEN), ("TOPPADDING", (0, 0), (-1, -1), 4)]))
    story += [t, Spacer(1, 6)]

    if plan.get("ziel"):
        story.append(P(f"Ziel der Einheit: {plan['ziel']}", "kasten"))

    story.append(P("Ablauf", "h2"))
    kopf = [P(h, "zelle_b") for h in ("Uhrzeit", "Phase", "Übung", "Min", "Organisation heute")]
    daten = [kopf]
    for nr, (uhr, e) in enumerate(zeilen, 1):
        u = uebungen[e["uebung"]] if e.get("uebung") else {"name": e.get("titel", "Pause")}
        daten.append([P(uhr, "zelle"), P(e["phase"], "zelle"), P(f"{nr}. {u['name']}", "zelle_b"),
                      P(str(e["dauer_min"]), "zelle"), P(e.get("organisation", ""), "zelle")])
    t = Table(daten, colWidths=[19 * mm, 30 * mm, 50 * mm, 11 * mm, breite - 110 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRUEN), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HELL]), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c7d7ca")),
    ]))
    # Kopfzeile weiß: Paragraph-Farbe überschreiben
    for zelle in daten[0]:
        zelle.style = ParagraphStyle("kopf", parent=S["zelle_b"], textColor=colors.white)
    story += [t, Spacer(1, 4)]

    material = []
    for e in plan["einheiten"]:
        if e.get("uebung"):
            for m in uebungen[e["uebung"]].get("material") or []:
                if m not in material:
                    material.append(m)
    material += [m for m in plan.get("material_zusaetzlich", []) or [] if m not in material]
    if material:
        story.append(P("Material (gesamt)", "h3"))
        story.append(P(" · ".join(material)))
    if plan.get("hinweise"):
        story.append(P("Hinweise", "h3"))
        story.append(liste(plan["hinweise"]))


def seite_uebung(nr, uhr, e, u, story, breite):
    story.append(P(f"{nr}. {u['name']}", "h2"))
    meta = (f"{uhr} Uhr · {e['phase']} · {e['dauer_min']} min · Intensität {u.get('intensitaet', '–')}/5 · "
            f"Feld: {u.get('feldgroesse', '–')}")
    story.append(P(meta, "klein"))
    if e.get("organisation"):
        story.append(P(f"Heute: {e['organisation']}", "kasten"))

    svg = UEBUNGEN / e["uebung"] / "diagramm.svg"
    if svg.exists():
        story.append(grafik(svg, breite, 125 * mm))
        story.append(Spacer(1, 4))

    links = [P("Ablauf", "h3"), liste(u.get("ablauf"), nummeriert=True)]
    if u.get("regeln"):
        links += [P("Regeln", "h3"), liste(u["regeln"])]
    rechts = [P("Coachingpunkte", "h3"), liste(u.get("coachingpunkte"))]
    var = u.get("varianten") or {}
    if var.get("leichter"):
        rechts += [P("Leichter", "h3"), liste(var["leichter"])]
    if var.get("schwerer"):
        rechts += [P("Schwerer", "h3"), liste(var["schwerer"])]
    t = Table([[links, rechts]], colWidths=[breite * 0.55, breite * 0.45])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (0, -1), 10)]))
    story.append(t)

    unten = []
    if u.get("material"):
        unten.append(P(f"Material: {', '.join(u['material'])}", "klein"))
    if e.get("hinweis"):
        unten.append(P(f"Hinweis: {e['hinweis']}", "kasten"))
    fb = [f for f in u.get("feedback") or [] if f.get("notiz")]
    if fb:
        letzte = fb[-1]
        unten.append(P(f"Erfahrung ({letzte['datum']}): {letzte['notiz']}", "klein"))
    if unten:
        story.append(KeepTogether(unten))


def fusszeile(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5)
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
    uebungen = {e["uebung"]: lade_uebung(e["uebung"]) for e in plan["einheiten"] if e.get("uebung")}

    ziel = pfad.with_suffix(".pdf")
    doc = SimpleDocTemplate(str(ziel), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=13 * mm, bottomMargin=15 * mm,
                            title=f"Training {plan['datum']} – {plan['schwerpunkt']}", author="Trainerteam")
    breite = A4[0] - 30 * mm
    story = []
    seite_uebersicht(plan, uebungen, story, breite)
    zeilen, _ = zeitplan(plan)
    nr = 0
    for uhr, e in zeilen:
        nr += 1
        if e.get("uebung"):
            story.append(PageBreak())
            seite_uebung(nr, uhr, e, uebungen[e["uebung"]], story, breite)
    doc.build(story, onFirstPage=fusszeile, onLaterPages=fusszeile)
    print(ziel.relative_to(ROOT))


if __name__ == "__main__":
    main()
