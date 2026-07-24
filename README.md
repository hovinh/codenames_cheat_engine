# Codenames Cheat Engine

This is a python library to generate clue in the Boardgame Codenames, available both as a CLI and as a Streamlit web app. It is a part of fun experiment in this <a href="https://hovinh.github.io/blog/2021-01-16-codenames-cheat-engine/">blog post</a>. 

## Environment Setup

Dependencies are managed with [pip-tools](https://github.com/jazzband/pip-tools). Create a virtual environment and install the pinned dependencies as follows:
```bash
python -m venv .venv
.venv/Scripts/pip install pip-tools    # Windows; use .venv/bin/pip on macOS/Linux
.venv/Scripts/python -m piptools sync requirements.txt
```

To run the notebook, register the venv as a Jupyter kernel:
```bash
.venv/Scripts/python -m ipykernel install --user --name=codenames
```

To change dependencies, edit `requirements.in`, then regenerate the lockfile and re-sync:
```bash
.venv/Scripts/python -m piptools compile requirements.in -o requirements.txt
.venv/Scripts/python -m piptools sync requirements.txt
```

## Getting-started
### Directory structure
- `boardgame.py`, `hint.py`: the core game engine — `CodenamesBoardGame` and `Hint`. Pure logic, no I/O, shared by both frontends below.
- `spymaster.py`: the WordNet clue engine (`SpyMaster`) — dictionary hypernyms/similarity.
- `concept_net_spymaster.py`, `concept_net_hint.py`, `concept_net_data.py`: the ConceptNet clue engine (`ConceptNetSpyMaster`) — a broader commonsense association graph, read from a bundled offline dataset (`data/`). See `data/README.md` for how that dataset was built. Both engines are interchangeable — `CodenamesBoardGame` takes either via its `spy_master` parameter.
- `clue_safety.py`: shared "a clue can't be a form of a board word" check used by both engines.
- `sample_games.py`: the three built-in sample boards.
- `main.py`: the CLI frontend (always uses the WordNet engine). Define your game in `select_game()` (in `sample_games.py`) and pick the corresponding `game_idx` in `main.py`'s `__main__` block.
- `streamlit_app.py`: the Streamlit web app frontend — pick a sample board or build a custom one, choose a clue engine, then play through turns in the browser.
- `glove_tsne.ipynb`, `tsne.txt`: experiment to inspect hypothesis a centroid vector captures analogy to its nearby neighbour words, and its visualization with Open t-SNE tool.

### Running the CLI
1. Select `game_idx` in `main.py`.
```python
game_idx = 2
```
2. Run:
```bash
.venv/Scripts/python main.py
```

### Running the Streamlit app
```bash
.venv/Scripts/python -m streamlit run streamlit_app.py
```
Opens in your browser at `http://localhost:8501`. The landing page has a brief how-to-use guide. Pick a sample board or build a custom one (paste words, or upload/download `example_board.json`), pick a clue engine (WordNet or ConceptNet), then play through turns with clue suggestions, a color-coded board, and score tracking.

### Testing
```bash
.venv/Scripts/python -m pytest
```

### Expected Behaviour (CLI)

The board prints first (`O` = Team Blue, `X` = Team Red, blank = neutral), then each turn shows up to 8 candidate clues at a time (`<8> See the next 8 synsets out of N` to page through more), followed by a checkbox prompt to pick which of that clue's words your team is guessing. Sample transcript from `game_idx = 2`, first turn:

```
['dragon', 'green', 'new_york', 'australia', 'pie']
['seal', 'wake', 'robin', 'pool', 'france']
['trip', 'duck', 'ham', 'shark', 'grace']
['spell', 'buck', 'dice', 'bow', 'spring']
['tube', 'ghost', 'brush', 'drill', 'cotton']

['|X|', '|X|', '| |', '|O|', '| |']
['|X|', '|O|', '|O|', '| |', '|O|']
['|O|', '|X|', '|O|', '|X|', '|O|']
['|O|', '| |', '|X|', '|X|', '| |']
['| |', '|O|', '|X|', '| |', '| |']

Legend
O: Team Blue
X: Team Red

This is team_blue's turn.
<0>  Synset Synset('charm.v.02') | Definition: control by magic spells, as by practicing witchcraft
Examples: []
Count: 4 | Lemmas: [charm, becharm] | Connected words: [spell, wake, trip, ghost]

<1>  Synset Synset('spiritual_being.n.01') | Definition: an incorporeal being believed to have powers to affect the course of human events
Examples: []
Count: 4 | Lemmas: [spiritual_being, supernatural_being] | Connected words: [grace, ghost, trip, wake]

... (up to 8 shown per page, paginated via "<8> See the next 8 synsets out of 62.")

? Select hint (Use arrow keys)
? Select one or more guessed words (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)
Selected hint: Synset('charm.v.02') | Selected guessed words: ['spell']
Updated score: 1/9
```

(Captured directly from running today's code against `game_idx = 2`. The exact clue ordering varies between runs — Python's hash randomization affects `set()` iteration order inside the hypernym search — but the format and safety guarantees are stable.)


## Contact
Feel free to contact me via email: hxvinh.hcmus@gmail.com