#!/usr/bin/env bash
# Setup für die Übungsdatenbank: Video-Tools, Transkription, Grafik/PDF.
# Läuft idempotent – kann bei jeder Session erneut ausgeführt werden.
set -euo pipefail

echo "==> System-Pakete (ffmpeg, poppler, Schriften)"
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v pdftoppm >/dev/null 2>&1 || ! fc-list 2>/dev/null | grep -qi dejavu; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO apt-get update -qq
  $SUDO apt-get install -y -qq ffmpeg poppler-utils fonts-dejavu-core >/dev/null
fi

echo "==> Python-Pakete"
python3 -m pip install -q --upgrade \
  yt-dlp \
  faster-whisper \
  pyyaml \
  ruamel.yaml \
  reportlab \
  svglib

echo "==> Whisper-Modell vorladen (optional, braucht Zugriff auf huggingface.co)"
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" \
  >/dev/null 2>&1 && echo "Whisper-Modell bereit" || echo "WARNUNG: Whisper-Modell nicht geladen (Netzwerk?) - Transkription fällt aus"

echo "==> Prüfung"
ffmpeg -version | head -1
yt-dlp --version
python3 -c "import faster_whisper, yaml, ruamel.yaml, reportlab, svglib; print('Python-Pakete OK')"
echo "Setup fertig."
