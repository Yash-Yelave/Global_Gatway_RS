# Autonomous News Processing & Recommendation Engine - Project Summary

## What This Project Is
This repository implements a **modular, 5-stage, end-to-end news ingestion + enrichment + recommendation pipeline** in Python. It:

1. Pulls article URLs from a large set of **RSS feeds**.
2. Scrapes full article text from the web.
3. Cleans and filters low-quality / non-English / boilerplate content.
4. Enriches articles with **tags, sentiment, category**, and a **freshness decay score**.
5. Produces recommendation artifacts:
   - **Trending** ranking
   - **Content-similar** article mappings (TF-IDF + cosine similarity)
   - **Per-category** rankings
6. Persists outputs into local **SQLite** databases for downstream consumption.

The pipeline is orchestrated by `main.py` and is designed to be run manually or scheduled (APScheduler hooks are referenced in the README).

## Repository Layout (Top-Level)
Core code:
- `main.py`: Pipeline orchestrator / CLI entrypoint.
- `scraper.py`: RSS ingestion + web scraping + optional Groq LLM extraction.
- `cleaner.py`: Text normalization + quality filtering + language filtering.
- `nlp_pipeline.py`: spaCy/TextBlob enrichment + freshness decay.
- `recommender.py`: Trending score + TF-IDF similarity + category ranking.
- `database.py`: SQLAlchemy models + DB initialization helpers.
- `config.py`: Central configuration via environment variables + RSS feed registry.

Docs and references:
- `README.md`: Setup + how to run.
- `SYSTEM_ARCHITECTURE.md`: Detailed architectural description of the 5 stages.
- `WEEK_2_DAY_1_ARCHITECTURE_REPORT.md`: Integration notes and a proposed "data contract".
- `Global Gateway RS - Unified Technic.md`: Additional project write-up (reference/spec notes).

Data artifacts (generated / used locally):
- `raw_data.db`: SQLite DB written by `main.py` containing the raw scrape output (`raw_articles`).
- `recommendations.db`: SQLite DB written by `main.py` containing final outputs/tables.
- `news_engine.db`: Additional SQLite DB artifact present in the repo (not used by `main.py` by default).

Other folders:
- `venv/`: Local virtual environment (repo-local).
- `__pycache__/`: Python bytecode cache.
- `old_codes/`, `old_docs/`: Archived material (not referenced by current pipeline entrypoint).

## How the Pipeline Runs (High Level)
`main.py` is the single entrypoint. It performs these steps in order:

1. **Initialize DB schema** (SQLAlchemy `create_all`) via `init_db()` from `database.py`.
2. **Scrape** articles (RSS -> URL -> full text) via `run_scraper()` in `scraper.py`.
3. **Save raw scrape output** into `raw_data.db` as table `raw_articles` (via `pandas.to_sql(..., if_exists="replace")`).
4. **Clean** via `run_cleaner()` in `cleaner.py`.
5. **Enrich** via `run_nlp()` in `nlp_pipeline.py` (local NLP and/or hybrid with Groq mode).
6. **Recommend** via `run_recommender()` in `recommender.py` to generate multiple output DataFrames.
7. **Persist** final DataFrames into the configured SQLite DB (default `recommendations.db`) as multiple tables (again using `to_sql(..., if_exists="replace")`).
8. **Verify output** by querying and printing a preview of the `trending_articles` and `similar_articles` tables.

## Runtime Modes (Groq vs Local vs Hybrid)
When you run `python main.py`, it prompts for a mode (or accepts an argument `1`, `2`, or `3`):

- **1 = Groq LLM** extraction for tags/sentiment/category at scrape-time.
- **2 = Local NLP** using spaCy + TextBlob (no Groq calls).
- **3 = Both (Hybrid)**: scrape-time Groq extraction, then local NLP runs and may override/supplement tags/sentiment/category.

### Practical Implications
- Mode **1** depends on a valid `GROQ_API_KEY` (and network access).
- Mode **2** requires the spaCy model `en_core_web_sm` to be installed locally.
- Mode **3** requires both.

## Module-by-Module Behavior (Detailed)

### 1. `config.py` (Central Settings)
`config.py` loads environment variables using `python-dotenv` and exposes a singleton:

- `settings = Config()`
- Backward-compat aliases: `config = settings`, plus `DATABASE_URI`, `RAW_DATA_URI`

