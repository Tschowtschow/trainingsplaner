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


def quelle_normal(url: str) -> str:
    """Einheitliche Form eines Video-Links, damit Duplikate erkannt werden.

    Entfernt Tracking-Parameter (?psln=, ?si=, ?igsh= ...), www/m-Präfixe und Schrägstriche am Ende;
    YouTube-Kurzlinks und Shorts werden auf watch?v=<id> abgebildet."""
    from urllib.parse import parse_qs, urlparse

    url = str(url).strip()
    if not re.match(r"https?://", url):
        return url
    u = urlparse(url)
    host = re.sub(r"^(www\.|m\.|vm\.)", "", u.netloc.lower())
    pfad = u.path.rstrip("/")
    if host == "youtu.be":
        return f"https://www.youtube.com/watch?v={pfad.lstrip('/')}"
    if host.endswith("youtube.com"):
        if pfad.startswith("/shorts/"):
            return f"https://www.youtube.com/watch?v={pfad.split('/')[2]}"
        vid = parse_qs(u.query).get("v")
        if vid:
            return f"https://www.youtube.com/watch?v={vid[0]}"
    if host.endswith("instagram.com"):
        teile = [t for t in pfad.split("/") if t]
        for i, t in enumerate(teile):
            if t in ("reel", "reels", "p", "tv") and i + 1 < len(teile):
                return f"https://www.instagram.com/reel/{teile[i + 1]}"
    return f"https://{host}{pfad}"


def finde_quelle(url: str) -> list[str]:
    """Kurznamen der Übungen, die schon aus diesem Video angelegt wurden."""
    ziel = quelle_normal(url)
    return [u["_kurz"] for u in alle() if quelle_normal(str(u.get("quelle", ""))) == ziel]


PLAENE = ROOT / "plaene"


def plaene(mit_tests=False):
    """Alle gespeicherten Pläne, älteste zuerst; Testpläne (`test: true`) nur auf Wunsch."""
    for p in sorted(PLAENE.glob("*.yaml")):
        plan = yaml.safe_load(p.read_text())
        if plan.get("test") and not mit_tests:
            continue
        plan["_datei"] = p.name
        yield plan


def historie() -> dict[str, list]:
    """Kurzname -> Liste der Plandaten (datetime.date), an denen die Übung eingeplant war."""
    import datetime as dt

    h: dict[str, list] = {}
    for plan in plaene():
        datum = dt.date.fromisoformat(str(plan["datum"]))
        for e in plan.get("teile") or []:
            if e.get("uebung"):
                h.setdefault(e["uebung"], []).append(datum)
    return h


def bewertung(u) -> tuple[float | None, int]:
    """(Durchschnitt, Anzahl) der Feedback-Bewertungen."""
    w = [f["bewertung"] for f in u.get("feedback") or [] if f.get("bewertung")]
    return (sum(w) / len(w), len(w)) if w else (None, 0)
