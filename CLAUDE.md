# Übungsdatenbank & Trainingsplaner – Herren, Kreisliga C (Frankfurt)

Der Trainer arbeitet **nur vom Handy** per Chat. Daraus folgt:
- Antworten auf Deutsch, kurz, ohne Code-Blöcke und lange Tabellen. Grafiken (PNG-Vorschau) und PDFs immer als Datei schicken (`SendUserFile`), dazu den Repo-Pfad nennen.
- Den Trainer nie etwas selbst ausführen lassen. Alles erledigst du.
- Jede Änderung sofort committen und auf den aktuellen Branch pushen (`git push -u origin <branch>`). Der Container ist flüchtig.
- Rückfragen nur, wenn wirklich nötig, gebündelt in **einer** Nachricht.

## Setup
Zu Beginn prüfen: `command -v yt-dlp ffmpeg pdftoppm && python3 -c "import faster_whisper, ruamel.yaml, svglib"`.
Fehlt etwas: `bash setup.sh` (idempotent). Rohmaterial (Videos, Frames, Audio, Vorschauen) liegt in `arbeit/` und kommt nie ins Repo.

## Chat-Befehle

| Nachricht (Beispiel) | Aktion |
|---|---|
| Ein oder mehrere Links (YouTube, TikTok, Instagram) | **Übungen aus Videos anlegen** |
| Hochgeladene Video-Datei | **Übung anlegen** mit `--datei` |
| „Rondo 5v2: Feld zu groß, mit 12 Leuten besser, 4/5“ | **Feedback** |
| „Donnerstag, Umschalten, 14 Feldspieler + 2 TW“ | **Trainingsplan** |
| „Liste“, „Welche Übungen für Pressing?“ | `scripts/suche.py` mit Filtern, kurz zusammenfassen |
| „Zeig <Übung>“ | Kurzfassung + PNG-Vorschau der Grafik(en) |
| „Ändere <Übung>: …“ | YAML anpassen, Grafik neu, prüfen, pushen |
| „Lösch <Übung>“ | erst nachfragen, dann löschen und pushen |

Übungen dürfen ungefähr benannt werden („Rondo 5v2“). Auflösen mit `scripts/datenbank.py` (über `feedback.py` oder `suche.py --details`); bei mehreren Treffern kurz nachfragen.

## Ablauf: Übungen aus Videos

Mehrere Links → **nacheinander** abarbeiten, jeden komplett (inkl. Commit/Push), dann der nächste. Ein gescheiterter Link hält die anderen nicht auf.

1. Kurzname: klein, Bindestriche, ohne Umlaute, sprechend (`pressing-4gegen4-plus3`). Prüfen, dass es ihn und dieselbe `quelle` noch nicht gibt (`grep -r "<url>" uebungen/`).
2. `python3 scripts/video_holen.py <kurzname> <url>` (oder `--datei <pfad>`).
   - **Exit-Code 2 = Download gescheitert** (Bot-Sperre, Login, Netzwerksperre 403): dem Trainer in einem Satz Bescheid geben („Link X ging nicht: Instagram verlangt Login – schick mir die Datei“) und mit dem nächsten Link weitermachen. Nichts erfinden.
   - Ergebnis in `arbeit/<kurzname>/`: Titel/Beschreibung, `transkript.txt` (faster-whisper), Kontaktbögen `uebersicht_*.jpg` (je 9 Standbilder mit Zeitstempel; Raster + Szenenwechsel), Einzelbilder `frames/*.jpg` (960 px).
3. **Alle Kontaktbögen ansehen** (Read auf die JPGs). **Eingeblendeten Text** (Übungsname, Regeln, Maße, Spielerzahlen, Pfeile/Grafiken im Video) auswerten – dafür die betreffenden Einzelbilder in voller Größe öffnen. Transkript und Beschreibung lesen.
4. `uebungen/<kurzname>/uebung.yaml` nach dem Format unten schreiben – in eigenen Worten, auf Deutsch, so konkret, dass ein Co-Trainer die Übung **ohne Video** aufbauen kann. Auf unser Niveau (Kreisliga C) und unser Material einordnen (Material, das wir nicht haben, z. B. Dummies → Stangen; Profi-Varianten in `varianten.schwerer`).
   **Unsicheres kennzeichnen:** Alles, was du nicht sicher erkennst (geschätzte Maße, Spielerzahl, Regel nur vermutet), im Text mit „(unsicher)“ markieren **und** in der Liste `unsicher:` kurz aufführen.
