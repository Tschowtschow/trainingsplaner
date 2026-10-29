# Trainingsplaner – Übungsdatenbank Fußball

Übungskarten aus Videos, Feedback und fertige Trainingspläne als PDF – gesteuert per Chat mit Claude Code.
Arbeitsanweisungen, Formate und Trainingsrahmen: siehe [CLAUDE.md](CLAUDE.md). Übersicht aller Übungen: [UEBUNGEN.md](UEBUNGEN.md).

```
uebungen/<kurzname>/uebung.yaml    Übungskarte
uebungen/<kurzname>/diagramm.svg   Grafik (aus den Daten in uebung.yaml erzeugt; weitere Phasen: diagramm-2.svg, ...)
plaene/<datum>_<schwerpunkt>.yaml  Auswahl für einen Trainingstag
plaene/<datum>_<schwerpunkt>.pdf   Plan für den Co-Trainer
scripts/video_holen.py             Download, Transkript (faster-whisper), Standbilder
scripts/diagramm.py                YAML -> SVG (+ PNG-Vorschau)
scripts/plan_pdf.py                Plan-YAML -> PDF
scripts/feedback.py                Feedback an eine Übung anhängen
scripts/suche.py                   Übungen filtern
scripts/pruefen.py                 Übungskarten prüfen
scripts/datenbank.py               Laden, ungefähre Namen, Link-Normalisierung, Historie
scripts/rahmen.py                  Trainingsrahmen als Konstanten
scripts/plan_vorschlag.py          Planentwurf nach Rahmen (Auswahl + Minuten + Aufteilung)
scripts/aufteilung.py              Gruppen/Teams für eine Spielerzahl
scripts/katalog_pdf.py             Übungskatalog als PDF
scripts/uebersicht.py              UEBUNGEN.md erzeugen
tests/                             pytest-Tests, laufen auch auf GitHub (.github/workflows)
UEBUNGEN.md                        Übersicht aller Übungen und Pläne
katalog/uebungskatalog.pdf         alle Übungskarten als PDF
setup.sh                           Installiert alle Werkzeuge
arbeit/                            Videos, Frames, Audio, Vorschauen (nicht im Repo)
```

## Cloud-Umgebung einrichten

**Setup-Skript:** Umgebungsmenü in der Titelleiste der Session → *Edit* → Feld *Setup script*:

```bash
#!/bin/bash
set -e
command -v ffmpeg >/dev/null && command -v pdftoppm >/dev/null || \
  (apt-get update -qq && apt-get install -y -qq ffmpeg poppler-utils fonts-dejavu-core)
python3 -m pip install -q --upgrade yt-dlp faster-whisper pyyaml ruamel.yaml reportlab svglib pytest
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" || true
```
(Entspricht `setup.sh`; das Setup-Skript läuft eigenständig, deshalb steht der Inhalt hier direkt drin.)

**Netzwerkzugriff:** Im selben Dialog unter *Network access* die Stufe so wählen, dass diese Domains erreichbar sind
(bei *Limited* unter *Allowed domains* eintragen, „Allow package managers“ angehakt lassen):

```
youtube.com, *.youtube.com, youtu.be, *.googlevideo.com, *.ytimg.com
tiktok.com, *.tiktok.com, *.tiktokcdn.com, *.tiktokcdn-us.com, *.tiktokv.com
instagram.com, *.instagram.com, *.cdninstagram.com, *.fbcdn.net
huggingface.co, *.huggingface.co, *.hf.co
```
Doku: https://code.claude.com/docs/en/cloud-environments#network-access
