import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TESTPLAN = ROOT / "plaene" / "2026-11-03_torabschluss.yaml"


def lauf(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=ROOT)


def test_testplan_ergibt_pdf(tmp_path):
    ziel = tmp_path / "plan.yaml"
    ziel.write_text(TESTPLAN.read_text())
    r = lauf(ROOT / "scripts" / "plan_pdf.py", ziel)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "plan.pdf").stat().st_size > 10_000


def test_rahmenverstoss_bricht_ab(tmp_path):
    plan = yaml.safe_load(TESTPLAN.read_text())
    plan["teile"][-1]["dauer_min"] = 15          # Abschlussspiel < 20 und Summe != 120
    ziel = tmp_path / "plan.yaml"
    ziel.write_text(yaml.safe_dump(plan, allow_unicode=True))
    r = lauf(ROOT / "scripts" / "plan_pdf.py", ziel)
    assert r.returncode == 1
    assert "Abschlussspiel" in r.stderr and "120" in r.stderr


def test_vorschlag_haelt_rahmen_ein(tmp_path):
    ziel = tmp_path / "entwurf.yaml"
    r = lauf(ROOT / "scripts" / "plan_vorschlag.py", "Donnerstag", "Torabschluss", 14, 2,
             "--heute", "2026-10-30", "--ausgabe", ziel)
    assert r.returncode == 0, r.stderr
    plan = yaml.safe_load(ziel.read_text())
    assert str(plan["datum"]) == "2026-11-05"
    assert [e["teil"] for e in plan["teile"]] == ["Lauf-ABC", "Erweitertes Aufwärmen", "Hauptteil 1",
                                                   "Hauptteil 2", "Schlussteil 1", "Abschlussspiel"]
    assert sum(e["dauer_min"] for e in plan["teile"]) == 120
    assert len({e["uebung"] for e in plan["teile"]}) == 6
    # Entwurf enthält TODOs -> PDF wird verweigert
    r = lauf(ROOT / "scripts" / "plan_pdf.py", ziel)
    assert r.returncode == 1 and "TODO" in r.stderr


def test_uebersicht_aktuell():
    r = lauf(ROOT / "scripts" / "uebersicht.py", "--check")
    assert r.returncode == 0, r.stderr + r.stdout
