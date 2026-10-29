#!/usr/bin/env python3
"""Lädt ein Übungsvideo, transkribiert den Ton und zieht Standbilder.

Alles landet in arbeit/<kurzname>/ (nicht im Repo):
  video.mp4, info.json, audio.wav, transkript.txt, frames/*.jpg, uebersicht_*.jpg

Aufruf:
  python3 scripts/video_holen.py <kurzname> <url>
  python3 scripts/video_holen.py <kurzname> --datei /pfad/zum/video.mp4
Optionen:
  --frames N        Standbilder im Raster (Standard 24) – dazu kommen Bilder bei Szenenwechseln
  --whisper MODELL  tiny/base/small/medium (Standard small)
  --ohne-ton        keine Transkription
"""
import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def download(url, ziel: Path) -> dict:
    import yt_dlp

    opts = {
        "outtmpl": str(ziel / "video.%(ext)s"),
        "format": "bv*[height<=720]+ba/b[height<=720]/bv*+ba/b",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    meta = {k: info.get(k) for k in ("title", "uploader", "description", "duration", "webpage_url", "tags")}
    (ziel / "info.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    # yt-dlp kann je nach Quelle .mp4/.webm/.mkv liefern
    for f in ziel.glob("video.*"):
        if f.suffix != ".json":
            if f.name != "video.mp4":
                run(["ffmpeg", "-y", "-i", str(f), "-c", "copy", str(ziel / "video.mp4")])
            break
    return meta


def dauer(video: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out or 0)


def szenenwechsel(video: Path, schwelle: float = 0.3) -> list[float]:
    """Zeitpunkte, an denen sich das Bild stark ändert (Schnitt, neue Einblendung, neue Übungsphase)."""
    out = subprocess.run(
        ["ffmpeg", "-i", str(video), "-vf", f"select='gt(scene,{schwelle})',showinfo", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    return [float(m.group(1)) for m in re.finditer(r"pts_time:([\d.]+)", out)]


def zeitpunkte(video: Path, anzahl: int, laenge: float) -> list[float]:
    """Gleichmäßiges Raster + Szenenwechsel, ohne Dopplungen, höchstens 1,5 x anzahl Bilder."""
    abstand = max(1.0, laenge / anzahl)
    raster = [min(0.5, laenge / 2) + i * abstand for i in range(anzahl) if i * abstand < laenge]
    # kurz nach dem Schnitt, damit Einblendungen schon stehen
    szenen = [min(t + 0.4, laenge - 0.1) for t in szenenwechsel(video)]
    alle = sorted(raster + szenen)
    zeiten = []
    for t in alle:
        if not zeiten or t - zeiten[-1] >= abstand / 2:
            zeiten.append(t)
    grenze = int(anzahl * 1.5)
    if len(zeiten) > grenze:  # gleichmäßig ausdünnen
        zeiten = [zeiten[round(i * (len(zeiten) - 1) / (grenze - 1))] for i in range(grenze)]
    return zeiten


def frames(video: Path, ziel: Path, anzahl: int, laenge: float) -> list[tuple[float, Path]]:
    fdir = ziel / "frames"
    shutil.rmtree(fdir, ignore_errors=True)
    fdir.mkdir()
    bilder = []
    for i, t in enumerate(zeitpunkte(video, anzahl, laenge)):
        # 960 px breit, damit eingeblendeter Text lesbar bleibt
        p = fdir / f"f{i:03d}_{int(t // 60):02d}m{int(t % 60):02d}s.jpg"
        run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
             "-vf", "scale=960:-2", "-q:v", "3", str(p)])
        if p.exists():
            bilder.append((t, p))
    return bilder


def uebersichten(bilder, ziel: Path, pro_blatt: int = 9) -> list[Path]:
    """Fasst je 9 Standbilder mit Zeitstempel zu einem Kontaktbogen zusammen."""
    from PIL import Image, ImageDraw, ImageFont

    for alt in ziel.glob("uebersicht_*.jpg"):
        alt.unlink()
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    blaetter = []
    for b in range(math.ceil(len(bilder) / pro_blatt)):
        teil = bilder[b * pro_blatt:(b + 1) * pro_blatt]
        imgs = [Image.open(p).convert("RGB") for _, p in teil]
        w = 400
        h = max(int(im.height * w / im.width) for im in imgs)
        spalten = 3
        zeilen = math.ceil(len(imgs) / spalten)
        blatt = Image.new("RGB", (spalten * w, zeilen * h), "white")
        d = ImageDraw.Draw(blatt)
        for k, ((t, _), im) in enumerate(zip(teil, imgs)):
            im = im.resize((w, int(im.height * w / im.width)))
            x, y = (k % spalten) * w, (k // spalten) * h
            blatt.paste(im, (x, y))
            label = f"{int(t // 60)}:{int(t % 60):02d}"
            d.rectangle([x, y, x + 70, y + 28], fill="black")
            d.text((x + 6, y + 2), label, fill="yellow", font=font)
        p = ziel / f"uebersicht_{b + 1}.jpg"
        blatt.save(p, quality=80)
        blaetter.append(p)
    return blaetter


def transkribieren(video: Path, ziel: Path, modell: str) -> str:
    audio = ziel / "audio.wav"
    run(["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
    from faster_whisper import WhisperModel

    m = WhisperModel(modell, device="cpu", compute_type="int8")
    segmente, info = m.transcribe(str(audio), vad_filter=True)
    zeilen = [f"[{int(s.start // 60)}:{int(s.start % 60):02d}] {s.text.strip()}" for s in segmente]
    text = f"# Sprache: {info.language} ({info.language_probability:.0%})\n" + "\n".join(zeilen)
    (ziel / "transkript.txt").write_text(text)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kurzname")
    ap.add_argument("url", nargs="?")
    ap.add_argument("--datei")
    ap.add_argument("--frames", type=int, default=24)
    ap.add_argument("--whisper", default="small")
    ap.add_argument("--ohne-ton", action="store_true")
    a = ap.parse_args()
    if not a.url and not a.datei:
        ap.error("URL oder --datei angeben")

    ziel = ROOT / "arbeit" / a.kurzname
    ziel.mkdir(parents=True, exist_ok=True)

    meta = {}
    if a.datei:
        shutil.copy(a.datei, ziel / "video_quelle")
        run(["ffmpeg", "-y", "-i", str(ziel / "video_quelle"), "-c", "copy", str(ziel / "video.mp4")])
    else:
        try:
            meta = download(a.url, ziel)
        except Exception as e:  # noqa: BLE001 – Fehlermeldung an den Chat weitergeben
            print(f"DOWNLOAD FEHLGESCHLAGEN: {e}", file=sys.stderr)
            sys.exit(2)

    video = ziel / "video.mp4"
    laenge = dauer(video)
    bilder = frames(video, ziel, a.frames, laenge)
    blaetter = uebersichten(bilder, ziel)

    text = ""
    if not a.ohne_ton:
        try:
            text = transkribieren(video, ziel, a.whisper)
        except Exception as e:  # noqa: BLE001
            text = f"(Transkription fehlgeschlagen: {e})"

    print(f"== {a.kurzname} ==")
    if meta:
        print(f"Titel:   {meta.get('title')}")
        print(f"Kanal:   {meta.get('uploader')}")
        print(f"Quelle:  {meta.get('webpage_url')}")
        if meta.get("description"):
            print(f"Beschreibung:\n{meta['description'][:1500]}")
    print(f"Länge:   {laenge:.0f} s, {len(bilder)} Standbilder")
    print("Kontaktbögen:")
    for p in blaetter:
        print(f"  {p}")
    print(f"Einzelbilder: {ziel / 'frames'}")
    print("Transkript:")
    print(text or "(keins)")


if __name__ == "__main__":
    main()
