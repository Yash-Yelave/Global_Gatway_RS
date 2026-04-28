# Enterprise Architecture & Integration Report
**Phase:** Week 2, Day 1 — Pipeline Integration Architecture
**Objective:** Establish a unified structure across all pipeline stages, enforce strict data contracts, and eliminate system inconsistencies.

## 1. Pipeline Flow Consolidation
The system architecture has been formally consolidated into a synchronous, 5-stage execution flow. Each stage is strictly isolated, ensuring modularity and easier debugging.

1. **Ingestion (Scraper):** Connects to `settings.RSS_FEEDS`. Generates raw metadata dictionaries.
2. **Sanitization (Cleaner):** Strips HTML, enforces `settings.MIN_WORD_COUNT`, standardizes timestamps, and removes exact duplicates.
3. **Semantic Enrichment (NLP):** Applies `spaCy` (NER) and `TextBlob` (Sentiment). Calculates the Exponential Freshness Decay using `settings.DECAY_RATE`.
4. **Machine Learning (Recommender):** Vectorizes text via TF-IDF (capped at `settings.TFIDF_MAX_FEATURES`), computes Cosine Similarity, and calculates the Logarithmic Trending Score.
5. **Storage (Database):** Splits the unified DataFrame into relational SQLite tables (`trending_articles`, `similar_articles`, `category_rankings`).

## 2. Unified Data Contract
To prevent pipeline fractures, a strict Data Contract has been established. Before writing to the database, the overarching `master_articles` DataFrame must conform to the following schema:

| Column Name | Data Type | Constraint / Rules |
| :--- | :--- | :--- |
| `article_id` | String | Primary Key (Format: `art_{UUID}`). |
| `title` | String | Non-null. |
| `description` | String | Non-null. Minimum word count enforced. |
| `url` | String | Unique constraint. |
| `source` | String | Mapped from RSS feed title. |
| `publish_date` | Datetime | Standardized ISO/UTC format. |
| `nlp_keywords_json` | JSON | Stringified array of extracted entities. |
| `tb_sentiment_score` | Float | Range: `-1.0000` to `1.0000`. |
| `tb_sentiment_label` | String | Enum: `positive`, `negative`, `neutral`. |
| `auto_category` | String | Must match predefined `CATEGORY_MAPPING`. |
| `freshness_decay_score`| Float | Range: `0.0000` to `1.0000`. |
| `trending_score` | Float | Normalized Range: `0.00` to `10.00`. |

## 3. Centralized Configuration
All hardcoded parameters, thresholds, and mappings have been stripped from individual processing scripts and moved to a centralized `Config` class within `config.py`.

* **Benefit:** Adjusting the algorithm (e.g., changing the freshness decay rate, adding a new category, or altering the minimum word count) now requires editing only a single line of code in the configuration file, rather than hunting through multiple modules.

## 4. Integration Readiness & Technical Debt Addressed
During the integration check, three primary operational gaps were identified for resolution in upcoming sprints:

1. **Global Error Handling (Resolved):** Implemented Python `logging` and global `try/except` blocks in the orchestrator to prevent catastrophic crashes during autonomous background scheduling.
2. **Database Upserting (Pending):** Transitioning `pandas.to_sql` from `replace` mode to an `upsert` (append/update) mode to preserve historical data.
3. **Vector Scalability (Pending):** Identifying a future transition from in-memory TF-IDF cosine similarity to an Approximate Nearest Neighbor (ANN) index (like FAISS) to handle corpus sizes exceeding 100,000 articles.