5. Diagramm(e) im YAML anlegen. Mehrere Phasen der Übung → mehrere Diagramme (Liste mit `titel`).
   `python3 scripts/diagramm.py <kurzname> --png` und **jede Vorschau** `arbeit/vorschau/<kurzname>_diagramm*.png` ansehen. Überlappungen, falsche Pfeile, Spieler außerhalb korrigieren, bis es stimmt.
6. `python3 scripts/pruefen.py <kurzname>` → ✓.
7. Commit („Übung: <name>“), Push.
8. Ans Handy: **Name, Tags, Spielerzahl, 2–3 Sätze Ablauf**, ggf. „Unsicher: …“ + Diagramm-PNG(s) per `SendUserFile`.

Mehrere Übungen in einem Video → mehrere Karten mit gleicher `quelle`.
Nach allen Links: eine Zeile Zusammenfassung (x angelegt, y gescheitert – welche).

## Ablauf: Feedback

Beispiel „Rondo 5v2: Feld zu groß, mit 12 Leuten besser, 4/5“:
1. `python3 scripts/feedback.py "<übung>" --bewertung 4 --notiz "Feld zu groß, mit 12 Leuten besser" [--datum JJJJ-MM-TT]`
   (Exit-Code 3 = mehrdeutig → nachfragen.) Ohne Datum = heute; „gestern“, „Dienstag“ umrechnen. Notiz sinngemäß wie geschrieben.
2. **Karte anpassen, wenn das Feedback es nahelegt** – direkt, ohne Nachfrage: z. B. `feldgroesse` verkleinern, unter `varianten.spielerzahl` „mit 12 Spielern bewährt“ ergänzen, Regel präzisieren. Diagramm neu erzeugen, falls Maße betroffen. Nur Eindeutiges ändern; Geschmacksfragen bleiben in der Notiz.
3. Commit („Feedback: <kurzname>“), Push. Kurz bestätigen: gespeichert + neuer Schnitt + was an der Karte geändert wurde.

## Ablauf: Trainingsplan

Eingabe z. B. „Donnerstag, Umschalten, 14 Feldspieler + 2 TW“. Datum = nächster genannter Wochentag (ab heute). Der genannte Schwerpunkt ist der Wochenfokus.

1. Kandidaten je Teil suchen: `python3 scripts/suche.py --phase <Phase> --spieler <n> --tw <t> [--schwerpunkt <S>]`.
2. Auswahl **strikt nach dem Trainingsrahmen** (unten):
   - genau die 6 Teile in der Reihenfolge, Minuten wie vorgegeben verteilen;
   - **nur Übungen aus der Datenbank**, passend zu Phase, Spielerzahl, TW und Schwerpunkt;
   - Hauptteil 1 → Hauptteil 2 als Steigerung zum Schwerpunkt (z. B. ohne → mit Gegner, Unterzahl → Gleichzahl), Schlussteil 1 führt zum Abschlussspiel hin;
   - Tagescharakter beachten (Di technisch/athletisch, Do spielerisch);
   - gut bewertete bevorzugen, Schnitt ≤ 2 meiden, Feedback-Notizen berücksichtigen (z. B. Feldgröße/Spielerzahl, die sich bewährt hat);
   - Übungen aus den letzten 2–3 Plänen (`plaene/*.yaml`) möglichst nicht wiederholen;
   - nur Vereinsmaterial (Liste unten).
   **Fehlt etwas Passendes:** eine eigene Übung entwerfen, als normale Karte anlegen (mit Diagramm, `quelle: eigene Übung (neu)`), im Plan `neu: true` setzen. Im PDF und in der Antwort erscheint sie als **[NEU]**.
3. Für **jede** Übung die konkrete `aufteilung` für die genannte Spielerzahl schreiben: `gruppen` (Teams/Gruppengrößen), `rollen`, `wechsel`, `torhueter` (nach Tagesregel).
4. `plaene/<datum>_<schwerpunkt>.yaml` schreiben (Schwerpunkt klein, ohne Umlaute, Bindestriche).
5. `python3 scripts/plan_pdf.py plaene/<datei>.yaml` – prüft den Rahmen (bricht mit FEHLER ab, Warnungen ernst nehmen) und erzeugt das PDF daneben. Deckblatt + eine Übungsseite mit `pdftoppm -png -r 50` ansehen.
6. Commit („Plan: <datum> <schwerpunkt>“), Push. PDF per `SendUserFile` + Pfad + 6 Zeilen Überblick (Teil, Übung, Minuten, [NEU]).

