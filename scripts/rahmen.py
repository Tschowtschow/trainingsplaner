"""Trainingsrahmen der Mannschaft – einzige Quelle für alle Skripte (Text dazu in CLAUDE.md)."""

TEILE = ["Lauf-ABC", "Erweitertes Aufwärmen", "Hauptteil 1", "Hauptteil 2", "Schlussteil 1", "Abschlussspiel"]
PHASE_ZU_TEIL = {"Lauf-ABC": "Lauf-ABC", "Erweitertes Aufwärmen": "Erweitertes Aufwärmen",
                 "Hauptteil 1": "Hauptteil", "Hauptteil 2": "Hauptteil",
                 "Schlussteil 1": "Schlussteil", "Abschlussspiel": "Abschlussspiel"}
# Schlussteil (und Abschlussspiel): nur Spielformen mit Gegenspielern, kein fester Ablauf/Pattern
NUR_SPIELFORM = ["Schlussteil", "Abschlussspiel"]
GESAMT_MIN = 120
BEGINN = "19:45"
PLATZ = "Halber Kunstrasenplatz (+ 2 DFB-Käfige)"
TAGE = {  # Tag -> (Charakter, Torhüter-Regel)
    "Dienstag": ("eher technisch / athletisch", "anfangs separat, dann integriert"),
    "Donnerstag": ("eher spielerisch", "meist komplett integriert"),
}
# Minutenverteilung je Tag (Lauf-ABC fest 10, Abschlussspiel >= 20, Summe 120)
MINUTEN = {
    "Dienstag": [10, 20, 25, 25, 15, 25],
    "Donnerstag": [10, 15, 20, 20, 20, 35],
}
# Schlagworte für erlaubtes Material
MATERIAL = ["hütchen", "leibchen", "ball", "bälle", "minitor", "stange", "leiter", "ring", "markier"]
# Materialkategorien für die Checkliste: Anzeige -> Schlagworte
MATERIAL_KATEGORIEN = {
    "Bälle": ["ball", "bälle"],
    "Hütchen": ["hütchen", "markier"],
    "Leibchen": ["leibchen"],
    "Minitore": ["minitor"],
    "Stangen": ["stange"],
    "Koordinationsleiter": ["leiter"],
    "Ringe": ["ring"],
}
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
