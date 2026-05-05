#!/usr/bin/env python3
"""
build_reference.py — Starts With Black Bot
Processes the AAVE Corpora Collection into a compact term-frequency JSON
that tracks WHICH cultural moment each term appeared in — not just that
it appeared in "social media."

Key design decisions:
- Each social media file is treated as a named cultural collection
- A term appearing in #ThanksgivingClapBack (2015) is a stronger provenance
  signal than just "appears in social media corpus"
- Hashtag event terms (blacklivesmatter, oscarssowhite, etc.) are stripped
  as vocabulary but their COLLECTIONS remain as provenance markers
- Claude uses the collection metadata at analysis time to reason about
  cultural provenance

Run ONCE from the starts-with-black-bot/ directory after cloning:
    https://github.com/jazmiahenry/aave_corpora

Usage:
    python3 build_reference.py

Output:
    aave_reference.json
"""

import json
import re
import os
import csv
from collections import defaultdict

# ── PATHS ───────────────────────────────────────────────────────────────────
CORPORA_DIR  = "../aave_corpora/corpora"
SOCIAL_DIR   = "../aave_corpora/social_media"
OUTPUT_FILE  = "aave_reference.json"

# ── FREQUENCY THRESHOLDS ────────────────────────────────────────────────────
MIN_FREQ_UNIGRAM = 2
MIN_FREQ_NGRAM   = 3

# ── CULTURAL COLLECTION METADATA ────────────────────────────────────────────
SOCIAL_COLLECTIONS = {
    "thanksgivingclapback_15.json": {
        "id": "thanksgiving_clapback", "label": "#ThanksgivingClapBack", "years": [2015],
        "context": "Viral Black Twitter holiday tradition — clapping back at family. Originated in Black cultural spaces.",
        "format": "ndjson_snscrape",
    },
    "thanksgivingclapback_16.json": {
        "id": "thanksgiving_clapback", "label": "#ThanksgivingClapBack", "years": [2016],
        "context": "Viral Black Twitter holiday tradition — clapping back at family. Originated in Black cultural spaces.",
        "format": "ndjson_snscrape",
    },
    "thanksgivingclapback_17.json": {
        "id": "thanksgiving_clapback", "label": "#ThanksgivingClapBack", "years": [2017],
        "context": "Viral Black Twitter holiday tradition — clapping back at family. Originated in Black cultural spaces.",
        "format": "ndjson_snscrape",
    },
    "oscarssowhite_15.json": {
        "id": "oscars_so_white", "label": "#OscarsSoWhite", "years": [2015],
        "context": "Black-led critique of the Academy Awards' racial exclusion. Coined by April Reign.",
        "format": "ndjson_snscrape",
    },
    "sayhername_15.json": {
        "id": "say_her_name", "label": "#SayHerName", "years": [2015],
        "context": "Black feminist movement by AAPF to raise visibility of Black women killed by police.",
        "format": "ndjson_snscrape",
    },
    "#SayHerName.json": {
        "id": "say_her_name", "label": "#SayHerName", "years": [2022],
        "context": "Black feminist movement by AAPF to raise visibility of Black women killed by police.",
        "format": "tweepy_object",
    },
    "BlackLivesMatter_20.json": {
        "id": "black_lives_matter", "label": "#BlackLivesMatter", "years": [2020],
        "context": "Black civil rights movement responding to police violence. Peak activity following George Floyd's murder.",
        "format": "ndjson_snscrape",
    },
    "blm_tweets_june_22.csv": {
        "id": "blm_2022", "label": "#BLM", "years": [2022],
        "context": "Black Lives Matter movement discourse, June 2022.",
        "format": "csv",
    },
    "blackmoms_19.json": {
        "id": "black_moms", "label": "#BlackMoms", "years": [2019],
        "context": "Black parenting and motherhood community discourse.",
        "format": "ndjson_snscrape",
    },
    "#BlackGirlMagic.json": {
        "id": "black_girl_magic", "label": "#BlackGirlMagic", "years": [2022],
        "context": "Celebration of Black women coined by CaShawn Thompson (2013). Core Black cultural expression.",
        "format": "tweepy_object",
    },
    "#BlackTwitter.json": {
        "id": "black_twitter", "label": "#BlackTwitter", "years": [2022],
        "context": "Black Twitter community discourse — cultural hub of AAVE language innovation on social media.",
        "format": "tweepy_object",
    },
    "lilnasx_tweets.json": {
        "id": "lil_nas_x", "label": "Lil Nas X / BET Awards discourse", "years": [2022],
        "context": "Tweets about Lil Nas X BET Awards snub. Black LGBTQ+ cultural discourse.",
        "format": "tweepy_object",
    },
}

