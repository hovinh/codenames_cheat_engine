import json

import streamlit as st

from boardgame import CodenamesBoardGame
from concept_net_spymaster import ConceptNetSpyMaster
from sample_games import select_game
from spymaster import SpyMaster

TEAM_LABELS = {'team_blue': 'Blue', 'team_red': 'Red'}
TEAM_COLORS = {'team_blue': '#3b82f6', 'team_red': '#ef4444'}
NEUTRAL_COLOR = '#9ca3af'
SAMPLE_GAME_COUNT = 3
EXAMPLE_BOARD_PATH = 'example_board.json'
CLUE_ENGINES = {
    'WordNet': SpyMaster,
    'ConceptNet (experimental)': ConceptNetSpyMaster,
}


def init_state():
    st.session_state.setdefault('game', None)
    st.session_state.setdefault('current_hints', None)


def reset_game():
    st.session_state['game'] = None
    st.session_state['current_hints'] = None


def parse_word_list(raw_text):
    return [w.strip().lower() for w in raw_text.replace('\n', ',').split(',') if w.strip()]


def parse_custom_board_json(raw_json):
    '''
    @params:
        - raw_json: str or bytes, JSON with "keyword_list" (list of str) and
          "team_guessword_dict" (dict with "team_blue"/"team_red" lists of str).
    @returns: (keyword_list, team_guessword_dict), words lower-cased and stripped.
    @raises: ValueError if the JSON is malformed or missing the expected keys.
    '''
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ValueError(f'Not valid JSON: {e}')

    try:
        keyword_list = [str(w).strip().lower() for w in data['keyword_list']]
        team_guessword_dict = {
            'team_blue': [str(w).strip().lower() for w in data['team_guessword_dict']['team_blue']],
            'team_red': [str(w).strip().lower() for w in data['team_guessword_dict']['team_red']],
        }
    except (KeyError, TypeError) as e:
        raise ValueError(
            f'JSON must have a "keyword_list" array and a "team_guessword_dict" '
            f'object with "team_blue"/"team_red" arrays (missing/invalid: {e}).'
        )

    return keyword_list, team_guessword_dict


def validate_custom_board(keyword_list, team_guessword_dict):
    '''Return a list of human-readable error strings; empty list means the board is valid.'''
    blue_words = team_guessword_dict.get('team_blue', [])
    red_words = team_guessword_dict.get('team_red', [])

    errors = []
    if len(keyword_list) != 25:
        errors.append(f'Board must have exactly 25 words (got {len(keyword_list)}).')
    if not set(blue_words) <= set(keyword_list):
        errors.append('Some Blue words are not on the board.')
    if not set(red_words) <= set(keyword_list):
        errors.append('Some Red words are not on the board.')
    if set(blue_words) & set(red_words):
        errors.append('A word cannot belong to both teams.')
    return errors


def try_create_game(keyword_list, team_guessword_dict, spy_master=None):
    try:
        st.session_state['game'] = CodenamesBoardGame(keyword_list, team_guessword_dict, spy_master=spy_master)
        st.session_state['current_hints'] = None
    except ValueError as e:
        st.error(str(e))


def render_help_guide():
    st.markdown(
        '- **Pick a board** — a sample one, or build your own (paste words, or upload/download the example JSON).\n'
        "- Each turn, the engine suggests clues for whichever team's turn it is. Pick a clue, then pick the "
        "word(s) your team is guessing for it.\n"
        '- The team with **more** words to find goes first (ties go to Blue) — that extra word offsets '
        'the advantage of going first. A team wins once all of its own words have been found.\n'
        '- Colors show **both** teams\' words — this is a spymaster tool, nothing is hidden. Guessed words fade '
        'out and get struck through.'
    )


def render_engine_selector():
    return st.radio('Clue engine', list(CLUE_ENGINES.keys()), horizontal=True,
                     help='WordNet uses dictionary hypernyms (precise, sometimes narrow). '
                          'ConceptNet uses a broader commonsense association graph (more creative, experimental).')