Key settings:
- `DATABASE_URL` (default: `sqlite:///recommendations.db`)
- `RAW_DATA_URL` (default: `sqlite:///raw_data.db`)
- `NEWS_API_KEY` (default: empty string)
- `GROQ_API_KEY` (default: empty string)
- `MAX_ARTICLES_PER_FEED` (default: `50`)
- `MIN_WORD_COUNT` (default: `15`)
- `TFIDF_MAX_FEATURES` (default: `5000`)
- `CATEGORY_MAPPING` (keyword lists used for classification)
- `RSS_FEEDS`: a large dictionary of RSS sources keyed by human-readable name

Note: `scraper.py` currently embeds its own `RSS_FEEDS` dict as well, instead of importing `settings.RSS_FEEDS`.

### 2. `scraper.py` (Ingestion + Scraping + Optional Groq Extraction)
Primary responsibilities:

- **Fetch RSS entries** using `feedparser`:
  - `fetch_rss_urls(feeds, max_per_feed)` returns a list of dicts containing `source`, `url`, `rss_title`, and `published`.
- **Scrape article content** from each URL using `newspaper3k`:
  - `scrape_article(url)` downloads/parses and returns scraped fields like `raw_text`, `scraped_title`, `scraped_author`, `scraped_date`, `meta_desc`, `top_image`.
- **(Optional) Groq LLM extraction**:
  - `extract_with_groq(scraped)` sends a prompt to Groq chat completions (model: `llama-3.1-8b-instant`) and expects JSON output.
  - A basic `time.sleep(RATE_LIMIT_SEC)` throttles calls.
- **Data contract enforcement** via a Pydantic model:
  - Validates/normalizes: `title`, `description`, `author`, `tags` (max 5), `category` (enum), `sentiment` (enum), and `publish_date`.
- **Stable IDs**:
  - `build_article_id(url)` generates `art_` + truncated MD5 hash.

Output:
- `run_scraper(nlp_choice, max_articles)` returns a `list[dict]` of validated article dictionaries.

Important fields produced by this stage (typical):
- `article_id`, `url`, `source`, `title`, `description`, `author`
- `tags` (list in-memory; later JSON-serialized)
- `category`, `sentiment`
- `publish_date`
- `top_image`, `scraped_at`

### 3. `cleaner.py` (Normalization + Filtering)
Primary responsibilities:

- Text cleanup via regex:
  - Strip HTML tags
  - Collapse whitespace
  - Remove non-ASCII characters
  - Remove embedded URLs
- Enforce valid enums:
  - Categories: `technology`, `politics`, `sports`, `business`, `health`, `science`, `entertainment`, `general`
  - Sentiments: `positive`, `neutral`, `negative`
- Filtering / quality gates:
  - Drop if description < 10 words
  - Drop if "boilerplate phrases" appear (paywall/cookie banners/etc.)
  - Drop if `langdetect` does not classify the description as English (`en`)

Output:
- `run_cleaner(raw_data)` returns a cleaned `pandas.DataFrame` with `is_clean` + `lang` columns used for filtering.

### 4. `nlp_pipeline.py` (Local NLP Enrichment + Freshness Decay)
Primary responsibilities:

- Local tag extraction using **spaCy** NER + noun chunks:
  - Entities used: `PERSON`, `ORG`, `GPE`, `LOC`, `PRODUCT`, `EVENT`
- Sentiment labeling using **TextBlob** polarity thresholds:
  - `> 0.05` => positive
  - `< -0.05` => negative
  - else neutral
- Auto-categorization via keyword matching against `CATEGORY_MAPPING`.
- Freshness scoring:
  - Exponential decay based on days-old:
    - `score = exp(-DECAY_RATE * days_old)`
    - `DECAY_RATE` is currently `0.1` in this module.

Output:
- `run_nlp(df, nlp_choice)` returns an enriched DataFrame.

Serialization behavior:
- Tags are stored into `df['tags']` and JSON-serialized (`json.dumps`) so they can be stored in SQLite.

### 5. `recommender.py` (Trending + Similarity + Category Ranking)
Primary responsibilities:

1. Trending score:
   - If `view_count` not present, it is simulated with a seeded RNG (10..10000).
   - `trending_score = log1p(view_count) * freshness_decay_score`
   - Normalized to a 0..10-ish scale (rounded to 2 decimals).

2. Similarity:
   - Build a `text_corpus = title + " " + description`.
   - `TfidfVectorizer(stop_words='english', max_features=5000)` (note: currently hard-coded 5000 here).
   - `cosine_similarity` between all pairs.
   - For each article, capture top 5 most similar (excluding itself) and store as JSON string:
     - `similar_articles_json = [{"similar_article_id": ..., "similarity_score": ...}, ...]`

