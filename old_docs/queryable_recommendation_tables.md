<a href="https://colab.research.google.com/github/Yash-Yelave/Global_Gatway_RS/blob/main/queryable_recommendation_tables.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

Environment Setup & Data Loading


```python
import pandas as pd
import numpy as np
import sqlite3
import json
import io
import warnings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from google.colab import files

warnings.filterwarnings("ignore")

# Prompt for file upload
print("Please upload your 'news_nlp_enriched.csv' from Day 5...")
uploaded = files.upload()

# Read the uploaded CSV
filename = list(uploaded.keys())[0]
df = pd.read_csv(io.BytesIO(uploaded[filename]))

# Ensure we have a unique identifier for relational mapping
if 'article_id' not in df.columns:
    df['article_id'] = ['art_' + str(i).zfill(4) for i in range(len(df))]

print(f"\n✓ Successfully loaded {len(df)} articles.")
```

    Please upload your 'news_nlp_enriched.csv' from Day 5...
    



     <input type="file" id="files-8cd474ce-5a42-43b2-9ab0-916749210a41" name="files[]" multiple disabled
        style="border:none" />
     <output id="result-8cd474ce-5a42-43b2-9ab0-916749210a41">
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


    Saving news_nlp_enriched.csv to news_nlp_enriched.csv
    
    ✓ Successfully loaded 250 articles.
    

The Trending Score Engine


```python
# ==========================================
# 1. TRENDING SCORE LOGIC
# ==========================================
print("Calculating Trending Scores...")

# Simulate view counts for the sake of the recommendation engine (10 to 10,000 views)
# In production, this would be a live metric pulled from your analytics database
np.random.seed(42)
df['view_count'] = np.random.randint(10, 10000, size=len(df))

# Formula: log(views) * freshness_decay
# We use log scale so an article with 10,000 views doesn't completely eclipse a fresh article with 500 views.
df['trending_score'] = np.log1p(df['view_count']) * df['freshness_decay_score']

# Normalize the trending score to a clean 0.0 to 10.0 scale for the UI
max_score = df['trending_score'].max()
df['trending_score'] = (df['trending_score'] / max_score * 10).round(2)

# Create the specific Trending Table layout
df_trending = df[['article_id', 'title', 'auto_category', 'view_count', 'freshness_decay_score', 'trending_score']]
df_trending = df_trending.sort_values(by='trending_score', ascending=False)

print(f"✓ Trending table generated. Top article score: {df_trending['trending_score'].iloc[0]}")
```

    Calculating Trending Scores...
    ✓ Trending table generated. Top article score: 10.0
    

Content Similarity Engine (TF-IDF)


```python
# ==========================================
# 2. COMPUTE TF-IDF COSINE SIMILARITY
# ==========================================
print("Computing Article Similarity Matrix...")

# Combine title and description for a robust summary
text_corpus = df['title'].fillna("") + " " + df['description'].fillna("")

# Vectorize the text
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
tfidf_matrix = vectorizer.fit_transform(text_corpus)

# Compute the Cosine Similarity matrix
cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

# Build the relational Similar Articles table
similar_articles_data = []

for idx in range(len(df)):
    art_id = df.iloc[idx]['article_id']

    # Get similarity scores for this specific article
    sim_scores = list(enumerate(cosine_sim_matrix[idx]))

    # Sort by similarity (descending), ignoring the first one (which is the article matching itself)
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]

    # Extract the article IDs and similarity scores of the top 5 matches
    top_matches = [{"similar_article_id": df.iloc[i[0]]['article_id'], "similarity_score": round(i[1], 4)} for i in sim_scores]

    similar_articles_data.append({
        "article_id": art_id,
        "similar_articles_json": json.dumps(top_matches) # Store as JSON array for easy DB retrieval
    })

df_similar = pd.DataFrame(similar_articles_data)
print("✓ Similar Articles mapped (Top 5 per article).")
```

    Computing Article Similarity Matrix...
    ✓ Similar Articles mapped (Top 5 per article).
    

Category Grouping & Database Export


