# Übungsdatenbank & Trainingsplaner – Herren, Kreisliga C (Frankfurt)

Der Trainer arbeitet **nur vom Handy** per Chat. Daraus folgt:
- Antworten auf Deutsch, kurz, ohne Code-Blöcke oder lange Tabellen. Ergebnisse (Grafik-Vorschau, PDF) immer als Datei schicken (`SendUserFile`).
- Nie nach Shell-Befehlen fragen oder den Trainer etwas selbst ausführen lassen. Alles erledigst du.
- Jede Änderung sofort committen und auf den aktuellen Branch pushen (`git push -u origin <branch>`). Der Container ist flüchtig, was nicht gepusht ist, ist weg.
- Rückfragen nur, wenn wirklich nötig, und dann gebündelt in **einer** Nachricht.

## Setup
Zu Beginn prüfen: `command -v yt-dlp ffmpeg pdftoppm && python3 -c "import faster_whisper, ruamel.yaml, svglib"`.
Fehlt etwas: `bash setup.sh` ausführen (idempotent).

## Chat-Befehle

Der Trainer schreibt frei, diese Muster erkennen (Groß/Klein, Tippfehler egal):

| Nachricht (Beispiel) | Aktion |
|---|---|
| Nur ein Link, oder „Neue Übung: <link> [Kurzname]“ | → **Übung anlegen** |
| Video-Datei hochgeladen (+ evtl. Link) | → **Übung anlegen** mit `--datei` |
| „Feedback rondo-5gegen2: 4, lief gut, Feld zu klein“ | → **Feedback speichern** |
| „Plan Torabschluss, Dienstag, 14+2“ / „Plan Pressing 5.11. 12 Feldspieler 1 TW“ | → **Trainingsplan erstellen** |
| „Liste“, „Welche Übungen für Umschalten?“ | `scripts/suche.py` mit Filtern, kurz zusammenfassen |
| „Zeig <übung>“ | Kurzfassung der Karte + PNG-Vorschau der Grafik schicken |
| „Ändere <übung>: …“ | YAML anpassen, Grafik neu, prüfen, pushen |
| „Lösch <übung>“ | erst nachfragen, dann Ordner löschen und pushen |

Ist eine Übung nicht eindeutig benannt, per `scripts/suche.py --text <wort>` suchen und bei mehreren Treffern kurz nachfragen.

## Ablauf: Übung anlegen

1. Kurzname festlegen: klein, Bindestriche, ohne Umlaute (`ae/oe/ue/ss`), sprechend, z. B. `pressing-4gegen4-plus3`. Prüfen, dass es ihn noch nicht gibt. Gibt es schon eine Karte mit derselben `quelle`, Bescheid geben statt doppelt anlegen.
2. `python3 scripts/video_holen.py <kurzname> <url>` (oder `--datei <pfad>`). Ergebnis in `arbeit/<kurzname>/` (nicht im Repo):
   Titel/Beschreibung, `transkript.txt`, Kontaktbögen `uebersicht_*.jpg` (je 9 Standbilder mit Zeitstempel), Einzelbilder in `frames/`.
3. **Alle Kontaktbögen ansehen** (Read auf die JPGs), Transkript und Beschreibung lesen. Bei Unklarheiten einzelne Frames in voller Größe ansehen.
   Daraus Aufbau, Abstände, Spielerzahl, Laufwege und Passfolge ableiten. Feldmaße schätzen, wenn sie nicht genannt werden (Hütchenabstände, Strafraum = 16,5 m als Referenz).
