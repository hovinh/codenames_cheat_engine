from nltk.corpus import wordnet as wn

from hint import Hint


def test_hint_get_info_returns_constructor_values():
    synset = wn.synsets('dog')[0]
    hint = Hint(synset=synset, valid_word_count=2, correlated_word_list=['dog', 'cat'])

    returned_synset, count, words = hint.get_info()
    assert returned_synset == synset
    assert count == 2
    assert words == ['dog', 'cat']


def test_hint_str_contains_key_fields():
    synset = wn.synsets('dog')[0]
    hint = Hint(synset=synset, valid_word_count=2, correlated_word_list=['dog', 'cat'])

    rendered = str(hint)
    assert synset.name() in rendered
    assert synset.definition() in rendered
    assert 'dog' in rendered
    assert 'cat' in rendered
