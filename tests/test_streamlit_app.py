import json

import pytest

from streamlit_app import EXAMPLE_BOARD_PATH, parse_custom_board_json, validate_custom_board


def test_parse_custom_board_json_lowercases_and_strips():
    raw_json = json.dumps({
        'keyword_list': [' Dog ', 'CAT', 'car'],
        'team_guessword_dict': {'team_blue': [' Dog '], 'team_red': ['CAT']},
    })

    keyword_list, team_guessword_dict = parse_custom_board_json(raw_json)

    assert keyword_list == ['dog', 'cat', 'car']
    assert team_guessword_dict == {'team_blue': ['dog'], 'team_red': ['cat']}


def test_parse_custom_board_json_accepts_bytes():
    raw_json = json.dumps({
        'keyword_list': ['dog'],
        'team_guessword_dict': {'team_blue': ['dog'], 'team_red': []},
    }).encode('utf-8')

    keyword_list, team_guessword_dict = parse_custom_board_json(raw_json)
    assert keyword_list == ['dog']


def test_parse_custom_board_json_rejects_malformed_json():
    with pytest.raises(ValueError):
        parse_custom_board_json('{not valid json')


def test_parse_custom_board_json_rejects_missing_keys():
    with pytest.raises(ValueError):
        parse_custom_board_json(json.dumps({'keyword_list': ['dog']}))


def test_validate_custom_board_requires_exactly_25_words():
    errors = validate_custom_board(['dog', 'cat'], {'team_blue': ['dog'], 'team_red': ['cat']})
    assert any('25 words' in e for e in errors)


def test_validate_custom_board_rejects_team_words_off_board():
    keyword_list = [f'word{i}' for i in range(25)]
    errors = validate_custom_board(keyword_list, {'team_blue': ['not_on_board'], 'team_red': []})
    assert any('not on the board' in e for e in errors)


def test_validate_custom_board_rejects_word_on_both_teams():
    keyword_list = [f'word{i}' for i in range(25)]
    errors = validate_custom_board(keyword_list, {'team_blue': ['word0'], 'team_red': ['word0']})
    assert any('both teams' in e for e in errors)


def test_validate_custom_board_accepts_well_formed_board():
    keyword_list = [f'word{i}' for i in range(25)]
    errors = validate_custom_board(keyword_list, {'team_blue': ['word0'], 'team_red': ['word1']})
    assert errors == []


def test_example_board_file_is_well_formed():
    with open(EXAMPLE_BOARD_PATH, 'r', encoding='utf-8') as f:
        raw_json = f.read()

    keyword_list, team_guessword_dict = parse_custom_board_json(raw_json)
    assert validate_custom_board(keyword_list, team_guessword_dict) == []


def test_example_board_words_are_all_valid_in_wordnet():
    from boardgame import CodenamesBoardGame

    with open(EXAMPLE_BOARD_PATH, 'r', encoding='utf-8') as f:
        keyword_list, team_guessword_dict = parse_custom_board_json(f.read())

    game = CodenamesBoardGame(keyword_list, team_guessword_dict)
    assert game.get_keyword_list() == keyword_list
