from concept_net_hint import ConceptNetHint


def test_get_info_returns_constructor_values():
    hint = ConceptNetHint('spoon', 3, ['fork', 'knife', 'plate'])
    assert hint.get_info() == ('spoon', 3, ['fork', 'knife', 'plate'])


def test_get_label_returns_concept_word():
    hint = ConceptNetHint('spoon', 2, ['fork', 'knife'])
    assert hint.get_label() == 'spoon'


def test_get_definition_and_examples_are_empty():
    hint = ConceptNetHint('spoon', 2, ['fork', 'knife'])
    assert hint.get_definition() == ''
    assert hint.get_examples() == []


def test_str_contains_concept_and_words():
    hint = ConceptNetHint('spoon', 2, ['fork', 'knife'])
    rendered = str(hint)
    assert 'spoon' in rendered
    assert 'fork' in rendered
    assert 'knife' in rendered
