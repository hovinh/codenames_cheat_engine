# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Python tool that generates spymaster clues for the boardgame Codenames, usable both as a CLI (`main.py`) and a Streamlit web app (`streamlit_app.py`, intended for deployment on Streamlit Community Cloud). Two interchangeable clue engines are available: WordNet (NLTK hypernym/similarity search) and ConceptNet (a broader commonsense association graph, read from a bundled offline dataset). It is an experiment from this blog post: https://hovinh.github.io/blog/2021-01-16-codenames-cheat-engine/. `glove_tsne.ipynb`/`tsne.txt` is a separate, unrelated experiment testing whether centroid vectors capture word analogies, visualized via openTSNE.

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

Tests live in `tests/` and cover `boardgame.py`, `hint.py`, `spymaster.py`, `clue_safety.py`, and the ConceptNet engine (`concept_net_data.py`, `concept_net_hint.py`, `concept_net_spymaster.py`). `pytest.ini` sets `pythonpath = .` so tests can `import boardgame` etc. directly without installing the package. Tests require the WordNet corpus (see above) but never hit the network or the real ConceptNet dataset — ConceptNet tests either use a tiny fixture file (`tests/test_concept_net_data.py`, via `monkeypatch`-ing `concept_net_data.DATA_PATH` + `_load_index.cache_clear()`) or mock `concept_net_data.get_related_concepts` entirely (`tests/test_concept_net_spymaster.py`). Assertions generally check structural invariants (e.g. every suggested hint covers ≥2 of the team's own words and none of the opponent's, and never leaks a form of a board word) rather than exact hint content, since both engines' outputs are sensitive to corpus/dataset version.

## Architecture

The engine layer (`boardgame.py`, `spymaster.py`, `hint.py`, `concept_net_spymaster.py`, `concept_net_hint.py`, `concept_net_data.py`, `clue_safety.py`) is pure — no I/O, no printing, no `questionary`/`streamlit` calls — so it can be driven by either frontend. `main.py` (CLI) and `streamlit_app.py` (web) are both thin orchestration layers on top of it.