```python
# ==========================================
# 3. CATEGORY & KEYWORD CLUSTERING
# ==========================================
print("Grouping Category Rankings...")

# Rank articles within their specific categories based on the new trending score
df['category_rank'] = df.groupby('auto_category')['trending_score'].rank(method='dense', ascending=False)

df_category_rankings = df[['article_id', 'title', 'auto_category', 'category_rank', 'trending_score']]
df_category_rankings = df_category_rankings.sort_values(by=['auto_category', 'category_rank'])

# ==========================================
# 4. DATABASE EXPORT
# ==========================================
db_filename = "recommendations.db"
conn = sqlite3.connect(db_filename)

print(f"\nWriting dedicated tables to {db_filename}...")

# 1. Main Master Table
df.to_sql("master_articles", conn, if_exists="replace", index=False)

# 2. Trending Table
df_trending.to_sql("trending_articles", conn, if_exists="replace", index=False)

# 3. Similar Articles Table
df_similar.to_sql("similar_articles", conn, if_exists="replace", index=False)

# 4. Category Rankings Table
df_category_rankings.to_sql("category_rankings", conn, if_exists="replace", index=False)

conn.commit()
conn.close()

print("\n" + "="*50)
print("DAY 6 PIPELINE COMPLETE!")
print("Ready for downstream API querying.")
print("="*50)

# Trigger the download in Colab
print("\nDownloading database file...")
files.download(db_filename)
```

    Grouping Category Rankings...
    
    Writing dedicated tables to recommendations.db...
    
    ==================================================
    DAY 6 PIPELINE COMPLETE!
    Ready for downstream API querying.
    ==================================================
    
    Downloading database file...
    


    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



