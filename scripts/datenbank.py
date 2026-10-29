"""Gemeinsame Hilfen: Übungen laden und Übungen über ungefähre Namen finden."""
import difflib
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
UEBUNGEN = ROOT / "uebungen"


def alle():
    for p in sorted(UEBUNGEN.glob("*/uebung.yaml")):
        u = yaml.safe_load(p.read_text())
        u["_kurz"] = p.parent.name
        yield u


def normal(text: str) -> str:
    """'Rondo 5v2' == 'rondo-5gegen2' == 'Rondo 5 gegen 2'."""
    t = str(text).lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    t = re.sub(r"(\d)\s*(?:v|vs|gg|gegen|:|x)\s*(\d)", r"\1gegen\2", t)
    return re.sub(r"[^a-z0-9]", "", t)


def finde(begriff: str) -> list[dict]:
    """Liefert die passenden Übungen – genau eine = eindeutig."""
    uebungen = list(alle())
    q = normal(begriff)
    for u in uebungen:
        if u["_kurz"] == begriff or normal(u["_kurz"]) == q or normal(u["name"]) == q:
            return [u]
    treffer = [u for u in uebungen if q in normal(u["name"]) or q in normal(u["_kurz"])]
    if treffer:
        return treffer
    werte = sorted(((max(difflib.SequenceMatcher(None, q, normal(u["name"])).ratio(),
                         difflib.SequenceMatcher(None, q, normal(u["_kurz"])).ratio()), u) for u in uebungen),
                   key=lambda x: -x[0])
    if werte and werte[0][0] >= 0.6:
        beste = werte[0][0]
        return [u for w, u in werte if w >= beste - 0.05]
    return []
