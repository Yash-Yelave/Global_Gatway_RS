Install libraries


```python
!pip install pandas numpy scikit-learn nltk textblob spacy rapidfuzz langdetect python-dateutil sentence-transformers -q
!python -m spacy download en_core_web_sm -q
```

    [?25l     [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m0.0/981.5 kB[0m [31m?[0m eta [36m-:--:--[0m[2K     [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m981.5/981.5 kB[0m [31m35.4 MB/s[0m eta [36m0:00:00[0m
    [?25h  Preparing metadata (setup.py) ... [?25l[?25hdone
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m3.1/3.1 MB[0m [31m79.7 MB/s[0m eta [36m0:00:00[0m
    [?25h  Building wheel for langdetect (setup.py) ... [?25l[?25hdone
    [2K     [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m12.8/12.8 MB[0m [31m72.0 MB/s[0m eta [36m0:00:00[0m
    [?25h[38;5;2m✔ Download and installation successful[0m
    You can now load the package via spacy.load('en_core_web_sm')
    [38;5;3m⚠ Restart to reload dependencies[0m
    If you are in a Jupyter or Colab notebook, you may need to restart Python in
    order to load all the package's dependencies. You can do this by selecting the
    'Restart kernel' or 'Restart runtime' option.
    

NLTK downloads


```python
import nltk
nltk.download("vader_lexicon", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("averaged_perceptron_tagger", quiet=True)
print("✓ NLTK data downloaded")
```

    ✓ NLTK data downloaded
    

Imports


```python
import re
import json
import hashlib
import warnings
import numpy as np
import pandas as pd
import sqlite3

from datetime        import datetime
from dateutil        import parser as dateparser
from langdetect      import detect, LangDetectException
from rapidfuzz       import fuzz
from textblob        import TextBlob
from nltk.sentiment  import SentimentIntensityAnalyzer
from nltk.corpus     import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise        import cosine_similarity
from sentence_transformers           import SentenceTransformer
import spacy

warnings.filterwarnings("ignore")

# Load models once
print("Loading models...")
nlp       = spacy.load("en_core_web_sm")
sia       = SentimentIntensityAnalyzer()
embedder  = SentenceTransformer("all-MiniLM-L6-v2")
STOPWORDS = set(stopwords.words("english"))
print("✓ spaCy loaded (en_core_web_sm)")
print("✓ VADER sentiment analyser loaded")
print("✓ SentenceTransformer loaded (all-MiniLM-L6-v2)")
```

    Loading models...
    


    modules.json:   0%|          | 0.00/349 [00:00<?, ?B/s]



    config_sentence_transformers.json:   0%|          | 0.00/116 [00:00<?, ?B/s]



    README.md: 0.00B [00:00, ?B/s]


    Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
    WARNING:huggingface_hub.utils._http:Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
    


    sentence_bert_config.json:   0%|          | 0.00/53.0 [00:00<?, ?B/s]



    config.json:   0%|          | 0.00/612 [00:00<?, ?B/s]



    model.safetensors:   0%|          | 0.00/90.9M [00:00<?, ?B/s]



    Loading weights:   0%|          | 0/103 [00:00<?, ?it/s]


    BertModel LOAD REPORT from: sentence-transformers/all-MiniLM-L6-v2
    Key                     | Status     |  | 
    ------------------------+------------+--+-
    embeddings.position_ids | UNEXPECTED |  | 
    
    Notes:
    - UNEXPECTED	:can be ignored when loading from different task/architecture; not ok if you expect identical arch.
    


    tokenizer_config.json:   0%|          | 0.00/350 [00:00<?, ?B/s]



    vocab.txt: 0.00B [00:00, ?B/s]



    tokenizer.json: 0.00B [00:00, ?B/s]



    special_tokens_map.json:   0%|          | 0.00/112 [00:00<?, ?B/s]



    config.json:   0%|          | 0.00/190 [00:00<?, ?B/s]


    ✓ spaCy loaded (en_core_web_sm)
    ✓ VADER sentiment analyser loaded
    ✓ SentenceTransformer loaded (all-MiniLM-L6-v2)
    

Load CSV


```python
from google.colab import files

print("Please upload your news_dataset.csv from Phase 1...\n")
uploaded = files.upload()

csv_filename = list(uploaded.keys())[0]
df_raw       = pd.read_csv(csv_filename)

print(f"\n✓ File loaded : {csv_filename}")
print(f"  Rows        : {len(df_raw)}")
print(f"  Columns     : {list(df_raw.columns)}")
print(f"\nSample row:")
print(df_raw.iloc[0].to_string())
```

    Please upload your news_dataset.csv from Phase 1...
    
    



     <input type="file" id="files-a330aeb3-4487-42c0-abad-094f66ac171b" name="files[]" multiple disabled
        style="border:none" />
     <output id="result-a330aeb3-4487-42c0-abad-094f66ac171b">
      Upload widget is only available when the cell has been executed in the
      current browser session. Please rerun this cell to enable.
      </output>
      <script>// Copyright 2017 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Helpers for google.colab Python module.
 */
(function(scope) {
function span(text, styleAttributes = {}) {
  const element = document.createElement('span');
  element.textContent = text;
  for (const key of Object.keys(styleAttributes)) {
    element.style[key] = styleAttributes[key];
  }
  return element;
}

// Max number of bytes which will be uploaded at a time.
const MAX_PAYLOAD_SIZE = 100 * 1024;

function _uploadFiles(inputId, outputId) {
  const steps = uploadFilesStep(inputId, outputId);
  const outputElement = document.getElementById(outputId);
  // Cache steps on the outputElement to make it available for the next call
  // to uploadFilesContinue from Python.
  outputElement.steps = steps;

  return _uploadFilesContinue(outputId);
}

// This is roughly an async generator (not supported in the browser yet),
// where there are multiple asynchronous steps and the Python side is going
// to poll for completion of each step.
// This uses a Promise to block the python side on completion of each step,
// then passes the result of the previous step as the input to the next step.
function _uploadFilesContinue(outputId) {
  const outputElement = document.getElementById(outputId);
  const steps = outputElement.steps;

  const next = steps.next(outputElement.lastPromiseValue);
  return Promise.resolve(next.value.promise).then((value) => {
    // Cache the last promise value to make it available to the next
    // step of the generator.
    outputElement.lastPromiseValue = value;
    return next.value.response;
  });
}

/**
 * Generator function which is called between each async step of the upload
 * process.
 * @param {string} inputId Element ID of the input file picker element.
 * @param {string} outputId Element ID of the output display.
 * @return {!Iterable<!Object>} Iterable of next steps.
 */
function* uploadFilesStep(inputId, outputId) {
  const inputElement = document.getElementById(inputId);
  inputElement.disabled = false;

  const outputElement = document.getElementById(outputId);
  outputElement.innerHTML = '';

  const pickedPromise = new Promise((resolve) => {
    inputElement.addEventListener('change', (e) => {
      resolve(e.target.files);
    });
  });

  const cancel = document.createElement('button');
  inputElement.parentElement.appendChild(cancel);
  cancel.textContent = 'Cancel upload';
  const cancelPromise = new Promise((resolve) => {
    cancel.onclick = () => {
      resolve(null);
    };
  });

  // Wait for the user to pick the files.
  const files = yield {
    promise: Promise.race([pickedPromise, cancelPromise]),
    response: {
      action: 'starting',
    }
  };

  cancel.remove();

  // Disable the input element since further picks are not allowed.
  inputElement.disabled = true;

  if (!files) {
    return {
      response: {
        action: 'complete',
      }
    };
  }

  for (const file of files) {
    const li = document.createElement('li');
    li.append(span(file.name, {fontWeight: 'bold'}));
    li.append(span(
        `(${file.type || 'n/a'}) - ${file.size} bytes, ` +
        `last modified: ${
            file.lastModifiedDate ? file.lastModifiedDate.toLocaleDateString() :
                                    'n/a'} - `));
    const percent = span('0% done');
    li.appendChild(percent);

    outputElement.appendChild(li);

    const fileDataPromise = new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        resolve(e.target.result);
      };
      reader.readAsArrayBuffer(file);
    });
    // Wait for the data to be ready.
    let fileData = yield {
      promise: fileDataPromise,
      response: {
        action: 'continue',
      }
    };

    // Use a chunked sending to avoid message size limits. See b/62115660.
    let position = 0;
    do {
      const length = Math.min(fileData.byteLength - position, MAX_PAYLOAD_SIZE);
      const chunk = new Uint8Array(fileData, position, length);
      position += length;

      const base64 = btoa(String.fromCharCode.apply(null, chunk));
      yield {
        response: {
          action: 'append',
          file: file.name,
          data: base64,
        },
      };

      let percentDone = fileData.byteLength === 0 ?
          100 :
          Math.round((position / fileData.byteLength) * 100);
      percent.textContent = `${percentDone}% done`;

    } while (position < fileData.byteLength);
  }

  // All done.
  yield {
    response: {
      action: 'complete',
    }
  };
}

scope.google = scope.google || {};
scope.google.colab = scope.google.colab || {};
scope.google.colab._files = {
  _uploadFiles,
  _uploadFilesContinue,
};
})(self);
</script> 


    Saving news_dataset (1).csv to news_dataset (1).csv
    
    ✓ File loaded : news_dataset (1).csv
      Rows        : 252
      Columns     : ['article_id', 'url', 'source', 'title', 'description', 'author', 'tags', 'category', 'sentiment', 'publish_date', 'language', 'top_image', 'scraped_at']
    
    Sample row:
    article_id                                           9b8c748a78a0
    url             https://www.aljazeera.com/news/2026/4/21/iran-...
    source                                         Al Jazeera English
    title           Iran-US war: Four scenarios for what’s next as...
    description     The US and Iran are at an impasse in their tal...
    author                                             Yashraj Sharma
    tags                  ['iran', 'us', 'war', 'talks', 'ceasefire']
    category                                                 politics
    sentiment                                                 neutral
    publish_date                                  2026-04-21 00:00:00
    language                                                       en
    top_image       https://www.aljazeera.com/wp-content/uploads/2...
    scraped_at                             2026-04-21T13:01:51.274520
    

Stage 1 : Basic cleaning


```python
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — BASIC CLEANING
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STAGE 1 — BASIC CLEANING")
print("=" * 60)

df = df_raw.copy()
report = {}

# ── 1.1 Drop exact URL duplicates ─────────────────────────────────────────
before = len(df)
df     = df.drop_duplicates(subset=["url"], keep="first")
report["1.1 Exact URL duplicates removed"] = before - len(df)
print(f"\n[1.1] Exact URL duplicates removed : {before - len(df)}")

# ── 1.2 Drop rows with missing title or description ───────────────────────
before = len(df)
df     = df.dropna(subset=["title", "description"])
df     = df[df["title"].str.strip().ne("") & df["description"].str.strip().ne("")]
report["1.2 Missing title/description dropped"] = before - len(df)
print(f"[1.2] Missing title/description dropped : {before - len(df)}")

# ── 1.3 Drop rows where title or description is too short ─────────────────
before  = len(df)
df      = df[df["title"].str.split().str.len().ge(3)]
df      = df[df["description"].str.split().str.len().ge(10)]
report["1.3 Too-short title/description dropped"] = before - len(df)
print(f"[1.3] Too-short rows dropped            : {before - len(df)}")

# ── 1.4 Strip HTML tags from all text columns ─────────────────────────────
def strip_html(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return re.sub(r"<[^>]+>", " ", text).strip()

for col in ["title", "description", "author"]:
    if col in df.columns:
        df[col] = df[col].apply(strip_html)
print(f"[1.4] HTML tags stripped from title, description, author")

# ── 1.5 Normalize whitespace & special characters ─────────────────────────
def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"\s+",         " ",  text)   # collapse whitespace
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # remove non-ASCII
    text = re.sub(r"http\S+",     "",   text)   # remove URLs
    return text.strip()

df["title"]       = df["title"].apply(clean_text)
df["description"] = df["description"].apply(clean_text)
print(f"[1.5] Whitespace & special characters normalized")

# ── 1.6 Normalize tags column (stored as JSON string from Phase 1) ─────────
def parse_tags(val) -> list:
    if isinstance(val, list):
        return [t.lower().strip() for t in val if t.strip()]
    try:
        parsed = json.loads(val)
        return [t.lower().strip() for t in parsed if t.strip()]
    except Exception:
        return []

df["tags"] = df["tags"].apply(parse_tags)
print(f"[1.6] Tags parsed and normalized to lists")

# ── 1.7 Normalize category and sentiment ──────────────────────────────────
VALID_CATEGORIES = ["technology", "politics", "sports", "business",
                    "health", "science", "entertainment", "finance",
                    "travel", "culture", "environment", "general"]
VALID_SENTIMENTS = ["positive", "neutral", "negative"]

df["category"]  = df["category"].str.lower().str.strip()
df["sentiment"] = df["sentiment"].str.lower().str.strip()
df["category"]  = df["category"].apply(lambda x: x if x in VALID_CATEGORIES else "general")
df["sentiment"] = df["sentiment"].apply(lambda x: x if x in VALID_SENTIMENTS else "neutral")
print(f"[1.7] Category and sentiment values normalized")

# ── 1.8 Normalize publish_date to datetime ────────────────────────────────
def parse_date(val) -> str | None:
    if not val or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        return dateparser.parse(str(val)).strftime("%Y-%m-%d")
    except Exception:
        return None

df["publish_date"] = df["publish_date"].apply(parse_date)
valid_dates        = df["publish_date"].notna().sum()
print(f"[1.8] Dates normalized — {valid_dates}/{len(df)} articles have valid dates")

# ── 1.9 Fill missing author ────────────────────────────────────────────────
df["author"] = df["author"].fillna("Unknown").replace("", "Unknown")
print(f"[1.9] Missing authors filled with 'Unknown'")

# ── Summary ────────────────────────────────────────────────────────────────
print(f"\n{'─'*60}")
print(f"Stage 1 complete.")
print(f"  Rows before : {len(df_raw)}")
print(f"  Rows after  : {len(df)}")
print(f"  Rows removed: {len(df_raw) - len(df)}")
print(f"{'─'*60}")
```

    ============================================================
    STAGE 1 — BASIC CLEANING
    ============================================================
    
    [1.1] Exact URL duplicates removed : 0
    [1.2] Missing title/description dropped : 0
    [1.3] Too-short rows dropped            : 2
    [1.4] HTML tags stripped from title, description, author
    [1.5] Whitespace & special characters normalized
    [1.6] Tags parsed and normalized to lists
    [1.7] Category and sentiment values normalized
    [1.8] Dates normalized — 217/250 articles have valid dates
    [1.9] Missing authors filled with 'Unknown'
    
    ────────────────────────────────────────────────────────────
    Stage 1 complete.
      Rows before : 252
      Rows after  : 250
      Rows removed: 2
    ────────────────────────────────────────────────────────────
    

Stage 2 : Text quality filtering


```python
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — TEXT QUALITY FILTERING
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STAGE 2 — TEXT QUALITY FILTERING")
print("=" * 60)

df["is_clean"] = True   # start with everyone clean, flag bad rows

BOILERPLATE_PHRASES = [
    "subscribe to read", "sign in to read", "subscribe now",
    "cookie policy", "privacy policy", "terms of service",
    "all rights reserved", "javascript is required",
    "enable javascript", "ad blocker", "please disable",
    "create an account", "log in to continue",
    "this content is for subscribers", "paywall",
    "continue reading", "read the full article",
    "newsletter signup", "follow us on",
]

# ── 2.1 Flag articles where description == title ──────────────────────────
mask = df["title"].str.lower().str.strip() == df["description"].str.lower().str.strip()
df.loc[mask, "is_clean"] = False
print(f"\n[2.1] Description == title (flagged) : {mask.sum()}")

# ── 2.2 Flag articles with description under 10 words ────────────────────
mask = df["description"].str.split().str.len().lt(10)
df.loc[mask, "is_clean"] = False
print(f"[2.2] Description under 10 words (flagged) : {mask.sum()}")

# ── 2.3 Detect & flag boilerplate-dominated descriptions ─────────────────
def is_boilerplate(text: str) -> bool:
    if not isinstance(text, str):
        return True
    text_lower = text.lower()
    hits       = sum(1 for phrase in BOILERPLATE_PHRASES if phrase in text_lower)
    return hits >= 2

mask = df["description"].apply(is_boilerplate)
df.loc[mask, "is_clean"] = False
print(f"[2.3] Boilerplate-dominated (flagged)       : {mask.sum()}")

# ── 2.4 Detect repeated sentences in description ──────────────────────────
def has_high_repetition(text: str, threshold: float = 0.5) -> bool:
    if not isinstance(text, str):
        return False
    sentences  = [s.strip() for s in re.split(r"[.!?]", text) if s.strip()]
    if len(sentences) <= 1:
        return False
    unique     = set(sentences)
    repetition = 1 - len(unique) / len(sentences)
    return repetition >= threshold

mask = df["description"].apply(has_high_repetition)
df.loc[mask, "is_clean"] = False
print(f"[2.4] High sentence repetition (flagged)    : {mask.sum()}")

# ── 2.5 Language detection ────────────────────────────────────────────────
def detect_language(text: str) -> str:
    try:
        return detect(str(text))
    except LangDetectException:
        return "unknown"

print(f"[2.5] Running language detection on all articles...")
df["detected_language"] = df["description"].apply(detect_language)

lang_counts = df["detected_language"].value_counts()
print(f"      Language distribution:")
for lang, count in lang_counts.items():
    print(f"        {lang:10s} : {count}")

# ── 2.6 Flag language mismatch (source says English but detected otherwise)
english_sources_mask = ~df["source"].str.contains(
    "Arabic|Al Khaleej|Al Bayan|Xinhua|CGTN|China Daily",
    case=False, na=False
)
lang_mismatch = english_sources_mask & ~df["detected_language"].isin(["en", "unknown"])
df.loc[lang_mismatch, "is_clean"] = False
print(f"[2.6] Language mismatch on English sources (flagged) : {lang_mismatch.sum()}")

# ── 2.7 Summary of clean vs flagged ──────────────────────────────────────
total   = len(df)
clean   = df["is_clean"].sum()
flagged = total - clean

print(f"\n{'─'*60}")
print(f"Stage 2 complete.")
print(f"  Total articles : {total}")
print(f"  Clean articles : {clean}")
print(f"  Flagged        : {flagged}  (kept in dataset with is_clean=False)")
print(f"{'─'*60}")

# Work only on clean articles for feature engineering but keep full df
df_clean = df[df["is_clean"]].copy().reset_index(drop=True)
print(f"\nWorking dataset for feature engineering: {len(df_clean)} articles")
```

    ============================================================
    STAGE 2 — TEXT QUALITY FILTERING
    ============================================================
    
    [2.1] Description == title (flagged) : 0
    [2.2] Description under 10 words (flagged) : 0
    [2.3] Boilerplate-dominated (flagged)       : 0
    [2.4] High sentence repetition (flagged)    : 0
    [2.5] Running language detection on all articles...
          Language distribution:
            en         : 250
    [2.6] Language mismatch on English sources (flagged) : 0
    
    ────────────────────────────────────────────────────────────
    Stage 2 complete.
      Total articles : 250
      Clean articles : 250
      Flagged        : 0  (kept in dataset with is_clean=False)
    ────────────────────────────────────────────────────────────
    
    Working dataset for feature engineering: 250 articles
    

Stage 3a : Basic text features


```python
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3a — BASIC TEXT FEATURES
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STAGE 3a — BASIC TEXT FEATURES")
print("=" * 60)

# ── 3.1 Word count ─────────────────────────────────────────────────────────
df_clean["word_count"] = df_clean["description"].str.split().str.len()
print(f"\n[3.1] word_count added")
print(f"      Min: {df_clean['word_count'].min()}  "
      f"Max: {df_clean['word_count'].max()}  "
      f"Mean: {df_clean['word_count'].mean():.1f}")

# ── 3.2 Reading time (200 words per minute average) ────────────────────────
df_clean["reading_time_mins"] = (df_clean["word_count"] / 200).round(1).clip(lower=0.1)
print(f"[3.2] reading_time_mins added")
print(f"      Range: {df_clean['reading_time_mins'].min()} – "
      f"{df_clean['reading_time_mins'].max()} mins")

# ── 3.3 Keyword density (how often tags appear in description) ─────────────
def keyword_density(row) -> float:
    text = str(row["description"]).lower()
    tags = row["tags"] if isinstance(row["tags"], list) else []
    if not tags or not text:
        return 0.0
    words      = text.split()
    if not words:
        return 0.0
    tag_words  = " ".join(tags).split()
    hits       = sum(1 for w in words if w in tag_words)
    return round(hits / len(words), 4)

df_clean["keyword_density"] = df_clean.apply(keyword_density, axis=1)
print(f"[3.3] keyword_density added")
print(f"      Mean: {df_clean['keyword_density'].mean():.4f}  "
      f"Max: {df_clean['keyword_density'].max():.4f}")

# ── 3.4 Title word count ───────────────────────────────────────────────────
df_clean["title_word_count"] = df_clean["title"].str.split().str.len()
print(f"[3.4] title_word_count added")

# ── 3.5 Has image flag ────────────────────────────────────────────────────
df_clean["has_image"] = df_clean["top_image"].notna() & df_clean["top_image"].ne("")
print(f"[3.5] has_image added — "
      f"{df_clean['has_image'].sum()} articles have a top image")

print(f"\n{'─'*60}")
print("Stage 3a complete — 5 basic features added.")
print(f"{'─'*60}")
```

    ============================================================
    STAGE 3a — BASIC TEXT FEATURES
    ============================================================
    
    [3.1] word_count added
          Min: 11  Max: 81  Mean: 26.1
    [3.2] reading_time_mins added
          Range: 0.1 – 0.4 mins
    [3.3] keyword_density added
          Mean: 0.0000  Max: 0.0000
    [3.4] title_word_count added
    [3.5] has_image added — 244 articles have a top image
    
    ────────────────────────────────────────────────────────────
    Stage 3a complete — 5 basic features added.
    ────────────────────────────────────────────────────────────
    

Stage 3b : Sentiment scoring


```python
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3b — SENTIMENT SCORING (VADER — fully local)
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STAGE 3b — SENTIMENT SCORING (VADER)")
print("=" * 60)

def get_vader_scores(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
    return sia.polarity_scores(text)

print("\n[3.6] Running VADER on title + description for each article...")

scores = df_clean["title"].fillna("") + " " + df_clean["description"].fillna("")
scores = scores.apply(get_vader_scores)

df_clean["sentiment_score"]    = scores.apply(lambda x: round(x["compound"], 4))
df_clean["sentiment_positive"] = scores.apply(lambda x: round(x["pos"], 4))
df_clean["sentiment_negative"] = scores.apply(lambda x: round(x["neg"], 4))
df_clean["sentiment_neutral"]  = scores.apply(lambda x: round(x["neu"], 4))

# Recalculate sentiment label from compound score for consistency
def compound_to_label(score: float) -> str:
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    return "neutral"

df_clean["sentiment_label_vader"] = df_clean["sentiment_score"].apply(compound_to_label)

# Compare Groq label vs VADER label
agreement = (df_clean["sentiment"] == df_clean["sentiment_label_vader"]).sum()
print(f"[3.6] VADER scores computed")
print(f"      Compound score range : "
      f"{df_clean['sentiment_score'].min():.3f} to "
      f"{df_clean['sentiment_score'].max():.3f}")
print(f"      VADER label distribution:")
print(df_clean["sentiment_label_vader"].value_counts().to_string())
print(f"      Agreement with Groq label : "
      f"{agreement}/{len(df_clean)} ({100*agreement/len(df_clean):.1f}%)")

print(f"\n{'─'*60}")
print("Stage 3b complete — 5 sentiment columns added.")
print(f"{'─'*60}")
```

    ============================================================
    STAGE 3b — SENTIMENT SCORING (VADER)
    ============================================================
    
    [3.6] Running VADER on title + description for each article...
    [3.6] VADER scores computed
          Compound score range : -0.979 to 0.971
          VADER label distribution:
    sentiment_label_vader
    positive    129
    negative     85
    neutral      36
          Agreement with Groq label : 88/250 (35.2%)
    
    ────────────────────────────────────────────────────────────
    Stage 3b complete — 5 sentiment columns added.
    ────────────────────────────────────────────────────────────
    

Stage 3c : Named entity recognition (spaCy)


```python
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3c — NAMED ENTITY RECOGNITION (spaCy — fully local)
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STAGE 3c — NAMED ENTITY RECOGNITION (spaCy)")
print("=" * 60)
print("\n[3.7] Extracting named entities from title + description...")
print("      (This may take 1-3 minutes depending on dataset size)\n")

def extract_entities(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        return {"persons": [], "organizations": [], "locations": [], "misc": []}
    doc     = nlp(text[:1000])   # cap at 1000 chars for speed
    persons = []
    orgs    = []
    locs    = []
    misc    = []
    for ent in doc.ents:
        val = ent.text.strip()
        if not val:
            continue
        if ent.label_ in ("PERSON",):
            persons.append(val)
        elif ent.label_ in ("ORG", "NORP"):
            orgs.append(val)
        elif ent.label_ in ("GPE", "LOC", "FAC"):
            locs.append(val)
        else:
            misc.append(val)
    return {
        "persons"      : list(set(persons)),
        "organizations": list(set(orgs)),
        "locations"    : list(set(locs)),
        "misc"         : list(set(misc)),
    }

combined_text = (
    df_clean["title"].fillna("") + ". " + df_clean["description"].fillna("")
)

entities = combined_text.apply(extract_entities)

df_clean["entities_persons"]       = entities.apply(lambda x: x["persons"])
df_clean["entities_organizations"] = entities.apply(lambda x: x["organizations"])
df_clean["entities_locations"]     = entities.apply(lambda x: x["locations"])

# Count of entities per article
df_clean["entity_count"] = entities.apply(
    lambda x: len(x["persons"]) + len(x["organizations"]) + len(x["locations"])
)

# Sample output
print(f"[3.7] Named entities extracted")
print(f"      Articles with at least 1 entity : "
      f"{(df_clean['entity_count'] > 0).sum()}/{len(df_clean)}")
print(f"\n      Sample entities from first 3 articles:")
for i in range(min(3, len(df_clean))):
    row = df_clean.iloc[i]
    print(f"\n      [{i+1}] {row['title'][:60]}")
    print(f"           Persons : {row['entities_persons'][:3]}")
    print(f"           Orgs    : {row['entities_organizations'][:3]}")
    print(f"           Locs    : {row['entities_locations'][:3]}")

print(f"\n{'─'*60}")
print("Stage 3c complete — 4 entity columns added.")
print(f"{'─'*60}")
```

    ============================================================
    STAGE 3c — NAMED ENTITY RECOGNITION (spaCy)
    ============================================================
    
    [3.7] Extracting named entities from title + description...
          (This may take 1-3 minutes depending on dataset size)
    
    [3.7] Named entities extracted
          Articles with at least 1 entity : 222/250
    
          Sample entities from first 3 articles:
    
          [1] Iran-US war: Four scenarios for what s next as talks stumble
               Persons : []
               Orgs    : []
               Locs    : ['US', 'Iran']
    
          [2] Are we heading into a world divided by AI tribes?
               Persons : []
               Orgs    : []
               Locs    : ['AI']
    
          [3] What was the Iran nuclear deal Trump dumped in search of  be
               Persons : ['Donald Trump']
               Orgs    : ['Trump']
               Locs    : ['US', 'Iran']
    
    ────────────────────────────────────────────────────────────
    Stage 3c complete — 4 entity columns added.
    ────────────────────────────────────────────────────────────
    

Stage 3d : Time-based features


```python
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3d — TIME-BASED FEATURES
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STAGE 3d — TIME-BASED FEATURES")
print("=" * 60)

today = datetime.utcnow().date()

def safe_parse_date(val):
    if not val or val != val:
        return None
    try:
        return dateparser.parse(str(val)).date()
    except Exception:
        return None

parsed_dates = df_clean["publish_date"].apply(safe_parse_date)

# 3.8 Article age in days
df_clean["article_age_days"] = parsed_dates.apply(
    lambda d: (today - d).days if d else None
)

# 3.9 Day of week (0=Monday, 6=Sunday)
df_clean["publish_day_of_week"] = parsed_dates.apply(
    lambda d: d.strftime("%A") if d else None
)

# 3.10 Hour of publish (not always available but try)
df_clean["publish_hour"] = df_clean["publish_date"].apply(
    lambda v: dateparser.parse(str(v)).hour
    if v and v == v else None
)

# 3.11 Is recent (published within last 48 hours)
df_clean["is_recent"] = df_clean["article_age_days"].apply(
    lambda x: True if (x is not None and x <= 2) else False
)

# 3.12 Freshness score (1.0 = today, decays toward 0)
def freshness_score(age_days) -> float:
    if age_days is None:
        return 0.5
    return round(max(0.0, 1.0 - (age_days / 30)), 4)

df_clean["freshness_score"] = df_clean["article_age_days"].apply(freshness_score)

print(f"\n[3.8]  article_age_days added")
print(f"       Range: {df_clean['article_age_days'].min()} – "
      f"{df_clean['article_age_days'].max()} days")

print(f"[3.9]  publish_day_of_week added")
print(f"       Distribution:")
day_dist = df_clean["publish_day_of_week"].value_counts()
for day, count in day_dist.items():
    print(f"         {day:10s} : {count}")

print(f"[3.10] publish_hour added")
print(f"[3.11] is_recent added — "
      f"{df_clean['is_recent'].sum()} articles published in last 48h")
print(f"[3.12] freshness_score added — "
      f"Mean: {df_clean['freshness_score'].mean():.3f}")

print(f"\n{'─'*60}")
print("Stage 3d complete — 5 time features added.")
print(f"{'─'*60}")
```

    ============================================================
    STAGE 3d — TIME-BASED FEATURES
    ============================================================
    
    [3.8]  article_age_days added
           Range: -72.0 – 3301.0 days
    [3.9]  publish_day_of_week added
           Distribution:
             Tuesday    : 138
             Monday     : 39
             Friday     : 12
             Sunday     : 9
             Saturday   : 7
             Wednesday  : 6
             Thursday   : 6
    [3.10] publish_hour added
    [3.11] is_recent added — 170 articles published in last 48h
    [3.12] freshness_score added — Mean: 0.739
    
    ────────────────────────────────────────────────────────────
    Stage 3d complete — 5 time features added.
    ────────────────────────────────────────────────────────────
    

Stage 3e : Source-based features



```python
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3e — SOURCE-BASED FEATURES
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STAGE 3e — SOURCE-BASED FEATURES")
print("=" * 60)

# Region mapping
UAE_SOURCES = [
    "Khaleej Times", "Gulf News", "The National UAE", "Gulf Business",
    "Emirates 24/7", "Arabian Business", "Al Arabiya English",
    "Zawya UAE", "Dubai Eye News", "Al Khaleej (Arabic)", "Al Bayan (Arabic)",
    "WAM UAE State News", "Time Out Dubai", "What's On Dubai",
    "Construction Week Online", "MEED Middle East",
]
GULF_SOURCES = [
    "Arab News", "Saudi Gazette", "Oman Observer", "Kuwait Times",
    "Bahrain News Agency", "Qatar Tribune", "Middle East Eye", "Roya News Jordan",
    "Al Jazeera English",
]
CHINA_SOURCES = [
    "China Daily", "China Daily Business", "CGTN World", "CGTN Business",
    "CGTN Science", "Xinhua Top News", "Xinhua China",
    "South China Morning Post", "SCMP Business", "SCMP Tech",
    "Hong Kong Free Press", "Caixin Global", "Sixth Tone China",
]
ASIA_SOURCES = [
    "The Diplomat Asia", "Asia Times", "Nikkei Asia", "Japan Times",
    "Korea Herald", "Times of India", "Straits Times Singapore",
]

# Credibility tiers (manually set based on editorial standards)
TIER_1 = [
    "BBC Top Stories", "BBC World", "BBC Technology", "BBC Business",
    "BBC Health", "Reuters Top News", "Reuters World", "Reuters Business",
    "Reuters Technology", "AP Top News", "AP World", "AP Business",
    "The Guardian World", "The Guardian Tech", "Financial Times World",
    "The National UAE", "South China Morning Post", "Al Jazeera English",
    "Bloomberg Technology", "Nature News", "NASA Breaking News",
    "WHO News", "Xinhua Top News", "China Daily",
]
TIER_2 = [
    "Gulf News", "Khaleej Times", "Arab News", "CGTN World",
    "TechCrunch", "The Verge", "Wired", "Ars Technica", "MIT Tech Review",
    "CNBC World", "CNBC Finance", "Forbes Business", "Forbes Tech",
    "Harvard Health", "Science Daily", "ESPN Headlines", "BBC Sport",
    "Nikkei Asia", "Straits Times Singapore",
]

def get_region(source: str) -> str:
    if source in UAE_SOURCES:
        return "UAE"
    elif source in GULF_SOURCES:
        return "Gulf"
    elif source in CHINA_SOURCES:
        return "China"
    elif source in ASIA_SOURCES:
        return "Asia"
    else:
        return "Global"

def get_tier(source: str) -> int:
    if source in TIER_1:
        return 1
    elif source in TIER_2:
        return 2
    return 3

df_clean["source_region"] = df_clean["source"].apply(get_region)
df_clean["source_tier"]   = df_clean["source"].apply(get_tier)

print(f"\n[3.13] source_region added")
print(f"       Distribution:")
region_dist = df_clean["source_region"].value_counts()
for region, count in region_dist.items():
    print(f"         {region:10s} : {count}")

print(f"\n[3.14] source_tier added")
print(f"       Distribution:")
tier_dist = df_clean["source_tier"].value_counts().sort_index()
for tier, count in tier_dist.items():
    print(f"         Tier {tier}      : {count}")

print(f"\n{'─'*60}")
print("Stage 3e complete — 2 source features added.")
print(f"{'─'*60}")
```

    ============================================================
    STAGE 3e — SOURCE-BASED FEATURES
    ============================================================
    
    [3.13] source_region added
           Distribution:
             Global     : 174
             China      : 43
             Asia       : 19
             Gulf       : 9
             UAE        : 5
    
    [3.14] source_tier added
           Distribution:
             Tier 1      : 64
             Tier 2      : 59
             Tier 3      : 127
    
    ────────────────────────────────────────────────────────────
    Stage 3e complete — 2 source features added.
    ────────────────────────────────────────────────────────────
    

Stage 3f : Sub-category (keyword rules)



```python
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3f — SUB-CATEGORY (keyword rule-based — fully local, no model needed)
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STAGE 3f — SUB-CATEGORY (keyword rules)")
print("=" * 60)

SUB_CATEGORY_RULES = {
    "technology" : {
        "AI & Machine Learning"   : ["artificial intelligence", "machine learning", "deep learning",
                                     "llm", "chatgpt", "neural network", "generative ai", "openai",
                                     "claude", "gemini", "gpt"],
        "Cybersecurity"           : ["cybersecurity", "hacker", "malware", "data breach",
                                     "ransomware", "phishing", "vulnerability", "cyber attack"],
        "Smartphones & Gadgets"   : ["iphone", "android", "smartphone", "tablet", "wearable",
                                     "apple", "samsung", "google pixel"],
        "Cloud & Software"        : ["cloud computing", "saas", "software", "aws", "azure",
                                     "google cloud", "kubernetes", "devops"],
        "Cryptocurrency"          : ["bitcoin", "ethereum", "crypto", "blockchain", "nft",
                                     "defi", "web3", "coinbase"],
    },
    "politics"   : {
        "UAE Politics"            : ["uae", "dubai", "abu dhabi", "sheikh", "emirates",
                                     "federal", "ministry", "expo"],
        "Middle East Politics"    : ["saudi", "iran", "israel", "palestine", "iraq",
                                     "jordan", "egypt", "qatar", "gcc"],
        "China Politics"          : ["xi jinping", "beijing", "chinese government", "ccp",
                                     "national people's congress", "taiwan", "hong kong"],
        "US Politics"             : ["trump", "biden", "congress", "senate", "white house",
                                     "democrat", "republican", "washington"],
        "Global Diplomacy"        : ["un", "united nations", "nato", "g7", "g20",
                                     "treaty", "sanctions", "diplomacy"],
    },
    "business"   : {
        "Startups & VC"           : ["startup", "venture capital", "funding", "series a",
                                     "unicorn", "ipo", "seed round"],
        "Real Estate"             : ["real estate", "property", "housing market", "mortgage",
                                     "construction", "rent", "dubai property"],
        "Energy & Oil"            : ["oil", "opec", "gas", "energy", "renewable",
                                     "solar", "wind power", "saudi aramco"],
        "Retail & E-commerce"     : ["amazon", "e-commerce", "retail", "online shopping",
                                     "supply chain", "consumer"],
    },
    "sports"     : {
        "Football"                : ["football", "soccer", "premier league", "fifa",
                                     "champions league", "goal", "match", "world cup"],
        "Cricket"                 : ["cricket", "ipl", "test match", "odi", "bcci"],
        "Formula 1"               : ["formula 1", "f1", "grand prix", "ferrari",
                                     "mercedes", "red bull racing"],
        "Basketball"              : ["nba", "basketball", "lebron", "curry"],
        "Tennis"                  : ["tennis", "wimbledon", "us open", "djokovic",
                                     "federer", "nadal", "serena"],
    },
    "health"     : {
        "Mental Health"           : ["mental health", "depression", "anxiety", "therapy",
                                     "psychiatry", "wellbeing", "burnout"],
        "Nutrition & Diet"        : ["nutrition", "diet", "obesity", "calories",
                                     "vitamins", "weight loss", "food"],
        "Medical Research"        : ["clinical trial", "vaccine", "drug approval", "fda",
                                     "cancer", "research", "study"],
        "Public Health"           : ["pandemic", "who", "disease", "outbreak",
                                     "epidemic", "public health", "infection"],
    },
}

def get_sub_category(row) -> str:
    category = row.get("category", "")
    text     = (str(row.get("title", "")) + " " +
                str(row.get("description", ""))).lower()

    if category not in SUB_CATEGORY_RULES:
        return "General"

    best_match = "General"
    best_count = 0

    for sub_cat, keywords in SUB_CATEGORY_RULES[category].items():
        count = sum(1 for kw in keywords if kw in text)
        if count > best_count:
            best_count = count
            best_match = sub_cat

    return best_match

df_clean["sub_category"] = df_clean.apply(get_sub_category, axis=1)

print(f"\n[3.15] sub_category added using keyword rules")
print(f"       Distribution (top 15):")
sub_dist = df_clean["sub_category"].value_counts().head(15)
for sub, count in sub_dist.items():
    print(f"         {sub:30s} : {count}")

print(f"\n{'─'*60}")
print("Stage 3f complete — sub_category added.")
print(f"{'─'*60}")
```

    ============================================================
    STAGE 3f — SUB-CATEGORY (keyword rules)
    ============================================================
    
    [3.15] sub_category added using keyword rules
           Distribution (top 15):
             General                        : 158
             Smartphones & Gadgets          : 17
             Middle East Politics           : 10
             China Politics                 : 8
             US Politics                    : 8
             Global Diplomacy               : 7
             Medical Research               : 6
             Football                       : 6
             Energy & Oil                   : 4
             Cryptocurrency                 : 4
             Public Health                  : 4
             Basketball                     : 3
             UAE Politics                   : 3
             Cloud & Software               : 2
             Cybersecurity                  : 2
    
    ────────────────────────────────────────────────────────────
    Stage 3f complete — sub_category added.
    ────────────────────────────────────────────────────────────
    

Stage 4 : TF-IDF vectors + semantic embeddings



```python
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — TF-IDF VECTORS + SENTENCE EMBEDDINGS (fully local)
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STAGE 4 — TF-IDF + SENTENCE EMBEDDINGS")
print("=" * 60)

combined_text = (
    df_clean["title"].fillna("") + " " + df_clean["description"].fillna("")
).tolist()

# ── 4.1 TF-IDF ────────────────────────────────────────────────────────────
print("\n[4.1] Building TF-IDF matrix...")
tfidf_vec    = TfidfVectorizer(
    max_features = 5000,
    stop_words   = "english",
    ngram_range  = (1, 2),
    min_df       = 1,
)
tfidf_matrix = tfidf_vec.fit_transform(combined_text)

# Store as compressed JSON string per article (top 10 terms only for storage)
feature_names = tfidf_vec.get_feature_names_out()

def top_tfidf_terms(row_vec, top_n: int = 10) -> list:
    scores = zip(feature_names, row_vec.toarray()[0])
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    return [term for term, score in sorted_scores if score > 0][:top_n]

df_clean["tfidf_top_terms"] = [
    top_tfidf_terms(tfidf_matrix[i])
    for i in range(tfidf_matrix.shape[0])
]

print(f"       TF-IDF matrix shape : {tfidf_matrix.shape}")
print(f"       Vocabulary size      : {len(feature_names)}")
print(f"       Sample top terms from article 0 : "
      f"{df_clean['tfidf_top_terms'].iloc[0]}")

# ── 4.2 Sentence embeddings ───────────────────────────────────────────────
print(f"\n[4.2] Computing sentence embeddings (all-MiniLM-L6-v2)...")
print(f"      (May take 2-5 minutes for large datasets)")

embeddings = embedder.encode(
    combined_text,
    batch_size    = 32,
    show_progress_bar = True,
    normalize_embeddings = True,
)

# Store embedding dimension info (actual vectors saved separately as .npy)
df_clean["embedding_dim"] = embeddings.shape[1]

import numpy as np
np.save("article_embeddings.npy", embeddings)
print(f"\n       Embedding matrix shape : {embeddings.shape}")
print(f"       Saved to article_embeddings.npy")
print(f"       (Load later with: embeddings = np.load('article_embeddings.npy'))")

print(f"\n{'─'*60}")
print("Stage 4 complete — TF-IDF terms and embeddings computed.")
print(f"{'─'*60}")
```

    ============================================================
    STAGE 4 — TF-IDF + SENTENCE EMBEDDINGS
    ============================================================
    
    [4.1] Building TF-IDF matrix...
           TF-IDF matrix shape : (250, 5000)
           Vocabulary size      : 5000
           Sample top terms from article 0 : ['talks', 'ceasefire', 'scenarios', 'iran', 'breakthrough ceasefire', 'ceasefire expires', 'ceasefire extended', 'ceasefire extension', 'deal talks', 'emerging talks']
    
    [4.2] Computing sentence embeddings (all-MiniLM-L6-v2)...
          (May take 2-5 minutes for large datasets)
    


    Batches:   0%|          | 0/8 [00:00<?, ?it/s]


    
           Embedding matrix shape : (250, 384)
           Saved to article_embeddings.npy
           (Load later with: embeddings = np.load('article_embeddings.npy'))
    
    ────────────────────────────────────────────────────────────
    Stage 4 complete — TF-IDF terms and embeddings computed.
    ────────────────────────────────────────────────────────────
    

Stage 5 : Deduplication & story grouping


```python
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 5 — DEDUPLICATION & STORY GROUPING
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STAGE 5 — DEDUPLICATION & STORY GROUPING")
print("=" * 60)

# ── 5.1 Fuzzy title dedup ──────────────────────────────────────────────────
print(f"\n[5.1] Running fuzzy title deduplication (threshold=85)...")
print(f"      Comparing {len(df_clean)} titles...")

titles     = df_clean["title"].tolist()
n          = len(titles)
keep_mask  = [True] * n
dup_groups = {}

for i in range(n):
    if not keep_mask[i]:
        continue
    for j in range(i + 1, n):
        if not keep_mask[j]:
            continue
        score = fuzz.ratio(titles[i].lower(), titles[j].lower())
        if score >= 85:
            keep_mask[j] = False
            if i not in dup_groups:
                dup_groups[i] = []
            dup_groups[i].append(j)

fuzzy_dupes = n - sum(keep_mask)
print(f"       Near-duplicate titles found & removed : {fuzzy_dupes}")
if dup_groups:
    sample_key = list(dup_groups.keys())[0]
    print(f"       Example duplicate pair:")
    print(f"         Original : {titles[sample_key][:70]}")
    print(f"         Duplicate: {titles[dup_groups[sample_key][0]][:70]}")

df_dedup = df_clean[keep_mask].copy().reset_index(drop=True)
embeddings_dedup = embeddings[keep_mask]

print(f"       Articles after fuzzy dedup : {len(df_dedup)}")

# ── 5.2 Semantic story grouping ────────────────────────────────────────────
print(f"\n[5.2] Running semantic story grouping (cosine similarity >= 0.88)...")

similarity_matrix = cosine_similarity(embeddings_dedup)
story_ids         = [-1] * len(df_dedup)
current_story_id  = 0

for i in range(len(df_dedup)):
    if story_ids[i] != -1:
        continue
    story_ids[i] = current_story_id
    for j in range(i + 1, len(df_dedup)):
        if story_ids[j] == -1 and similarity_matrix[i][j] >= 0.88:
            story_ids[j] = current_story_id
    current_story_id += 1

df_dedup["story_id"] = story_ids

# Stories that have more than 1 article (same event from multiple sources)
story_counts = pd.Series(story_ids).value_counts()
multi_source_stories = (story_counts > 1).sum()

print(f"       Unique story clusters        : {current_story_id}")
print(f"       Multi-source story clusters  : {multi_source_stories}")
print(f"       (Same event covered by 2+ outlets)")

if multi_source_stories > 0:
    sample_story = story_counts[story_counts > 1].index[0]
    sample_arts  = df_dedup[df_dedup["story_id"] == sample_story][["source", "title"]].head(3)
    print(f"\n       Example multi-source story (story_id={sample_story}):")
    for _, row in sample_arts.iterrows():
        print(f"         [{row['source']}] {row['title'][:60]}")

print(f"\n{'─'*60}")
print(f"Stage 5 complete. Final dataset: {len(df_dedup)} articles.")
print(f"{'─'*60}")
```

    ============================================================
    STAGE 5 — DEDUPLICATION & STORY GROUPING
    ============================================================
    
    [5.1] Running fuzzy title deduplication (threshold=85)...
          Comparing 250 titles...
           Near-duplicate titles found & removed : 0
           Articles after fuzzy dedup : 250
    
    [5.2] Running semantic story grouping (cosine similarity >= 0.88)...
           Unique story clusters        : 247
           Multi-source story clusters  : 2
           (Same event covered by 2+ outlets)
    
           Example multi-source story (story_id=87):
             [BBC Technology] john ternus named as apple chief executive to replace tim co
             [The Guardian Tech] tim cook to step down as apple chief as john ternus named re
             [Ars Technica] john ternus to replace tim cook as apple ceo
    
    ────────────────────────────────────────────────────────────
    Stage 5 complete. Final dataset: 250 articles.
    ────────────────────────────────────────────────────────────
    

Final output and full summary


```python
# ─────────────────────────────────────────────────────────────────────────────
# FINAL OUTPUT — SAVE ENRICHED DATASET
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("FINAL OUTPUT")
print("=" * 60)

# Columns to save (list columns serialized to JSON strings for CSV/SQLite)
df_final = df_dedup.copy()

list_cols = ["tags", "entities_persons", "entities_organizations",
             "entities_locations", "tfidf_top_terms"]

for col in list_cols:
    if col in df_final.columns:
        df_final[col] = df_final[col].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else x
        )

# CSV
df_final.to_csv("news_cleaned.csv", index=False)
print(f"\n✓ Saved news_cleaned.csv")

# JSON
df_dedup.to_json("news_cleaned.json", orient="records", indent=2, force_ascii=False)
print(f"✓ Saved news_cleaned.json")

# SQLite
conn = sqlite3.connect("news_cleaned.db")
df_final.to_sql("articles", conn, if_exists="replace", index=False)
conn.commit()
conn.close()
print(f"✓ Saved news_cleaned.db (table: articles)")

# Embeddings already saved as .npy in Stage 4
print(f"✓ Embeddings saved as article_embeddings.npy")

# ── Full pipeline summary ──────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"COMPLETE PIPELINE SUMMARY")
print(f"{'='*60}")
print(f"  Input articles (raw CSV)        : {len(df_raw)}")
print(f"  After Stage 1 basic cleaning    : {len(df)}")
print(f"  Clean articles (is_clean=True)  : {len(df_clean)}")
print(f"  After fuzzy dedup               : {len(df_dedup)}")
print(f"\n  New columns added               : {len(df_dedup.columns) - len(df_raw.columns)}")
print(f"  Final columns                   : {list(df_dedup.columns)}")
print(f"\n  Language distribution:")
print(df_dedup["detected_language"].value_counts().to_string())
print(f"\n  Region distribution:")
print(df_dedup["source_region"].value_counts().to_string())
print(f"\n  Category distribution:")
print(df_dedup["category"].value_counts().to_string())
print(f"\n  Unique story clusters           : {df_dedup['story_id'].nunique()}")
print(f"{'='*60}")
```

    ============================================================
    FINAL OUTPUT
    ============================================================
    
    ✓ Saved news_cleaned.csv
    ✓ Saved news_cleaned.json
    ✓ Saved news_cleaned.db (table: articles)
    ✓ Embeddings saved as article_embeddings.npy
    
    ============================================================
    COMPLETE PIPELINE SUMMARY
    ============================================================
      Input articles (raw CSV)        : 252
      After Stage 1 basic cleaning    : 250
      Clean articles (is_clean=True)  : 250
      After fuzzy dedup               : 250
    
      New columns added               : 27
      Final columns                   : ['article_id', 'url', 'source', 'title', 'description', 'author', 'tags', 'category', 'sentiment', 'publish_date', 'language', 'top_image', 'scraped_at', 'is_clean', 'detected_language', 'word_count', 'reading_time_mins', 'keyword_density', 'title_word_count', 'has_image', 'sentiment_score', 'sentiment_positive', 'sentiment_negative', 'sentiment_neutral', 'sentiment_label_vader', 'entities_persons', 'entities_organizations', 'entities_locations', 'entity_count', 'article_age_days', 'publish_day_of_week', 'publish_hour', 'is_recent', 'freshness_score', 'source_region', 'source_tier', 'sub_category', 'tfidf_top_terms', 'embedding_dim', 'story_id']
    
      Language distribution:
    detected_language
    en    250
    
      Region distribution:
    source_region
    Global    174
    China      43
    Asia       19
    Gulf        9
    UAE         5
    
      Category distribution:
    category
    technology       74
    politics         54
    entertainment    27
    business         26
    sports           18
    general          16
    health           15
    science          12
    environment       4
    travel            4
    
      Unique story clusters           : 247
    ============================================================
    


```python
from google.colab import files

files.download("news_cleaned.csv")
files.download("news_cleaned.json")
files.download("news_cleaned.db")
files.download("article_embeddings.npy")
```


    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>


### Fix for GitHub Rendering Issue

The error "the 'state' key is missing from 'metadata.widgets'" usually occurs when the notebook contains interactive widget metadata that GitHub's renderer can't process. The following code will remove the `metadata.widgets` entry from this notebook's metadata, which should fix the rendering problem on GitHub. Any interactive widget states will not be preserved after this operation.


```python
# First, find the current notebook's filename
import os

notebook_name = None
# Look for .ipynb files in the /content/ directory, common for Colab notebooks
for file in os.listdir('/content/'):
    if file.endswith('.ipynb'):
        notebook_name = os.path.join('/content/', file)
        break

if notebook_name:
    print(f"Detected notebook name: {notebook_name}")
else:
    print("Could not find a .ipynb file in the /content/ directory. Please ensure the notebook is saved.")
```

    Could not find a .ipynb file in the /content/ directory. Please ensure the notebook is saved.
    


```python
import nbformat

if notebook_name:
    # Load the notebook
    with open(notebook_name, 'r') as f:
        notebook = nbformat.read(f, as_version=4)

    # Remove the 'widgets' key from metadata if it exists
    if 'widgets' in notebook.metadata:
        del notebook.metadata['widgets']
        print("Successfully removed 'metadata.widgets'.")
    else:
        print("'metadata.widgets' not found or already removed.")

    # Save the modified notebook
    with open(notebook_name, 'w') as f:
        nbformat.write(notebook, f)
    print(f"Notebook '{notebook_name}' modified and saved. Please download this notebook and try uploading it to GitHub again.")
else:
    print("Cannot modify notebook: filename not found.")
```

    Cannot modify notebook: filename not found.
    
