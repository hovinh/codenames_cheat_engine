# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Python CLI tool that generates spymaster clues for the boardgame Codenames using WordNet (NLTK) hypernym/similarity search. It is an experiment from this blog post: https://hovinh.github.io/blog/2021-01-16-codenames-cheat-engine/. `glove_tsne.ipynb`/`tsne.txt` is a separate, unrelated experiment testing whether centroid vectors capture word analogies, visualized via openTSNE.

## Environment Setup

Dependencies are managed with [pip-tools](https://github.com/jazzband/pip-tools): top-level deps go in `requirements.in`, and `requirements.txt` is the pinned, auto-generated lockfile — never edit `requirements.txt` by hand.

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

Edit `game_idx` in `main.py`'s `__main__` block to select one of the three hardcoded games defined in `select_game()`, then:

```bash
.venv/Scripts/python main.py
```

There is no test suite, linter, or build step in this repo — verification is manual, by running a game end-to-end.

## Architecture

Three classes, one per file, wired together in `main.py`:

- **`CodenamesBoardGame`** (`boardgame.py`) — owns game state: the 25-word board (`_keyword_list`), each team's target words (`_team_guessword_dict`), score, turn order, and `_chosenword_list` (words already picked). `start_game()` runs the turn loop: get a suggestion from `SpyMaster`, prompt the human via `questionary` to pick a hint and guess words (`select_hint_and_guesswords`), update state, check win condition (blue needs 9, red needs 8 — red has one fewer target word so plays second), switch turns. Validates on construction that every board word exists in WordNet.
- **`SpyMaster`** (`spymaster.py`) — the clue-generation engine, stateless across turns (shared by both teams). `suggest()` is the entry point:
  1. Filters out already-chosen words from keywords/guesswords, and derives `forbidword_list` (opponent's + neutral words still on the board — anything the hint must NOT lead to).
  2. Generates candidate hypernym synsets two ways: `retrieve_hypernym_set_with_common_approach` (BFS over pairwise `common_hypernyms` of guess words, expanding as new hypernyms are found) and `retrieve_hypernym_set_with_trace_to_root_approach` (walk every guess word's synsets, plus `also_sees`/`similar_tos` relations, up to the WordNet root via `hypernyms()` closure).
  3. `generate_hints()` scores each candidate hypernym against every board-word synset using a configurable WordNet similarity metric (`path`, `lch`, or `wup` — default `lch`, set via `SpyMaster(similarity_method=...)`), reducing per-synset scores to per-word scores, then walks words in descending-score order until hitting a forbidden word. If ≥2 own words are reachable before that cutoff, it becomes a valid `Hint`, ranked by how many words it covers.
- **`Hint`** (`hint.py`) — a small value object bundling a synset, its valid word count, and the correlated board words it covers; `__str__` renders it (definition, examples, lemmas, connected words) for the CLI menu.

`main.py` also defines the three sample games (`select_game`) and a `print_game` helper that renders the board with `|O|`/`|X|`/`| |` markers for blue/red/neutral.

## Notes for changes

- `CodenamesBoardGame` and `SpyMaster` communicate purely through plain lists/dicts of words and `Hint` objects — no shared mutable state beyond what's passed explicitly, aside from `SpyMaster` being reused across both teams' turns within a game.
- Interactive prompts (`questionary.select`, `questionary.checkbox`) are the only user input path; there's no non-interactive/scriptable mode.
