from clue_safety import is_related_to_board_word


def test_exact_match_is_related():
    assert is_related_to_board_word('dog', ['cat', 'dog', 'bird']) is True


def test_case_insensitive():
    assert is_related_to_board_word('Dog', ['dog']) is True


def test_substring_of_board_word():
    assert is_related_to_board_word('seal', ['sealed', 'cat']) is True


def test_board_word_substring_of_candidate():
    assert is_related_to_board_word('disgrace', ['grace']) is True


def test_unrelated_words_not_flagged():
    assert is_related_to_board_word('walk', ['dog', 'cat', 'bird']) is False


def test_short_words_exempt_from_substring_check():
    # 'a' is a substring of almost everything; short words shouldn't trigger false positives
    assert is_related_to_board_word('a', ['apple', 'cat']) is False


def test_underscore_and_space_normalized():
    assert is_related_to_board_word('new york', ['new_york']) is True
    assert is_related_to_board_word('new_york', ['new york']) is True
