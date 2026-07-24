from nltk.corpus import wordnet as wn

from spymaster import SpyMaster


def test_filter_out_chosen_words_removes_chosen_and_derives_forbidden():
    spy_master = SpyMaster()
    keyword_list, guessword_list, forbidword_list = spy_master.filter_out_chosen_words(
        keyword_list=['dog', 'cat', 'car'],
        guessword_list=['dog', 'cat'],
        chosenword_list=['cat'],
    )
    assert keyword_list == ['dog', 'car']
    assert guessword_list == ['dog']
    assert forbidword_list == ['car']


def test_generate_all_pairs_returns_unique_combinations():
    spy_master = SpyMaster()
    pairs = spy_master.generate_all_pairs(['a', 'b', 'c'])
    assert pairs == [('a', 'b'), ('a', 'c'), ('b', 'c')]


def test_suggest_only_returns_hints_covering_own_words_without_forbidden():
    spy_master = SpyMaster()
    hint_list, filtered_guessword_list = spy_master.suggest(
        keyword_list=['dog', 'cat', 'car'],
        guessword_list=['dog', 'cat'],
        chosenword_list=[],
    )

    assert filtered_guessword_list == ['dog', 'cat']
    for hint in hint_list:
        _, valid_word_count, corr_words = hint.get_info()
        assert valid_word_count >= 2
        assert set(corr_words) <= {'dog', 'cat'}


def test_suggest_ranks_hints_by_descending_word_count():
    spy_master = SpyMaster()
    hint_list, _ = spy_master.suggest(
        keyword_list=['dog', 'cat', 'wolf', 'car'],
        guessword_list=['dog', 'cat', 'wolf'],
        chosenword_list=[],
    )
    counts = [hint.get_info()[1] for hint in hint_list]
    assert counts == sorted(counts, reverse=True)


def test_suggest_excludes_chosen_words_from_candidates():
    spy_master = SpyMaster()
    hint_list, filtered_guessword_list = spy_master.suggest(
        keyword_list=['dog', 'cat', 'car'],
        guessword_list=['dog', 'cat'],
        chosenword_list=['dog'],
    )
    assert filtered_guessword_list == ['cat']
    for hint in hint_list:
        _, _, corr_words = hint.get_info()
        assert 'dog' not in corr_words


def test_generate_hints_excludes_candidates_whose_lemma_is_a_board_word():
    spy_master = SpyMaster()
    dog_synset = wn.synsets('dog', pos=wn.NOUN)[0]

    hint_list = spy_master.generate_hints(
        keyword_list=['dog', 'pet', 'cat'],
        forbidword_list=[],
        hypernym_list=[dog_synset],
    )

    assert hint_list == []


def test_suggest_never_returns_a_hint_that_is_a_form_of_a_board_word():
    spy_master = SpyMaster()
    hint_list, _ = spy_master.suggest(
        keyword_list=['dog', 'cat', 'wolf'],
        guessword_list=['dog', 'cat', 'wolf'],
        chosenword_list=[],
    )
    board_words = ['dog', 'cat', 'wolf']
    for hint in hint_list:
        for lemma_name in [lemma.name() for lemma in hint.get_info()[0].lemmas()]:
            for board_word in board_words:
                assert lemma_name.lower() != board_word.lower()
