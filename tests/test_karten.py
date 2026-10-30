from pathlib import Path

import pytest
import yaml

from diagramm import Zeichner, diagramme, pruefen as diagramm_pruefen
from pruefen import pruefe

ROOT = Path(__file__).resolve().parent.parent
KARTEN = sorted((ROOT / "uebungen").glob("*/uebung.yaml"))


@pytest.mark.parametrize("karte", KARTEN, ids=lambda p: p.parent.name)
def test_karte_gueltig(karte):
    assert pruefe(karte) == []


@pytest.mark.parametrize("karte", KARTEN, ids=lambda p: p.parent.name)
def test_grafik_ohne_warnungen_und_aktuell(karte):
    u = yaml.safe_load(karte.read_text())
    namen = ["diagramm.svg"] + [f"diagramm-{i}.svg" for i in range(2, len(diagramme(u)) + 1)]
    for d, name in zip(diagramme(u), namen):
        assert diagramm_pruefen(d) == []
        # eingecheckte SVG muss zur YAML passen (sonst diagramm.py vergessen)
        assert (karte.parent / name).read_text() == Zeichner(d).svg(d)


def test_ueberlappung_wird_erkannt():
    d = {"feld": {"laenge": 20, "breite": 20},
         "objekte": [{"typ": "spieler", "x": 5, "y": 5}, {"typ": "spieler", "x": 5.5, "y": 5}],
         "pfeile": []}
    assert any("überlappen" in w for w in diagramm_pruefen(d))


def test_schlussteil_nur_spielform(tmp_path):
    karte = yaml.safe_load((ROOT / "uebungen" / "torabschluss-zwei-ablagen" / "uebung.yaml").read_text())
    karte["phase"] = ["Hauptteil", "Schlussteil"]          # fester Ablauf, keine Gegenspieler
    p = tmp_path / "x" / "uebung.yaml"
    p.parent.mkdir()
    p.write_text(yaml.safe_dump(karte, allow_unicode=True))
    (p.parent / "diagramm.svg").write_text("<svg/>")
    assert any("Schlussteil" in f for f in pruefe(p))
