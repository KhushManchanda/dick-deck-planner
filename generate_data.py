"""
generate_data.py

Generates a synthetic set of players with skill (Elo-style) ratings, standing
in for real Dink Deck match history. Dink Deck currently only tracks names +
anti-repeat logic (no ratings yet), so this simulates what a ratings table
would look like once basic win/loss tracking is added.

Usage:
    python generate_data.py --players 16 --seed 42 --out examples/players.json
"""
import argparse
import json
import random


def generate_players(n_players: int, seed: int):
    rng = random.Random(seed)
    first_names = [
        "Aria", "Blake", "Carter", "Dana", "Eli", "Farah", "Gus", "Hana",
        "Ivan", "Jade", "Kai", "Luna", "Milo", "Nora", "Omar", "Priya",
        "Quinn", "Rosa", "Sam", "Tara", "Umar", "Vera", "Wes", "Xena",
    ]
    rng.shuffle(first_names)
    players = []
    for i in range(n_players):
        name = first_names[i % len(first_names)]
        # Elo-style skill rating, roughly N(1500, 200), clipped to a sane range.
        skill = round(min(max(rng.gauss(1500, 200), 900), 2100))
        players.append({"id": i, "name": name, "skill": skill})
    return players


def main():
    ap = argparse.ArgumentParser(description="Generate synthetic player data")
    ap.add_argument("--players", type=int, default=16, help="Number of players")
    ap.add_argument("--seed", type=int, default=42, help="Random seed")
    ap.add_argument("--out", type=str, default="examples/players.json")
    args = ap.parse_args()

    players = generate_players(args.players, args.seed)
    with open(args.out, "w") as f:
        json.dump(players, f, indent=2)
    print(f"Wrote {len(players)} synthetic players to {args.out}")


if __name__ == "__main__":
    main()