HASHTAG_EVENT_TERMS = {
    "thanksgivingclapback", "oscarssowhite", "blacklivesmatter",
    "sayhername", "blackmoms", "blackgirlmagic", "blacktwitter",
    "blm", "blacklives", "kneel4hockey", "kneelingathletes",
}

STOP_WORDS = {
    'the','a','an','is','are','was','were','be','been','being','have','has',
    'had','do','does','did','will','would','could','should','may','might',
    'shall','of','in','to','for','on','at','by','from','with','that','this',
    'these','those','it','its','he','she','they','we','you','me','him','her',
    'them','us','my','your','his','their','our','and','or','but','if','as',
    'so','up','out','about','into','through','during','before','after','above',
    'below','between','each','more','most','other','some','such','not','only',
    'same','than','too','very','just','because','while','although','though',
    'when','where','who','which','what','how','all','both','any','few',
    'rt','http','https','via','amp','com','www','co','t',
    'de','el','en','la','los','es','le','un','une',
}

ALL_EXCLUSIONS = STOP_WORDS | HASHTAG_EVENT_TERMS


# ── TEXT EXTRACTION ──────────────────────────────────────────────────────────

def extract_text_snscrape(filepath):
    texts = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                content = obj.get('content') or obj.get('renderedContent') or ''
                texts.append(content)
            except json.JSONDecodeError:
                continue
    return texts


def extract_text_tweepy(filepath):
    texts = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            ft = re.search(r"'full_text':\s*'((?:[^'\\]|\\.)*)'", line)
            if ft:
                texts.append(ft.group(1))
                continue
            t = re.search(r"'text':\s*'((?:[^'\\]|\\.)*)'", line)
            if t:
                texts.append(t.group(1))
    return texts


def extract_text_csv(filepath):
    texts = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row.get('Text') or row.get('text') or '')
    return texts


