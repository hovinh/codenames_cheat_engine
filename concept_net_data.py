import functools
import gzip
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'conceptnet_nouns_en.tsv.gz')


@functools.lru_cache(maxsize=1)
def _load_index():
    '''
    Lazily builds {word: {neighbor_word: weight}} from a pre-filtered ConceptNet
    subset (English, noun-noun, curated commonsense relations only — see
    data/README.md for how it was generated). Read directly from the gzipped
    file (never decompressed to disk) and cached in memory for the process
    lifetime, since the data never changes at runtime.

    Reads the module-level DATA_PATH (rather than a default-arg snapshot) so
    tests can monkeypatch it and force a reload via _load_index.cache_clear().

    Each row is indexed in both directions regardless of the underlying
    relation's directionality (e.g. IsA/PartOf/UsedFor aren't symmetric in
    ConceptNet — "dog IsA animal" doesn't imply "animal IsA dog") — for clue
    purposes, either direction is a useful associative link, and indexing both
    maximizes recall from an intentionally narrow relation set.
    '''
    index = {}
    with gzip.open(DATA_PATH, 'rt', encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) != 3:
                continue
            word1, word2, weight_str = parts
            weight = float(weight_str)

            neighbors1 = index.setdefault(word1, {})
            neighbors1[word2] = max(neighbors1.get(word2, 0.0), weight)

            neighbors2 = index.setdefault(word2, {})
            neighbors2[word1] = max(neighbors2.get(word1, 0.0), weight)
    return index


def get_related_concepts(word):
    '''@returns: dict of {neighbor_word: weight} for word, or {} if word is unknown to the dataset.'''
    return _load_index().get(word.lower(), {})
