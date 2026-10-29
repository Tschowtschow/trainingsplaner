from aufteilung import gruppen, gruppen_text, teams_text


def test_gruppen_gleichmaessig():
    assert gruppen(14, 6, 7) == [7, 7]
    assert gruppen(15, 6, 8) == [8, 7]
    assert gruppen(15, 6, 7) is None
    assert gruppen(4, 6, 8) is None


def test_texte():
    assert gruppen_text([7, 7]) == "2 Gruppen à 7"
    assert teams_text(14) == "7 gegen 7"
    assert teams_text(15) == "7 gegen 7 + 1 neutraler Joker"
