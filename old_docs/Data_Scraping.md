<a href="https://colab.research.google.com/github/Yash-Yelave/Global_Gatway_RS/blob/main/Data_Scraping.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

Install dependencies


```python
!pip install groq newspaper3k feedparser requests beautifulsoup4 pandas pydantic lxml_html_clean -q
```

      Preparing metadata (setup.py) ... [?25l[?25hdone
    [2K     [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m7.4/7.4 MB[0m [31m33.0 MB/s[0m eta [36m0:00:00[0m
    [?25h  Preparing metadata (setup.py) ... [?25l[?25hdone
      Preparing metadata (setup.py) ... [?25l[?25hdone
      Preparing metadata (setup.py) ... [?25l[?25hdone
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m142.3/142.3 kB[0m [31m9.0 MB/s[0m eta [36m0:00:00[0m
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m211.1/211.1 kB[0m [31m13.5 MB/s[0m eta [36m0:00:00[0m
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m81.5/81.5 kB[0m [31m4.9 MB/s[0m eta [36m0:00:00[0m
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m105.9/105.9 kB[0m [31m6.7 MB/s[0m eta [36m0:00:00[0m
    [?25h  Building wheel for tinysegmenter (setup.py) ... [?25l[?25hdone
      Building wheel for feedfinder2 (setup.py) ... [?25l[?25hdone
      Building wheel for jieba3k (setup.py) ... [?25l[?25hdone
      Building wheel for sgmllib3k (setup.py) ... [?25l[?25hdone
    

Imports & config



```python
import os
import time
import json
import hashlib
import sqlite3
import feedparser
import pandas as pd
import requests

from datetime import datetime
from bs4 import BeautifulSoup
from newspaper import Article
from groq import Groq
from pydantic import BaseModel, field_validator
from typing import Optional, List
from google.colab import userdata

# ── Groq client ──────────────────────────────────────────────────────────────
# In Colab: Secrets (key icon) → add GROQ_API_KEY
client = Groq(api_key=userdata.get("GROQ_API_KEY"))

GROQ_MODEL     = "llama-3.1-8b-instant"
MAX_TOKENS_IN  = 2000          # truncate article before sending to Groq
RATE_LIMIT_SEC = 2.5           # stay safely under 30 req/min free tier
CATEGORIES     = ["technology", "politics", "sports", "business",
                  "health", "science", "entertainment", "general"]
```

RSS feed sources


```python
RSS_FEEDS = {
    "BBC Top Stories"       : "http://feeds.bbci.co.uk/news/rss.xml",
    "BBC Technology"        : "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "Reuters Top News"      : "https://feeds.reuters.com/reuters/topNews",
    "TechCrunch"            : "https://techcrunch.com/feed/",
    "The Guardian World"    : "https://www.theguardian.com/world/rss",
    "The Guardian Tech"     : "https://www.theguardian.com/uk/technology/rss",
    "Al Jazeera"            : "https://www.aljazeera.com/xml/rss/all.xml",
    "NASA Breaking News"    : "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "ESPN Top Headlines"    : "https://www.espn.com/espn/rss/news",
    "Harvard Health"        : "https://www.health.harvard.edu/blog/feed",
}

def fetch_rss_urls(feeds: dict, max_per_feed: int = 10) -> list[dict]:
    """
    Parse each RSS feed and return a flat list of
    {title, url, published, source} dicts.
    """
    articles = []
    for source_name, feed_url in feeds.items():
        try:
            feed = feedparser.parse(feed_url)
            entries = feed.entries[:max_per_feed]
            for entry in entries:
                url = entry.get("link", "")
                if not url:
                    continue
                articles.append({
                    "source"   : source_name,
                    "url"      : url,
                    "rss_title": entry.get("title", ""),
                    "published": entry.get("published", ""),
                })
            print(f"  ✓ {source_name}: {len(entries)} URLs")
        except Exception as e:
            print(f"  ✗ {source_name}: {e}")
    return articles

print("Fetching RSS feeds...")
raw_urls = fetch_rss_urls(RSS_FEEDS, max_per_feed=10)
print(f"\nTotal URLs collected: {len(raw_urls)}")
```

    Fetching RSS feeds...
      ✓ BBC Top Stories: 10 URLs
      ✓ BBC Technology: 10 URLs
      ✓ Reuters Top News: 0 URLs
      ✓ TechCrunch: 10 URLs
      ✓ The Guardian World: 10 URLs
      ✓ The Guardian Tech: 10 URLs
      ✓ Al Jazeera: 10 URLs
      ✓ NASA Breaking News: 10 URLs
      ✓ ESPN Top Headlines: 10 URLs
      ✓ Harvard Health: 0 URLs
    
    Total URLs collected: 80
    

Article scraper


```python
def scrape_article(url: str) -> dict | None:
    """
    Use newspaper3k to pull full article text, author, and publish date.
    Falls back to BeautifulSoup for the meta description if needed.
    Returns None on failure.
    """
    try:
        art = Article(url, fetch_images=False, request_timeout=10)
        art.download()
        art.parse()

        # BeautifulSoup fallback for meta description
        meta_desc = ""
        try:
            soup = BeautifulSoup(art.html, "html.parser")
            tag = (soup.find("meta", attrs={"name": "description"}) or
                   soup.find("meta", attrs={"property": "og:description"}))
            if tag:
                meta_desc = tag.get("content", "")
        except Exception:
            pass

        return {
            "url"          : url,
            "scraped_title": art.title or "",
            "raw_text"     : art.text or "",
            "scraped_author": ", ".join(art.authors) if art.authors else "",
            "scraped_date" : str(art.publish_date) if art.publish_date else "",
            "meta_desc"    : meta_desc,
            "top_image"    : art.top_image or "",
        }
    except Exception as e:
        print(f"    Scrape failed [{url[:60]}]: {e}")
        return None
```

Groq extraction prompt


```python
EXTRACTION_PROMPT = """
You are a structured data extractor for a news recommendation system.

Given the raw text of a news article, return ONLY a valid JSON object — no explanation, no markdown fences.

JSON schema:
{{
  "title"       : "clean headline (string)",
  "description" : "2-3 sentence plain-English summary (string)",
  "author"      : "author name or null",
  "tags"        : ["keyword1", "keyword2", "keyword3"],
  "category"    : "one of: technology | politics | sports | business | health | science | entertainment | general",
  "sentiment"   : "positive | neutral | negative",
  "publish_date": "YYYY-MM-DD or null"
}}

Rules:
- tags must be 3 to 5 short lowercase keywords relevant to the article.
- description must be written in your own words, not copied from the article.
- If a field cannot be determined, use null.
- Return ONLY the JSON object, nothing else.

Article title (hint): {title_hint}
Article text:
{article_text}
""".strip()


def extract_with_groq(scraped: dict) -> dict | None:
    """
    Send truncated article text to Groq and parse the returned JSON.
    """
    raw_text = scraped.get("raw_text", "")
    if not raw_text.strip():
        raw_text = scraped.get("meta_desc", "")
    if not raw_text.strip():
        return None

    # Truncate to keep within context window
    truncated = raw_text[:MAX_TOKENS_IN * 4]   # ~4 chars per token estimate

    prompt = EXTRACTION_PROMPT.format(
        title_hint   = scraped.get("scraped_title", ""),
        article_text = truncated,
    )

    try:
        response = client.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = [{"role": "user", "content": prompt}],
            max_tokens  = 512,
            temperature = 0.1,
        )
        raw_json = response.choices[0].message.content.strip()

        # Strip accidental markdown fences if present
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]

        return json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"    JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"    Groq API error: {e}")
        return None
```

Pydantic schema for validation


```python
class NewsArticle(BaseModel):
    article_id  : str
    url         : str
    source      : str
    title       : str
    description : str
    author      : Optional[str]
    tags        : List[str]
    category    : str
    sentiment   : str
    publish_date: Optional[str]
    top_image   : Optional[str]
    scraped_at  : str

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        return v if v in CATEGORIES else "general"

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment(cls, v):
        return v if v in ("positive", "neutral", "negative") else "neutral"

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        return [t.lower().strip() for t in v if t.strip()][:5]

    @field_validator("title", "description")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


def build_article_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def validate_and_merge(rss_meta: dict, scraped: dict, extracted: dict) -> NewsArticle | None:
    """
    Merge RSS metadata + scraped data + Groq extracted fields into
    a validated NewsArticle. Returns None if required fields are missing.
    """
    try:
        return NewsArticle(
            article_id  = build_article_id(rss_meta["url"]),
            url         = rss_meta["url"],
            source      = rss_meta["source"],
            title       = extracted.get("title") or scraped.get("scraped_title") or rss_meta.get("rss_title", ""),
            description = extracted.get("description", ""),
            author      = extracted.get("author") or scraped.get("scraped_author") or None,
            tags        = extracted.get("tags", []),
            category    = extracted.get("category", "general"),
            sentiment   = extracted.get("sentiment", "neutral"),
            publish_date= extracted.get("publish_date") or scraped.get("scraped_date") or rss_meta.get("published") or None,
            top_image   = scraped.get("top_image") or None,
            scraped_at  = datetime.utcnow().isoformat(),
        )
    except Exception as e:
        print(f"    Validation error: {e}")
        return None
```

Main pipeline loop


```python
def run_pipeline(raw_urls: list[dict], max_articles: int = 50) -> list[dict]:
    """
    Full pipeline: scrape → Groq extract → validate.
    Returns a list of clean article dicts ready for saving.
    """
    results    = []
    seen_urls  = set()
    processed  = 0

    for item in raw_urls:
        if processed >= max_articles:
            break

        url = item["url"]

        # Deduplicate by URL
        if url in seen_urls:
            continue
        seen_urls.add(url)

        print(f"[{processed + 1}/{max_articles}] {url[:80]}")

        # Step 1: Scrape
        scraped = scrape_article(url)
        if not scraped:
            continue

        # Step 2: Groq extraction
        extracted = extract_with_groq(scraped)
        if not extracted:
            continue

        # Step 3: Validate & merge
        article = validate_and_merge(item, scraped, extracted)
        if not article:
            continue

        results.append(article.model_dump())
        processed += 1
        print(f"    ✓ [{article.category}] [{article.sentiment}] {article.title[:60]}")

        # Rate limiting
        time.sleep(RATE_LIMIT_SEC)

    print(f"\nPipeline complete. {len(results)} clean articles collected.")
    return results


# Run — set max_articles to however many you want
clean_articles = run_pipeline(raw_urls, max_articles=50)
```

    [1/50] https://www.bbc.com/news/articles/c895jpwl9gpo?at_medium=RSS&at_campaign=rss
    

    /tmp/ipykernel_4716/3272300405.py:60: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
      scraped_at  = datetime.utcnow().isoformat(),
    

        ✓ [politics] [neutral] dangerous moment for keir starmer
    [2/50] https://www.bbc.com/news/articles/cjd84pkkjgpo?at_medium=RSS&at_campaign=rss
        ✓ [business] [neutral] unemployment rate unexpectedly falls
    [3/50] https://www.bbc.com/news/articles/c5ylw4q5jv2o?at_medium=RSS&at_campaign=rss
        ✓ [general] [negative] drive-by shooting outside Harlesden church
    [4/50] https://www.bbc.com/news/articles/cn08jy6w0l5o?at_medium=RSS&at_campaign=rss
        ✓ [health] [neutral] uk smoking ban for people born after 2008 agreed
    [5/50] https://www.bbc.com/news/articles/crm19j48wnno?at_medium=RSS&at_campaign=rss
        ✓ [entertainment] [neutral] madonna offers reward for missing coachella costume
    [6/50] https://www.bbc.com/news/articles/cn9qw1jqpgxo?at_medium=RSS&at_campaign=rss
        ✓ [politics] [neutral] No 10 considered giving Doyle ambassador role, sacked offici
    [7/50] https://www.bbc.com/news/articles/cd9v420y190o?at_medium=RSS&at_campaign=rss
        ✓ [politics] [negative] zelensky criticizes us envoys for not visiting kyiv
    [8/50] https://www.bbc.com/news/articles/cvg0yekk2vko?at_medium=RSS&at_campaign=rss
        ✓ [general] [neutral] woman in court after car hits pedestrians in soho
    [9/50] https://www.bbc.com/sport/football/articles/cly7ejx9nx5o?at_medium=RSS&at_campai
        ✓ [sports] [neutral] baroness karren brady steps down as west ham vice-chair
    [10/50] https://www.bbc.com/news/articles/cn4vkye71ypo?at_medium=RSS&at_campaign=rss
        ✓ [technology] [neutral] john ternus challenges as new apple boss
    [11/50] https://www.bbc.com/news/articles/c4gxj049wljo?at_medium=RSS&at_campaign=rss
        ✓ [technology] [neutral] ofcom probing telegram over child sexual abuse material conc
    [12/50] https://www.bbc.com/news/articles/c1kr19lry18o?at_medium=RSS&at_campaign=rss
        ✓ [technology] [neutral] john ternus named as apple ceo
    [13/50] https://www.bbc.com/news/articles/c5yvm11xrn6o?at_medium=RSS&at_campaign=rss
        ✓ [science] [neutral] fusion breakthrough
    [14/50] https://www.bbc.com/news/articles/cjr9vwz48npo?at_medium=RSS&at_campaign=rss
        ✓ [technology] [neutral] blue origin rocket grounded after satellite mishap
    [15/50] https://www.bbc.com/news/articles/crk151nn7j3o?at_medium=RSS&at_campaign=rss
        ✓ [technology] [negative] musk snubs french prosecutors amid x probe
    [16/50] https://www.bbc.com/news/articles/cyv10e1d13po?at_medium=RSS&at_campaign=rss
        ✓ [technology] [negative] anthropic ai model sparks fears over surveillance and autono
    [17/50] https://www.bbc.com/news/articles/cp9vppem4evo?at_medium=RSS&at_campaign=rss
        ✓ [technology] [neutral] Combating AI with Human Verification
    [18/50] https://www.bbc.com/news/articles/crk1py1jgzko?at_medium=RSS&at_campaign=rss
        ✓ [technology] [negative] anthopic's claude mythos risks
    [19/50] https://www.bbc.com/news/articles/c1d907lq6nyo?at_medium=RSS&at_campaign=rss
        ✓ [technology] [neutral] digital twin could make you a superworker
    [20/50] https://techcrunch.com/2026/04/21/yelps-updated-ai-assistant-can-answer-question
        ✓ [technology] [neutral] yelp's updated ai assistant can answer questions and book a 
    [21/50] https://techcrunch.com/2026/04/21/blue-energy-raises-380m-to-build-grid-scale-nu
        ✓ [technology] [neutral] Blue Energy raises $380M to build grid-scale nuclear reactor
    [22/50] https://techcrunch.com/2026/04/20/who-is-john-ternus-the-incoming-apple-ceo/
        ✓ [technology] [neutral] Who is John Ternus, the incoming Apple CEO?
    [23/50] https://techcrunch.com/2026/04/20/anthropic-takes-5b-from-amazon-and-pledges-100
        ✓ [technology] [neutral] anthropic secures $5b from amazon, pledges $100b in cloud sp
    [24/50] https://techcrunch.com/2026/04/20/google-rolls-out-gemini-in-chrome-in-seven-new
        ✓ [technology] [neutral] google rolls out gemini in chrome in 7 new countries
    [25/50] https://techcrunch.com/2026/04/20/tim-cook-stepping-down-as-apple-ceo-john-ternu
        ✓ [technology] [neutral] Tim Cook stepping down as Apple CEO, John Ternus taking over
    [26/50] https://techcrunch.com/2026/04/20/google-photos-adds-new-touch-up-tools-for-quic
        ✓ [technology] [neutral] google photos adds new touch-up tools
    [27/50] https://techcrunch.com/2026/04/20/ai-writing-its-not-just-this-its-that-barrons/
        ✓ [technology] [neutral] AI-generated writing is becoming increasingly common in corp
    [28/50] https://techcrunch.com/2026/04/20/north-korea-hackers-blamed-for-290m-crypto-the
        ✓ [technology] [negative] north korean hackers blamed for $290m crypto theft
    [29/50] https://techcrunch.com/2026/04/20/mastodon-says-its-flagship-server-was-hit-by-a
        ✓ [technology] [neutral] mastodon hit by ddos attack
    [30/50] https://www.theguardian.com/film/2026/apr/20/charlize-theron-timothee-chalamet-b
        ✓ [entertainment] [negative] Charlize Theron joins chorus of disapproval over Timothée Ch
    [31/50] https://www.theguardian.com/world/2026/apr/20/madagascar-gen-z-protesters-fear-n
        ✓ [politics] [negative] Madagascar Gen Z protesters fear new regime no better than o
    [32/50] https://www.theguardian.com/us-news/2026/apr/19/woman-arrested-la-arms-trafficki
        ✓ [politics] [negative] iranian american woman arrested for alleged arms trafficking
    [33/50] https://www.theguardian.com/technology/2026/apr/17/kenyan-outsourcing-company-fo
        ✓ [technology] [negative] kenyan firm sacks 1000 workers after losing meta contract
    [34/50] https://www.theguardian.com/environment/2026/apr/17/weather-tracker-hail-covers-
        ✓ [general] [neutral] hail covers parts of tunisia and algeria like snow
    [35/50] https://www.theguardian.com/global-development/2026/apr/21/ecuador-us-boat-strik
        ✓ [politics] [negative] US boat strike: Fishers who survived attack speak out
    [36/50] https://www.theguardian.com/world/2026/apr/20/canadian-woman-killed-after-gunman
        ✓ [politics] [negative] canadian woman killed in shooting at mexico's teotihuacán py
    [37/50] https://www.theguardian.com/world/2026/apr/20/mark-carney-canada-us-economy-trad
        ✓ [politics] [negative] carney says canadas strong economic ties to us are weakness 
    [38/50] https://www.theguardian.com/us-news/2026/apr/20/mexico-car-accident-drug-officia
        ✓ [politics] [negative] us and mexican officials killed in car accident
    [39/50] https://www.theguardian.com/world/2026/apr/19/artemis-astronaut-jeremy-hansen-fr
        ✓ [general] [positive] Canadian astronaut's French words help heal wounds from lang
    [40/50] https://www.theguardian.com/technology/2026/apr/21/palantir-manifesto-uk-contrac
        ✓ [technology] [negative] Palantir manifesto described as 'ramblings of a supervillain
    [41/50] https://www.theguardian.com/technology/2026/apr/20/tim-cook-apple-ceo-replacemen
        ✓ [technology] [neutral] tim cook to step down as apple chief, john ternus named repl
    [42/50] https://www.theguardian.com/technology/2026/apr/20/french-prosecutors-summon-elo
        ✓ [technology] [negative] elon musk snubs paris legal summons over alleged child abuse
    [43/50] https://www.theguardian.com/science/audio/2026/apr/21/mythos-are-fears-over-new-
        ✓ [technology] [neutral] anthropic's mythos preview ai model raises concerns
    [44/50] https://www.theguardian.com/technology/2026/apr/18/sam-altman-house-attack-ai
        ✓ [technology] [negative] Attack on Sam Altman's home unfolds
    [45/50] https://www.theguardian.com/technology/2026/apr/20/sonos-play-review-portable-sp
        ✓ [technology] [positive] Sonos Play review: a great jack-of-all-trades portable speak
    [46/50] https://www.theguardian.com/news/audio/2026/apr/20/teacher-v-chatbot-classroom-a
        ✓ [technology] [neutral] Teacher v chatbot: my journey into the classroom in the age 
    [47/50] https://www.theguardian.com/business/2026/apr/19/uber-lyft-drivers-gas-prices
        ✓ [business] [negative] Uber and Lyft drivers reeling as fuel prices soar
    [48/50] https://www.theguardian.com/film/2026/apr/17/hollywood-big-screen-imax
        ✓ [entertainment] [neutral] Screenmaxxing: why Hollywood is supersizing the big screen e
    [49/50] https://www.theguardian.com/us-news/2026/apr/16/big-tech-breakup-parties
        ✓ [technology] [neutral] Break Up With Big Tech at a Bar: Cybersecurity Disguised as 
    [50/50] https://www.aljazeera.com/video/newsfeed/2026/4/21/mass-trial-for-nearly-500-all
        ✓ [politics] [neutral] mass trial for alleged gang members in el salvador
    
    Pipeline complete. 50 clean articles collected.
    

Save to CSV, JSON, and SQLite


```python
def save_outputs(articles: list[dict], prefix: str = "news_dataset"):
    df = pd.DataFrame(articles)

    # ── CSV ──────────────────────────────────────────────────────────────────
    csv_path = f"{prefix}.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV  → {csv_path}  ({len(df)} rows)")

    # ── JSON (records orient) ─────────────────────────────────────────────────
    json_path = f"{prefix}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON → {json_path}")

    # ── SQLite ───────────────────────────────────────────────────────────────
    db_path = f"{prefix}.db"
    conn    = sqlite3.connect(db_path)

    df_sql = df.copy()
    # SQLite can't store Python lists — serialise tags to JSON string
    df_sql["tags"] = df_sql["tags"].apply(json.dumps)
    df_sql.to_sql("articles", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()
    print(f"Saved DB   → {db_path}  (table: articles)")

    return df

df = save_outputs(clean_articles)
df.head()
```

    Saved CSV  → news_dataset.csv  (50 rows)
    Saved JSON → news_dataset.json
    Saved DB   → news_dataset.db  (table: articles)
    





  <div id="df-028165d3-dd37-4dab-950d-32e68aaa642f" class="colab-df-container">
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
      <th>url</th>
      <th>source</th>
      <th>title</th>
      <th>description</th>
      <th>author</th>
      <th>tags</th>
      <th>category</th>
      <th>sentiment</th>
      <th>publish_date</th>
      <th>top_image</th>
      <th>scraped_at</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>40dc511eb4a1</td>
      <td>https://www.bbc.com/news/articles/c895jpwl9gpo...</td>
      <td>BBC Top Stories</td>
      <td>dangerous moment for keir starmer</td>
      <td>labour party's judgment on the prime minister ...</td>
      <td>None</td>
      <td>[labour, politics, uk]</td>
      <td>politics</td>
      <td>neutral</td>
      <td>Tue, 21 Apr 2026 12:16:18 GMT</td>
      <td>https://ichef.bbci.co.uk/news/1024/branded_new...</td>
      <td>2026-04-21T12:30:37.150789</td>
    </tr>
    <tr>
      <th>1</th>
      <td>795becaf0ccc</td>
      <td>https://www.bbc.com/news/articles/cjd84pkkjgpo...</td>
      <td>BBC Top Stories</td>
      <td>unemployment rate unexpectedly falls</td>
      <td>the unemployment rate has decreased due to few...</td>
      <td>None</td>
      <td>[unemployment, economy, war]</td>
      <td>business</td>
      <td>neutral</td>
      <td>Tue, 21 Apr 2026 11:20:19 GMT</td>
      <td>https://ichef.bbci.co.uk/news/1024/branded_new...</td>
      <td>2026-04-21T12:30:40.263711</td>
    </tr>
    <tr>
      <th>2</th>
      <td>26e07c3ba064</td>
      <td>https://www.bbc.com/news/articles/c5ylw4q5jv2o...</td>
      <td>BBC Top Stories</td>
      <td>drive-by shooting outside Harlesden church</td>
      <td>A drive-by shooting occurred outside a church ...</td>
      <td>None</td>
      <td>[shooting, murder, harlesden]</td>
      <td>general</td>
      <td>negative</td>
      <td>Tue, 21 Apr 2026 11:49:29 GMT</td>
      <td>https://ichef.bbci.co.uk/news/1024/branded_new...</td>
      <td>2026-04-21T12:30:43.238631</td>
    </tr>
    <tr>
      <th>3</th>
      <td>129e95f24cfe</td>
      <td>https://www.bbc.com/news/articles/cn08jy6w0l5o...</td>
      <td>BBC Top Stories</td>
      <td>uk smoking ban for people born after 2008 agreed</td>
      <td>the uk government has agreed to implement a sm...</td>
      <td>None</td>
      <td>[uk, smoking ban, health]</td>
      <td>health</td>
      <td>neutral</td>
      <td>Tue, 21 Apr 2026 11:39:52 GMT</td>
      <td>https://ichef.bbci.co.uk/news/1024/branded_new...</td>
      <td>2026-04-21T12:30:46.255826</td>
    </tr>
    <tr>
      <th>4</th>
      <td>53fca67a3c96</td>
      <td>https://www.bbc.com/news/articles/crm19j48wnno...</td>
      <td>BBC Top Stories</td>
      <td>madonna offers reward for missing coachella co...</td>
      <td>madonna is offering a reward for the return of...</td>
      <td>None</td>
      <td>[madonna, coachella, costume, reward]</td>
      <td>entertainment</td>
      <td>neutral</td>
      <td>Tue, 21 Apr 2026 10:29:05 GMT</td>
      <td>https://ichef.bbci.co.uk/news/1024/branded_new...</td>
      <td>2026-04-21T12:30:49.254757</td>
    </tr>
  </tbody>
</table>
</div>
    <div class="colab-df-buttons">

  <div class="colab-df-container">
    <button class="colab-df-convert" onclick="convertToInteractive('df-028165d3-dd37-4dab-950d-32e68aaa642f')"
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
        document.querySelector('#df-028165d3-dd37-4dab-950d-32e68aaa642f button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-028165d3-dd37-4dab-950d-32e68aaa642f');
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




Quick EDA (optional sanity check)


```python
print("=== Dataset summary ===\n")
print(f"Total articles : {len(df)}")
print(f"Sources        : {df['source'].nunique()}")
print(f"Date range     : {df['publish_date'].min()} → {df['publish_date'].max()}")

print("\n── Category distribution ──")
print(df["category"].value_counts().to_string())

print("\n── Sentiment distribution ──")
print(df["sentiment"].value_counts().to_string())

print("\n── Articles per source ──")
print(df["source"].value_counts().to_string())

print("\n── Null counts ──")
print(df.isnull().sum().to_string())
```

    === Dataset summary ===
    
    Total articles : 50
    Sources        : 6
    Date range     : 2024-04-10 → null
    
    ── Category distribution ──
    category
    technology       28
    politics         10
    general           4
    entertainment     3
    business          2
    health            1
    sports            1
    science           1
    
    ── Sentiment distribution ──
    sentiment
    neutral     30
    negative    18
    positive     2
    
    ── Articles per source ──
    source
    BBC Top Stories       10
    TechCrunch            10
    The Guardian Tech     10
    The Guardian World    10
    BBC Technology         9
    Al Jazeera             1
    
    ── Null counts ──
    article_id       0
    url              0
    source           0
    title            0
    description      0
    author          22
    tags             0
    category         0
    sentiment        0
    publish_date     0
    top_image        0
    scraped_at       0
    

Download files from Colab



```python
from google.colab import files

files.download("news_dataset.csv")
files.download("news_dataset.json")
files.download("news_dataset.db")
```


    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>



    <IPython.core.display.Javascript object>