4. `uebungen/<kurzname>/uebung.yaml` nach dem Format unten schreiben. Inhalt in eigenen Worten, auf Deutsch, so konkret, dass ein Co-Trainer die Übung **ohne Video** aufbauen kann. Für unsere Mannschaft (Hobby-/Amateurniveau, Kreisliga C) realistisch einordnen; Profi-Varianten in `varianten.schwerer`.
5. `python3 scripts/diagramm.py <kurzname> --png` und die Vorschau `arbeit/vorschau/<kurzname>.png` **ansehen**. Überlappungen, falsche Pfeilrichtungen, Spieler außerhalb des Feldes korrigieren und neu erzeugen, bis die Grafik stimmt.
6. `python3 scripts/pruefen.py <kurzname>` muss ✓ zeigen.
7. Committen („Übung: <name>“) und pushen.
8. Antwort ans Handy: Name, Phase(n), Schwerpunkte, Spielerzahl, Dauer, 2–3 Sätze Ablauf + Vorschau-PNG per `SendUserFile`. Angaben, die du geschätzt hast (Feldgröße, Zeiten), kurz als geschätzt kennzeichnen.

**Wenn der Download scheitert** (Login-Pflicht bei Instagram/TikTok, Bot-Sperre, Netzwerk-Sperre „403 Forbidden“ vom Proxy):
Fehler in einem Satz nennen und dem Trainer anbieten, das Video direkt in den Chat hochzuladen (dann `--datei`), oder Screenshots/eine kurze Beschreibung zu schicken. Niemals eine Übung erfinden, die nur zum Titel passt. Bei Netzwerksperre: die Domain nennen, die in den Umgebungs-Einstellungen freigegeben werden muss (siehe README.md).
Scheitert nur die Transkription, mit Bildern + Beschreibung weitermachen und das erwähnen.

Mehrere Übungen in einem Video → mehrere Karten (`<kurzname>-1`, `-2` oder sprechende Namen), gleiche `quelle`.

## Ablauf: Feedback speichern

`python3 scripts/feedback.py <kurzname> --bewertung <1-5> --notiz "<text>" [--datum JJJJ-MM-TT]`
- Ohne Datum = heute. „gestern“, „Dienstag“ usw. in ein Datum umrechnen.
- Notiz sinngemäß übernehmen, nicht umformulieren. Keine Zahl genannt → nur Notiz (oder aus dem Ton eine Bewertung ableiten und kurz bestätigen lassen).
- Ergibt sich aus dem Feedback eine klare Verbesserung der Karte (z. B. „Feld war zu klein“), anbieten, die Karte anzupassen – nicht ungefragt ändern.
- Committen („Feedback: <kurzname>“), pushen, mit einer Zeile bestätigen (inkl. neuem Schnitt).

## Ablauf: Trainingsplan erstellen

Eingabe: Schwerpunkt, Trainingstag (oder Datum), Feldspieler + Torhüter. Fehlt etwas, sinnvoll annehmen (nächster passender Trainingstag, Spielerzahl vom letzten Plan) und die Annahme in der Antwort nennen.

1. Kandidaten suchen: `python3 scripts/suche.py --schwerpunkt <S> --spieler <n> --tw <t>`, zusätzlich je Phase (`--phase`).
2. Auswahl nach dem **Trainingsrahmen** unten:
   - jede Phase des Rahmens besetzen, Schwerpunkt im Hauptteil und Abschlussspiel klar erkennbar, Aufwärmen hinführend;
   - gut bewertete Übungen bevorzugen, Übungen mit Schnitt ≤ 2 nur, wenn nichts anderes passt;
   - Übungen der letzten 2 Pläne (`plaene/*.yaml`) möglichst nicht wiederholen;
   - Torhüter einplanen (`torhueter: ja`-Übungen brauchen mind. 1 TW; ohne TW → Minitore/Variante);
   - Intensität passend zum Trainingstag (siehe Rahmen).
   Fehlt für eine Phase eine passende Übung in der Datenbank, das dem Trainer sagen und eine bekannte Standardübung als Notlösung vorschlagen – nicht stillschweigend erfinden. Wenn der Trainer zustimmt, als richtige Karte anlegen (`quelle: eigene Übung`).
