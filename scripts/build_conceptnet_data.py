'''
One-time (re-runnable) data prep: builds data/conceptnet_relatedto_nouns_en.tsv.gz
from ConceptNet 5.7, for use by concept_net_data.py at app runtime.

This does NOT run as part of the app — it's a developer tool to (re)generate the
bundled dataset, e.g. after changing RELATIONS below to tighten/loosen which
ConceptNet relations count as "related" for clue purposes.

Source: the conceptnet5/conceptnet5 dataset on Hugging Face (parquet shards,
mirroring the official ConceptNet 5.7 assertions dump, but noticeably faster to
pull in a bandwidth-constrained environment than the official S3 .csv.gz).

Pipeline:
  1. Download each of the 23 parquet shards, filter to rows where lang == 'en'
     and rel is in RELATIONS, normalize arg1/arg2 to bare words, and append
     (word1, word2, weight) to a scratch TSV. Shards are deleted after use.
  2. Re-scan the scratch TSV, keep only pairs where BOTH words have a noun
     sense in WordNet (Codenames board words are effectively always nouns),
     dedupe (keeping max weight per unordered pair), and write the final
     gzipped TSV.

Run from the repo root:
    .venv/Scripts/python scripts/build_conceptnet_data.py
'''
import gzip
import os
import sys
import tempfile
import time

import pyarrow.compute as pc
import pyarrow.parquet as pq
import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
from nltk.corpus import wordnet as wn  # noqa: E402

NUM_SHARDS = 23
SHARD_URL_TMPL = 'https://huggingface.co/datasets/conceptnet5/conceptnet5/resolve/main/conceptnet5/train-{i:05d}-of-00023.parquet'
RELATIONS = ('/r/RelatedTo',)  # tighten later, e.g. add '/r/IsA', '/r/UsedFor', '/r/AtLocation'
OUT_PATH = os.path.join(REPO_ROOT, 'data', 'conceptnet_relatedto_nouns_en.tsv.gz')


def normalize_word(concept_uri):
    # e.g. '/c/en/dog' or '/c/en/dog/n' or '/c/en/ice_cream/n/wn/food' -> 'dog' / 'dog' / 'ice_cream'
    parts = concept_uri.split('/')
    if len(parts) < 4 or not parts[3]:
        return None
    return parts[3]


def download_shard(i, path):
    url = SHARD_URL_TMPL.format(i=i)
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)


def step1_download_and_filter_shards(raw_pairs_path, shard_dir):
    start = time.time()
    total_kept = 0
    with open(raw_pairs_path, 'w', encoding='utf-8') as fout:
        for i in range(NUM_SHARDS):
            shard_path = os.path.join(shard_dir, f'shard{i}.parquet')
            download_shard(i, shard_path)

            table = pq.read_table(shard_path, columns=['rel', 'arg1', 'arg2', 'lang', 'weight'])
            rel_mask = pc.is_in(table.column('rel'), value_set=pc.array(list(RELATIONS)))
            mask = pc.and_(pc.equal(table.column('lang'), 'en'), rel_mask)
            filtered = table.filter(mask)

            shard_kept = 0
            for arg1, arg2, weight in zip(filtered.column('arg1').to_pylist(),
                                           filtered.column('arg2').to_pylist(),
                                           filtered.column('weight').to_pylist()):
                w1, w2 = normalize_word(arg1), normalize_word(arg2)
                if not w1 or not w2 or w1 == w2:
                    continue
                fout.write(f'{w1}\t{w2}\t{weight}\n')
                shard_kept += 1
            total_kept += shard_kept

            os.remove(shard_path)
            print(f'shard {i}/{NUM_SHARDS-1}: kept={shard_kept:,} total_kept={total_kept:,} '
                  f'elapsed={time.time()-start:.0f}s', flush=True)

    print(f'STEP1 DONE: total_kept={total_kept:,} elapsed={time.time()-start:.0f}s', flush=True)


def step2_apply_noun_filter_and_write_output(raw_pairs_path):
    start = time.time()
    noun_cache = {}

    def is_noun(word):
        if word not in noun_cache:
            spaced = word.replace('_', ' ')
            noun_cache[word] = bool(wn.synsets(word, pos=wn.NOUN)) or bool(wn.synsets(spaced, pos=wn.NOUN))
        return noun_cache[word]

    best_weight = {}
    with open(raw_pairs_path, 'r', encoding='utf-8') as fin:
        for line in fin:
            parts = line.rstrip('\n').split('\t')
            if len(parts) != 3:
                continue
            w1, w2, weight_str = parts
            if not (is_noun(w1) and is_noun(w2)):
                continue
            weight = float(weight_str)
            key = (w1, w2) if w1 < w2 else (w2, w1)
            if key not in best_weight or weight > best_weight[key]:
                best_weight[key] = weight

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with gzip.open(OUT_PATH, 'wt', encoding='utf-8') as fout:
        for (w1, w2), weight in best_weight.items():
            fout.write(f'{w1}\t{w2}\t{weight}\n')

    out_size_mb = os.path.getsize(OUT_PATH) / 1024 / 1024
    print(f'STEP2 DONE: unique_pairs={len(best_weight):,} out_size_mb={out_size_mb:.2f} '
          f'elapsed={time.time()-start:.0f}s', flush=True)


def main():
    with tempfile.TemporaryDirectory() as scratch_dir:
        raw_pairs_path = os.path.join(scratch_dir, 'raw_pairs.tsv')
        step1_download_and_filter_shards(raw_pairs_path, scratch_dir)
        step2_apply_noun_filter_and_write_output(raw_pairs_path)


if __name__ == '__main__':
    main()
