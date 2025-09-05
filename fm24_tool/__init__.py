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

    # Normalize header text to uppercase for case-insensitive matching.
    headers = [c.get_text(strip=True).upper() for c in rows[0].find_all(["th", "td"])]

    def _idx(names: Iterable[str]) -> int | None:
        for n in names:
            n_upper = n.upper()
            if n_upper in headers:
                return headers.index(n_upper)
        return None

    name_idx = _idx(["Player", "Name"])
    pos_idx = _idx(["Position"])
    rating_idx = _idx(["CA", "Ability", "Rating"])  # Allow fallback "Ability"
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
        # Ratings in FM range from 0-200 (CA).  Normalize to a 0-100 scale and
        # clip values outside that range so unrealistic numbers do not skew
        # formation scores.
        rating = max(0.0, min(rating, 200.0)) / 2.0
        players.append(Player(name=name, position=position, rating=rating))
    return players


def _categories(position: str) -> List[str]:
    """Return all category labels a player can cover."""
    pos = position.upper()
    cats: List[str] = []
    if "GK" in pos:
        cats.append("GK")
    if "ST" in pos or "FW" in pos:
        cats.append("FWD")
    if "M" in pos:
        cats.append("MID")
    if "D" in pos:
        cats.append("DEF")
    return cats


def formation_score(players: List[Player], formation: Dict[str, int]) -> float:
    """Return the average rating for a given formation.

    Players are greedily assigned to any category (GK/DEF/MID/FWD) they can
    cover, prioritising higher-rated players.  Ratings are expected to be on a
    0-100 scale.
    """
    remaining = formation.copy()
    total_slots = sum(remaining.values())
    total_rating = 0.0
    for p in sorted(players, key=lambda pl: pl.rating, reverse=True):
        eligible = [c for c in _categories(p.position) if remaining.get(c, 0) > 0]
        if not eligible:
            continue
        # Choose the category with the most remaining slots to reduce skew.
        cat = max(eligible, key=lambda c: remaining[c])
        total_rating += max(0.0, min(p.rating, 100.0))
        remaining[cat] -= 1
    score = total_rating / total_slots if total_slots else 0.0
    return min(score, 100.0)


def formation_scores(players: List[Player]) -> Dict[str, float]:
    """Compute scores for all supported formations sorted by score."""
    scores = {name: formation_score(players, f) for name, f in FORMATIONS.items()}
    return dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))


def best_formation(players: List[Player]) -> tuple[str, float]:
    scores = formation_scores(players)
    best = next(iter(scores.items()))
    return best[0], best[1]


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Suggest best formation for a squad")
    parser.add_argument("html_file", help="Path to HTML file with player table")
    args = parser.parse_args(argv)
    players = parse_players(args.html_file)
    if not players:
        print("No players found in HTML file.")
        raise SystemExit(1)
    scores = formation_scores(players)
    for name, score in scores.items():
        print(f"{name}: {score:.2f}/100")
    best_form, best_score = next(iter(scores.items()))
    print(f"Best formation: {best_form} (score {best_score:.2f}/100)")
