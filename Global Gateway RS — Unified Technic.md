Global Gateway RS --- Unified Technical Documentation 1. Project Summary

This project is a complete news intelligence pipeline that starts with
collecting articles from RSS feeds, then scrapes and validates the
content, stores it in a relational database layer, enriches it with NLP
and feature engineering, and finally prepares precomputed recommendation
tables for instant downstream serving. The overall goal is to support
news recommendation systems, data analysis workflows, and AI-driven
content categorization with high-quality, structured, machine-ready
data.

2\. End-to-End Pipeline Architecture

The full workflow follows this order:

RSS feed collection and article scraping Data cleaning, validation, and
feature engineering Persistent storage design with PostgreSQL and SQLite
fallback NLP enrichment and semantic feature generation Recommendation
data preparation and precomputation

This layered design separates acquisition, transformation, storage,
semantic analysis, and recommendation serving so that each stage can be
optimized independently.

3\. Data Scraping, Aggregation, and AI-Based Extraction 3.1 Project
Overview

The scraping layer implements a scalable news data pipeline that
aggregates articles from multiple RSS feeds, scrapes full article
content, and uses a large language model through the Groq API to extract
structured insights. It is intended for use in recommendation systems,
analysis pipelines, and AI-based content categorization. The reference
implementation is linked to the GitHub repository Global_Gatway_RS.

3.2 Objectives

The goals of this stage are to:

Aggregate news from 100+ global RSS feeds Scrape full article content
efficiently Extract structured metadata using Groq / LLaMA 3.1 Validate
and standardize the data Store results in CSV, JSON, and SQLite Perform
quick exploratory data analysis for insights 3.3 Tech Stack

The scraping and extraction workflow uses the following tools and
libraries:

groq newspaper3k feedparser pandas pydantic BeautifulSoup 3.4 System
Architecture

The pipeline architecture is:

RSS Feeds → URL Extraction → Article Scraping → LLM Processing (Groq) →
Data Validation → Storage → EDA Analysis.

3.5 Workflow Explanation 3.5.1 Dependency Setup

The pipeline installs the required libraries for feed parsing, scraping,
validation, and AI extraction.

3.5.2 Configuration and Initialization

The system defines:

Groq API client configuration The model llama-3.1-8b-instant Rate-limit
handling Retry logic Category definitions used later for classification
3.5.3 RSS Feed Collection

The feed collection stage retrieves articles from 100+ sources across
regions and topics such as UAE, China, Global, Tech, and Business. The
function fetch_rss_urls() outputs metadata such as:

{ \"source\": \"BBC\", \"url\": \"\...\", \"rss_title\": \"\...\",
\"published\": \"\...\" }

This stage also handles duplicate removal and logs failed feeds.

3.5.4 Article Scraping

The function scrape_article() extracts:

Title Full text Author Publish date Meta description Top image

It uses newspaper3k as the primary extractor and BeautifulSoup as a
fallback.

3.5.5 AI-Based Extraction with Groq

The function extract_with_groq() converts raw article text into
structured JSON fields such as:

{ \"title\": \"\", \"description\": \"\", \"author\": \"\", \"tags\":
\[\], \"category\": \"\", \"sentiment\": \"\", \"publish_date\": \"\",
\"language\": \"\" }

This stage includes retry logic, rate-limit handling, token control,
JSON cleanup, and quota handling.

3.5.6 Data Validation with Pydantic

A NewsArticle model validates:

Category correctness Sentiment values Tag normalization Non-empty fields

It also generates a unique article_id using an MD5 hash.

3.5.7 Data Merging Logic

The function validate_and_merge() combines:

RSS metadata Scraped content LLM output

The fallback priority is:

LLM → Scraped → RSS.

3.5.8 Pipeline Execution

The function run_pipeline() performs the full execution sequence:

Fetch URLs Scrape articles Process with Groq Validate data Save results

Operational features include auto-save every 25 articles, deduplication,
live progress logs, error handling, and rate limiting.

3.5.9 Data Storage

The function save_outputs() saves the dataset in:

news_dataset.csv news_dataset.json news_dataset.db (SQLite)

Tags are stored as JSON in SQLite.

3.5.10 Exploratory Data Analysis

The pipeline also provides EDA for:

Total articles Unique sources Language distribution Category
distribution Sentiment distribution Missing values 3.6 Run Metrics

For the documented run:

Target articles: 500 Articles collected: 252 Unique sources: 53 API
calls: 459 Token usage: approximately 299.9K Limitation reached: Groq
rate/token limit 4. Phase 2 --- Data Cleaning and Feature Engineering
4.1 Overview

This stage processes raw web-scraped news articles in CSV format through
a fully offline, five-stage pipeline. Its purpose is to transform noisy,
unstructured web data into a clean, enriched, machine-learning-ready
dataset. It performs text cleaning, quality filtering, feature
engineering across NLP, sentiment, temporal, and source dimensions,
vectorization, and semantic clustering. The resulting data is saved in
multiple formats: CSV, JSON, SQLite, and NumPy arrays.

4.2 Prerequisites and Environment Setup

The pipeline is designed for Jupyter or Google Colab and runs entirely
with local models and offline processing. No external API calls are
required. The required packages are:

pandas numpy scikit-learn nltk spacy sentence-transformers rapidfuzz
langdetect python-dateutil

The pre-downloaded models include:

spaCy en_core_web_sm NLTK vader_lexicon, stopwords, punkt,
averaged_perceptron_tagger Sentence Transformers all-MiniLM-L6-v2 4.3
Pipeline Architecture Stage 1: Basic Cleaning

This stage ensures structural integrity and consistent formatting:

Removes exact URL duplicates Drops rows missing essential fields such as
title or description Drops titles shorter than 3 words Drops
descriptions shorter than 10 words Removes lingering HTML tags using
regex Normalizes whitespace Removes non-ASCII characters Removes
embedded URLs Parses the tags column from JSON strings into Python lists
Normalizes category and sentiment to predefined valid lists, defaulting
to general or neutral when unmatched Parses publish_date into standard
YYYY-MM-DD datetime format Fills missing authors with \"Unknown\" Stage
2: Text Quality Filtering

Instead of removing suspicious content immediately, this stage evaluates
quality and assigns an is_clean boolean mask. Only articles marked
is_clean=True move forward into deep feature engineering. Checks
include:

Title-description parity detection when the description is an exact copy
of the title Description length check below 10 words Boilerplate
detection using phrases such as \"subscribe to read\" and \"cookie
policy\" Sentence repetition penalty using a uniqueness ratio Language
validation using langdetect, especially for assumed English sources that
are detected as non-English Stage 3: Feature Engineering

This stage enriches the dataset with actionable metadata.

3a. Basic Text Features

It generates:

word_count reading_time_mins using an average reading speed of 200 words
per minute keyword_density title_word_count has_image 3b. Sentiment
Scoring

Using NLTK VADER on the combined title and description, the pipeline
produces:

sentiment_score in the range -1 to 1 positive, negative, and neutral
ratios sentiment_label_vader based on compound thresholds 3c. Named
Entity Recognition

Using spaCy on the first 1000 characters for performance, the pipeline
extracts:

entities_persons entities_organizations entities_locations entity_count
3d. Temporal Features

The pipeline creates:

article_age_days publish_day_of_week publish_hour is_recent for articles
published within the last 48 hours freshness_score, a linear decay from
1.0 down to 0.0 over 30 days 3e. Source-Based Features

The system maps the source name against predefined dictionaries to
assign:

source_region such as UAE, Gulf, China, Asia, or Global source_tier with
values 1, 2, or 3, representing editorial credibility or authority 3f.
Sub-Categorization

A rule-based keyword matching dictionary assigns granular sub-categories
such as mapping "technology" into "AI & Machine Learning" or
"Cybersecurity."

Stage 4: Vectorization and Embeddings

The text is prepared for similarity-based algorithms:

TF-IDF is generated with a maximum of 5000 features and 1--2 n-grams The
top 10 TF-IDF terms per article are stored in tfidf_top_terms Combined
title and description are fed into all-MiniLM-L6-v2 The model generates
dense 384-dimensional embeddings Embeddings are stored externally in an
.npy file to avoid bloating the CSV or database Stage 5: Deduplication
and Story Grouping

This stage prevents the recommendation engine from suggesting the same
story from multiple outlets:

Fuzzy deduplication uses rapidfuzz with a threshold of at least 85
Semantic story grouping computes cosine similarity on dense embeddings
Articles with similarity score \>= 0.88 receive the same integer
story_id, clustering coverage of the same event 4.4 Final Outputs

Before saving, all Python lists such as NER entities, tags, and TF-IDF
terms are serialized into JSON strings for safe storage. The pipeline
produces:

news_cleaned.csv news_cleaned.json news_cleaned.db
article_embeddings.npy 5. Day 4 --- PostgreSQL Storage Layer and Schema
Design 5.1 Overview and Objectives

This document defines the relational storage architecture for the Global
Gateway RS pipeline. It builds on the Phase 2 cleaned and enriched
dataset, which already includes advanced NLP features such as VADER
sentiment scoring, spaCy-based NER, and MiniLM-L6-v2 semantic
clustering. Day 4 focuses on persisting these structures efficiently
using PostgreSQL in production, with native JSONB, TSVECTOR, SQLAlchemy
ORM, and a repository pattern.

5.2 File Structure and Component Breakdown

The storage layer is modularized into three main components:

models.py: Contains the SQLAlchemy Declarative Base and the Article
schema definition, mapping Python types to PostgreSQL-specific dialects
repository.py: Implements ArticleRepository, abstracts the database
connection via SessionLocal, and provides CRUD operations with
transaction rollback and integrity error handling alembic/: Contains the
migration environment, alembic.ini, and version-controlled migration
scripts for schema evolution 5.3 Database Schema: articles Table

The schema is designed to store both the raw scraped data and the
enriched NLP features.

5.3.1 Core Metadata

The following fields are included:

id --- auto-incrementing integer primary key url_hash --- MD5 hash of
the article URL, unique and indexed, used for strict deduplication and
primary lookup url title description author, defaulting to \"Unknown\"
published_at, indexed datetime top_image 5.3.2 Phase 2 Enriched Features

The table stores:

is_clean word_count reading_time_mins keyword_density tags as JSONB
sentiment_score sentiment_label_vader 5.3.3 Named Entity Recognition

The schema stores entity lists as JSONB:

entities_persons entities_organizations entities_locations 5.3.4 Source
Metrics and Semantic Clustering

Additional relational and semantic fields include:

category_id / source_id as indexed integer foreign keys for future
Categories and Sources tables source_region source_tier sub_category
story_id, the semantic cluster ID generated from cosine similarity on
384-dimensional embeddings to avoid redundant recommendations 5.4
Full-Text Search Configuration

The schema includes a PostgreSQL TSVECTOR column named search_vector. An
Alembic raw SQL trigger, article_search_vector_update, automatically
populates this vector on INSERT or UPDATE by concatenating weighted
title and description fields. A GIN index is used on search_vector for
high-performance text queries.

5.5 Local Development Fallback with SQLite

For offline development and local analysis, the system maintains an
SQLite implementation that matches the news_cleaned.db outputs from
Phase 2. Differences from production include:

SQLite does not support native JSONB, so Python lists must be serialized
with json.dumps() TSVECTOR and GIN indexing are not available Execution
uses the native sqlite3 library 6. Day 5 --- NLP Processing Pipeline 6.1
Overview

The Day 5 pipeline converts structurally clean news into semantically
rich, machine-readable data. It extracts meaning, tone, and contextual
weight from each article so that the later recommendation engine can
match stories by conceptual overlap, emotional tone, and time relevance.

6.2 Pipeline Architecture and Execution Flow

This pipeline runs in memory on Google Colab, takes a flat CSV input,
processes the text through four NLP and mathematical modules, and
outputs an enriched CSV.

6.3 Step 1: Data Ingestion and Setup

The first step installs the required libraries spacy and textblob,
downloads the en_core_web_sm model, loads news_cleaned.csv, and merges
the title and description into a temporary full_text column to maximize
NLP context.

6.4 Step 2: Semantic Keyword Extraction with spaCy

This is the conceptual extraction engine of the pipeline. It uses spaCy
to extract:

Named entities such as people, organizations, geopolitical entities, and
events Noun chunks such as "artificial intelligence" and "global supply
chain"

The system filters meaningless pronouns and determiners so that the
resulting output is a clean array of unique lowercase keywords for each
article.

6.5 Step 3: Sentiment Analysis with TextBlob

The full text is passed through TextBlob to calculate sentiment
polarity:

-1.0 represents extremely negative 1.0 represents extremely positive

The system labels sentiment using these thresholds:

\> 0.05 → positive \< -0.05 → negative between -0.05 and 0.05 → neutral
6.6 Step 4: Auto-Categorization with Rule-Based Mapping

The extracted nlp_keywords are compared against a predefined
CATEGORY_MAPPING dictionary covering categories such as Technology,
Business, Politics, Sports, and Health. The category with the highest
keyword overlap is selected. If no matching keywords are found, the
article is assigned to general.

6.7 Step 5: Exponential Freshness Decay

This module calculates the age of an article in days from the current
UTC date and applies the formula:

e\^(-0.1 \* days_old)

A newly published article receives a score near 1.0, while the score
drops sharply over time and then tapers toward 0.0. This ensures
breaking news ranks above older content in the recommendation stage.

6.8 Step 6: Data Serialization and Export

Because CSV cannot natively store Python arrays, the nlp_keywords array
is converted into a stringified JSON format called nlp_keywords_json.
Temporary columns are dropped, memory is cleaned up, and the final
news_nlp_enriched.csv is automatically downloaded.

6.9 Input and Output Specifications Input

The expected input is news_cleaned.csv, with required columns:

title description publish_date Output

The generated file is news_nlp_enriched.csv, with appended columns:

nlp_keywords_json tb_sentiment_score tb_sentiment_label auto_category
freshness_decay_score 6.10 Why This Architecture Matters

This feature set is essential for Phase 3 recommendation logic:

auto_category enables instant filtering when a user selects a topic tab
nlp_keywords_json supports content-based matching against user reading
history tb_sentiment_score helps detect and balance overly negative news
exposure freshness_decay_score acts as a multiplier so newer stories
rank above older ones when relevance is otherwise similar 7. Day 6 ---
Recommendation Data Preparation 7.1 Overview

The Day 6 pipeline is the bridge between data science and software
engineering. It takes the enriched dataset from Day 5, which already
contains sentiment, categories, and decay metrics, and converts it into
structured, precomputed recommendation tables. By calculating semantic
similarity and trending order in Google Colab in advance, the
architecture allows downstream frontend or API layers to serve
recommendations with near-zero latency.

7.2 Pipeline Architecture and Execution Flow

The script processes the enriched data fully in memory using:

pandas scikit-learn IPython.display for visual verification 7.3 Step 1:
Data Ingestion and ID Generation

The pipeline ingests news_nlp_enriched.csv and ensures every article has
a unique relational article_id such as art_0042. This is required to
support relational features like "Related Article" recommendations
later.

7.4 Step 2: Trending Engine

This module determines what belongs on the application's front page.

Simulated Metrics

Because live production traffic data is not available, the system
generates synthetic view_count values to simulate user behavior.

Trending Score Formula

The trending score is calculated as:

log(view_count) \* freshness_decay_score

The use of logarithmic scaling ensures that one old article with massive
view counts does not permanently dominate newer articles with fewer
initial views. The curve is flattened so both popularity and freshness
remain balanced. The final result is normalized to a 0.00 to 10.00 scale
for UI rendering and sorting.

7.5 Step 3: Content Similarity Engine

This is the machine learning core of the "Read More" or "Similar
Articles" widget.

Vectorization

The pipeline combines title and description into a corpus and applies
TfidfVectorizer with:

Maximum 5000 features English stopword filtering Similarity Matrix

It computes cosine_similarity across all article vectors to measure how
close each article is to every other article in the dataset.

Extraction

For each article, the pipeline sorts the similarity matrix and keeps the
top 5 closest matches. These matches are stored as lightweight JSON
arrays with similarity scores.

7.6 Step 4: Category Clustering

This module builds topic-specific navigation feeds.

The dataset is grouped by auto_category Articles are ranked inside each
category Ranking is based on the newly computed trending_score 7.7
Generated Data Tables

Instead of relying on one huge table, the pipeline outputs three
targeted DataFrames.

Table 1: df_trending

This is the homepage feed table and includes:

article_id title auto_category view_count freshness_decay_score
trending_score

It is sorted by descending trending_score.

Table 2: df_similar

This is the relationship graph used when a user opens an article and
needs recommendations at the bottom of the page.

Schema: article_id, similar_articles_json JSON structure: exactly 5
mapped relationships per article, such as \[{\"similar_article_id\":
\"art_X\", \"similarity_score\": 0.85}, \...\]

Table 3: df_category_rankings

This is the topic-feed table used when a user filters by category.

Schema: article_id title auto_category category_rank trending_score

It is grouped by category and sorted in ascending order of
category_rank.

7.8 Strategic Importance

This architecture avoids expensive runtime recomputation. If TF-IDF
similarity were calculated on every page refresh over thousands of
articles, the server would either crash or experience severe latency.
The main achievement is precomputation, which gives the application O(1)
read latency because the expensive similarity and ranking work is
already finished in Colab before the web app serves the data.

8\. Unified Data Flow Across All Stages

The complete lifecycle of the news data is:

RSS feeds are collected and scraped Raw content is cleaned, validated,
and enriched Persistent storage is designed for PostgreSQL and SQLite
NLP features are generated for semantic understanding Recommendation
tables are precomputed for instant serving

This means the system evolves from raw external news sources into clean
structured records, then into semantically rich records, and finally
into ready-to-serve recommendation datasets.

9\. Final Consolidated Output Structure

At the end of the full pipeline, the system produces:

Raw aggregated news datasets Cleaned and feature-engineered datasets
NLP-enriched datasets PostgreSQL-ready schema with JSONB and TSVECTOR
SQLite fallback storage Semantic embeddings Recommendation tables for
trending, similar content, and category feeds 10. Conclusion

This project forms a complete production-oriented news intelligence
stack. It covers acquisition, cleaning, enrichment, semantic analysis,
storage design, and recommendation preparation in a disciplined
pipeline. The design choices---such as offline NLP processing, semantic
clustering, structured storage, and precomputed recommendation
tables---ensure the system is scalable, maintainable, and fast enough
for real-time user experiences.