3. Category rankings:
   - Dense rank by `trending_score` within each category.

Output:
- `run_recommender(df)` returns a dict of DataFrames:
  - `master`
  - `trending`
  - `similar`
  - `category_rankings`

### 6. `database.py` (SQLAlchemy Schema Helpers)
This module defines SQLAlchemy ORM models and helpers:

- `engine = create_engine(config.DATABASE_URI, echo=False)`
- `init_db()` calls `Base.metadata.create_all(bind=engine)`

Models declared:
- `Article` -> table `articles`
- `TrendingArticle` -> table `trending_articles`
- `SimilarArticle` -> table `similar_articles`
- `CategoryRanking` -> table `category_rankings`

Important: although SQLAlchemy models exist, **`main.py` persists data with `pandas.to_sql(..., if_exists="replace")`** rather than ORM sessions. That means the ORM schema is more of a reference/initializer than the actual writer used during pipeline runs.

## Databases and Tables Produced

### Raw DB: `raw_data.db`
Written by `main.py` every run (replace mode).

- `raw_articles`: the raw scraped output from `scraper.py` (after converting `tags` to JSON strings if needed).

### Final DB (default): `recommendations.db`
Controlled by `DATABASE_URL` in `.env` (defaults to `sqlite:///recommendations.db`).

Tables written by `main.py` every run (all replace mode):
- `articles`: master enriched dataset (all columns carried forward).
- `trending_articles`: subset of columns focused on trending output.
- `similar_articles`: mapping table containing `article_id` and `similar_articles_json`.
- `category_rankings`: per-category ranks.

## Configuration and Environment Variables
Environment files:
- `.env.example`: template values
- `.env`: your local secrets/config (present in repo)

Expected keys (based on code):
- `DATABASE_URL` (optional; defaults to `sqlite:///recommendations.db`)
- `RAW_DATA_URL` (optional; defaults to `sqlite:///raw_data.db`)
- `NEWS_API_KEY` (optional; not strictly required for RSS scraping)
- `GROQ_API_KEY` (required for Groq mode)
- `MAX_ARTICLES_PER_FEED` (optional)
- `MIN_WORD_COUNT` (optional)
- `TFIDF_MAX_FEATURES` (optional; not currently wired into `recommender.py`)

## Installing / Running (What the Repo Expects)
Dependencies are listed in `requirements.txt` and include:
`pandas`, `numpy`, `spacy`, `textblob`, `scikit-learn`, `SQLAlchemy`, `feedparser`, `python-dateutil`,
`APScheduler`, `python-dotenv`, `newspaper3k`, `beautifulsoup4`, `groq`, `pydantic`, `langdetect`, etc.

Local NLP requires the spaCy model:
```bash
python -m spacy download en_core_web_sm
```

Run the pipeline:
```bash
python main.py
```

Run with a non-interactive mode selection:
```bash
python main.py 2
```

## Current "Design Notes" and Known Gaps (Based on Code in This Repo)
These are not necessarily bugs, but they matter if you're extending the project:

1. `config.py` and `scraper.py` both contain RSS feed registries.
   - The pipeline currently uses `scraper.py`'s internal `RSS_FEEDS`, not `settings.RSS_FEEDS`.

2. `database.py` defines ORM tables, but pipeline writes happen through `pandas.to_sql(..., if_exists="replace")`.
   - That discards history each run (no upserts, no accumulation).

3. `recommender.py` hardcodes `max_features=5000` even though `config.py` has `TFIDF_MAX_FEATURES`.

4. `view_count` is simulated (seeded RNG) unless you provide it upstream.
   - Trending is therefore deterministic for a given run size, but not based on real engagement signals.

5. Freshness decay uses `DECAY_RATE = 0.1` in `nlp_pipeline.py`.
   - `WEEK_2_DAY_1_ARCHITECTURE_REPORT.md` references a `settings.DECAY_RATE`, but that's not implemented in `config.py` currently.

6. `config.py` contains some non-ASCII/encoding artifacts in comment separators.
   - They do not affect runtime, but they can display oddly in some editors/terminals.

## Where To Start Reading the Code
If you're onboarding to this repository:

1. Read `main.py` to understand the execution order and the produced tables.
2. Read `scraper.py` to understand data ingestion and the Groq/local mode split.
3. Read `cleaner.py` and `nlp_pipeline.py` to understand what fields are guaranteed downstream.
4. Read `recommender.py` for how trending/similarity/category ranking is computed.
5. Refer to `SYSTEM_ARCHITECTURE.md` for a narrative explanation of the same flow.
