import pytest

from boardgame import CodenamesBoardGame

INVALID_WORD = 'zzznotarealword123'


def make_game(keyword_list=None, team_blue=None, team_red=None):
    keyword_list = keyword_list or ['dog', 'cat', 'car', 'tree']
    team_blue = team_blue if team_blue is not None else ['dog', 'cat']
    team_red = team_red if team_red is not None else ['car']
    return CodenamesBoardGame(keyword_list, {'team_blue': team_blue, 'team_red': team_red})


def test_check_all_keywords_valid_flags_invalid_words():
    game = make_game()
    is_valid, invalid_list = game.check_all_keywords_valid(['dog', INVALID_WORD, 'cat'])
    assert is_valid is False
    assert invalid_list == [INVALID_WORD]


def test_check_all_keywords_valid_accepts_valid_words():
    game = make_game()
    is_valid, invalid_list = game.check_all_keywords_valid(['dog', 'cat', 'car', 'tree'])
    assert is_valid is True
    assert invalid_list == []


def test_construction_rejects_invalid_words():
    with pytest.raises(ValueError):
        CodenamesBoardGame([INVALID_WORD], {'team_blue': [], 'team_red': []})


def test_construction_sets_initial_state():
    game = make_game()
    assert game.get_team_turn() == 'team_blue'
    assert game.get_score_dict() == {'team_blue': 0, 'team_red': 0}
    assert game.is_game_over() is False
    assert game.get_winner() is None
    assert game.get_chosen_words() == []
    assert game.get_game_history() == []


def test_switch_turn_alternates_and_wraps():
    game = make_game()
    assert game.get_team_turn() == 'team_blue'
    game.switch_turn()
    assert game.get_team_turn() == 'team_red'
    game.switch_turn()
    assert game.get_team_turn() == 'team_blue'


def test_apply_turn_updates_score_history_and_switches_turn():
    game = make_game()  # team_blue has 2 words, so required_score is 2
    team_name, score, required_score = game.apply_turn(hint='animal', selected_words=['dog'])

    assert team_name == 'team_blue'
    assert score == 1
    assert required_score == 2
    assert game.get_team_turn() == 'team_red'
    assert game.get_chosen_words() == ['dog']

    history = game.get_game_history()
    assert history == [{
        'team': 'team_blue',
        'hint': 'animal',
        'selected_words': ['dog'],
        'score': 1,
        'required_score': 2,
    }]


def test_apply_turn_with_no_hint_stores_none_in_history():
    game = make_game()
    game.apply_turn(hint=None, selected_words=['dog'])
    assert game.get_game_history()[0]['hint'] is None


def test_team_wins_when_all_its_words_found_in_one_turn():
    game = make_game()
    game.apply_turn(hint=None, selected_words=['dog', 'cat'])
    assert game.is_game_over() is True
    assert game.get_winner() == 'team_blue'


def test_get_suggestions_only_offers_safe_words():
    game = make_game(
        keyword_list=['dog', 'cat', 'car'],
        team_blue=['dog', 'cat'],
        team_red=['car'],
    )
    hint_list, filtered_guessword_list = game.get_suggestions()

    assert filtered_guessword_list == ['dog', 'cat']
    for hint in hint_list:
        _, valid_word_count, corr_words = hint.get_info()
        assert valid_word_count >= 2
        assert valid_word_count == len(corr_words)
        assert set(corr_words) <= set(filtered_guessword_list)
        assert 'car' not in corr_words


def test_get_suggestions_excludes_chosen_words():
    game = make_game(
        keyword_list=['dog', 'cat', 'car'],
        team_blue=['dog', 'cat'],
        team_red=['car'],
    )
    game.apply_turn(hint=None, selected_words=['dog'])  # now it's team_red's turn

    _, filtered_guessword_list = game.get_suggestions()
    assert filtered_guessword_list == ['car']
    assert game.get_chosen_words() == ['dog']


def test_getters_return_defensive_copies():
    game = make_game()

    keywords = game.get_keyword_list()
    keywords.append('extra')
    assert 'extra' not in game.get_keyword_list()

    team_dict = game.get_team_guessword_dict()
    team_dict['team_blue'].append('extra')
    assert 'extra' not in game.get_team_guessword_dict()['team_blue']
