# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Python tool that generates spymaster clues for the boardgame Codenames using WordNet (NLTK) hypernym/similarity search, usable both as a CLI (`main.py`) and a Streamlit web app (`streamlit_app.py`, intended for deployment on Streamlit Community Cloud). It is an experiment from this blog post: https://hovinh.github.io/blog/2021-01-16-codenames-cheat-engine/. `glove_tsne.ipynb`/`tsne.txt` is a separate, unrelated experiment testing whether centroid vectors capture word analogies, visualized via openTSNE.

## Environment Setup

Dependencies are managed with [pip-tools](https://github.com/jazzband/pip-tools): top-level deps (including `pytest`) go in `requirements.in`, and `requirements.txt` is the pinned, auto-generated lockfile — this is also what Streamlit Community Cloud installs from, and it's what gets installed for local dev/testing too. Never edit `requirements.txt` by hand.

```bash
python -m venv .venv
.venv/Scripts/pip install pip-tools    # Windows; use .venv/bin/pip on macOS/Linux
.venv/Scripts/python -m piptools sync requirements.txt
```

To add/remove/upgrade a dependency: edit `requirements.in`, then recompile and re-sync:

```bash
.venv/Scripts/python -m piptools compile requirements.in -o requirements.txt
.venv/Scripts/python -m piptools sync requirements.txt
```

NLTK's WordNet corpus must be downloaded separately (`nltk.download('wordnet')`) if not already present, since `boardgame.py` and `spymaster.py` both depend on `nltk.corpus.wordnet` at import time.

## Running

### CLI

Edit `game_idx` in `main.py`'s `__main__` block to select one of the three sample games defined in `sample_games.select_game()`, then:

```bash
.venv/Scripts/python main.py
```

### Streamlit app

```bash
.venv/Scripts/python -m streamlit run streamlit_app.py
```

Lets a user pick a sample board or paste in a custom 25-word board + team assignments, then plays through turns in the browser with clue suggestions, a color-coded board, and score tracking.

## Testing

```bash
.venv/Scripts/python -m pytest
```

Tests live in `tests/` and cover `boardgame.py`, `hint.py`, and `spymaster.py`. `pytest.ini` sets `pythonpath = .` so tests can `import boardgame` etc. directly without installing the package. Tests require the WordNet corpus (see above) and are otherwise deterministic — they assert structural invariants (e.g. every suggested hint covers ≥2 of the team's own words and none of the opponent's) rather than exact hint content, since WordNet traversal results are sensitive to corpus/version.

## Architecture

The engine (`boardgame.py`, `spymaster.py`, `hint.py`) is pure — no I/O, no printing, no `questionary`/`streamlit` calls — so it can be driven by either frontend. `main.py` (CLI) and `streamlit_app.py` (web) are both thin orchestration layers on top of it.

- **`CodenamesBoardGame`** (`boardgame.py`) — owns game state: the board (`_keyword_list`), each team's target words (`_team_guessword_dict`), score, turn order, and `_chosenword_list` (words already picked). Validates on construction that every board word exists in WordNet; winning score per team is derived from how many words that team owns (not hardcoded 9/8), so custom-sized boards work. Key methods:
  - `get_suggestions()` — returns `(hint_list, filtered_guessword_list)` for whichever team's turn it currently is (delegates to `SpyMaster`).
  - `apply_turn(hint, selected_words)` — records the guess, updates score, appends a structured entry to game history, advances the turn, and returns `(team_name, score, required_score)`.
  - `is_game_over()` / `get_winner()` — pure state queries, no printing (the old `check_game_is_over()` printed the winner as a side effect; that's gone).
  - `get_keyword_list()` / `get_team_guessword_dict()` / `get_chosen_words()` / `get_score_dict()` / `get_game_history()` — read-only accessors returning defensive copies, used by both frontends to render the board.
- **`SpyMaster`** (`spymaster.py`) — the clue-generation engine, stateless across turns (shared by both teams). `suggest()` is the entry point:
  1. Filters out already-chosen words from keywords/guesswords, and derives `forbidword_list` (opponent's + neutral words still on the board — anything the hint must NOT lead to).
  2. Generates candidate hypernym synsets two ways: `retrieve_hypernym_set_with_common_approach` (BFS over pairwise `common_hypernyms` of guess words, expanding as new hypernyms are found) and `retrieve_hypernym_set_with_trace_to_root_approach` (walk every guess word's synsets, plus `also_sees`/`similar_tos` relations, up to the WordNet root via `hypernyms()` closure).
  3. `generate_hints()` scores each candidate hypernym against every board-word synset using a configurable WordNet similarity metric (`path`, `lch`, or `wup` — default `lch`, set via `SpyMaster(similarity_method=...)`), reducing per-synset scores to per-word scores, then walks words in descending-score order until hitting a forbidden word. If ≥2 own words are reachable before that cutoff, it becomes a valid `Hint`, ranked by how many words it covers.
- **`Hint`** (`hint.py`) — a small value object bundling a synset, its valid word count, and the correlated board words it covers; `__str__` renders it (definition, examples, lemmas, connected words) for the CLI menu.
- **`sample_games.py`** — the three hardcoded sample boards (`select_game`) and a `print_game` CLI-rendering helper. Kept separate from `main.py` so `streamlit_app.py` can reuse the sample data without pulling in `questionary`/CLI-only code.

### Frontends

- **`main.py`** — CLI orchestrator: `clear_screen()`, `select_hint_and_guesswords()` (the `questionary`-driven prompt loop, with pagination for long hint lists), and `run_cli_game()` (the turn loop, printing state and calling `game.get_suggestions()` / `game.apply_turn()`).
- **`streamlit_app.py`** — Streamlit orchestrator. Holds the `CodenamesBoardGame` instance in `st.session_state['game']`, and caches the current turn's `(hint_list, guessword_list)` in `st.session_state['current_hints']` so `get_suggestions()` (a WordNet BFS, non-trivial cost) isn't recomputed on every widget interaction within a turn — only invalidated after `apply_turn()`. Renders the board as a 5-column grid color-coded by team, with chosen words faded/struck-through.

## Notes for changes

- `CodenamesBoardGame` and `SpyMaster` communicate purely through plain lists/dicts of words and `Hint` objects — no shared mutable state beyond what's passed explicitly, aside from `SpyMaster` being reused across both teams' turns within a game.
- Keep the engine free of I/O and framework imports (`questionary`, `streamlit`) — anything a frontend needs to display should be exposed as a getter on `CodenamesBoardGame`, not printed or rendered from within the engine.