```python
import pandas as pd
import numpy as np
import json
import io
import warnings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from google.colab import files
from IPython.display import display, HTML

warnings.filterwarnings("ignore")

# ==========================================
# 0. UPLOAD DATA
# ==========================================
print("Please upload your 'news_nlp_enriched.csv' from Day 5...")
uploaded = files.upload()

filename = list(uploaded.keys())[0]
df = pd.read_csv(io.BytesIO(uploaded[filename]))

# Ensure we have unique IDs
if 'article_id' not in df.columns:
    df['article_id'] = ['art_' + str(i).zfill(4) for i in range(len(df))]

print(f"\n✓ Successfully loaded {len(df)} articles.")

# ==========================================
# 1. TRENDING SCORE LOGIC
# ==========================================
print("\n1/3 Calculating Trending Scores...")

# Simulate views (since we don't have live user data yet)
np.random.seed(42)
df['view_count'] = np.random.randint(10, 10000, size=len(df))

# Formula: log(views) * freshness_decay
df['trending_score'] = np.log1p(df['view_count']) * df['freshness_decay_score']

# Normalize to a 0-10 scale
max_score = df['trending_score'].max()
df['trending_score'] = (df['trending_score'] / max_score * 10).round(2)

df_trending = df[['article_id', 'title', 'auto_category', 'view_count', 'freshness_decay_score', 'trending_score']]
df_trending = df_trending.sort_values(by='trending_score', ascending=False)

# ==========================================
# 2. COMPUTE TF-IDF COSINE SIMILARITY
# ==========================================
print("2/3 Computing Article Similarity Matrix...")

text_corpus = df['title'].fillna("") + " " + df['description'].fillna("")

vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
tfidf_matrix = vectorizer.fit_transform(text_corpus)
cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

similar_articles_data = []

for idx in range(len(df)):
    art_id = df.iloc[idx]['article_id']
    sim_scores = list(enumerate(cosine_sim_matrix[idx]))

    # Sort descending, drop the first one (it's the article matching itself), keep top 5
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]

    top_matches = [{"similar_article_id": df.iloc[i[0]]['article_id'], "similarity_score": round(i[1], 4)} for i in sim_scores]

    similar_articles_data.append({
        "article_id": art_id,
        "similar_articles_json": json.dumps(top_matches)
    })

df_similar = pd.DataFrame(similar_articles_data)

# ==========================================
# 3. CATEGORY & KEYWORD CLUSTERING
# ==========================================
print("3/3 Grouping Category Rankings...")

df['category_rank'] = df.groupby('auto_category')['trending_score'].rank(method='dense', ascending=False)

df_category_rankings = df[['article_id', 'title', 'auto_category', 'category_rank', 'trending_score']]
df_category_rankings = df_category_rankings.sort_values(by=['auto_category', 'category_rank'])

# ==========================================
# 4. DISPLAY RESULTS IN COLAB
# ==========================================
print("\n" + "="*50)
print("DAY 6 PIPELINE COMPLETE! Here are your Recommendation Tables:")
print("="*50)

print("\n\n📊 TABLE 1: TRENDING ARTICLES (Top 5)")
display(df_trending.head(5))

print("\n\n🔗 TABLE 2: SIMILAR ARTICLES ('Read More' Widget) - First 5 rows")
display(df_similar.head(5))

print("\n\n📑 TABLE 3: CATEGORY RANKINGS (Top 5 across categories)")
display(df_category_rankings.head(5))
```

    Please upload your 'news_nlp_enriched.csv' from Day 5...
    



     <input type="file" id="files-a64dce21-1e18-4803-9c08-221c65b7eed6" name="files[]" multiple disabled
        style="border:none" />
     <output id="result-a64dce21-1e18-4803-9c08-221c65b7eed6">
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


    Saving news_nlp_enriched.csv to news_nlp_enriched (2).csv
    
    ✓ Successfully loaded 250 articles.
    
    1/3 Calculating Trending Scores...
    2/3 Computing Article Similarity Matrix...
    3/3 Grouping Category Rankings...
    
    ==================================================
    DAY 6 PIPELINE COMPLETE! Here are your Recommendation Tables:
    ==================================================
    
    
    📊 TABLE 1: TRENDING ARTICLES (Top 5)
    



  <div id="df-33e47a8f-391a-41c3-aa48-8564020e8ab6" class="colab-df-container">
    <div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>article_id</th>
      <th>title</th>
      <th>auto_category</th>
      <th>view_count</th>
      <th>freshness_decay_score</th>
      <th>trending_score</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>9</th>
      <td>4d83f4049ae2</td>
      <td>flydubai to launch daily Bangkok flights from ...</td>
      <td>technology</td>
      <td>8332</td>
      <td>1.0000</td>
      <td>10.00</td>
    </tr>
    <tr>
      <th>188</th>
      <td>c537e1b7097f</td>
      <td>AI swarms could hijack democracy without anyon...</td>
      <td>technology</td>
      <td>5801</td>
      <td>1.0000</td>
      <td>9.60</td>
    </tr>
    <tr>
      <th>185</th>
      <td>4c2415707a32</td>
      <td>Scientists Find Cheaper Way to Kill Western Dr...</td>
      <td>general</td>
      <td>5259</td>
      <td>1.0000</td>
      <td>9.49</td>
    </tr>
    <tr>
      <th>246</th>
      <td>50db63baa17f</td>
      <td>Michael Review: Jaafar Jackson Dazzles As His ...</td>
      <td>general</td>
      <td>1164</td>
      <td>1.0000</td>
      <td>7.82</td>
    </tr>
    <tr>
      <th>141</th>
      <td>a224803feccd</td>
      <td>The Download: turning down human noise, and LA...</td>
      <td>technology</td>
      <td>9924</td>
      <td>0.7408</td>
      <td>7.55</td>
    </tr>
  </tbody>
