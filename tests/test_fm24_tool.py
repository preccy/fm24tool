import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fm24_tool import parse_players, best_formation, formation_scores


def test_parse_players():
    players = parse_players("tests/data/exported_squad.html")
    assert len(players) > 0
    assert players[0].name == "Gogoated"
    assert players[0].position == "GK"
    assert players[0].rating == 94.0


def test_best_formation():
    players = parse_players("tests/data/exported_squad.html")
    formation, score = best_formation(players)
    assert formation == "4-4-2"
    assert 0 <= score <= 100


def test_formation_scores():
    players = parse_players("tests/data/exported_squad.html")
    scores = formation_scores(players)
    assert list(scores)[0] == best_formation(players)[0]
    assert all(0 <= s <= 100 for s in scores.values())