- **`CodenamesBoardGame`** (`boardgame.py`) — owns game state: the board (`_keyword_list`), each team's target words (`_team_guessword_dict`), score, turn order, and `_chosenword_list` (words already picked). Validates on construction that every board word exists in WordNet; winning score per team is derived from how many words that team owns (not hardcoded 9/8), so custom-sized boards work. Takes an optional `spy_master` param (defaults to `SpyMaster()`) — this is the seam that lets a frontend swap in `ConceptNetSpyMaster` instead. Key methods:
  - `get_suggestions()` — returns `(hint_list, filtered_guessword_list)` for whichever team's turn it currently is (delegates to whichever `spy_master` was injected).
  - `apply_turn(hint, selected_words)` — records the guess, updates score, appends a structured entry to game history, advances the turn, and returns `(team_name, score, required_score)`.
  - `is_game_over()` / `get_winner()` — pure state queries, no printing (the old `check_game_is_over()` printed the winner as a side effect; that's gone).
  - `get_keyword_list()` / `get_team_guessword_dict()` / `get_chosen_words()` / `get_score_dict()` / `get_game_history()` — read-only accessors returning defensive copies, used by both frontends to render the board.
- **`SpyMaster`** (`spymaster.py`) — the WordNet clue-generation engine, stateless across turns (shared by both teams). `suggest()` is the entry point:
  1. Filters out already-chosen words from keywords/guesswords, and derives `forbidword_list` (opponent's + neutral words still on the board — anything the hint must NOT lead to).
  2. Generates candidate hypernym synsets two ways: `retrieve_hypernym_set_with_common_approach` (BFS over pairwise `common_hypernyms` of guess words, expanding as new hypernyms are found) and `retrieve_hypernym_set_with_trace_to_root_approach` (walk every guess word's synsets, plus `also_sees`/`similar_tos` relations, up to the WordNet root via `hypernyms()` closure).
  3. `generate_hints()` skips any candidate hypernym whose lemma is itself a form of a board word (via `clue_safety.is_related_to_board_word`, see below), then scores the rest against every board-word synset using a configurable WordNet similarity metric (`path`, `lch`, or `wup` — default `lch`, set via `SpyMaster(similarity_method=...)`), reducing per-synset scores to per-word scores, then walks words in descending-score order until hitting a forbidden word. If ≥2 own words are reachable before that cutoff, it becomes a valid `Hint`, ranked by how many words it covers.
- **`ConceptNetSpyMaster`** (`concept_net_spymaster.py`) — a second engine implementing the same `suggest(keyword_list, guessword_list, chosenword_list) -> (hint_list, filtered_guessword_list)` contract, using ConceptNet's `RelatedTo` commonsense graph instead of WordNet's is-a taxonomy. For each guess word, looks up its neighbors via `concept_net_data.get_related_concepts()`; a neighbor shared by ≥2 guess words (each above `min_weight`) becomes a candidate, ranked by summed edge weight. Rejected if it's a form of any board word (`clue_safety`) or also shows up as a neighbor of a forbidden word. Currently only queries the `/r/RelatedTo` relation (deliberately narrow start — see `data/README.md` for how to broaden it).
- **`concept_net_data.py`** — lazy-loads `data/conceptnet_relatedto_nouns_en.tsv.gz` (a pre-filtered, English, noun-noun, `RelatedTo`-only subset of ConceptNet 5.7 — see `data/README.md`) into an in-memory `{word: {neighbor: weight}}` index on first use, cached for the process lifetime via `functools.lru_cache`. Reads the gzip file directly, never decompresses to disk. No network calls at runtime — ConceptNet's live public API was found to be unreliable (502s), so this project uses a bundled offline dataset instead.
- **`clue_safety.is_related_to_board_word()`** — shared by both engines. Mirrors Codenames' "a clue can't be a form of a word on the board" rule via a substring heuristic (e.g. `"seal"` vs `"sealed"`), with a minimum-length guard so short words don't produce false positives.
- **`Hint`** (`hint.py`) / **`ConceptNetHint`** (`concept_net_hint.py`) — both expose the same small interface so frontends don't need to know which engine produced a hint: `get_info()` → `(identifier, valid_word_count, correlated_word_list)`, `get_label()`, `get_definition()`, `get_examples()`, and `__str__()`. `Hint` wraps a WordNet synset (real definitions/examples); `ConceptNetHint` wraps a bare concept word (no definition/examples — ConceptNet doesn't have dictionary glosses).
- **`sample_games.py`** — the three hardcoded sample boards (`select_game`) and a `print_game` CLI-rendering helper. Kept separate from `main.py` so `streamlit_app.py` can reuse the sample data without pulling in `questionary`/CLI-only code.

### Frontends

- **`main.py`** — CLI orchestrator: `clear_screen()`, `select_hint_and_guesswords()` (the `questionary`-driven prompt loop, with pagination for long hint lists), and `run_cli_game()` (the turn loop, printing state and calling `game.get_suggestions()` / `game.apply_turn()`). Always uses the default WordNet engine.
- **`streamlit_app.py`** — Streamlit orchestrator. Holds the `CodenamesBoardGame` instance in `st.session_state['game']`, and caches the current turn's `(hint_list, guessword_list)` in `st.session_state['current_hints']` so `get_suggestions()` isn't recomputed on every widget interaction within a turn — only invalidated after `apply_turn()`. Renders the board as a 5-column grid color-coded by team, with chosen words faded/struck-through. `CLUE_ENGINES` maps the UI's "Clue engine" radio (WordNet / ConceptNet) to the corresponding class, instantiated when the game is created. The landing page (`render_setup`) shows a brief bulleted how-to-use guide above the board-source picker.

## Notes for changes

- `CodenamesBoardGame` and both `SpyMaster`/`ConceptNetSpyMaster` communicate purely through plain lists/dicts of words and `Hint`/`ConceptNetHint` objects — no shared mutable state beyond what's passed explicitly, aside from the spy_master being reused across both teams' turns within a game.
- Keep the engine free of I/O and framework imports (`questionary`, `streamlit`) — anything a frontend needs to display should be exposed as a getter on `CodenamesBoardGame` or the `Hint`/`ConceptNetHint` interface, not printed or rendered from within the engine.
- To regenerate/broaden the ConceptNet dataset (e.g. add relations beyond `RelatedTo`), see `data/README.md` and `scripts/build_conceptnet_data.py`.
