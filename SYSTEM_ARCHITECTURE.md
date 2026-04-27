# Autonomous News Recommendation Engine
## Comprehensive System Documentation & Architecture

This document provides a highly detailed, granular breakdown of the Autonomous News Recommendation Engine. It covers the data flow, specific algorithms, NLP methodologies, and database schemas used to process raw RSS feeds into a fully structured, queryable recommendation backend.

---

## 1. System Overview & Architecture

The system is a 5-stage Python-based data engineering pipeline designed to autonomously fetch, clean, enrich, and map news articles.

**The Data Flow Pipeline:**
1. **Scraper (`scraper.py`)**: Fetches raw articles from RSS feeds and uses an LLM (Groq) or standard parsers to extract text.
2. **Cleaner (`cleaner.py`)**: Normalizes the text, removes HTML, filters out non-English articles, and drops paywall/boilerplate content.
3. **NLP Pipeline (`nlp_pipeline.py`)**: Enriches the clean text with keyword extraction, sentiment analysis, auto-categorization, and calculates exponential freshness.
4. **Recommender (`recommender.py`)**: Calculates logarithmic trending scores and builds a TF-IDF Cosine Similarity matrix to map related articles.
5. **Database (`main.py` / `database.py`)**: Serializes complex data types (JSON arrays) and persists the final dataframes to a local SQLite database for downstream API consumption.

---

## 2. Module Breakdown

### Stage 1: Data Scraping (`scraper.py`)
This module is responsible for raw data ingestion and structural mapping.

*   **RSS Ingestion**: Connects to predefined publisher endpoints (e.g., BBC, TechCrunch, Al Jazeera). It uses `feedparser` to extract the top `X` article URLs (currently configured to fetch up to 40 per feed to satisfy a 100-article pipeline).
*   **Web Scraping**: Utilizes `newspaper3k` and `BeautifulSoup4`. It downloads the HTML of each URL, bypasses basic bot protections, and extracts the `raw_text`, `scraped_title`, `authors`, `publish_date`, and `top_image`.
*   **LLM Extraction (Optional Mode)**: 
    *   If selected, the raw text is passed to the **Groq API** (`llama-3.1-8b-instant`).
    *   A strict prompt forces the LLM to output pure JSON containing an intelligent summary, sentiment, 3-5 keywords, and a category.
    *   *Rate Limiting*: A hardcoded `time.sleep(2.5)` prevents API rate limits.
*   **Data Validation**: Before an article enters the pipeline, it passes through a `Pydantic` validation model (`NewsArticle`). This ensures types are correct (e.g., ensuring `category` strictly matches one of the 8 predefined categories, and `sentiment` is exactly positive/neutral/negative).
*   **Unique Hashing**: An MD5 hash of the URL is generated and truncated to 8 characters to create a unique `article_id` (e.g., `art_a1b2c3d4`).

### Stage 2: Data Cleaning (`cleaner.py`)
Raw scraped data is inherently messy. This stage drops unusable data.

*   **Text Normalization**: Regular expressions (`re.sub`) strip out all `<HTML>` tags, non-ASCII characters, stray URLs within the text body, and compresses multiple spaces into a single space.
*   **Quality Control (Boilerplate Removal)**: Articles containing phrases like "subscribe to read", "cookie policy", or "javascript is required" are flagged as paywalled or blocked and are dropped.
*   **Length Enforcement**: Articles with a description length of fewer than 10 words are considered too sparse for TF-IDF calculations and are dropped.
*   **Language Enforcement**: Uses the `langdetect` library to analyze the description. Any article not classified as `"en"` (English) is dropped to prevent the NLP models from hallucinating or failing.

### Stage 3: NLP Enrichment (`nlp_pipeline.py`)
This stage gives the system "intelligence" using traditional Natural Language Processing.

*   **Named Entity Recognition (NER)**: Uses `spaCy` (`en_core_web_sm`). It parses the text and extracts entities labeled as `PERSON`, `ORG`, `GPE` (Geopolitical Entities), and `EVENT`. It also extracts primary Noun Chunks. These become the article's `tags`.
*   **Sentiment Analysis**: Uses `TextBlob` to calculate the polarity of the text. 
    *   Polarity > `0.05` = Positive
    *   Polarity < `-0.05` = Negative
    *   Otherwise = Neutral
*   **Auto-Categorization**: Uses a dictionary mapping of keywords (e.g., "AI", "Apple", "Software" -> `technology`). It cross-references the spaCy extracted keywords against this map. The category with the highest hits wins. If tied at 0, it defaults to `"general"`.
*   **Freshness Decay Algorithm**: 
    *   News becomes irrelevant quickly. The system uses an **Exponential Decay Formula**: $Score = e^{-0.1 \times \text{days\_old}}$.
    *   An article published today gets a freshness score of `1.0`. An article published 7 days ago gets a score of `~0.49`.

### Stage 4: Recommendation Engine (`recommender.py`)
This stage generates the metrics required to actually serve recommendations to users.

*   **Trending Score Calculation**:
    *   The system simulates page views (random integer between 10 and 10,000).
    *   The formula balances raw popularity against time: `Log(view_count) * freshness_decay_score`.
    *   Using a logarithm (`log1p`) ensures that an article with 10,000 views doesn't completely eclipse an article with 1,000 views, allowing newer articles with decent views to outrank older viral articles. Scores are normalized to a 0-10 scale.
*   **Similar Articles Mapping (TF-IDF)**:
    *   Concatenates the `title` and `description` to create a `text_corpus`.
    *   Uses `scikit-learn`'s `TfidfVectorizer` (Term Frequency-Inverse Document Frequency) capped at 5000 max features, dropping standard English stop words.
    *   Calculates a `cosine_similarity` matrix across all articles.
    *   For every article, it slices the top 5 highest similarity scores and packages them into a JSON string map: `[{"similar_article_id": "art_123", "similarity_score": 0.89}, ...]`.
*   **Category Rankings**: Groups articles by category and uses a `dense` ranking method based on the `trending_score` to determine the top articles per category.

### Stage 5: Database Persistence (`main.py` & `database.py`)
Data must be serialized and saved for API usage.

*   **SQLite Operations**: Uses `SQLAlchemy` and `pandas.to_sql`.
*   **JSON Serialization**: SQLite does not support native Arrays. Therefore, the list of `tags` and the `similar_articles` dictionaries are converted into `json.dumps()` strings before insertion.
*   **Generated Tables**:
    1.  `articles`: The master table containing all scraped, cleaned, and NLP-enriched data.
    2.  `trending_articles`: A view table isolating the `trending_score` and `freshness_decay_score`.
    3.  `similar_articles`: A mapping table linking an `article_id` directly to its JSON similarity map.
    4.  `category_rankings`: A view table mapping articles to their local category rank.

---

## 3. Orchestrator & Execution

The system is tied together by `main.py`.

1.  **Interactive Selection**: Upon running `python main.py`, the user is prompted to select the processing mode:
    *   **Mode 1**: High-Accuracy (Groq LLM for tags/sentiment)
    *   **Mode 2**: Offline/Fast (spaCy/TextBlob for tags/sentiment)
    *   **Mode 3**: Hybrid (Groq extraction supplemented by local NLP)
2.  **Verification Tool**: After saving to SQLite, the orchestrator triggers `verify_output()`. This function queries the live database using `pandas.read_sql` and uses the `tabulate` library to print a formatted Markdown table of the Top 10 Trending articles and prints the raw JSON maps for similarity verification.

---
*End of Documentation.*
