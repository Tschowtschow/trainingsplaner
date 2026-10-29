#!/usr/bin/env python3
"""Erzeugt diagramm.svg aus dem Block `diagramm:` einer uebung.yaml.

Koordinaten in Metern, Ursprung (0,0) = linke obere Feldecke,
x nach rechts (Feldlänge), y nach unten (Feldbreite).
Vollständiges Format: siehe CLAUDE.md, Abschnitt "Diagramm-Format".

Aufruf:
  python3 scripts/diagramm.py <kurzname> [<kurzname> ...]
  python3 scripts/diagramm.py --alle
  python3 scripts/diagramm.py <kurzname> --png   # zusätzlich arbeit/vorschau/<kurzname>_diagramm*.png

Mehrere Phasen einer Übung: `diagramm:` als Liste -> diagramm.svg, diagramm-2.svg, ...
"""
import argparse
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
UEBUNGEN = ROOT / "uebungen"

BREITE_PX = 900          # Zielbreite der Grafik
RAND_M = 2.5             # Rand um das Feld (für Tore, Labels)

FARBEN = {
    "rot": "#d62828", "blau": "#1d4ed8", "gelb": "#facc15", "gruen": "#16a34a",
    "orange": "#f97316", "weiss": "#ffffff", "schwarz": "#111827", "lila": "#7c3aed",
    "grau": "#9ca3af", "pink": "#db2777", "tuerkis": "#0891b2",
}
TEAMS = {  # team -> (Füllung, Textfarbe, Legendentext)
    "a": ("rot", "weiss", "Team A"),
    "b": ("blau", "weiss", "Team B"),
    "c": ("lila", "weiss", "Team C"),
    "neutral": ("gelb", "schwarz", "Neutral / Joker"),
    "tw": ("gruen", "weiss", "Torhüter"),
    "trainer": ("schwarz", "weiss", "Trainer"),
}
PFEILE = {  # typ -> (Farbe, Strichbreite m, Strichmuster, Legendentext)
    "pass": ("schwarz", 0.18, None, "Pass"),
    "lauf": ("schwarz", 0.14, "dash", "Laufweg ohne Ball"),
    "dribbling": ("schwarz", 0.14, "welle", "Dribbling"),
    "schuss": ("rot", 0.26, None, "Torschuss"),
    "flanke": ("blau", 0.18, "dash", "Flanke / hoher Ball"),
}
ZONENFARBEN = {"gelb": "#fde68a", "blau": "#bfdbfe", "rot": "#fecaca", "weiss": "#ffffff",
               "grau": "#e5e7eb", "orange": "#fed7aa", "lila": "#ddd6fe"}


def farbe(name, standard="schwarz"):
    name = name or standard
    return FARBEN.get(name, name)  # erlaubt auch #hex


