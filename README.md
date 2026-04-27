# Autonomous News Processing & Recommendation Engine

A modular Python pipeline that autonomously scrapes, cleans, processes, and recommends news articles. Originally developed as a Google Colab notebook, this project has been ported into a production-ready local Python architecture.

## Project Architecture

The pipeline is split into distinct modules, orchestrated by `main.py`:

* **`scraper.py`**: Fetches raw data from RSS feeds and NewsAPI.
* **`cleaner.py`**: Standardizes text and removes unwanted characters/stopwords.
* **`nlp_pipeline.py`**: Enriches data using spaCy (NER) and TextBlob (Sentiment Analysis).
* **`recommender.py`**: Calculates TF-IDF Cosine Similarity and trending/freshness scores.
* **`database.py`**: Manages the SQLite database schema and connections using SQLAlchemy.
* **`config.py`**: Handles environment variables securely using `python-dotenv`.
* **`main.py`**: The integrator that runs the pipeline and schedules automated executions.

## Local Setup

### 1. Requirements

Ensure you have Python 3.8+ installed.

### 2. Create a Virtual Environment

Open your terminal in the project directory and run:

```bash
python -m venv venv
```

Activate the virtual environment:
* **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
* **Mac/Linux:** `source venv/bin/activate`

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Download the necessary spaCy English language model:

```bash
python -m spacy download en_core_web_sm
```

### 4. Configuration

1. Copy the `.env.example` file to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your actual `NEWS_API_KEY` and database configurations.

## Usage

To initialize the database and run the pipeline manually:

```bash
python main.py
```

`main.py` includes a `verify_output()` function that will use `pandas` to print out the top 5 trending, similar, and category-ranked articles directly to your terminal.

## Automated Scheduling

To run the pipeline continuously in the background (e.g., every 6 hours), uncomment the `APScheduler` code blocks at the bottom of `main.py`.
