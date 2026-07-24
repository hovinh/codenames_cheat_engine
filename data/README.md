# data/

`conceptnet_nouns_en.tsv.gz` is a pre-filtered subset of [ConceptNet 5.7](https://github.com/commonsense/conceptnet5/wiki/Downloads), used by `concept_net_data.py` to power the ConceptNet clue engine (`concept_net_spymaster.py`) entirely offline — no live API calls at runtime.

## Format

Gzipped, tab-separated: `word1<TAB>word2<TAB>weight`. `concept_net_data.py` indexes each row in both directions, regardless of the underlying relation's actual directionality (see below) — for clue purposes either direction is a useful associative link.

## How it was generated

Run `scripts/build_conceptnet_data.py` from the repo root (needs `pyarrow` and `requests`, both already in `requirements.txt`, plus the NLTK WordNet corpus). It:

1. Downloads the 23 parquet shards of the [`conceptnet5/conceptnet5`](https://huggingface.co/datasets/conceptnet5/conceptnet5) Hugging Face mirror of ConceptNet 5.7 (faster to pull than the official S3 `.csv.gz` in a bandwidth-constrained environment), filtering each shard to English-language rows whose relation is in `RELATIONS`.
2. Filters that intermediate set down to pairs where **both** words have a noun sense in WordNet — Codenames board words are effectively always nouns, so this trims a large, mostly-irrelevant tail (verbs, adjectives, phrases) without touching a POS tagger.
3. Dedupes (keeping the max weight per unordered pair) and writes the final gzipped TSV to this directory.

Re-run it whenever `RELATIONS` changes.

## Relation set

`RELATIONS` currently holds ConceptNet's core curated commonsense relations — `IsA`, `PartOf`, `HasA`, `UsedFor`, `CapableOf`, `AtLocation`, `MadeOf`, `HasProperty` — deliberately **narrow** (high-precision) rather than the broad `RelatedTo` catch-all (ConceptNet's noisiest, crowd-sourced-and-unfiltered relation). None of these are symmetric in ConceptNet itself (e.g. "dog IsA animal" doesn't imply "animal IsA dog"), but `concept_net_data.py` indexes both directions anyway for recall — see the note above.

If suggestions feel too sparse, loosen by adding relations back in (e.g. `Synonym`, `SimilarTo`, or `RelatedTo` itself) and re-running the script.
