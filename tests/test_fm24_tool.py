import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fm24_tool import parse_players, best_formation


def test_parse_players():
    players = parse_players("tests/data/sample_squad.html")
    assert len(players) == 13
    assert players[0].name == "G1"


def test_best_formation():
    players = parse_players("tests/data/sample_squad.html")
    formation, score = best_formation(players)
    assert formation == "4-4-2"
    assert 0 <= score <= 100
