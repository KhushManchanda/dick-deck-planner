# Dink Deck Session Planner — Capstone Baseline

A minimal, runnable baseline for planning pickleball tournament/open-play
sessions: given a pool of players (with skill ratings), a number of courts,
and a number of rounds, it produces a round-by-round schedule of doubles
matches that avoids double-booking, balances skill across courts, and tries
to minimize repeated partnerships.

This extends [Dink Deck](https://github.com/) (mobile-friendly pickleball
team randomizer) from single-round randomization into multi-round session
*planning* under real constraints (courts, time/rounds) — the actual capstone
target ties this to search/CSP-based planning (CSE 574) in later phases.

## 1. Dependencies

- Python 3.8+ (standard library only — no external packages required)

```bash
python3 --version   # confirm 3.8+
```

## 2. No API keys / environment variables required

This baseline is fully local and rule-based — no LLM or external API calls,
so there is nothing to configure.

## 3. Setup

```bash
git clone <this-repo-url>
cd dink-deck-planner
```

No installation step needed beyond having Python 3 available.

## 4. Running the baseline

Step 1 — generate synthetic player data (stand-in for real Dink Deck match
history, since Dink Deck does not yet track skill ratings):

```bash
python3 generate_data.py --players 16 --seed 42 --out examples/players.json
```

Step 2 — run the planner on that data:

```bash
python3 planner.py --players examples/players.json --courts 4 --rounds 4 --out examples/schedule.json
```

## 5. Inputs and outputs

- **Input**: `examples/players.json` — list of `{id, name, skill}` objects.
- **Output**:
  - Console: a human-readable round-by-round schedule + summary stats.
  - `examples/schedule.json`: the full machine-readable schedule and stats.

## 6. Test case

Command used:

```bash
python3 generate_data.py --players 16 --seed 42 --out examples/players.json
python3 planner.py --players examples/players.json --courts 4 --rounds 4 --out examples/schedule.json
```

Expected behavior: 4 rounds of 4 courts each (16 players, 4 per court),
no player double-booked within a round, skill roughly balanced across the
two teams on each court.

Actual output: see `examples/run_output.png` (screenshot) and
`examples/schedule.json` (raw output). Summary stats from this run:

```
total_rounds: 4
total_matches: 16
distinct_partnerships: 24
repeated_partnerships: 8
avg_within_match_skill_gap: 368.1
max_within_match_skill_gap: 916
```

## 7. Known limitations (see proposal Section 7 for more)

- Court groupings are skill-sorted deterministically each round, so with no
  randomization the same 4 players tend to land on the same court every
  round (only their 2v2 split rotates) — visible in this run as Round 4
  duplicating Round 1 exactly. A future version should add randomized
  restarts or real search over groupings, not just team splits.
- Skill balance is "good enough" greedy, not optimal — `max_within_match_skill_gap`
  of 916 in this run shows some rounds are meaningfully lopsided.