## Trainingsrahmen

- Training **dienstags und donnerstags**, Start **19:45 Uhr**, **120 Minuten**.
- Gliederung, immer genau so:
  1. **Lauf-ABC** – 10 min
  2. **Erweitertes Aufwärmen**
  3. **Hauptteil 1**
  4. **Hauptteil 2**
  5. **Schlussteil 1**
  6. **Abschlussspiel** – mindestens 20 min

  Die übrigen Minuten sinnvoll auf Teil 2–5 verteilen und im Plan ausweisen (Richtwert: Aufwärmen 15, Hauptteil 1 20, Hauptteil 2 25, Schlussteil 1 20, Abschlussspiel 30; Trinkpausen sind in den Zeiten enthalten).
  Hauptteil 1 und 2 bauen aufeinander auf (Steigerung zum Schwerpunkt). Schlussteil 1 führt zum Abschlussspiel hin.
- **Dienstag** eher technisch/athletisch, **Donnerstag** eher spielerisch. Dazu ein Wochenfokus, den der Trainer nennt.
- **Platz:** meist halber Kunstrasenplatz (ca. 50 x 64 m, ein Großtor), dazu theoretisch 2 DFB-Käfige (Minispielfelder ca. 20 x 13 m mit kleinen Toren). Großtore sind fest am Platz, nur eins pro halbem Platz.
- **Material** (nur damit planen): Hütchen, Leibchen, Bälle, Minitore, Stangen, Koordinationsleiter, Ringe.
- **Torhüter:** dienstags anfangs separat (Lauf-ABC + Aufwärmen mit eigenem Programm), dann integriert; donnerstags meist komplett integriert.

Diese Regeln stehen zusätzlich als Konstanten in `scripts/plan_pdf.py` (`TEILE`, `GESAMT_MIN`, `BEGINN`, `TAGE`, `MATERIAL`). Ändert der Trainer den Rahmen, **beides** anpassen.

## Format: Übungskarte (`uebungen/<kurzname>/uebung.yaml`)

```yaml
name: Rondo 5 gegen 2
schwerpunkte: [Passspiel, Pressing]   # Pressing, Umschalten, Torabschluss, Passspiel, Athletik, Koordination,
                                      # Spielaufbau, Flanken, Zweikampf, Standards, ...
phase: [Erweitertes Aufwärmen]        # eine oder mehrere: Lauf-ABC, Erweitertes Aufwärmen, Hauptteil,
                                      # Schlussteil, Abschlussspiel
spieler_min: 7                        # Feldspieler
spieler_max: 21
torhueter: nein                       # ja | nein | optional
feldgroesse: 12 x 12 m pro Gruppe
material: [4 Hütchen pro Gruppe, 2-3 Bälle pro Gruppe, Leibchen]   # nur Vereinsmaterial; Großtor nicht aufführen
dauer_min: 12
intensitaet: 3                        # 1 locker – 5 maximal
ablauf: [Schritt 1, Schritt 2]        # im PDF nummeriert
regeln: [...]
coachingpunkte: [...]
varianten:
  leichter: [...]
  schwerer: [...]
  spielerzahl: [...]                  # wie mit mehr/weniger Spielern organisieren
quelle: https://...                   # Link; eigene: "eigene Übung" bzw. "eigene Übung (neu)"
unsicher: []                          # was aus dem Video nicht sicher erkennbar war
feedback:                             # nur über scripts/feedback.py anhängen
  - {datum: '2026-11-03', bewertung: 4, notiz: "..."}
diagramm: {...}                       # ein Diagramm oder Liste mehrerer (siehe unten)
```
Texte mit `: ` (Doppelpunkt + Leerzeichen) **in Anführungszeichen**, sonst liest YAML sie falsch (`pruefen.py` meldet das).

## Format: Diagramm

Koordinaten in **Metern**, Ursprung (0, 0) = **linke obere** Feldecke, `x` nach rechts (`laenge`), `y` nach unten (`breite`).
Die Grafik entsteht nur aus diesen Daten (`scripts/diagramm.py` → `diagramm.svg`, bei mehreren `diagramm-2.svg`, …). Einheitlicher Stil: grüner Platz, weiße Linien, Legende.
**Querformat bevorzugen** (laenge ≥ breite): Übungen auf ein Tor mit dem Tor **oben** zeichnen (`tor` bei `y: 0`, `richtung: unten`, Linien `*_oben`).

