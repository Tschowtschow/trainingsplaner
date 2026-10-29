from datenbank import finde, normal, quelle_normal


def test_normal_gleicht_schreibweisen_an():
    assert normal("Rondo 5v2") == normal("rondo-5gegen2") == normal("Rondo 5 gegen 2")
    assert normal("Übung") == "uebung"


def test_finde_ungefaehren_namen():
    assert [u["_kurz"] for u in finde("Rondo 5v2")] == ["rondo-5gegen2"]
    assert [u["_kurz"] for u in finde("rondo-5gegen2")] == ["rondo-5gegen2"]
    assert finde("gibtsnicht-xyz") == []


def test_finde_meldet_mehrdeutige_treffer():
    assert len(finde("Doppelpass")) == 2


def test_quelle_normal_entfernt_tracking():
    assert quelle_normal("https://www.instagram.com/reel/De3it5is6Nl/?psln=abc") == \
        "https://www.instagram.com/reel/De3it5is6Nl"
    assert quelle_normal("https://youtu.be/abc?si=x") == "https://www.youtube.com/watch?v=abc"
    assert quelle_normal("https://m.youtube.com/shorts/XYZ") == "https://www.youtube.com/watch?v=XYZ"
    assert quelle_normal("https://www.youtube.com/watch?v=abc&t=10") == "https://www.youtube.com/watch?v=abc"
    assert quelle_normal("eigene Übung") == "eigene Übung"
