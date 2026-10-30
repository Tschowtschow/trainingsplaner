from video_holen import beschreibung_schreiben


def test_beschreibung_vollstaendig_mit_kommentaren_und_hand(tmp_path):
    lang = "Feld 30 x 20 m. " * 200            # länger als die frühere 1500-Zeichen-Grenze
    meta = {"description": lang, "kanal_kommentare": ["Variante: mit Joker"]}
    text = beschreibung_schreiben(tmp_path, meta, "Caption vom Trainer")
    assert lang.strip() in text
    assert "[Kommentar des Kanals] Variante: mit Joker" in text
    assert text.endswith("Caption vom Trainer")
    assert (tmp_path / "beschreibung.txt").read_text().strip() == text


def test_ohne_beschreibung_leer(tmp_path):
    assert beschreibung_schreiben(tmp_path, {}, None) == ""