def render_setup():
    st.title('🕵️ Codenames Cheat Engine')
    st.write(
        'Pick a sample board or build your own, then let the engine suggest '
        'clues for each team, turn by turn.'
    )
    render_help_guide()
    st.divider()

    mode = st.radio('Board source', ['Sample game', 'Custom game'], horizontal=True)

    if mode == 'Sample game':
        idx = st.selectbox('Pick a sample board', list(range(SAMPLE_GAME_COUNT)),
                            format_func=lambda i: f'Sample game {i}')
        engine_name = render_engine_selector()
        if st.button('Start game', type='primary'):
            keyword_list, team_guessword_dict = select_game(idx)
            try_create_game(keyword_list, team_guessword_dict, spy_master=CLUE_ENGINES[engine_name]())

    else:
        try:
            with open(EXAMPLE_BOARD_PATH, 'rb') as f:
                example_board_bytes = f.read()
            st.download_button(
                'Download example_board.json',
                data=example_board_bytes,
                file_name='example_board.json',
                mime='application/json',
            )
        except FileNotFoundError:
            example_board_bytes = None

        uploaded_file = st.file_uploader(
            'Upload a board as JSON (see the example above for the schema)',
            type=['json'],
        )

        if example_board_bytes is not None:
            try:
                example_keyword_list, example_team_dict = parse_custom_board_json(example_board_bytes)
                with st.expander('📋 Copy-paste text (handy on mobile, instead of uploading a file)'):
                    st.caption('Board words (25 total)')
                    st.code(', '.join(example_keyword_list), language=None)
                    st.caption('Team Blue words')
                    st.code(', '.join(example_team_dict['team_blue']), language=None)
                    st.caption('Team Red words')
                    st.code(', '.join(example_team_dict['team_red']), language=None)
            except ValueError:
                pass

        st.caption(
            'Or fill in manually: words separated by commas or newlines. '
            'Every word must exist in WordNet. Ignored if a file is uploaded above.'
        )
        words_raw = st.text_area('Board words (25 total)', height=100)
        blue_raw = st.text_area('Team Blue words (subset of the board)')
        red_raw = st.text_area('Team Red words (subset of the board)')
        engine_name = render_engine_selector()

        if st.button('Start game', type='primary'):
            if uploaded_file is not None:
                try:
                    keyword_list, team_guessword_dict = parse_custom_board_json(uploaded_file.getvalue())
                except ValueError as e:
                    st.error(str(e))
                    keyword_list, team_guessword_dict = None, None
            else:
                keyword_list = parse_word_list(words_raw)
                team_guessword_dict = {
                    'team_blue': parse_word_list(blue_raw),
                    'team_red': parse_word_list(red_raw),
                }

            if keyword_list is not None:
                errors = validate_custom_board(keyword_list, team_guessword_dict)
                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    try_create_game(keyword_list, team_guessword_dict, spy_master=CLUE_ENGINES[engine_name]())

    if st.session_state['game'] is not None:
        st.rerun()


