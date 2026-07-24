from unittest.mock import patch

from concept_net_spymaster import ConceptNetSpyMaster


def suggest_with_fake_neighbors(spy_master, neighbors, **suggest_kwargs):
    def fake_get_related_concepts(word):
        return neighbors.get(word, {})

    with patch('concept_net_spymaster.concept_net_data.get_related_concepts', side_effect=fake_get_related_concepts):
        return spy_master.suggest(**suggest_kwargs)


def test_filter_out_chosen_words_removes_chosen_and_derives_forbidden():
    spy_master = ConceptNetSpyMaster()
    keyword_list, guessword_list, forbidword_list = spy_master.filter_out_chosen_words(
        keyword_list=['dog', 'cat', 'car'],
        guessword_list=['dog', 'cat'],
        chosenword_list=['cat'],
    )
    assert keyword_list == ['dog', 'car']
    assert guessword_list == ['dog']
    assert forbidword_list == ['car']


def test_suggest_requires_at_least_two_covered_words():
    spy_master = ConceptNetSpyMaster(min_weight=1.0)
    neighbors = {
        'dog': {'bone': 3.0, 'pet': 1.5},
        'cat': {'yarn': 2.5, 'pet': 1.8},
    }
    hint_list, filtered_guessword_list = suggest_with_fake_neighbors(
        spy_master, neighbors,
        keyword_list=['dog', 'cat'], guessword_list=['dog', 'cat'], chosenword_list=[],
    )

    assert filtered_guessword_list == ['dog', 'cat']
    labels = [h.get_label() for h in hint_list]
    assert 'pet' in labels     # covered by both dog and cat
    assert 'bone' not in labels  # only covered by dog


def test_suggest_excludes_candidates_related_to_forbidden_words():
    spy_master = ConceptNetSpyMaster(min_weight=1.0)
    neighbors = {
        'dog': {'pet': 3.0, 'animal': 2.0},
        'cat': {'pet': 2.5, 'animal': 1.8},
        'car': {'animal': 1.0},  # forbidden word also related to 'animal'
    }
    hint_list, _ = suggest_with_fake_neighbors(
        spy_master, neighbors,
        keyword_list=['dog', 'cat', 'car'], guessword_list=['dog', 'cat'], chosenword_list=[],
    )

    labels = [h.get_label() for h in hint_list]
    assert 'pet' in labels
    assert 'animal' not in labels


def test_suggest_excludes_candidates_that_are_forms_of_board_words():
    spy_master = ConceptNetSpyMaster(min_weight=1.0)
    neighbors = {
        'dog': {'sealed': 3.0},
        'cat': {'sealed': 2.0},
    }
    hint_list, _ = suggest_with_fake_neighbors(
        spy_master, neighbors,
        keyword_list=['dog', 'cat', 'seal'], guessword_list=['dog', 'cat'], chosenword_list=[],
    )
    assert hint_list == []


def test_suggest_respects_min_weight_threshold():
    spy_master = ConceptNetSpyMaster(min_weight=1.0)
    neighbors = {
        'dog': {'pet': 0.5},
        'cat': {'pet': 0.5},
    }
    hint_list, _ = suggest_with_fake_neighbors(
        spy_master, neighbors,
        keyword_list=['dog', 'cat'], guessword_list=['dog', 'cat'], chosenword_list=[],
    )
    assert hint_list == []


def test_suggest_ranks_by_descending_score():
    spy_master = ConceptNetSpyMaster(min_weight=1.0)
    neighbors = {
        'dog': {'pet': 5.0, 'mammal': 2.0},
        'cat': {'pet': 5.0, 'mammal': 2.0},
        'wolf': {'mammal': 2.0},
    }
    hint_list, _ = suggest_with_fake_neighbors(
        spy_master, neighbors,
        keyword_list=['dog', 'cat', 'wolf'], guessword_list=['dog', 'cat', 'wolf'], chosenword_list=[],
    )
    labels = [h.get_label() for h in hint_list]
    assert labels[0] == 'pet'  # combined weight 10 > mammal's combined weight 6


def test_suggest_excludes_chosen_words_from_guesswords():
    spy_master = ConceptNetSpyMaster(min_weight=1.0)
    neighbors = {
        'dog': {'pet': 3.0},
        'cat': {'pet': 3.0},
    }
    hint_list, filtered_guessword_list = suggest_with_fake_neighbors(
        spy_master, neighbors,
        keyword_list=['dog', 'cat'], guessword_list=['dog', 'cat'], chosenword_list=['dog'],
    )
    assert filtered_guessword_list == ['cat']
    assert hint_list == []  # only 1 guess word left, can't cover >=2