```yaml
diagramm:                # eine Phase; bei mehreren: Liste von solchen Blöcken, je mit titel
  titel: "Phase 1: Ballzirkulation"   # optional (bei mehreren Pflicht), erscheint als Kopfzeile
  feld:
    laenge: 46
    breite: 35
    linien: [strafraum_oben, fuenfer_oben, elfmeter_oben, mittellinie, mittelkreis, "linie: 0,20,46,20"]
            # Seiten: _oben/_unten/_links/_rechts; "linie: x1,y1,x2,y2" = gestrichelte Hilfslinie
  zonen:
    - {x: 0, y: 0, b: 10, h: 35, label: "Zone 1", farbe: gelb}   # gelb|blau|rot|weiss|grau|orange|lila
  objekte:
    - {typ: spieler, team: a, x: 30, y: 31, label: "A"}  # team: a rot | b blau | c lila | neutral gelb | trainer schwarz
    - {typ: torhueter, x: 23, y: 1.2}                    # grün, "TW"
    - {typ: huetchen, x: 0, y: 0, farbe: orange}
    - {typ: stange, x: 14.5, y: 19}
    - {typ: ring, x: 5, y: 5}
    - {typ: leiter, x: 2, y: 2, laenge: 4, richtung: rechts}   # x/y = Ecke oben links
    - {typ: ball, x: 6, y: 1}
    - {typ: balldepot, x: 27, y: 33}
    - {typ: tor, x: 23, y: 0, richtung: unten}           # x/y = Mitte Torlinie; richtung = wohin die Öffnung zeigt
    - {typ: minitor, x: 10, y: 35, richtung: oben, breite: 2}
    - {typ: text, x: 17, y: 2, text: "Station 1", groesse: 1.2}
  pfeile:
    - {typ: pass, von: [30, 31], nach: [17, 19], nr: 1}       # durchgezogen
    - {typ: lauf, von: [30, 31], nach: [27, 19], kurve: 0.1}  # gestrichelt
    - {typ: dribbling, von: [26, 17.5], nach: [25, 12.5]}     # Wellenlinie
    - {typ: schuss, von: [25, 12.5], nach: [20.5, 0]}         # rot, dick
    - {typ: flanke, von: [2, 10], nach: [20, 8]}              # blau gestrichelt
```
Pfeil-Optionen: `kurve` (−0.5…0.5), `nr` (Reihenfolge), `ab_spieler: false` (nicht vom Startpunkt wegkürzen, wenn dort kein Spieler steht), `farbe`.
Tipps: Spieler mind. ~2 m auseinander, Reihenfolge mit `nr`, nur die wichtigsten Wege; Feld nur so groß wie der genutzte Raum.

## Format: Plan (`plaene/<datum>_<schwerpunkt>.yaml`)

```yaml
datum: 2026-11-05
trainingstag: Donnerstag
schwerpunkt: Umschalten
feldspieler: 14
torhueter: 2
beginn: "19:45"
ziel: "Ein Satz, worum es heute geht."
teile:                       # genau 6, in dieser Reihenfolge
  - teil: Lauf-ABC           # Lauf-ABC | Erweitertes Aufwärmen | Hauptteil 1 | Hauptteil 2 | Schlussteil 1 | Abschlussspiel
    uebung: lauf-abc-grundform
    dauer_min: 10
    neu: false               # true = eigene, neu entworfene Übung -> [NEU]
    aufteilung:
      gruppen: "4 Bahnen à 3-4 Spieler"
      rollen: "..."
      wechsel: "..."
      torhueter: "..."
    hinweis: "optional, erscheint auf der Übungsseite"
hinweise: [optional, Deckblatt]
```
Uhrzeiten rechnet `plan_pdf.py` aus `beginn` + Minuten; Material wird aus den Karten zusammengefasst.

## Skripte

| Skript | Zweck |
|---|---|
| `scripts/video_holen.py <kurz> <url>` / `--datei` | Download, Standbilder, Kontaktbögen, Transkript |
| `scripts/diagramm.py <kurz> [--png]` / `--alle` | YAML → SVG (+ Vorschau) |
| `scripts/pruefen.py [<kurz>]` | Karten prüfen |
| `scripts/feedback.py "<übung>" --bewertung N --notiz "…"` | Feedback anhängen (Formatierung bleibt erhalten) |
| `scripts/suche.py [--phase --schwerpunkt --spieler --tw --text]` / `--details <übung>` | Datenbank durchsuchen |
| `scripts/plan_pdf.py plaene/<datei>.yaml` | Rahmen prüfen + PDF |
