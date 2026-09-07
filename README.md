# Pickleball Session Planner — Capstone Baseline

A minimal, runnable baseline for planning pickleball open-play/tournament
sessions: given a pool of players (with skill ratings), a number of courts,
and a number of rounds, it produces a round-by-round schedule of doubles
matches that avoids double-booking, balances skill across courts, and tries
to minimize repeated partnerships.

This baseline is deliberately rule-based and pickleball-specific (court size
and team structure are hardcoded). The planned next phase is an LLM-based
scheduler that can reason about the rules of other sports directly instead
of needing hardcoded logic rewritten per sport — see the proposal for the
full motivation and evaluation plan.

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

Step 1 — generate synthetic player data (stand-in for real match history and
skill ratings, since no real dataset exists yet):

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
  duplicating Round 1 exactly.
- Skill balance is "good enough" greedy, not optimal — `max_within_match_skill_gap`
  of 916 in this run shows some rounds are meaningfully lopsided.

## Next phase

The planned next step is an LLM-based scheduler that reasons about a given
sport's rules (team size, court structure) directly, instead of relying on
hardcoded rules like this baseline does. It will be benchmarked against this
baseline on repeated-partnership rate, skill-balance gap, constraint
satisfaction (no double-booking), and added cost/latency per LLM call. See
the proposal (Sections 2, 6, 7) for details.
