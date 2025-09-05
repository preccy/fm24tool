"""FM24 squad formation analyzer.

Parse a squad list exported as HTML and suggest the best formation
based on player ratings.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from bs4 import BeautifulSoup


@dataclass
class Player:
    name: str
    position: str
    rating: float


# Common FM24 formations expressed as defender-midfield-forward counts.
FORMATION_STRINGS: Iterable[str] = (
    "4-4-2",
    "4-3-3",
    "3-5-2",
    "4-2-3-1",
    "4-4-1-1",
    "4-1-4-1",
    "4-1-3-2",
    "4-5-1",
    "4-3-1-2",
    "4-2-2-2",
    "4-2-4",
    "4-3-2-1",
    "3-4-3",
    "3-4-1-2",
    "3-3-4",
    "5-3-2",
    "5-4-1",
    "5-2-3",
    "5-2-1-2",
    "3-6-1",
)


def _parse_formation(s: str) -> Dict[str, int]:
    """Convert a formation string like "4-2-3-1" into slot counts."""
    parts = [int(p) for p in s.split("-") if p.isdigit()]
    if not parts:
        return {"GK": 1, "DEF": 0, "MID": 0, "FWD": 0}
    defenders = parts[0]
    forwards = parts[-1] if len(parts) > 1 else 0
    midfielders = sum(parts[1:-1]) if len(parts) > 2 else (parts[1] if len(parts) == 2 else 0)
    return {"GK": 1, "DEF": defenders, "MID": midfielders, "FWD": forwards}


FORMATIONS: Dict[str, Dict[str, int]] = {s: _parse_formation(s) for s in FORMATION_STRINGS}


def parse_players(html_path: str | Path) -> List[Player]:
    """Parse player information from an exported HTML table."""
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    table = soup.find("table")
    if table is None:
        return []
    rows = table.find_all("tr")
    if not rows:
        return []

    headers = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]

    def _idx(names: Iterable[str]) -> int | None:
        for n in names:
            if n in headers:
                return headers.index(n)
        return None

    name_idx = _idx(["Player", "Name"])
    pos_idx = _idx(["Position"])
    rating_idx = _idx(["CA", "Rating"])
    if None in (name_idx, pos_idx, rating_idx):
        return []

    players: List[Player] = []
    for row in rows[1:]:
        cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
        if len(cells) <= max(name_idx, pos_idx, rating_idx):
            continue
        name = cells[name_idx].replace(" - Pick Player", "")
        position = cells[pos_idx]
        rating_str = cells[rating_idx]
        try:
            rating = float(rating_str)
        except ValueError:
            digits = "".join(ch for ch in rating_str if ch.isdigit() or ch == ".")
            if not digits:
                continue
            rating = float(digits)
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
