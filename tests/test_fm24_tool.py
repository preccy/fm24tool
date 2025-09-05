import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fm24_tool import parse_players, best_formation, formation_scores


def test_parse_players():
    players = parse_players("tests/data/sample_squad.html")
    assert len(players) == 13
    assert players[0].name == "G1"


def test_parse_exported_format():
    players = parse_players("tests/data/exported_squad.html")
    assert len(players) == 2
    assert players[0].name == "G1"
    assert players[0].position == "GK"
    # CA values are normalized to a 0-100 scale
    assert players[0].rating == 50.0


def test_best_formation():
    players = parse_players("tests/data/sample_squad.html")
    formation, score = best_formation(players)
    assert formation == "4-4-2"
    assert 0 <= score <= 100


def test_formation_scores():
    players = parse_players("tests/data/sample_squad.html")
    scores = formation_scores(players)
    assert list(scores)[0] == "4-4-2"
    assert all(0 <= s <= 100 for s in scores.values())