def render_board(game):
    keyword_list = game.get_keyword_list()
    team_dict = game.get_team_guessword_dict()
    chosen_words = set(game.get_chosen_words())

    words_per_row = 5
    numb_rows = -(-len(keyword_list) // words_per_row)  # ceil division

    for row in range(numb_rows):
        row_words = keyword_list[row * words_per_row:(row + 1) * words_per_row]
        cols = st.columns(words_per_row)
        for col, word in zip(cols, row_words):
            if word in team_dict['team_blue']:
                color = TEAM_COLORS['team_blue']
            elif word in team_dict['team_red']:
                color = TEAM_COLORS['team_red']
            else:
                color = NEUTRAL_COLOR

            is_chosen = word in chosen_words
            style = (
                f'background-color:{color};'
                f'opacity:{"0.4" if is_chosen else "1"};'
                f'text-decoration:{"line-through" if is_chosen else "none"};'
                'color:white;padding:0.6em 0.4em;border-radius:6px;'
                'text-align:center;margin-bottom:6px;font-weight:600;'
            )
            col.markdown(f"<div style='{style}'>{word}</div>", unsafe_allow_html=True)


def render_scoreboard(game):
    score = game.get_score_dict()
    team_dict = game.get_team_guessword_dict()

    col1, col2 = st.columns(2)
    col1.metric('Blue', f"{score['team_blue']} / {len(team_dict['team_blue'])}")
    col2.metric('Red', f"{score['team_red']} / {len(team_dict['team_red'])}")


def render_hint_label(hint):
    _, valid_word_count, corr_words = hint.get_info()
    return f"{hint.get_label()} — covers {valid_word_count} word(s): {', '.join(corr_words)}"


def render_turn(game):
    team_name = game.get_team_turn()
    st.subheader(f"{TEAM_LABELS[team_name]}'s turn")

    if st.session_state['current_hints'] is None:
        with st.spinner('Searching for clues...'):
            hint_list, guessword_list = game.get_suggestions()
        st.session_state['current_hints'] = (hint_list, guessword_list)

    hint_list, guessword_list = st.session_state['current_hints']

    chosen_words = set(game.get_chosen_words())
    available_words = [w for w in game.get_keyword_list() if w not in chosen_words]

    if hint_list:
        selected_idx = st.radio(
            'Pick a clue',
            options=list(range(len(hint_list))),
            format_func=lambda i: render_hint_label(hint_list[i]),
        )
        selected_hint = hint_list[selected_idx]
        _, _, corr_words = selected_hint.get_info()

        definition = selected_hint.get_definition()
        examples = selected_hint.get_examples()
        if definition or examples:
            with st.expander('Clue details'):
                if definition:
                    st.write(f"**Definition:** {definition}")
                if examples:
                    st.write(f"**Examples:** {'; '.join(examples)}")

        # Offer every remaining board word, not just the clue's intended targets —
        # a teammate can misread a clue and pick a word the spymaster didn't mean.
        ordered_words = corr_words + [w for w in available_words if w not in corr_words]
        selected_words = st.multiselect(
            'Word(s) your team guesses', ordered_words,
            help="Suggested words for this clue are listed first, but any remaining board word "
                 "can be picked in case your team guesses wrong."
        )

        if st.button('Submit turn', type='primary', disabled=not selected_words):
            game.apply_turn(selected_hint, selected_words)
            st.session_state['current_hints'] = None
            st.rerun()
    else:
        st.info('No clue covers 2+ words this turn — pick one word to guess directly.')
        word = st.selectbox('Word', available_words)
        if st.button('Submit turn', type='primary', disabled=not available_words):
            game.apply_turn(None, [word])
            st.session_state['current_hints'] = None
            st.rerun()


def render_history(game):
    history = game.get_game_history()
    if not history:
        return

    with st.expander(f'Game history ({len(history)} turn(s))'):
        for turn_number, entry in enumerate(history, start=1):
            st.write(
                f"{turn_number}. **{TEAM_LABELS[entry['team']]}** guessed "
                f"{entry['selected_words']} (clue: {entry['hint']}) "
                f"→ score {entry['score']}/{entry['required_score']}"
            )


def main():
    st.set_page_config(page_title='Codenames Cheat Engine', page_icon='🕵️', layout='centered')
    init_state()

    game = st.session_state['game']
    if game is None:
        render_setup()
        return

    render_board(game)
    render_scoreboard(game)

    if game.is_game_over():
        st.success(f"🎉 {TEAM_LABELS[game.get_winner()]} wins!")
    else:
        render_turn(game)

    render_history(game)

    st.button('Reset game', on_click=reset_game)


if __name__ == '__main__':
    main()