3. Für jede Einheit `organisation` passend zur **heutigen** Spielerzahl schreiben: Gruppen, Teams, was mit überzähligen Spielern und den Torhütern passiert (aus `varianten.spielerzahl` der Karte ableiten).
4. Plan-YAML `plaene/<datum>_<schwerpunkt>.yaml` schreiben (Schwerpunkt klein, ohne Umlaute, Bindestriche), Format unten.
5. `python3 scripts/plan_pdf.py plaene/<datei>.yaml` → PDF daneben. Mit `pdftoppm -png -r 50` stichprobenartig ansehen (Seite 1 + eine Übungsseite).
6. Committen („Plan: <datum> <schwerpunkt>“), pushen, PDF per `SendUserFile` schicken mit 3–5 Zeilen Überblick (Phasen + Übungen + Minuten).

## Format: Übungskarte (`uebungen/<kurzname>/uebung.yaml`)

```yaml
name: Rondo 5 gegen 2
schwerpunkte: [Passspiel, Pressing]   # Tags: Pressing, Umschalten, Torabschluss, Passspiel, Athletik,
                                      # Koordination, Spielaufbau, Flanken, Zweikampf, Standards, ...
phase: [Erweitertes Aufwärmen]        # eine oder mehrere aus: Lauf-ABC, Erweitertes Aufwärmen,
                                      # Hauptteil, Schlussteil, Abschlussspiel
spieler_min: 7                        # Feldspieler
spieler_max: 21
torhueter: nein                       # ja | nein | optional
feldgroesse: 12 x 12 m pro Gruppe
material: [4 Hütchen pro Gruppe, 2-3 Bälle pro Gruppe, Leibchen]
dauer_min: 12
intensitaet: 3                        # 1 (locker) – 5 (maximal)
ablauf: [Schritt 1, Schritt 2, ...]   # nummeriert im PDF
regeln: [...]
coachingpunkte: [...]
varianten:
  leichter: [...]
  schwerer: [...]
  spielerzahl: [...]                  # wie mit mehr/weniger Spielern organisieren
quelle: https://...                   # Link; bei eigenen Übungen "eigene Übung"
feedback:                             # nur über scripts/feedback.py anhängen
  - {datum: 2026-11-03, bewertung: 4, notiz: "..."}
diagramm: {...}                       # siehe unten
```
Texte mit `: ` (Doppelpunkt + Leerzeichen) **in Anführungszeichen** setzen, sonst wird YAML falsch gelesen (`pruefen.py` meldet das).

## Format: Diagramm (Block `diagramm:` in der Übungskarte)

Koordinaten in **Metern**. Ursprung (0, 0) = **linke obere** Feldecke, `x` nach rechts (Länge), `y` nach unten (Breite).
Die Grafik wird ausschließlich aus diesen Daten erzeugt (`scripts/diagramm.py`), nie von Hand gezeichnet.

