import gzip

import pytest

import concept_net_data


@pytest.fixture(autouse=True)
def clear_index_cache():
    concept_net_data._load_index.cache_clear()
    yield
    concept_net_data._load_index.cache_clear()


def write_fixture(path, rows):
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        for w1, w2, weight in rows:
            f.write(f'{w1}\t{w2}\t{weight}\n')


def test_get_related_concepts_reads_bundled_data(tmp_path, monkeypatch):
    fixture_path = tmp_path / 'fixture.tsv.gz'
    write_fixture(fixture_path, [
        ('dog', 'bone', 2.5),
        ('dog', 'leash', 1.8),
        ('cat', 'yarn', 3.0),
    ])
    monkeypatch.setattr(concept_net_data, 'DATA_PATH', str(fixture_path))

    assert concept_net_data.get_related_concepts('dog') == {'bone': 2.5, 'leash': 1.8}


def test_related_to_is_indexed_symmetrically(tmp_path, monkeypatch):
    fixture_path = tmp_path / 'fixture.tsv.gz'
    write_fixture(fixture_path, [('dog', 'bone', 2.5)])
    monkeypatch.setattr(concept_net_data, 'DATA_PATH', str(fixture_path))

    assert concept_net_data.get_related_concepts('bone') == {'dog': 2.5}


def test_get_related_concepts_unknown_word_returns_empty(tmp_path, monkeypatch):
    fixture_path = tmp_path / 'fixture.tsv.gz'
    write_fixture(fixture_path, [('dog', 'bone', 2.5)])
    monkeypatch.setattr(concept_net_data, 'DATA_PATH', str(fixture_path))

    assert concept_net_data.get_related_concepts('nonexistent') == {}


def test_get_related_concepts_case_insensitive_lookup(tmp_path, monkeypatch):
    fixture_path = tmp_path / 'fixture.tsv.gz'
    write_fixture(fixture_path, [('dog', 'bone', 2.5)])
    monkeypatch.setattr(concept_net_data, 'DATA_PATH', str(fixture_path))

    assert concept_net_data.get_related_concepts('DOG') == {'bone': 2.5}
