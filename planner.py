"""
planner.py

Baseline pickleball session planner (rule-based, non-LLM).

Problem: given a pool of players with skill ratings, a number of available
courts, and a session time budget (rounds), produce a round-by-round
schedule of doubles matches (2v2 per court) that:
  1. never double-books a player within a round (hard constraint),
  2. balances average skill across courts within each round, and
  3. minimizes repeated partnerships / repeated opponents across rounds.

Baseline approach (deliberately simple, no LLM / external API):
  - Greedy "snake draft" skill balancing: sort players by skill each round,
    snake them into courts so per-court skill sums are close.
  - Within each court's 4 players, try both possible 2v2 team splits and
    pick the one that reuses the fewest existing partnerships (from
    history), ties broken by skill balance between the two teams.
  - Court size (4) and team structure (2v2) are hardcoded here, which is
    fine for pickleball but doesn't generalize to other sports without
    rewriting those rules. The planned next phase is an LLM-based scheduler
    that can reason about a given sport's rules directly instead, and will
    be benchmarked against this baseline (see proposal Sections 2, 6, 7).
"""
import argparse
import itertools
import json
from collections import defaultdict


def snake_assign_to_courts(players, n_courts):
    """Sort by skill and snake-draft into n_courts groups of 4 to balance
    per-court skill sums."""
    ordered = sorted(players, key=lambda p: p["skill"], reverse=True)
    courts = [[] for _ in range(n_courts)]
    forward = True
    idx = 0
    court_order = list(range(n_courts))
    while idx < len(ordered):
        seq = court_order if forward else list(reversed(court_order))
        for c in seq:
            if idx >= len(ordered):
                break
            courts[c].append(ordered[idx])
            idx += 1
        forward = not forward
    return courts


def best_team_split(four_players, partner_history):
    """Given 4 players on a court, choose the 2v2 split that reuses the
    fewest prior partnerships; break ties by skill balance."""
    a, b, c, d = four_players
    splits = [
        ((a, b), (c, d)),
        ((a, c), (b, d)),
        ((a, d), (b, c)),
    ]

    def repeat_count(team1, team2):
        def pair_key(p, q):
            return tuple(sorted((p["id"], q["id"])))
        r = 0
        if partner_history[pair_key(*team1)] > 0:
            r += 1
        if partner_history[pair_key(*team2)] > 0:
            r += 1
        return r

    def skill_gap(team1, team2):
        s1 = sum(p["skill"] for p in team1)
        s2 = sum(p["skill"] for p in team2)
        return abs(s1 - s2)

    splits.sort(key=lambda st: (repeat_count(*st), skill_gap(*st)))
    return splits[0]


def plan_session(players, n_courts, n_rounds):
    """Produce a full session schedule: list of rounds, each a list of
    court matches. Returns (schedule, stats)."""
    slots_per_round = n_courts * 4
    if len(players) < 4:
        raise ValueError("Need at least 4 players to fill a single court.")
    if len(players) > slots_per_round:
        # Not everyone plays every round -- rotate a sitting-out group.
        pass

    partner_history = defaultdict(int)
    opponent_history = defaultdict(int)
    sit_out_count = defaultdict(int)
    schedule = []

    for r in range(n_rounds):
        # Choose who sits out this round (fewest total appearances so far
        # get priority to play).
        appearances = defaultdict(int)
        for rnd in schedule:
            for match in rnd["courts"]:
                for p in match["team1"] + match["team2"]:
                    appearances[p["id"]] += 1

        active_slots = min(slots_per_round, len(players))
        ranked = sorted(
            players,
            key=lambda p: (appearances[p["id"]], sit_out_count[p["id"]] * -1),
        )
        playing = ranked[:active_slots]
        sitting = ranked[active_slots:]
        for p in sitting:
            sit_out_count[p["id"]] += 1

        courts = snake_assign_to_courts(playing, min(n_courts, active_slots // 4))
        round_matches = []
        for court_idx, four in enumerate(courts):
            if len(four) < 4:
                continue  # leftover players who don't fill a full court sit out
            team1, team2 = best_team_split(four, partner_history)

            def pair_key(p, q):
                return tuple(sorted((p["id"], q["id"])))

            partner_history[pair_key(*team1)] += 1
            partner_history[pair_key(*team2)] += 1
            for p in team1:
                for q in team2:
                    opponent_history[pair_key(p, q)] += 1

            round_matches.append({
                "court": court_idx + 1,
                "team1": list(team1),
                "team2": list(team2),
                "team1_skill_sum": sum(p["skill"] for p in team1),
                "team2_skill_sum": sum(p["skill"] for p in team2),
            })

        schedule.append({
            "round": r + 1,
            "courts": round_matches,
            "sitting_out": [p["name"] for p in sitting],
        })

    stats = compute_stats(schedule, partner_history)
    return schedule, stats


def compute_stats(schedule, partner_history):
    repeat_partnerships = sum(1 for v in partner_history.values() if v > 1)
    total_partnerships = len(partner_history)
    skill_gaps = []
    for rnd in schedule:
        for m in rnd["courts"]:
            skill_gaps.append(abs(m["team1_skill_sum"] - m["team2_skill_sum"]))
    avg_gap = sum(skill_gaps) / len(skill_gaps) if skill_gaps else 0
    max_gap = max(skill_gaps) if skill_gaps else 0
    return {
        "total_rounds": len(schedule),
        "total_matches": sum(len(r["courts"]) for r in schedule),
        "distinct_partnerships": total_partnerships,
        "repeated_partnerships": repeat_partnerships,
        "avg_within_match_skill_gap": round(avg_gap, 1),
        "max_within_match_skill_gap": max_gap,
    }


def validate_schedule(schedule, players):
    """Hard-constraint check: no player appears twice within the same round."""
    player_ids = {p["id"] for p in players}
    for rnd in schedule:
        seen = set()
        for m in rnd["courts"]:
            for p in m["team1"] + m["team2"]:
                assert p["id"] not in seen, (
                    f"Player {p['name']} double-booked in round {rnd['round']}"
                )
                assert p["id"] in player_ids
                seen.add(p["id"])
    return True


def main():
    ap = argparse.ArgumentParser(description="Plan a pickleball session")
    ap.add_argument("--players", type=str, default="examples/players.json")
    ap.add_argument("--courts", type=int, default=4, help="Number of courts")
    ap.add_argument("--rounds", type=int, default=4, help="Number of rounds")
    ap.add_argument("--out", type=str, default="examples/schedule.json")
    args = ap.parse_args()

    with open(args.players) as f:
        players = json.load(f)

    schedule, stats = plan_session(players, args.courts, args.rounds)
    validate_schedule(schedule, players)

    print(f"Planned {stats['total_rounds']} rounds, {stats['total_matches']} matches "
          f"across {args.courts} courts for {len(players)} players.\n")
    for rnd in schedule:
        print(f"-- Round {rnd['round']} --")
        for m in rnd["courts"]:
            t1 = " & ".join(p["name"] for p in m["team1"])
            t2 = " & ".join(p["name"] for p in m["team2"])
            print(f"  Court {m['court']}: {t1} ({m['team1_skill_sum']}) "
                  f"vs {t2} ({m['team2_skill_sum']})")
        if rnd["sitting_out"]:
            print(f"  Sitting out: {', '.join(rnd['sitting_out'])}")
        print()

    print("Stats:", json.dumps(stats, indent=2))

    with open(args.out, "w") as f:
        json.dump({"schedule": schedule, "stats": stats}, f, indent=2)
    print(f"\nFull schedule written to {args.out}")


if __name__ == "__main__":
    main()