```yaml
diagramm:
  feld:
    laenge: 35        # m, x-Richtung
    breite: 46        # m, y-Richtung
    linien: [mittellinie, mittelkreis, strafraum_links, strafraum_rechts, fuenfer_links, fuenfer_rechts,
             elfmeter_links, elfmeter_rechts, "linie: 10,0,10,46"]   # alle optional; "linie:" = gestrichelte Hilfslinie x1,y1,x2,y2
  zonen:              # optional, halbtransparente Rechtecke
    - {x: 0, y: 0, b: 10, h: 46, label: "Zone 1", farbe: gelb}   # gelb|blau|rot|weiss|grau|orange|lila
  objekte:
    - {typ: spieler, team: a, x: 4, y: 30, label: "A"}  # team: a (rot) | b (blau) | c (lila) | neutral (gelb) | trainer (schwarz)
    - {typ: torhueter, x: 33.8, y: 23}                   # grün, Label "TW"
    - {typ: huetchen, x: 0, y: 0, farbe: orange}         # farbe optional (rot, gelb, blau, ...)
    - {typ: stange, x: 16, y: 14.5}
    - {typ: dummy, x: 10, y: 10}
    - {typ: ring, x: 5, y: 5}
    - {typ: leiter, x: 2, y: 2, laenge: 4, richtung: rechts}   # x/y = Ecke oben links
    - {typ: ball, x: 6, y: 1}
    - {typ: balldepot, x: 2, y: 27}
    - {typ: tor, x: 35, y: 23, richtung: links}          # x/y = Mitte der Torlinie; richtung = wohin die Öffnung zeigt
    - {typ: minitor, x: 0, y: 10, richtung: rechts, breite: 2}
    - {typ: text, x: 17, y: 2, text: "Station 1", groesse: 1.2}
  pfeile:
    - {typ: pass, von: [4, 30], nach: [16, 17], nr: 1}         # durchgezogen
    - {typ: lauf, von: [4, 30], nach: [16, 27], kurve: 0.1}    # gestrichelt (ohne Ball)
    - {typ: dribbling, von: [17.5, 26], nach: [22.5, 25]}      # Wellenlinie
    - {typ: schuss, von: [22.5, 25], nach: [35, 20.5]}         # rot, dick
    - {typ: flanke, von: [30, 2], nach: [28, 20]}              # blau gestrichelt
```
Pfeil-Optionen: `kurve` (−0.5…0.5, Bogen nach links/rechts), `nr` (Reihenfolge-Nummer), `ab_spieler: false` (Pfeil nicht vom Startpunkt wegkürzen, wenn dort kein Spieler steht), `farbe`.
Tipps: Spieler mind. ~2 m auseinander, Abfolge mit `nr` nummerieren, nur die wichtigsten Wege zeigen (eine Grafik, kein Film). Feld nur so groß wie der genutzte Raum.

## Format: Plan (`plaene/<datum>_<schwerpunkt>.yaml`)

```yaml
datum: 2026-11-03
trainingstag: Dienstag
schwerpunkt: Torabschluss
feldspieler: 14
torhueter: 2
beginn: "19:30"
ort: Kunstrasen                 # optional
ziel: "Ein Satz, worum es heute geht."
einheiten:
  - phase: Lauf-ABC
    uebung: lauf-abc-grundform  # Kurzname
    dauer_min: 10
    organisation: "Wie heute mit 14+2 organisiert wird."
    hinweis: "optional, erscheint als Kasten auf der Übungsseite"
hinweise: [optional, erscheinen auf Seite 1]
material_zusaetzlich: [optional]
```
Uhrzeiten rechnet `plan_pdf.py` aus `beginn` + Dauern. Material wird aus den Karten zusammengezählt.

## Trainingsrahmen

> **VORLÄUFIG.** Die Nachricht des Trainers mit dem Trainingsrahmen ist unvollständig angekommen.
> Bis er ergänzt ist, gelten diese Annahmen. Beim nächsten Plan kurz darauf hinweisen und den Rahmen hier ersetzen, sobald der Trainer ihn schickt.

- Mannschaft: Herren, Kreisliga C, Frankfurt. Amateure, gemischtes Niveau, Spieltag i. d. R. Sonntag.
- Trainingstage: _noch offen_ (Annahme: Dienstag und Donnerstag), Dauer 90 min.
- Phasen und Richtzeiten (Summe 90 min):
  | Phase | Minuten | Zweck |
  |---|---|---|
  | Lauf-ABC | 10 | Aktivierung, Koordination |
  | Erweitertes Aufwärmen | 15 | Ball, Passformen/Rondo, zum Schwerpunkt hinführen |
  | Hauptteil | 30–35 | Schwerpunkt, 1–2 Übungen |
  | Schlussteil | 10–15 | Schwerpunkt in spielnaher Form |
  | Abschlussspiel | 20 | freies Spiel mit Schwerpunktregel |
  Trinkpausen sind in den Zeiten enthalten.
- Intensität nach Tag (Annahme): erster Trainingstag der Woche = hohe Belastung (Intensität 3–5 erlaubt), letzter Trainingstag vor dem Spiel = kürzere, spritzige Formen, keine Übung mit Intensität 5 länger als 10 min.
