# Starts With Black Bot

A linguistic origin tracer for African American Vernacular English (AAVE).

Enter a slang term or paste tweet text to analyze whether the language originates in AAVE — grounded in real corpus data, academic sources, and Claude's linguistic knowledge.

## Using the App

**Live:** [https://nxcodex.github.io/starts-with-black-bot](https://nxcodex.github.io/starts-with-black-bot)

On first load, enter your Anthropic API key. It's stored in your browser only — never in the code.

### Two input modes

**Term** — type a single slang term and hit Analyze.

**Tweet** — paste the text of a tweet. The tool identifies candidate AAVE terms, shows them for your review, then analyzes confirmed selections.

### What the output includes

- **Origin label** — Likely AAVE / Possibly AAVE / Unlikely AAVE
- **Rationale** — evidence-based explanation citing corpus data and linguistic knowledge
- **Meaning & Usage** — what the term means and how it's used
- **Origin context** — when and where it likely emerged
- **Corpus evidence** — appearances in documented Black cultural collections (when found)
- **Academic sources** — real papers from Semantic Scholar with DOI links (when found)

## Files

| File | Purpose |
|---|---|
| `index.html` | The entire app — open this in any browser |
| `aave_reference.json` | Pre-processed AAVE Corpora term index |
| `build_reference.py` | Script to regenerate `aave_reference.json` from source corpus |
| `.gitignore` | Excludes the 400MB raw corpus folder |

## Regenerating the Corpus Reference

If you want to rebuild `aave_reference.json` from the source data:

```bash
# Clone the AAVE Corpora
git clone https://github.com/jazmiahenry/aave_corpora

# Run the processor from the project folder
python3 build_reference.py
```

## Data Sources

- **AAVE Corpora Collection** — [github.com/jazmiahenry/aave_corpora](https://github.com/jazmiahenry/aave_corpora) (MIT License)
- **Semantic Scholar** — academic paper search API
- **Anthropic Claude** — linguistic analysis engine

## Built by

Nick Mazzucco, 2026
