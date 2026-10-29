import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def test_feedback_haengt_an_und_erhaelt_format(tmp_path, monkeypatch):
    # Arbeitskopie des Repos, damit die echte Karte unberührt bleibt
    kopie = tmp_path / "repo"
    shutil.copytree(ROOT / "scripts", kopie / "scripts")
    shutil.copytree(ROOT / "uebungen" / "rondo-5gegen2", kopie / "uebungen" / "rondo-5gegen2")
    r = subprocess.run([sys.executable, kopie / "scripts" / "feedback.py", "Rondo 5v2", "--bewertung", "4",
                        "--notiz", "Feld zu groß: mit 12 besser", "--datum", "2026-11-03"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    karte = kopie / "uebungen" / "rondo-5gegen2" / "uebung.yaml"
    u = yaml.safe_load(karte.read_text())
    assert u["feedback"][-1] == {"datum": "2026-11-03", "bewertung": 4, "notiz": "Feld zu groß: mit 12 besser"}
    assert "{typ: huetchen, x: 0, y: 0}" in karte.read_text()   # Flow-Stil der Grafikdaten bleibt