</table>
</div>
    <div class="colab-df-buttons">

  <div class="colab-df-container">
    <button class="colab-df-convert" onclick="convertToInteractive('df-33e47a8f-391a-41c3-aa48-8564020e8ab6')"
            title="Convert this dataframe to an interactive table."
            style="display:none;">

  <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960">
    <path d="M120-120v-720h720v720H120Zm60-500h600v-160H180v160Zm220 220h160v-160H400v160Zm0 220h160v-160H400v160ZM180-400h160v-160H180v160Zm440 0h160v-160H620v160ZM180-180h160v-160H180v160Zm440 0h160v-160H620v160Z"/>
  </svg>
    </button>

  <style>
    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }
  </style>

    <script>
      const buttonEl =
        document.querySelector('#df-33e47a8f-391a-41c3-aa48-8564020e8ab6 button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-33e47a8f-391a-41c3-aa48-8564020e8ab6');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }
    </script>
  </div>


    </div>
  </div>



    
    
    🔗 TABLE 2: SIMILAR ARTICLES ('Read More' Widget) - First 5 rows
    



  <div id="df-de2799cc-c25b-4d77-839e-8eef2cca462f" class="colab-df-container">
    <div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>article_id</th>
      <th>similar_articles_json</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>9b8c748a78a0</td>
      <td>[{"similar_article_id": "b19b51e256bd", "simil...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>6c85e93eb2d8</td>
      <td>[{"similar_article_id": "210e676f4ba6", "simil...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>8f53abce0bfc</td>
      <td>[{"similar_article_id": "b19b51e256bd", "simil...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>ff2d206b77d7</td>
      <td>[{"similar_article_id": "1db2b9da3430", "simil...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>7de36895b31a</td>
      <td>[{"similar_article_id": "3d71190da94e", "simil...</td>
    </tr>
  </tbody>
</table>
</div>
    <div class="colab-df-buttons">

  <div class="colab-df-container">
    <button class="colab-df-convert" onclick="convertToInteractive('df-de2799cc-c25b-4d77-839e-8eef2cca462f')"
            title="Convert this dataframe to an interactive table."
            style="display:none;">

  <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960">
    <path d="M120-120v-720h720v720H120Zm60-500h600v-160H180v160Zm220 220h160v-160H400v160Zm0 220h160v-160H400v160ZM180-400h160v-160H180v160Zm440 0h160v-160H620v160ZM180-180h160v-160H180v160Zm440 0h160v-160H620v160Z"/>
  </svg>
    </button>

  <style>
    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }
  </style>

    <script>
      const buttonEl =
        document.querySelector('#df-de2799cc-c25b-4d77-839e-8eef2cca462f button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-de2799cc-c25b-4d77-839e-8eef2cca462f');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }
    </script>
  </div>


    </div>
  </div>



    
    
    📑 TABLE 3: CATEGORY RANKINGS (Top 5 across categories)
    



  <div id="df-c54f587b-b3ce-40dd-9947-e64a9aa0e2dc" class="colab-df-container">
    <div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>article_id</th>
      <th>title</th>
      <th>auto_category</th>
      <th>category_rank</th>
      <th>trending_score</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>116</th>
      <td>db8be5db4b3b</td>
      <td>What s the key to better vegan cheese? Microbr...</td>
      <td>business</td>
      <td>1.0</td>
      <td>7.48</td>
    </tr>
    <tr>
      <th>39</th>
      <td>82d055ba524d</td>
      <td>hong kong property investment soars on lower f...</td>
      <td>business</td>
      <td>2.0</td>
      <td>7.05</td>
    </tr>
    <tr>
      <th>120</th>
      <td>fdbe0d97ddf4</td>
      <td>Blue Energy raises $380M to build grid-scale n...</td>
      <td>business</td>
      <td>3.0</td>
      <td>7.01</td>
    </tr>
    <tr>
      <th>144</th>
      <td>337000087609</td>
      <td>Colossal Biosciences said it cloned red wolves...</td>
      <td>business</td>
      <td>4.0</td>
      <td>6.82</td>
    </tr>
    <tr>
      <th>177</th>
      <td>b1d652780252</td>
      <td>crypto market strength led by bitcoin as altco...</td>
      <td>business</td>
      <td>5.0</td>
      <td>6.74</td>
    </tr>
  </tbody>
</table>
</div>
    <div class="colab-df-buttons">

  <div class="colab-df-container">
    <button class="colab-df-convert" onclick="convertToInteractive('df-c54f587b-b3ce-40dd-9947-e64a9aa0e2dc')"
            title="Convert this dataframe to an interactive table."
            style="display:none;">

  <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960">
    <path d="M120-120v-720h720v720H120Zm60-500h600v-160H180v160Zm220 220h160v-160H400v160Zm0 220h160v-160H400v160ZM180-400h160v-160H180v160Zm440 0h160v-160H620v160ZM180-180h160v-160H180v160Zm440 0h160v-160H620v160Z"/>
  </svg>
    </button>

  <style>
    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }
  </style>

    <script>
      const buttonEl =
        document.querySelector('#df-c54f587b-b3ce-40dd-9947-e64a9aa0e2dc button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-c54f587b-b3ce-40dd-9947-e64a9aa0e2dc');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }
    </script>
  </div>


    </div>
  </div>