def extract_text_plain(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return [f.read()]


# ── TEXT PROCESSING ──────────────────────────────────────────────────────────

def clean(text):
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#(\w+)', r'\1', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s']", ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text):
    return [t for t in text.split() if len(t) > 1 and t not in ALL_EXCLUSIONS]


def ngrams(tokens, n):
    return [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def process_texts(text_list):
    all_uni, all_ng = [], []
    for text in text_list:
        tokens = tokenize(clean(text))
        all_uni.extend(tokens)
        all_ng.extend(ngrams(tokens, 2))
        all_ng.extend(ngrams(tokens, 3))
    return all_uni, all_ng


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  Starts With Black Bot — Collection-Aware Corpus Processor")
    print("=" * 65)

    uni_counts   = defaultdict(lambda: defaultdict(int))
    ngram_counts = defaultdict(lambda: defaultdict(int))
    collection_meta = {}

    # ── Social media files ────────────────────────────────────────────────
    print("\n── Social Media Collections ──")
    for filename, meta in SOCIAL_COLLECTIONS.items():
        filepath = os.path.join(SOCIAL_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  ⚠ MISSING: {filename}")
            continue

        coll_id = meta["id"]
        fmt     = meta["format"]

        if fmt == "ndjson_snscrape":    texts = extract_text_snscrape(filepath)
        elif fmt == "tweepy_object":    texts = extract_text_tweepy(filepath)
        elif fmt == "csv":              texts = extract_text_csv(filepath)
        else:                           texts = extract_text_plain(filepath)

        unis, ngs = process_texts(texts)
        for t in unis:  uni_counts[t][coll_id]   += 1
        for t in ngs:   ngram_counts[t][coll_id] += 1

        if coll_id not in collection_meta:
            collection_meta[coll_id] = {
                "label":   meta["label"],
                "years":   list(meta["years"]),
                "context": meta["context"],
            }
        else:
            for yr in meta["years"]:
                if yr not in collection_meta[coll_id]["years"]:
                    collection_meta[coll_id]["years"].append(yr)
                    collection_meta[coll_id]["years"].sort()

        year_str = ', '.join(str(y) for y in meta["years"])
        print(f"  ✓ {meta['label']:<30} ({year_str})  {len(texts):>5} tweets  {len(unis):>6} terms")

    # ── Literary corpora ──────────────────────────────────────────────────
    print("\n── Literary Corpora ──")
    literary = {
        "lyrics":     ("lyrics_corpora.txt",     "Hip-hop & R&B lyrics (~15,000 songs from influential Black artists)"),
        "literature": ("literature_corpora.txt",  "African American literature (54 books, HBCUs & Black archives)"),
        "leadership": ("leadership_corpora.txt",  "Speeches by Black leaders (Douglass, MLK, Obama, and others)"),
    }
    for coll_id, (filename, context) in literary.items():
        filepath = os.path.join(CORPORA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  ⚠ MISSING: {filename}")
            continue
        texts = extract_text_plain(filepath)
        unis, ngs = process_texts(texts)
        for t in unis:  uni_counts[t][coll_id]   += 1
        for t in ngs:   ngram_counts[t][coll_id] += 1
        collection_meta[coll_id] = {"label": coll_id.capitalize(), "context": context}
        print(f"  ✓ {coll_id:<14}  {len(unis):>6} terms")

    # ── Build reference ───────────────────────────────────────────────────
    print("\n── Filtering ──")
    all_coll_ids = list(collection_meta.keys())
    reference    = {}
    kept_uni = kept_ng = 0

    for term, counts in uni_counts.items():
        total = sum(counts.values())
        if total >= MIN_FREQ_UNIGRAM:
            entry = {c: counts.get(c, 0) for c in all_coll_ids}
            entry["_total"] = total
            reference[term] = entry
            kept_uni += 1

    for term, counts in ngram_counts.items():
        if term in reference:
            continue
        total = sum(counts.values())
        if total >= MIN_FREQ_NGRAM:
            entry = {c: counts.get(c, 0) for c in all_coll_ids}
            entry["_total"] = total
            reference[term] = entry
            kept_ng += 1

    reference = dict(sorted(reference.items(), key=lambda x: x[1]["_total"], reverse=True))

    print(f"  Unigrams: {kept_uni:,}  (min freq ≥ {MIN_FREQ_UNIGRAM})")
    print(f"  N-grams:  {kept_ng:,}  (min freq ≥ {MIN_FREQ_NGRAM})")

    # ── Write output ──────────────────────────────────────────────────────
    output = {
        "_meta": {
            "collections": collection_meta,
            "total_terms": len(reference),
            "corpus_note": (
                "AAVE Corpora Collection (jazmiahenry/aave_corpora). "
                "Social media data compiled 2015-2022. "
                "Literary corpora compiled through June 2022. "
                "Absence from this corpus does NOT indicate non-AAVE origin."
            ),
        },
        "terms": reference,
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\n── Output ──")
    print(f"  File:  {OUTPUT_FILE}")
    print(f"  Terms: {len(reference):,}")
    print(f"  Size:  {size_kb:.1f} KB")

    # ── Spot-check ────────────────────────────────────────────────────────
    spot_check = [
        "ain't", "finna", "gonna", "y'all", "lowkey", "no cap",
        "bussin", "slay", "woke", "clap back", "deadass", "bet",
        "tripping", "grandma", "savage", "smh", "smdh", "wassup",
        "sheesh", "periodt", "fr fr", "on god",
    ]
    print(f"\n── Spot-check ──")
    print(f"  {'TERM':<20}  {'FOUND':>5}  {'TOTAL':>5}  COLLECTIONS WITH HITS")
    print(f"  {'-'*70}")
    for term in spot_check:
        if term in reference:
            d = reference[term]
            hits = [(c, d[c]) for c in all_coll_ids if d.get(c, 0) > 0]
            hit_str = ', '.join(f"{c}:{n}" for c, n in hits[:5])
            print(f"  {repr(term):<20}  {'YES':>5}  {d['_total']:>5}  {hit_str}")
        else:
            print(f"  {repr(term):<20}  {'--':>5}")

    print(f"\n  Done.\n")


if __name__ == "__main__":
    main()