class Zeichner:
    def __init__(self, d):
        feld = d["feld"]
        self.L = float(feld["laenge"])
        self.B = float(feld["breite"])
        self.s = BREITE_PX / (self.L + 2 * RAND_M)   # px pro Meter
        # Symbole (Spieler, Pfeile, Schrift) wachsen bei großen Feldern mit, damit sie lesbar bleiben
        self.k = max(1.0, max(self.L, self.B) / 28)
        self.teile = []
        self.legende = {}

    # Meter -> Pixel
    def px(self, x, y):
        return (RAND_M + x) * self.s, (RAND_M + y) * self.s

    def m(self, v):
        return v * self.s

    def ms(self, v):  # Symbolgröße
        return v * self.s * self.k

    def add(self, s):
        self.teile.append(s)

    # ---------- Feld ----------
    def feld(self, feld):
        W, H = self.px(self.L + RAND_M, self.B + RAND_M)
        self.add(f'<rect x="0" y="0" width="{W:.1f}" height="{H:.1f}" fill="#2f7d32"/>')
        # Mähstreifen
        streifen = max(1, round(self.L / 5))
        sw = (self.L + 2 * RAND_M) / streifen
        for i in range(0, streifen, 2):
            self.add(f'<rect x="{self.m(i * sw):.1f}" y="0" width="{self.m(sw):.1f}" height="{H:.1f}" fill="#358a38"/>')
        x0, y0 = self.px(0, 0)
        lw = self.m(0.15)
        stil = f'fill="none" stroke="#ffffff" stroke-width="{lw:.1f}"'
        self.add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{self.m(self.L):.1f}" height="{self.m(self.B):.1f}" {stil}/>')
        for linie in feld.get("linien", []) or []:
            self.linie(linie, stil)

    def linie(self, art, stil):
        L, B = self.L, self.B
        if art == "mittellinie":
            self.strecke((L / 2, 0), (L / 2, B), stil)
        elif art == "mittelkreis":
            cx, cy = self.px(L / 2, B / 2)
            self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{self.m(9.15):.1f}" {stil}/>')
        elif art.startswith(("strafraum_", "fuenfer_")):
            tiefe, breite = (16.5, 40.32) if art.startswith("strafraum") else (5.5, 18.32)
            seite = art.split("_", 1)[1]
            if seite in ("links", "rechts"):
                breite = min(breite, B)
                x, y, w, h = (0 if seite == "links" else L - tiefe), (B - breite) / 2, tiefe, breite
            else:  # oben / unten
                breite = min(breite, L)
                x, y, w, h = (L - breite) / 2, (0 if seite == "oben" else B - tiefe), breite, tiefe
            x0, y0 = self.px(x, y)
            self.add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{self.m(w):.1f}" height="{self.m(h):.1f}" {stil}/>')
        elif art.startswith("elfmeter_"):
            punkt = {"links": (11, B / 2), "rechts": (L - 11, B / 2), "oben": (L / 2, 11), "unten": (L / 2, B - 11)}
            cx, cy = self.px(*punkt[art.split("_", 1)[1]])
            self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{self.m(0.25):.1f}" fill="#ffffff"/>')
        elif art.startswith("linie:"):
            # frei: "linie: x1,y1,x2,y2"
            x1, y1, x2, y2 = (float(v) for v in art.split(":", 1)[1].split(","))
            self.strecke((x1, y1), (x2, y2), stil.replace('stroke="#ffffff"', 'stroke="#ffffff" stroke-dasharray="6,5"'))
        else:
            print(f"  Warnung: unbekannte Linie '{art}'", file=sys.stderr)

    def strecke(self, a, b, stil):
        x1, y1 = self.px(*a)
        x2, y2 = self.px(*b)
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" {stil}/>')

    def zone(self, z):
        x0, y0 = self.px(z["x"], z["y"])
        fill = ZONENFARBEN.get(z.get("farbe", "weiss"), z.get("farbe", "#ffffff"))
        self.add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{self.m(z["b"]):.1f}" height="{self.m(z["h"]):.1f}" '
                 f'fill="{fill}" fill-opacity="0.28" stroke="#ffffff" stroke-width="{self.m(0.1):.1f}" stroke-dasharray="8,6"/>')
        if z.get("label"):
            tx, ty = self.px(z["x"] + 0.5, z["y"] + 1.6)
            self.text(tx, ty, z["label"], 1.3, "#ffffff", anker="start", fett=True)

    # ---------- Objekte ----------
    def text(self, x, y, t, groesse_m, fill, anker="middle", fett=False):
        t = str(t).replace("&", "&amp;").replace("<", "&lt;")
        w = ' font-weight="bold"' if fett else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="Helvetica" font-size="{self.ms(groesse_m):.1f}"{w} '
                 f'fill="{fill}" text-anchor="{anker}">{t}</text>')

    def objekt(self, o):
        typ = o["typ"]
        x, y = self.px(o["x"], o["y"])
        if typ in ("spieler", "torhueter"):
            team = "tw" if typ == "torhueter" else str(o.get("team", "a"))
            f, tf, leg = TEAMS.get(team, (team, "weiss", f"Team {team}"))
            r = self.ms(0.9)
            self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{farbe(f)}" stroke="#111827" stroke-width="{self.ms(0.12):.1f}"/>')
            label = o.get("label", "TW" if typ == "torhueter" else "")
            if label:
                self.text(x, y + self.ms(0.42), label, 1.1 if len(str(label)) < 2 else 0.85 if len(str(label)) == 2 else 0.65, farbe(tf), fett=True)
            self.legende[("spieler", team)] = (team, leg)
        elif typ == "huetchen":
            r = self.ms(0.45)
            self.add(f'<polygon points="{x:.1f},{y - r:.1f} {x + r:.1f},{y + r * 0.8:.1f} {x - r:.1f},{y + r * 0.8:.1f}" '
                     f'fill="{farbe(o.get("farbe"), "orange")}" stroke="#111827" stroke-width="{self.ms(0.05):.1f}"/>')
            self.legende[("huetchen",)] = "Hütchen"
        elif typ == "stange":
            self.add(f'<rect x="{x - self.ms(0.15):.1f}" y="{y - self.ms(0.9):.1f}" width="{self.ms(0.3):.1f}" height="{self.ms(1.8):.1f}" '
                     f'fill="{farbe(o.get("farbe"), "gelb")}" stroke="#111827" stroke-width="{self.ms(0.06):.1f}"/>')
            self.legende[("stange",)] = "Stange"
        elif typ == "ring":
            self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{self.ms(0.4):.1f}" fill="none" '
                     f'stroke="{farbe(o.get("farbe"), "orange")}" stroke-width="{self.ms(0.12):.1f}"/>')
            self.legende[("ring",)] = "Koordinationsring"
        elif typ == "ball":
            self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{self.ms(0.35):.1f}" fill="#ffffff" stroke="#111827" stroke-width="{self.ms(0.08):.1f}"/>')
            self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{self.ms(0.12):.1f}" fill="#111827"/>')
            self.legende[("ball",)] = "Ball"
        elif typ == "balldepot":
            for dx, dy in ((-0.35, 0), (0.35, 0), (0, -0.5)):
                bx, by = self.px(o["x"] + dx * self.k, o["y"] + dy * self.k)
                self.add(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{self.ms(0.3):.1f}" fill="#ffffff" stroke="#111827" stroke-width="{self.ms(0.07):.1f}"/>')
            self.legende[("ball",)] = "Ball"
        elif typ == "leiter":
            self.leiter(o)
        elif typ in ("tor", "minitor"):
            self.tor(o)
        elif typ == "text":
            self.text(x, y, o["text"], o.get("groesse", 1.2), farbe(o.get("farbe"), "weiss"), fett=True)
        else:
            print(f"  Warnung: unbekannter Objekttyp '{typ}'", file=sys.stderr)

    def leiter(self, o):
        laenge = o.get("laenge", 4.0)
        horiz = o.get("richtung", "rechts") in ("rechts", "links")
        b = 0.6
        w, h = (laenge, b) if horiz else (b, laenge)
        x0, y0 = self.px(o["x"], o["y"])
        stil = f'stroke="{farbe("gelb")}" stroke-width="{self.m(0.08):.1f}"'
        self.add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{self.m(w):.1f}" height="{self.m(h):.1f}" fill="none" {stil}/>')
        for i in range(1, int(laenge / 0.45)):
            d = i * 0.45
            if horiz:
                self.strecke((o["x"] + d, o["y"]), (o["x"] + d, o["y"] + b), stil)
            else:
                self.strecke((o["x"], o["y"] + d), (o["x"] + b, o["y"] + d), stil)
        self.legende[("leiter",)] = "Koordinationsleiter"

    def tor(self, o):
        gross = o["typ"] == "tor"
        breite = o.get("breite", 7.32 if gross else 2.0)
        tiefe = 1.8 if gross else 0.9
        # richtung = wohin die Toröffnung zeigt (von wo geschossen wird)
        r = o.get("richtung", "rechts")
        x, y = o["x"], o["y"]
        if r == "rechts":
            rx, ry, rw, rh, lx = x - tiefe, y - breite / 2, tiefe, breite, ("v", x)
        elif r == "links":
            rx, ry, rw, rh, lx = x, y - breite / 2, tiefe, breite, ("v", x)
        elif r == "unten":
            rx, ry, rw, rh, lx = x - breite / 2, y - tiefe, breite, tiefe, ("h", y)
        else:  # oben
            rx, ry, rw, rh, lx = x - breite / 2, y, breite, tiefe, ("h", y)
        x0, y0 = self.px(rx, ry)
        self.add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{self.m(rw):.1f}" height="{self.m(rh):.1f}" '
                 f'fill="#e5e7eb" fill-opacity="0.55" stroke="#ffffff" stroke-width="{self.m(0.12):.1f}"/>')
        # Netzraster
        schritt = 0.5
        stil = f'stroke="#9ca3af" stroke-width="{self.m(0.03):.1f}"'
        for i in range(1, math.ceil(rw / schritt)):
            self.strecke((rx + i * schritt, ry), (rx + i * schritt, ry + rh), stil)
        for i in range(1, math.ceil(rh / schritt)):
            self.strecke((rx, ry + i * schritt), (rx + rw, ry + i * schritt), stil)
        # Pfosten / Torlinie
        pstil = f'stroke="#ffffff" stroke-width="{self.m(0.25):.1f}"'
        if lx[0] == "v":
            self.strecke((lx[1], ry), (lx[1], ry + rh), pstil)
        else:
            self.strecke((rx, lx[1]), (rx + rw, lx[1]), pstil)
        self.legende[(o["typ"],)] = "Großtor" if gross else "Minitor"

    # ---------- Pfeile ----------
    def pfeil(self, p):
        typ = p.get("typ", "pass")
        fname, breite, muster, leg = PFEILE.get(typ, PFEILE["pass"])
        fname = p.get("farbe", fname)
        (x1, y1), (x2, y2) = p["von"], p["nach"]
        kurve = float(p.get("kurve", 0))
        dx, dy = x2 - x1, y2 - y1
        laenge = math.hypot(dx, dy) or 1e-6
        nx, ny = -dy / laenge, dx / laenge
        cx, cy = (x1 + x2) / 2 + nx * kurve * laenge, (y1 + y2) / 2 + ny * kurve * laenge

        def punkt(t):  # quadratische Bézierkurve
            return ((1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t * t * x2,
                    (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t * t * y2)

        # Pfeilspitze nicht in den Spieler hineinzeichnen
        kopf = 1.0 * self.k
        ende = max(0.5, 1 - 0.9 * self.k / laenge)
        start = min(0.3, 0.9 * self.k / laenge) if p.get("ab_spieler", True) else 0
        n = max(12, int(laenge * 4))
        pts = []
        for i in range(n + 1):
            t = start + (ende - start) * i / n
            px_, py_ = punkt(t)
            if muster == "welle" and 0 < i < n - 2:
                # Normale der Kurve an Stelle t
                ax, ay = punkt(min(t + 0.01, 1))
                bx, by = punkt(max(t - 0.01, 0))
                tl = math.hypot(ax - bx, ay - by) or 1e-6
                ox, oy = -(ay - by) / tl, (ax - bx) / tl
                amp = 0.35 * self.k * math.sin(i / n * laenge * 2 * math.pi / (1.4 * self.k))
                px_, py_ = px_ + ox * amp, py_ + oy * amp
            pts.append(self.px(px_, py_))
        col = farbe(fname)
        dash = f' stroke-dasharray="{self.ms(0.6):.1f},{self.ms(0.4):.1f}"' if muster == "dash" else ""
        d = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        self.add(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="{self.ms(breite):.1f}" '
                 f'stroke-linecap="round" stroke-linejoin="round"{dash}/>')
        # Spitze
        ex, ey = punkt(ende)
        bx, by = punkt(max(ende - 0.05, 0))
        tl = math.hypot(ex - bx, ey - by) or 1e-6
        ux, uy = (ex - bx) / tl, (ey - by) / tl
        b1 = (ex - ux * kopf + uy * kopf * 0.45, ey - uy * kopf - ux * kopf * 0.45)
        b2 = (ex - ux * kopf - uy * kopf * 0.45, ey - uy * kopf + ux * kopf * 0.45)
        tri = " ".join(f"{a:.1f},{b:.1f}" for a, b in (self.px(ex, ey), self.px(*b1), self.px(*b2)))
        self.add(f'<polygon points="{tri}" fill="{col}"/>')
        if p.get("nr") is not None:
            mx, my = self.px(*punkt(0.5))
            r = self.ms(0.6)
            self.add(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="{r:.1f}" fill="#ffffff" stroke="{col}" stroke-width="{self.ms(0.08):.1f}"/>')
            self.text(mx, my + self.ms(0.3), p["nr"], 0.85, "#111827", fett=True)
        self.legende[("pfeil", typ)] = (typ, leg)

    # ---------- Legende ----------
    def symbol(self, key, wert, x, y):
        if key[0] == "spieler":
            f = farbe(TEAMS.get(wert[0], (wert[0],))[0])
            return f'<circle cx="{x + 8:.1f}" cy="{y + 10:.1f}" r="7" fill="{f}" stroke="#111827" stroke-width="1"/>'
        if key[0] == "pfeil":
            fname, _, muster, _ = PFEILE.get(wert[0], PFEILE["pass"])
            col = farbe(fname)
            if muster == "welle":
                pts = " ".join(f"{x + i * 2:.1f},{y + 10 + 3 * math.sin(i / 1.5):.1f}" for i in range(11))
                s = f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"/>'
            else:
                dash = ' stroke-dasharray="5,3"' if muster == "dash" else ""
                s = f'<line x1="{x:.1f}" y1="{y + 10:.1f}" x2="{x + 22:.1f}" y2="{y + 10:.1f}" stroke="{col}" stroke-width="2.5"{dash}/>'
            return s + f'<polygon points="{x + 28:.1f},{y + 10:.1f} {x + 21:.1f},{y + 6:.1f} {x + 21:.1f},{y + 14:.1f}" fill="{col}"/>'
        return {
            "huetchen": f'<polygon points="{x + 8:.1f},{y + 3:.1f} {x + 15:.1f},{y + 16:.1f} {x + 1:.1f},{y + 16:.1f}" fill="{FARBEN["orange"]}" stroke="#111827" stroke-width="0.8"/>',
            "stange": f'<rect x="{x + 6:.1f}" y="{y + 1:.1f}" width="4" height="18" fill="{FARBEN["gelb"]}" stroke="#111827" stroke-width="0.8"/>',
            "ring": f'<circle cx="{x + 8:.1f}" cy="{y + 10:.1f}" r="6" fill="none" stroke="{FARBEN["orange"]}" stroke-width="2"/>',
            "ball": f'<circle cx="{x + 8:.1f}" cy="{y + 10:.1f}" r="6" fill="#ffffff" stroke="#111827" stroke-width="1.2"/>',
            "leiter": f'<rect x="{x:.1f}" y="{y + 5:.1f}" width="22" height="10" fill="none" stroke="{FARBEN["gelb"]}" stroke-width="2"/>',
            "tor": f'<rect x="{x:.1f}" y="{y + 3:.1f}" width="22" height="14" fill="#e5e7eb" stroke="#374151" stroke-width="1.5"/>',
            "minitor": f'<rect x="{x + 4:.1f}" y="{y + 5:.1f}" width="14" height="10" fill="#e5e7eb" stroke="#374151" stroke-width="1.5"/>',
        }[key[0]]

    def legende_svg(self, y):
        """Legende unter dem Feld, bricht bei Bedarf in mehrere Zeilen um."""
        teile, x, fs, zeile = [], 10.0, 15, 26
        for key, wert in self.legende.items():
            text = wert[1] if isinstance(wert, tuple) else wert
            breite = 50 + len(text) * fs * 0.5
            if x + breite > BREITE_PX - 10 and x > 10:
                x, y = 10.0, y + zeile
            teile.append(self.symbol(key, wert, x, y))
            teile.append(f'<text x="{x + 32:.1f}" y="{y + 15:.1f}" font-family="Helvetica" font-size="{fs}" fill="#111827">{text}</text>')
            x += breite
        return teile, y + zeile

    def svg(self, d):
        self.feld(d["feld"])
        for z in d.get("zonen", []) or []:
            self.zone(z)
        objekte = d.get("objekte", []) or []
        # erst Material, dann Pfeile, dann Spieler obendrauf
        for o in objekte:
            if o["typ"] not in ("spieler", "torhueter", "text"):
                self.objekt(o)
        for p in d.get("pfeile", []) or []:
            self.pfeil(p)
        for o in objekte:
            if o["typ"] in ("spieler", "torhueter", "text"):
                self.objekt(o)
        W, H = self.px(self.L + RAND_M, self.B + RAND_M)
        leg, hoehe = self.legende_svg(H + 8) if self.legende else ([], H)
        oben = 40 if d.get("titel") else 0
        gesamt_h = hoehe + 6 + oben
        kopf = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{gesamt_h:.0f}" '
                f'viewBox="0 0 {W:.0f} {gesamt_h:.0f}">')
        titel = []
        if oben:
            t = str(d["titel"]).replace("&", "&amp;").replace("<", "&lt;")
            titel = [f'<rect x="0" y="0" width="{W:.1f}" height="{oben}" fill="#1f6f2b"/>',
                     f'<text x="12" y="27" font-family="Helvetica" font-size="20" font-weight="bold" fill="#ffffff">{t}</text>']
        hinten = f'<rect x="0" y="{H:.1f}" width="{W:.1f}" height="{hoehe + 6 - H:.1f}" fill="#ffffff"/>'
        return "\n".join([kopf, *titel, f'<g transform="translate(0,{oben})">', *self.teile, hinten, *leg,
                          "</g>", "</svg>"]) + "\n"


def pruefen(d, name):
    """Warnt, wenn Objekte weit außerhalb des Feldes liegen (Tippfehler bei Koordinaten)."""
    L, B = d["feld"]["laenge"], d["feld"]["breite"]
    for o in d.get("objekte", []) or []:
        if not (-RAND_M <= o["x"] <= L + RAND_M and -RAND_M <= o["y"] <= B + RAND_M):
            print(f"  Warnung {name}: {o['typ']} bei ({o['x']}, {o['y']}) liegt außerhalb des Feldes {L}x{B}", file=sys.stderr)
    for p in d.get("pfeile", []) or []:
        for x, y in (p["von"], p["nach"]):
            if not (-RAND_M <= x <= L + RAND_M and -RAND_M <= y <= B + RAND_M):
                print(f"  Warnung {name}: Pfeil-Punkt ({x}, {y}) außerhalb des Feldes", file=sys.stderr)


def diagramme(data):
    """`diagramm` darf ein einzelnes Diagramm oder eine Liste (mehrere Phasen) sein."""
    d = data.get("diagramm")
    if not d:
        return []
    return d if isinstance(d, list) else [d]


def svg_namen(anzahl):
    return ["diagramm.svg"] + [f"diagramm-{i}.svg" for i in range(2, anzahl + 1)]


def render(kurzname, png=False):
    pfad = UEBUNGEN / kurzname / "uebung.yaml"
    liste = diagramme(yaml.safe_load(pfad.read_text()))
    if not liste:
        print(f"{kurzname}: kein diagramm-Block", file=sys.stderr)
        return []
    for alt in pfad.parent.glob("diagramm-*.svg"):
        alt.unlink()
    ziele = []
    for d, name in zip(liste, svg_namen(len(liste))):
        pruefen(d, kurzname)
        ziel = pfad.parent / name
        ziel.write_text(Zeichner(d).svg(d))
        print(f"{kurzname}: {ziel.relative_to(ROOT)}")
        if png:
            print(f"  Vorschau: {vorschau_png(ziel, f'{kurzname}_{ziel.stem}')}")
        ziele.append(ziel)
    return ziele


def vorschau_png(svg: Path, kurzname: str) -> Path:
    """PNG-Vorschau zum Kontrollieren der Grafik (nicht fürs Repo).

    Geht bewusst über svglib -> PDF, also denselben Weg wie der Trainingsplan."""
    import subprocess

    from reportlab.graphics import renderPDF
    from svglib.svglib import svg2rlg

    ordner = ROOT / "arbeit" / "vorschau"
    ordner.mkdir(parents=True, exist_ok=True)
    pdf = ordner / f"{kurzname}.pdf"
    renderPDF.drawToFile(svg2rlg(str(svg)), str(pdf))
    subprocess.run(["pdftoppm", "-png", "-r", "110", "-singlefile", str(pdf), str(ordner / kurzname)], check=True)
    pdf.unlink()
    return ordner / f"{kurzname}.png"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kurznamen", nargs="*")
    ap.add_argument("--alle", action="store_true")
    ap.add_argument("--png", action="store_true")
    a = ap.parse_args()
    namen = sorted(p.parent.name for p in UEBUNGEN.glob("*/uebung.yaml")) if a.alle else a.kurznamen
    if not namen:
        ap.error("Kurzname(n) oder --alle angeben")
    for n in namen:
        render(n, a.png)


if __name__ == "__main__":
    main()
