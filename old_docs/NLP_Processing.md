<a href="https://colab.research.google.com/github/Yash-Yelave/Global_Gatway_RS/blob/main/NLP_Processing.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

Install Dependencies


```python
!pip install textblob spacy pandas -q
!python -m spacy download en_core_web_sm -q
```

    [2K     [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m12.8/12.8 MB[0m [31m96.2 MB/s[0m eta [36m0:00:00[0m
    [?25h[38;5;2m✔ Download and installation successful[0m
    You can now load the package via spacy.load('en_core_web_sm')
    [38;5;3m⚠ Restart to reload dependencies[0m
    If you are in a Jupyter or Colab notebook, you may need to restart Python in
    order to load all the package's dependencies. You can do this by selecting the
    'Restart kernel' or 'Restart runtime' option.
    

Imports & File Upload


```python
import pandas as pd
import spacy
from textblob import TextBlob
from datetime import datetime
from dateutil import parser as dateparser
import json
import math
import warnings
import io
from google.colab import files

warnings.filterwarnings("ignore")

# Load NLP Model
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_sm")
print("✓ spaCy loaded\n")

# Prompt for file upload
print("Please upload your 'news_cleaned.csv' from Phase 2...")
uploaded = files.upload()

# Read the uploaded CSV
filename = list(uploaded.keys())[0]
df = pd.read_csv(io.BytesIO(uploaded[filename]))
print(f"\n✓ Successfully loaded {len(df)} articles from {filename}.")

# Create a combined text column for NLP processing
df['full_text'] = df['title'].fillna("") + ". " + df['description'].fillna("")
```

    Loading spaCy model...
    ✓ spaCy loaded
    
    Please upload your 'news_cleaned.csv' from Phase 2...
    



     <input type="file" id="files-ac17f774-cf13-4ce0-91b6-76deb18e3f8b" name="files[]" multiple disabled
        style="border:none" />
     <output id="result-ac17f774-cf13-4ce0-91b6-76deb18e3f8b">
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


    Saving news_cleaned.csv to news_cleaned.csv
    
    ✓ Successfully loaded 250 articles from news_cleaned.csv.
    

The Core NLP Pipeline


```python
# ==========================================
# 1. KEYWORD EXTRACTION (NER + Noun Chunks)
# ==========================================
def extract_keywords(text):
    if not str(text).strip() or pd.isna(text):
        return []

    doc = nlp(str(text)[:2000]) # Cap at 2000 chars for performance
    keywords = set()

    # Extract Named Entities
    valid_ents = {'PERSON', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT'}
    for ent in doc.ents:
        if ent.label_ in valid_ents:
            keywords.add(ent.text.lower().strip())

    # Extract Noun Chunks (ignoring isolated pronouns/determiners)
    for chunk in doc.noun_chunks:
        if chunk.root.pos_ != 'PRON' and len(chunk.text) > 2:
            clean_chunk = " ".join([t.text for t in chunk if t.pos_ != 'DET'])
            if clean_chunk:
                keywords.add(clean_chunk.lower().strip())

    return list(keywords)

print("1/4 Extracting keywords using NER and Noun Chunks...")
df['nlp_keywords'] = df['full_text'].apply(extract_keywords)

# ==========================================
# 2. SENTIMENT ANALYSIS (TextBlob)
# ==========================================
def get_textblob_sentiment(text):
    if pd.isna(text):
        return 0.0, "neutral"

    polarity = TextBlob(str(text)).sentiment.polarity
    if polarity > 0.05:
        label = "positive"
    elif polarity < -0.05:
        label = "negative"
    else:
        label = "neutral"
    return round(polarity, 4), label

print("2/4 Computing TextBlob sentiment scores...")
sentiment_results = df['full_text'].apply(get_textblob_sentiment)
df['tb_sentiment_score'] = [res[0] for res in sentiment_results]
df['tb_sentiment_label'] = [res[1] for res in sentiment_results]

# ==========================================
# 3. AUTO-CATEGORIZATION (Keyword Mapping)
# ==========================================
CATEGORY_MAPPING = {
    "technology": ["ai", "artificial intelligence", "software", "apple", "google", "cybersecurity", "tech", "app", "cloud", "crypto"],
    "business": ["economy", "stock", "market", "startup", "ceo", "funding", "revenue", "investor", "wall street", "inflation"],
    "politics": ["government", "election", "president", "senate", "law", "policy", "congress", "diplomacy", "minister"],
    "sports": ["football", "basketball", "fifa", "nba", "championship", "tournament", "coach", "league", "olympics"],
    "health": ["vaccine", "covid", "fda", "hospital", "mental health", "nutrition", "disease", "treatment", "research"]
}

def auto_categorize(keywords):
    scores = {cat: 0 for cat in CATEGORY_MAPPING.keys()}
    for kw in keywords:
        for category, target_words in CATEGORY_MAPPING.items():
            if any(target in kw for target in target_words):
                scores[category] += 1

    best_category = max(scores, key=scores.get)
    return "general" if scores[best_category] == 0 else best_category

print("3/4 Auto-categorizing articles based on keywords...")
df['auto_category'] = df['nlp_keywords'].apply(auto_categorize)

# ==========================================
# 4. FRESHNESS / DECAY SCORE
# ==========================================
today = datetime.utcnow().date()
DECAY_RATE = 0.1

def calculate_freshness(date_val):
    if not date_val or pd.isna(date_val):
        return 0.5
    try:
        pub_date = dateparser.parse(str(date_val)).date()
        days_old = max(0, (today - pub_date).days)
        score = math.exp(-DECAY_RATE * days_old)
        return round(score, 4)
    except:
        return 0.5

print("4/4 Calculating freshness decay scores...")
df['freshness_decay_score'] = df['publish_date'].apply(calculate_freshness)

print("\n✓ NLP Pipeline Processing Complete.")
```

    1/4 Extracting keywords using NER and Noun Chunks...
    2/4 Computing TextBlob sentiment scores...
    3/4 Auto-categorizing articles based on keywords...
    4/4 Calculating freshness decay scores...
    
    ✓ NLP Pipeline Processing Complete.
    

Format & Download File


```python
# Serialize the keyword array to JSON so it saves cleanly in a CSV cell
df['nlp_keywords_json'] = df['nlp_keywords'].apply(json.dumps)

# Clean up temporary processing columns
df = df.drop(columns=['full_text', 'nlp_keywords'])

output_filename = "news_nlp_enriched.csv"
df.to_csv(output_filename, index=False)

print("="*60)
print(f"Saved {len(df)} articles to {output_filename}")
print("New columns added:")
print(" - tb_sentiment_score\n - tb_sentiment_label\n - nlp_keywords_json\n - auto_category\n - freshness_decay_score")
print("="*60)

# Trigger the download in Colab
print("\nDownloading file...")
files.download(output_filename)
```

    ============================================================
    Saved 250 articles to news_nlp_enriched.csv
    New columns added:
     - tb_sentiment_score
     - tb_sentiment_label
     - nlp_keywords_json
     - auto_category
     - freshness_decay_score
    ============================================================
    
    Downloading file...
    


    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>

