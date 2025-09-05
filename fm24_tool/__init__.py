"""FM24 squad formation analyzer.

Parse a squad list exported as HTML and suggest the best formation
based on player ratings.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup


@dataclass
class Player:
    name: str
    position: str
    rating: float


FORMATIONS: Dict[str, Dict[str, int]] = {
    "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
    "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
    "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
}


def parse_players(html_path: str | Path) -> List[Player]:
    """Parse player information from an exported HTML table."""
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    table = soup.find("table")
    if table is None:
        return []
    players: List[Player] = []
    rows = table.find_all("tr")
    for row in rows[1:]:
        cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
        if len(cells) < 3:
            continue
        name, position, rating_str = cells[0], cells[1], cells[2]
        try:
            rating = float(rating_str)
        except ValueError:
            continue
        players.append(Player(name=name, position=position, rating=rating))
    return players


def _category(position: str) -> str | None:
    pos = position.upper()
    if "GK" in pos:
        return "GK"
    if "D" in pos:
        return "DEF"
    if "M" in pos:
        return "MID"
    if "ST" in pos or "FW" in pos:
        return "FWD"
    return None


def formation_score(players: List[Player], formation: Dict[str, int]) -> float:
    grouped: Dict[str, List[float]] = {"GK": [], "DEF": [], "MID": [], "FWD": []}
    for p in players:
        cat = _category(p.position)
        if cat:
            grouped[cat].append(p.rating)
    for ratings in grouped.values():
        ratings.sort(reverse=True)
    total_rating = 0.0
    total_slots = sum(formation.values())
    for cat, needed in formation.items():
        ratings = grouped.get(cat, [])
        if len(ratings) < needed:
            ratings = ratings + [0.0] * (needed - len(ratings))
        total_rating += sum(ratings[:needed])
    return total_rating / total_slots if total_slots else 0.0


def best_formation(players: List[Player]) -> tuple[str, float]:
    scores = {name: formation_score(players, f) for name, f in FORMATIONS.items()}
    best = max(scores, key=scores.get)
    return best, scores[best]


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Suggest best formation for a squad")
    parser.add_argument("html_file", help="Path to HTML file with player table")
    args = parser.parse_args(argv)
    players = parse_players(args.html_file)
    if not players:
        print("No players found in HTML file.")
        raise SystemExit(1)
    formation, score = best_formation(players)
    print(f"Best formation: {formation} (score {score:.2f}/100)")


if __name__ == "__main__":
    main()
