<a href="https://colab.research.google.com/github/Yash-Yelave/Global_Gatway_RS/blob/main/100news_Scrapping.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

Install Dependencies


```python
!pip install groq newspaper3k feedparser requests beautifulsoup4 pandas pydantic lxml_html_clean -q
```

      Preparing metadata (setup.py) ... [?25l[?25hdone
    [2K     [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m7.4/7.4 MB[0m [31m35.0 MB/s[0m eta [36m0:00:00[0m
    [?25h  Preparing metadata (setup.py) ... [?25l[?25hdone
      Preparing metadata (setup.py) ... [?25l[?25hdone
      Preparing metadata (setup.py) ... [?25l[?25hdone
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m142.3/142.3 kB[0m [31m11.2 MB/s[0m eta [36m0:00:00[0m
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m211.1/211.1 kB[0m [31m16.7 MB/s[0m eta [36m0:00:00[0m
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m81.5/81.5 kB[0m [31m6.6 MB/s[0m eta [36m0:00:00[0m
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m105.9/105.9 kB[0m [31m8.9 MB/s[0m eta [36m0:00:00[0m
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

client = Groq(api_key=userdata.get("GROQ_API_KEY_1"))

GROQ_MODEL          = "llama-3.1-8b-instant"
MAX_TOKENS_IN       = 2000
RATE_LIMIT_SEC      = 2.5
MAX_RETRIES         = 3
RETRY_WAIT_SEC      = 65        # wait 65s when quota is hit (resets per minute)
ARTICLES_PER_FEED   = 5
CATEGORIES          = [
    "technology", "politics", "sports", "business",
    "health", "science", "entertainment", "general",
    "finance", "travel", "culture", "environment"
]
```

100 RSS feed sources (UAE + China heavy)


```python
RSS_FEEDS = {

    # ── UAE / Gulf / Arabic ──────────────────────────────────────────────────
    "Khaleej Times"              : "https://www.khaleejtimes.com/rss",
    "Gulf News"                  : "https://gulfnews.com/rss",
    "The National UAE"           : "https://www.thenationalnews.com/rss",
    "Gulf Business"              : "https://gulfbusiness.com/feed/",
    "Emirates 24/7"              : "https://www.emirates247.com/rss",
    "Arabian Business"           : "https://www.arabianbusiness.com/rss",
    "Al Arabiya English"         : "https://english.alarabiya.net/tools/rss",
    "Al Jazeera English"         : "https://www.aljazeera.com/xml/rss/all.xml",
    "Zawya UAE"                  : "https://www.zawya.com/rss/uae/",
    "Dubai Eye News"             : "https://www.dubaieye1038.com/feed/",
    "Al Khaleej (Arabic)"        : "https://www.alkhaleej.ae/rss.xml",
    "Al Bayan (Arabic)"          : "https://albayan.ae/rss",
    "WAM UAE State News"         : "https://wam.ae/rss.xml",
    "Time Out Dubai"             : "https://www.timeoutdubai.com/rss",
    "What's On Dubai"            : "https://whatson.ae/feed/",
    "Construction Week Online"   : "https://www.constructionweekonline.com/rss",
    "MEED Middle East"           : "https://www.meed.com/rss/",
    "Arab News"                  : "https://www.arabnews.com/rss.xml",
    "Saudi Gazette"              : "https://saudigazette.com.sa/rss",
    "Oman Observer"              : "https://www.omanobserver.om/feed/",
    "Kuwait Times"               : "https://www.kuwaittimes.com/feed/",
    "Bahrain News Agency"        : "https://www.bna.bh/rss.xml",
    "Qatar Tribune"              : "https://www.qatar-tribune.com/rss",
    "Middle East Eye"            : "https://www.middleeasteye.net/rss",
    "Roya News Jordan"           : "https://en.royanews.tv/rss.xml",

    # ── China / Hong Kong / Asia ─────────────────────────────────────────────
    "China Daily"                : "https://www.chinadaily.com.cn/rss/china_rss.xml",
    "China Daily Business"       : "https://www.chinadaily.com.cn/rss/bizChina_rss.xml",
    "CGTN World"                 : "https://www.cgtn.com/subscribe/rss/section/world.xml",
    "CGTN Business"              : "https://www.cgtn.com/subscribe/rss/section/business.xml",
    "CGTN Science"               : "https://www.cgtn.com/subscribe/rss/section/sci-tech.xml",
    "Xinhua Top News"            : "https://www.xinhuanet.com/english/rss/worldrss.xml",
    "Xinhua China"               : "https://www.xinhuanet.com/english/rss/chinarss.xml",
    "South China Morning Post"   : "https://www.scmp.com/rss/2/feed",
    "SCMP Business"              : "https://www.scmp.com/rss/92/feed",
    "SCMP Tech"                  : "https://www.scmp.com/rss/36/feed",
    "Hong Kong Free Press"       : "https://hongkongfp.com/feed/",
    "Caixin Global"              : "https://www.caixinglobal.com/rss/index.xml",
    "Sixth Tone China"           : "https://www.sixthtone.com/rss",
    "The Diplomat Asia"          : "https://thediplomat.com/feed/",
    "Asia Times"                 : "https://asiatimes.com/feed/",
    "Nikkei Asia"                : "https://asia.nikkei.com/rss/feed/nar",
    "Japan Times"                : "https://www.japantimes.co.jp/feed/",
    "Korea Herald"               : "http://www.koreaherald.com/rss/050000000000.xml",
    "Times of India"             : "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "Straits Times Singapore"    : "https://www.straitstimes.com/global/rss.xml",

    # ── International / Global ───────────────────────────────────────────────
    "BBC Top Stories"            : "http://feeds.bbci.co.uk/news/rss.xml",
    "BBC World"                  : "http://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC Technology"             : "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "BBC Business"               : "http://feeds.bbci.co.uk/news/business/rss.xml",
    "BBC Health"                 : "http://feeds.bbci.co.uk/news/health/rss.xml",
    "Reuters Top News"           : "https://feeds.reuters.com/reuters/topNews",
    "Reuters World"              : "https://feeds.reuters.com/Reuters/worldNews",
    "Reuters Business"           : "https://feeds.reuters.com/reuters/businessNews",
    "Reuters Technology"         : "https://feeds.reuters.com/reuters/technologyNews",
    "AP Top News"                : "https://feeds.apnews.com/rss/apf-topnews",
    "AP World"                   : "https://feeds.apnews.com/rss/apf-WorldNews",
    "AP Business"                : "https://feeds.apnews.com/rss/apf-business",
    "The Guardian World"         : "https://www.theguardian.com/world/rss",
    "The Guardian Tech"          : "https://www.theguardian.com/uk/technology/rss",
    "The Guardian Business"      : "https://www.theguardian.com/business/rss",
    "The Guardian Environment"   : "https://www.theguardian.com/environment/rss",

    # ── Technology ───────────────────────────────────────────────────────────
    "TechCrunch"                 : "https://techcrunch.com/feed/",
    "TechCrunch AI"              : "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge"                  : "https://www.theverge.com/rss/index.xml",
    "Wired"                      : "https://www.wired.com/feed/rss",
    "Ars Technica"               : "http://feeds.arstechnica.com/arstechnica/index",
    "MIT Tech Review"            : "https://www.technologyreview.com/feed/",
    "VentureBeat"                : "https://venturebeat.com/feed/",
    "ZDNet"                      : "https://www.zdnet.com/news/rss.xml",
    "Engadget"                   : "https://www.engadget.com/rss.xml",
    "Mashable Tech"              : "https://mashable.com/feeds/rss/tech",

    # ── Business / Finance ───────────────────────────────────────────────────
    "Bloomberg Technology"       : "https://feeds.bloomberg.com/technology/news.rss",
    "CNBC World"                 : "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    "CNBC Finance"               : "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "Financial Times World"      : "https://www.ft.com/world?format=rss",
    "Forbes Business"            : "https://www.forbes.com/business/feed/",
    "Forbes Tech"                : "https://www.forbes.com/technology/feed/",
    "Business Insider"           : "https://feeds.businessinsider.com/custom/all",
    "MarketWatch"                : "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Investopedia"               : "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline",
    "CoinDesk Crypto"            : "https://www.coindesk.com/arc/outboundfeeds/rss/",

    # ── Health & Science ─────────────────────────────────────────────────────
    "WHO News"                   : "https://www.who.int/rss-feeds/news-english.xml",
    "Harvard Health"             : "https://www.health.harvard.edu/blog/feed",
    "Science Daily"              : "https://www.sciencedaily.com/rss/all.xml",
    "Nature News"                : "https://www.nature.com/nature.rss",
    "NASA Breaking News"         : "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "New Scientist"              : "https://www.newscientist.com/feed/home/",
    "Medical News Today"         : "https://www.medicalnewstoday.com/rss",

    # ── Sports ───────────────────────────────────────────────────────────────
    "ESPN Headlines"             : "https://www.espn.com/espn/rss/news",
    "BBC Sport"                  : "http://feeds.bbci.co.uk/sport/rss.xml",
    "Sky Sports"                 : "https://www.skysports.com/rss/12040",
    "Goal.com Football"          : "https://www.goal.com/feeds/en/news",
    "Sports Illustrated"         : "https://www.si.com/rss/si_topstories.rss",

    # ── Environment / Travel ─────────────────────────────────────────────────
    "National Geographic"        : "https://www.nationalgeographic.com/news/rss",
    "BBC Travel"                 : "http://feeds.bbci.co.uk/travel/rss.xml",
    "Lonely Planet"              : "https://www.lonelyplanet.com/news/feed",
    "CNN Travel"                 : "http://rss.cnn.com/rss/edition_travel.rss",
    "World Wildlife Fund"        : "https://www.worldwildlife.org/magazine/rss",

    # ── Entertainment / Culture ──────────────────────────────────────────────
    "Variety"                    : "https://variety.com/feed/",
    "Hollywood Reporter"         : "https://www.hollywoodreporter.com/feed/",
    "Rolling Stone"              : "https://www.rollingstone.com/feed/",
    "Pitchfork Music"            : "https://pitchfork.com/rss/news/",
    "Deadline Hollywood"         : "https://deadline.com/feed/",
}

print(f"Total feeds configured: {len(RSS_FEEDS)}")
```

    Total feeds configured: 103
    

RSS URL fetcher


```python
def fetch_rss_urls(feeds: dict, max_per_feed: int = ARTICLES_PER_FEED) -> list[dict]:
    articles  = []
    failed    = []
    seen_urls = set()

    for source_name, feed_url in feeds.items():
        try:
            feed    = feedparser.parse(feed_url)
            entries = feed.entries[:max_per_feed]
            count   = 0

            for entry in entries:
                url = entry.get("link", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                articles.append({
                    "source"   : source_name,
                    "url"      : url,
                    "rss_title": entry.get("title", ""),
                    "published": entry.get("published", ""),
                })
                count += 1

            status = f"✓ {count} articles" if count else "⚠ 0 articles (feed may be empty)"
            print(f"  {status} — {source_name}")

        except Exception as e:
            failed.append(source_name)
            print(f"  ✗ FAILED — {source_name}: {e}")

    print(f"\nRSS fetch done. {len(articles)} URLs | {len(failed)} feeds failed.")
    if failed:
        print("Failed feeds:", failed)

    return articles

print("Fetching all RSS feeds...\n")
raw_urls = fetch_rss_urls(RSS_FEEDS, max_per_feed=ARTICLES_PER_FEED)
print(f"\nTotal URLs to process: {len(raw_urls)}")
```

    Fetching all RSS feeds...
    
      ⚠ 0 articles (feed may be empty) — Khaleej Times
      ⚠ 0 articles (feed may be empty) — Gulf News
      ⚠ 0 articles (feed may be empty) — The National UAE
      ⚠ 0 articles (feed may be empty) — Gulf Business
      ⚠ 0 articles (feed may be empty) — Emirates 24/7
      ⚠ 0 articles (feed may be empty) — Arabian Business
      ⚠ 0 articles (feed may be empty) — Al Arabiya English
      ✓ 5 articles — Al Jazeera English
      ⚠ 0 articles (feed may be empty) — Zawya UAE
      ⚠ 0 articles (feed may be empty) — Dubai Eye News
      ⚠ 0 articles (feed may be empty) — Al Khaleej (Arabic)
      ⚠ 0 articles (feed may be empty) — Al Bayan (Arabic)
      ⚠ 0 articles (feed may be empty) — WAM UAE State News
      ⚠ 0 articles (feed may be empty) — Time Out Dubai
      ✓ 5 articles — What's On Dubai
      ⚠ 0 articles (feed may be empty) — Construction Week Online
      ⚠ 0 articles (feed may be empty) — MEED Middle East
      ⚠ 0 articles (feed may be empty) — Arab News
      ⚠ 0 articles (feed may be empty) — Saudi Gazette
      ⚠ 0 articles (feed may be empty) — Oman Observer
      ⚠ 0 articles (feed may be empty) — Kuwait Times
      ⚠ 0 articles (feed may be empty) — Bahrain News Agency
      ⚠ 0 articles (feed may be empty) — Qatar Tribune
      ✓ 5 articles — Middle East Eye
      ⚠ 0 articles (feed may be empty) — Roya News Jordan
      ✓ 3 articles — China Daily
      ⚠ 0 articles (feed may be empty) — China Daily Business
      ✓ 5 articles — CGTN World
      ✓ 5 articles — CGTN Business
      ⚠ 0 articles (feed may be empty) — CGTN Science
      ✓ 5 articles — Xinhua Top News
      ✓ 5 articles — Xinhua China
      ✓ 5 articles — South China Morning Post
      ✓ 3 articles — SCMP Business
      ✓ 4 articles — SCMP Tech
      ✓ 5 articles — Hong Kong Free Press
      ⚠ 0 articles (feed may be empty) — Caixin Global
      ✓ 5 articles — Sixth Tone China
      ✓ 5 articles — The Diplomat Asia
      ✓ 5 articles — Asia Times
      ✓ 5 articles — Nikkei Asia
      ✓ 5 articles — Japan Times
      ⚠ 0 articles (feed may be empty) — Korea Herald
      ✓ 5 articles — Times of India
      ⚠ 0 articles (feed may be empty) — Straits Times Singapore
      ✓ 5 articles — BBC Top Stories
      ✓ 5 articles — BBC World
      ✓ 5 articles — BBC Technology
      ✓ 3 articles — BBC Business
      ✓ 4 articles — BBC Health
      ⚠ 0 articles (feed may be empty) — Reuters Top News
      ⚠ 0 articles (feed may be empty) — Reuters World
      ⚠ 0 articles (feed may be empty) — Reuters Business
      ⚠ 0 articles (feed may be empty) — Reuters Technology
      ⚠ 0 articles (feed may be empty) — AP Top News
      ⚠ 0 articles (feed may be empty) — AP World
      ⚠ 0 articles (feed may be empty) — AP Business
      ✓ 5 articles — The Guardian World
      ✓ 5 articles — The Guardian Tech
      ✓ 4 articles — The Guardian Business
      ✓ 5 articles — The Guardian Environment
      ✓ 5 articles — TechCrunch
      ✓ 5 articles — TechCrunch AI
      ✓ 5 articles — The Verge
      ✓ 5 articles — Wired
      ✓ 5 articles — Ars Technica
      ✓ 5 articles — MIT Tech Review
      ✓ 5 articles — VentureBeat
      ✓ 5 articles — ZDNet
      ✓ 5 articles — Engadget
      ✓ 5 articles — Mashable Tech
      ✓ 5 articles — Bloomberg Technology
      ✓ 5 articles — CNBC World
      ✓ 4 articles — CNBC Finance
      ✓ 5 articles — Financial Times World
      ✓ 5 articles — Forbes Business
      ⚠ 0 articles (feed may be empty) — Forbes Tech
      ✓ 5 articles — Business Insider
      ✓ 5 articles — MarketWatch
      ⚠ 0 articles (feed may be empty) — Investopedia
      ✓ 5 articles — CoinDesk Crypto
      ✓ 5 articles — WHO News
      ⚠ 0 articles (feed may be empty) — Harvard Health
      ✓ 5 articles — Science Daily
      ✓ 5 articles — Nature News
      ✓ 5 articles — NASA Breaking News
      ✓ 5 articles — New Scientist
      ⚠ 0 articles (feed may be empty) — Medical News Today
      ✓ 5 articles — ESPN Headlines
      ✓ 5 articles — BBC Sport
      ✓ 5 articles — Sky Sports
      ⚠ 0 articles (feed may be empty) — Goal.com Football
      ⚠ 0 articles (feed may be empty) — Sports Illustrated
      ⚠ 0 articles (feed may be empty) — National Geographic
      ⚠ 0 articles (feed may be empty) — BBC Travel
      ⚠ 0 articles (feed may be empty) — Lonely Planet
      ✓ 5 articles — CNN Travel
      ⚠ 0 articles (feed may be empty) — World Wildlife Fund
      ✓ 5 articles — Variety
      ✓ 5 articles — Hollywood Reporter
      ✓ 5 articles — Rolling Stone
      ✓ 5 articles — Pitchfork Music
      ✓ 5 articles — Deadline Hollywood
    
    RSS fetch done. 285 URLs | 0 feeds failed.
    
    Total URLs to process: 285
    

Article scraper


```python
def scrape_article(url: str) -> dict | None:
    try:
        art = Article(url, fetch_images=False, request_timeout=12)
        art.download()
        art.parse()

        meta_desc = ""
        try:
            soup = BeautifulSoup(art.html or "", "html.parser")
            tag  = (soup.find("meta", attrs={"name": "description"}) or
                    soup.find("meta", attrs={"property": "og:description"}))
            if tag:
                meta_desc = tag.get("content", "")
        except Exception:
            pass

        return {
            "url"           : url,
            "scraped_title" : art.title or "",
            "raw_text"      : art.text or "",
            "scraped_author": ", ".join(art.authors) if art.authors else "",
            "scraped_date"  : str(art.publish_date) if art.publish_date else "",
            "meta_desc"     : meta_desc,
            "top_image"     : art.top_image or "",
        }
    except Exception as e:
        print(f"    ✗ Scrape failed: {e}")
        return None
```

Groq extraction with full quota handling


```python
EXTRACTION_PROMPT = """
You are a structured data extractor for a news recommendation system.

Given the raw text of a news article, return ONLY a valid JSON object.
No explanation, no markdown fences, no extra text — just the JSON.

JSON schema:
{{
  "title"       : "clean headline (string)",
  "description" : "2-3 sentence plain-English summary written in your own words",
  "author"      : "author full name or null",
  "tags"        : ["keyword1", "keyword2", "keyword3"],
  "category"    : "one of: technology | politics | sports | business | health | science | entertainment | finance | travel | culture | environment | general",
  "sentiment"   : "positive | neutral | negative",
  "publish_date": "YYYY-MM-DD or null",
  "language"    : "en | ar | zh | other"
}}

Rules:
- tags: 3 to 5 short lowercase keywords.
- description: your own summary, never copied text.
- If a field cannot be determined use null.
- Return ONLY the JSON object.

Article title hint: {title_hint}
Article text:
{article_text}
""".strip()


def extract_with_groq(scraped: dict, stats: dict) -> dict | None:
    """
    Call Groq with retry logic and quota exhaustion handling.
    stats dict is mutated in-place to track API usage.
    """
    raw_text = scraped.get("raw_text", "").strip()
    if not raw_text:
        raw_text = scraped.get("meta_desc", "").strip()
    if not raw_text:
        print("    ⚠ No text to extract from — skipping")
        return None

    truncated = raw_text[:MAX_TOKENS_IN * 4]
    prompt    = EXTRACTION_PROMPT.format(
        title_hint   = scraped.get("scraped_title", ""),
        article_text = truncated,
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model       = GROQ_MODEL,
                messages    = [{"role": "user", "content": prompt}],
                max_tokens  = 512,
                temperature = 0.1,
            )
            stats["api_calls"] += 1
            raw_json = response.choices[0].message.content.strip()

            # Strip accidental markdown fences
            if raw_json.startswith("```"):
                raw_json = raw_json.split("```")[1]
                if raw_json.startswith("json"):
                    raw_json = raw_json[4:]

            parsed = json.loads(raw_json)
            return parsed

        except Exception as e:
            err_str = str(e).lower()

            # ── Quota / rate limit hit ────────────────────────────────────────
            if any(kw in err_str for kw in ["rate_limit", "rate limit", "429",
                                             "quota", "too many requests",
                                             "tokens per minute",
                                             "requests per minute"]):
                stats["quota_hits"] += 1
                print(f"\n{'='*60}")
                print(f"  ⚠  GROQ QUOTA HIT (attempt {attempt}/{MAX_RETRIES})")
                print(f"  API calls so far : {stats['api_calls']}")
                print(f"  Articles saved   : {stats['articles_saved']}")
                print(f"  Waiting {RETRY_WAIT_SEC}s for quota reset...")
                print(f"{'='*60}\n")
                time.sleep(RETRY_WAIT_SEC)
                continue

            # ── JSON parse error ──────────────────────────────────────────────
            elif "json" in err_str or isinstance(e, json.JSONDecodeError):
                print(f"    ✗ JSON parse error (attempt {attempt}): {e}")
                if attempt == MAX_RETRIES:
                    return None
                time.sleep(2)
                continue

            # ── Auth error — hard stop ────────────────────────────────────────
            elif any(kw in err_str for kw in ["authentication", "api_key",
                                               "unauthorized", "401"]):
                print("\n✗ GROQ AUTH ERROR — check your API key in Colab Secrets.")
                raise SystemExit("Invalid Groq API key.")

            # ── Generic error ─────────────────────────────────────────────────
            else:
                print(f"    ✗ Groq error (attempt {attempt}): {e}")
                if attempt == MAX_RETRIES:
                    return None
                time.sleep(3)
                continue

    return None
```

Pydantic schema



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
    language    : Optional[str]
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
    try:
        return NewsArticle(
            article_id  = build_article_id(rss_meta["url"]),
            url         = rss_meta["url"],
            source      = rss_meta["source"],
            title       = (extracted.get("title") or
                           scraped.get("scraped_title") or
                           rss_meta.get("rss_title", "")),
            description = extracted.get("description", ""),
            author      = (extracted.get("author") or
                           scraped.get("scraped_author") or None),
            tags        = extracted.get("tags", []),
            category    = extracted.get("category", "general"),
            sentiment   = extracted.get("sentiment", "neutral"),
            publish_date= (extracted.get("publish_date") or
                           scraped.get("scraped_date") or
                           rss_meta.get("published") or None),
            language    = extracted.get("language", "en"),
            top_image   = scraped.get("top_image") or None,
            scraped_at  = datetime.utcnow().isoformat(),
        )
    except Exception as e:
        print(f"    ✗ Validation error: {e}")
        return None
```

Save helper


```python
def save_outputs(articles: list[dict], prefix: str = "news_dataset") -> pd.DataFrame:
    df = pd.DataFrame(articles)
    if df.empty:
        print("⚠ No articles to save yet.")
        return df

    # CSV
    csv_path = f"{prefix}.csv"
    df.to_csv(csv_path, index=False)

    # JSON
    json_path = f"{prefix}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    # SQLite
    db_path  = f"{prefix}.db"
    conn     = sqlite3.connect(db_path)
    df_sql   = df.copy()
    df_sql["tags"] = df_sql["tags"].apply(json.dumps)
    df_sql.to_sql("articles", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    print(f"  💾 Saved {len(df)} articles → {csv_path} | {json_path} | {db_path}")
    return df
```

Main pipeline


```python
def run_pipeline(raw_urls: list[dict], max_articles: int = 500,
                 autosave_every: int = 25) -> list[dict]:
    """
    Full pipeline with:
      - Groq quota retry handling
      - Live progress reporting
      - Auto-save every N articles so you never lose work
      - Final summary on completion
    """
    results   = []
    seen_urls = set()
    processed = 0
    skipped   = 0

    stats = {
        "api_calls"    : 0,
        "quota_hits"   : 0,
        "articles_saved": 0,
    }

    total_urls = min(len(raw_urls), max_articles * 3)  # rough upper bound
    print(f"Starting pipeline — target: {max_articles} articles from {len(raw_urls)} URLs\n")
    print("=" * 65)

    for idx, item in enumerate(raw_urls):
        if processed >= max_articles:
            break

        url = item["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)

        print(f"\n[{processed + 1}/{max_articles}] Source: {item['source']}")
        print(f"  URL: {url[:75]}")

        # ── Step 1: Scrape ─────────────────────────────────────────────────
        scraped = scrape_article(url)
        if not scraped:
            skipped += 1
            print("  → Scrape failed, skipping.")
            continue

        # ── Step 2: Groq extraction ────────────────────────────────────────
        extracted = extract_with_groq(scraped, stats)
        if not extracted:
            skipped += 1
            print("  → Groq extraction failed, skipping.")
            continue

        # ── Step 3: Validate & merge ───────────────────────────────────────
        article = validate_and_merge(item, scraped, extracted)
        if not article:
            skipped += 1
            print("  → Validation failed, skipping.")
            continue

        results.append(article.model_dump())
        processed            += 1
        stats["articles_saved"] = processed

        print(f"  ✓ [{article.language}] [{article.category}] [{article.sentiment}]")
        print(f"    Title : {article.title[:70]}")
        print(f"    Author: {article.author or 'N/A'} | Tags: {', '.join(article.tags)}")

        # ── Auto-save checkpoint ───────────────────────────────────────────
        if processed % autosave_every == 0:
            print(f"\n  ── Auto-save checkpoint at {processed} articles ──")
            save_outputs(results)

        time.sleep(RATE_LIMIT_SEC)

    # ── Final save ─────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("PIPELINE COMPLETE")
    print(f"  Articles collected : {processed}")
    print(f"  URLs skipped       : {skipped}")
    print(f"  Groq API calls     : {stats['api_calls']}")
    print(f"  Quota hits         : {stats['quota_hits']}")
    print("=" * 65)
    save_outputs(results)

    return results


# ── Run ─────────────────────────────────────────────────────────────────────
# max_articles = 500 targets 5 per feed across 100 feeds.
# Lower it to 50-100 first to do a test run.
clean_articles = run_pipeline(raw_urls, max_articles=500, autosave_every=25)
```

    Starting pipeline — target: 500 articles from 285 URLs
    
    =================================================================
    
    [1/500] Source: Al Jazeera English
      URL: https://www.aljazeera.com/news/2026/4/21/iran-us-war-four-scenarios-for-wha
    

    /tmp/ipykernel_19745/119334936.py:63: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
      scraped_at  = datetime.utcnow().isoformat(),
    

      ✓ [en] [politics] [neutral]
        Title : Iran-US war: Four scenarios for what’s next as talks stumble
        Author: Yashraj Sharma | Tags: iran, us, war, talks, ceasefire
    
    [2/500] Source: Al Jazeera English
      URL: https://www.aljazeera.com/video/doha-debates/2026/4/21/are-we-heading-into-
      ✓ [en] [technology] [neutral]
        Title : Are we heading into a world divided by AI tribes?
        Author: N/A | Tags: ai, society, technology
    
    [3/500] Source: Al Jazeera English
      URL: https://www.aljazeera.com/news/2026/4/21/what-was-the-iran-nuclear-deal-tru
      ✓ [en] [politics] [neutral]
        Title : What was the Iran nuclear deal Trump dumped in search of ‘better’ term
        Author: Usaid Siddiqui | Tags: iran, nuclear, deal, trump, politics
    
    [4/500] Source: Al Jazeera English
      URL: https://www.aljazeera.com/video/newsfeed/2026/4/21/mass-trial-for-nearly-50
      ✓ [en] [politics] [neutral]
        Title : mass trial for nearly 500 alleged gang members in el salvador
        Author: N/A | Tags: mass trial, el salvador, gang members
    
    [5/500] Source: Al Jazeera English
      URL: https://www.aljazeera.com/video/featured-documentaries/2026/4/21/strait-of-
      ✓ [en] [politics] [neutral]
        Title : strait of hormuz: how a threat became a playbook
        Author: N/A | Tags: strait of hormuz, iran, us
    
    [6/500] Source: What's On Dubai
      URL: https://whatson.ae/2026/04/smallest-library-for-world-book-day-bookends-jul
      ✓ [en] [general] [positive]
        Title : The Smallest Library in Dubai opens this week – but only for a limited
        Author: Aarti Saundalkar | Tags: dubai, library, reading
    
    [7/500] Source: What's On Dubai
      URL: https://whatson.ae/2026/04/this-is-when-summer-officially-begins-in-the-uae
      ✓ [en] [general] [neutral]
        Title : when summer officially begins in the UAE
        Author: Aarti Saundalkar | Tags: summer, uae, weather, solstice
    
    [8/500] Source: What's On Dubai
      URL: https://whatson.ae/2026/04/short-flights-from-dubai-within-4-hours-for-your
      ✓ [en] [travel] [positive]
        Title : Short flights from Dubai within 4 hours for your next getaway
        Author: Lana Du | Tags: dubai, short flights, getaway, sri lanka, georgia
    
    [9/500] Source: What's On Dubai
      URL: https://whatson.ae/2026/04/dine-out-for-less-dubais-top-restaurants-serving
      ✓ [en] [entertainment] [positive]
        Title : Dine out for less: Dubai’s top restaurants serving great deals right n
        Author: Alice Holtham-Pargin | Tags: dubai, restaurants, deals, food, drinks
    
    [10/500] Source: What's On Dubai
      URL: https://whatson.ae/2026/04/flydubai-to-launch-daily-bangkok-flights-from-ju
      ✓ [en] [travel] [neutral]
        Title : flydubai to launch daily Bangkok flights from July 1
        Author: Aarti Saundalkar | Tags: flydubai, bangkok, flights, dubai, travel
    
    [11/500] Source: Middle East Eye
      URL: https://www.middleeasteye.net/live-blog/live-blog-update/trump-says-he-does
      ✓ [en] [politics] [negative]
        Title : trump says he does not want to extend ceasefire with iran
        Author: null | Tags: trump, iran, ceasefire
    
    [12/500] Source: Middle East Eye
      URL: https://www.middleeasteye.net/live-blog/live-blog-update/shipping-traffic-t
      ✓ [en] [politics] [neutral]
        Title : shipping traffic through hormuz remains mostly halted
        Author: N/A | Tags: shipping, hormuz, iran, us, blockade
    
    [13/500] Source: Middle East Eye
      URL: https://www.middleeasteye.net/live-blog/live-blog-update/eu-warn-against-ea
      ✓ [en] [politics] [neutral]
        Title : eu to warn against early nuclear exits in effort to address energy cri
        Author: N/A | Tags: energy, nuclear, eu
    
    [14/500] Source: Middle East Eye
      URL: https://www.middleeasteye.net/live-blog/live-blog-update/trumps-board-peace
      ✓ [en] [politics] [neutral]
        Title : trump's 'board of peace' held talks with dp world over gaza reconstruc
        Author: N/A | Tags: trump, gaza, dp world, reconstruction
    
    [15/500] Source: Middle East Eye
      URL: https://www.middleeasteye.net/news/palestinian-boy-killed-israeli-ministers
      ✓ [en] [general] [negative]
        Title : Client Challenge
        Author: N/A | Tags: browser, issue, challenge
    
    [16/500] Source: China Daily
      URL: http://www.chinadaily.com.cn/a/201712/12/WS5a2f29d4a3108bc8c6721a30.html
      ✓ [en] [general] [neutral]
        Title : Education, health fees among key concerns
        Author: N/A | Tags: education, health, fees, china
    
    [17/500] Source: China Daily
      URL: http://www.chinadaily.com.cn/a/201712/12/WS5a2f2701a3108bc8c6721a16.html
      ✓ [en] [environment] [positive]
        Title : International group praises green revival
        Author: null | Tags: china, environment, pollution, green
    
    [18/500] Source: China Daily
      URL: http://www.chinadaily.com.cn/a/201712/12/WS5a2f25bda3108bc8c6721a0b.html
      ✓ [en] [politics] [neutral]
        Title : china and russia drill for potential missile warfare
        Author: zhangzhihao | Tags: china, russia, missile, warfare, defense
    
    [19/500] Source: CGTN World
      URL: https://news.cgtn.com/news/2026-04-13/Wang-Yi-Blockade-of-Strait-of-Hormuz-
      ✓ [en] [politics] [neutral]
        Title : wang yi: blockade of strait of hormuz not in common interests
        Author: N/A | Tags: wang yi, strait of hormuz, china
    
    [20/500] Source: CGTN World
      URL: https://news.cgtn.com/news/2026-04-14/Vietnam-s-top-leader-To-Lam-arrives-i
      ✓ [en] [politics] [neutral]
        Title : vietnam's top leader to lam arrives in beijing for state visit
        Author: N/A | Tags: vietnam, china, diplomacy
    
    [21/500] Source: CGTN World
      URL: https://newsus.cgtn.com/news/2026-04-12/Latin-America-feeling-the-fallout-o
      ✓ [en] [politics] [neutral]
        Title : Latin America feeling the fallout of Middle East conflict
        Author: Alasdair Baverstock | Tags: middle east, latin america, conflict
    
    [22/500] Source: CGTN World
      URL: https://news.cgtn.com/news/2026-04-13/news-1MjuPTZM544/p.html?UTM_Source=cg
      ✓ [en] [politics] [neutral]
        Title : us military to enforce blockade in gulf of oman, arabian sea
        Author: N/A | Tags: us military, blockade, gulf of oman
    
    [23/500] Source: CGTN World
      URL: https://newsaf.cgtn.com/news/2026-04-14/Nigeria-eyes-IMF-World-Bank-support
      ✓ [en] [politics] [neutral]
        Title : nigeria eyes imf, world bank support amidst fuel price surge
        Author: N/A | Tags: nigeria, imf, world bank, fuel price
    
    [24/500] Source: CGTN Business
      URL: https://news.cgtn.com/news/2026-04-04/Beihai-Park-is-brimming-with-spring-v
      ✓ [en] [general] [positive]
        Title : beihai park is brimming with spring vitality
        Author: N/A | Tags: beihai park, spring, beijing
    
    [25/500] Source: CGTN Business
      URL: https://news.cgtn.com/news/2026-04-12/Service-sector-powers-China-s-new-eng
      ✓ [en] [business] [neutral]
        Title : Service sector powers China's new engine of economic growth
        Author: N/A | Tags: china, economy, growth
    
      ── Auto-save checkpoint at 25 articles ──
      💾 Saved 25 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    
    [26/500] Source: CGTN Business
      URL: https://newsus.cgtn.com/news/2026-04-01/Iran-conflict-regulations-spike-gas
      ✓ [en] [politics] [neutral]
        Title : iran conflict, regulations spike gas prices in california
        Author: Ediz Tiyansan | Tags: iran, conflict, gas, prices
    
    [27/500] Source: CGTN Business
      URL: https://news.cgtn.com/news/2026-03-31/Beijing-in-full-bloom-as-spring-comes
      ✓ [en] [general] [neutral]
        Title : beijing in full bloom as spring comes early
        Author: N/A | Tags: beijing, spring, flowers
    
    [28/500] Source: CGTN Business
      URL: https://news.cgtn.com/news/2026-04-04/Gulf-oil-exporters-seek-alternative-r
      ✓ [en] [business] [neutral]
        Title : gulf oil exporters seek alternative routes as strait of hormuz disrupt
        Author: Zong Shukang Cgtn | Tags: oil, gulf, disruptions
    
    [29/500] Source: Xinhua Top News
      URL: http://www.xinhuanet.com/english/world/2018-01/24/c_136919909.htm
      ✓ [en] [politics] [neutral]
        Title : palestinians clash with israeli soldiers after protest against pence v
        Author: zhou xin | Tags: palestinians, israel, pence
    
    [30/500] Source: Xinhua Top News
      URL: http://www.xinhuanet.com/english/2018-01/03/c_136868968.htm
      ✓ [en] [politics] [negative]
        Title : u.s. failure to appoint australian ambassador 'diplomatic insult': for
        Author: null | Tags: diplomatic insult, australian ambassador, u.s. administration
    
    [31/500] Source: Xinhua Top News
      URL: http://www.xinhuanet.com/english/2017-10/28/c_136711043.htm
      ✓ [en] [general] [neutral]
        Title : Speaker of Hungarian Parliament addresses in Budapest
        Author: N/A | Tags: hungary, parliament, budapest
    
    [32/500] Source: Xinhua Top News
      URL: http://www.xinhuanet.com/english/2017-10/23/c_136699146.htm
      ✓ [en] [general] [negative]
        Title : Typhoon Lan lashes central Japan, killing 2 and disrupting transport s
        Author: Zhou Xin | Tags: typhoon, japan, transportation, weather, disaster
    
    [33/500] Source: Xinhua Top News
      URL: http://www.xinhuanet.com/english/2017-10/13/c_136677613.htm
      ✓ [en] [politics] [negative]
        Title : U.S. decision to withdraw from UNESCO triggers calls for multilaterali
        Author: N/A | Tags: united-states, unesco, multilateralism
    
    [34/500] Source: Xinhua China
      URL: http://www.xinhuanet.com/english/2017-05/07/c_136263471.htm
      ✓ [en] [technology] [neutral]
        Title : China Focus: Beijing firms bring tech to Belt and Road countries
        Author: N/A | Tags: china, belt and road, technology, innovation
    
    [35/500] Source: Xinhua China
      URL: http://www.xinhuanet.com/english/2017-04/24/c_136232199.htm
      ✓ [en] [politics] [neutral]
        Title : Xi, Trump discuss ties, Korean Peninsula situation over phone
        Author: N/A | Tags: xi, trump, korean peninsula, china, united states
    
    [36/500] Source: Xinhua China
      URL: http://www.xinhuanet.com/english/2017-04/21/c_136224369.htm
      ✓ [en] [business] [neutral]
        Title : Thai student dreams of selling rice to China
        Author: Mu Xuequan | Tags: thailand, china, rice, trade, business
    
    [37/500] Source: Xinhua China
      URL: http://www.xinhuanet.com/english/2017-04/20/c_136224230.htm
      ✓ [en] [business] [neutral]
        Title : Hebei promises dedication in building Xiongan New Area
        Author: N/A | Tags: xiongan, hebei, china, new-area, economy
    
    [38/500] Source: Xinhua China
      URL: http://www.xinhuanet.com/english/2017-04/08/c_136191678.htm
      ✓ [en] [politics] [neutral]
        Title : Xi, Trump pledge to expand mutually beneficial cooperation, manage dif
        Author: Mengjie | Tags: xi, trump, china, us, cooperation
    
    [39/500] Source: South China Morning Post
      URL: https://www.scmp.com/news/hong-kong/hong-kong-economy/article/3350914/first
      ✓ [en] [technology] [neutral]
        Title : first ai driverless trucks deployed to tackle hong kong port labour sh
        Author: Ambrose Li | Tags: hong kong, driverless trucks, labour shortage
    
    [40/500] Source: South China Morning Post
      URL: https://www.scmp.com/news/hong-kong/society/article/3350910/tai-po-blaze-pr
      ✓ [en] [politics] [neutral]
        Title : Tai Po blaze probe: temporary removal of fireproof windows ‘complied w
        Author: Brian Wong | Tags: hong kong, tai po, fire, safety
    
    [41/500] Source: South China Morning Post
      URL: https://www.scmp.com/news/hong-kong/hong-kong-economy/article/3350907/pop-s
      ✓ [en] [entertainment] [neutral]
        Title : pop star fujii kaze pulls plug on hong kong show as japanese acts shun
        Author: Danny Mok | Tags: fujii kaze, hong kong, japanese acts
    
    [42/500] Source: South China Morning Post
      URL: https://www.scmp.com/business/article/3350899/hong-kong-property-investment
      ✓ [en] [business] [positive]
        Title : hong kong property investment soars on lower funding costs, rising dem
        Author: Cheryl Arcibal | Tags: hong kong, property, investment
    
    [43/500] Source: South China Morning Post
      URL: https://www.scmp.com/business/article/3350897/scmps-original-finance-report
      ✓ [en] [business] [neutral]
        Title : SCMP’s ‘original’ finance reporting honoured at State Street Instituti
        Author: Scmp Reporter | Tags: south china morning post, state street institutional press awards, finance reporting
    
    [44/500] Source: SCMP Business
      URL: https://www.scmp.com/business/article/3350911/no-records-no-role-hsbc-rejec
      ✓ [en] [business] [neutral]
        Title : HSBC rejects Iran-linked money laundering claim
        Author: Enoch Yiu | Tags: hsbc, money laundering, iran
    
    [45/500] Source: SCMP Business
      URL: https://www.scmp.com/tech/policy/article/3350891/hidden-office-fractured-bo
      ✓ [en] [business] [negative]
        Title : Hidden office, fractured bone: violent resistance behind China’s recor
        Author: Coco Feng | Tags: china, food-safety, e-commerce, violence, resistance
    
    [46/500] Source: SCMP Business
      URL: https://www.scmp.com/business/companies/article/3350904/sino-land-led-conso
      ✓ [en] [business] [neutral]
        Title : sino land-led consortium clinches kam sheung road phase two with us$1.
        Author: Zhu Wenqian | Tags: hong kong, sino land, investment
    
    [47/500] Source: SCMP Tech
      URL: https://www.scmp.com/tech/big-tech/article/3350887/moonshot-ai-releases-fla
      ✓ [en] [technology] [neutral]
        Title : Moonshot AI releases flagship model as open-source push continues
        Author: Minxiao Chang | Tags: moonshot, ai, open-source, china
    
    [48/500] Source: SCMP Tech
      URL: https://www.scmp.com/tech/blockchain/article/3350852/crypto-industry-sees-a
      ✓ [en] [technology] [neutral]
        Title : crypto industry sees ai-driven agent economy as next growth driver
        Author: Yeon Woo Lee | Tags: crypto, ai, blockchain, web3
    
    [49/500] Source: SCMP Tech
      URL: https://www.scmp.com/plus/news/china/science/article/3350802/china-bets-ris
        ⚠ No text to extract from — skipping
      → Groq extraction failed, skipping.
    
    [49/500] Source: SCMP Tech
      URL: https://www.scmp.com/opinion/hong-kong-opinion/article/3350129/hong-kong-ca
      ✓ [en] [technology] [neutral]
        Title : hong kong can advance ai beyond the confines of geopolitical rivalry
        Author: Brian Y. S. Wong | Tags: hong kong, ai, governance
    
    [50/500] Source: Hong Kong Free Press
      URL: https://hongkongfp.com/2026/04/21/hong-kong-govt-applies-to-seize-hk127m-of
      ✓ [en] [politics] [neutral]
        Title : hk gov't applies to seize hk$127m of jailed media tycoon jimmy lai's a
        Author: Hillary Leung, More Hillary Leung, Senior Reporter | Tags: hong kong, jimmy lai, national security law, media mogul
    
      ── Auto-save checkpoint at 50 articles ──
      💾 Saved 50 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    
    [51/500] Source: Hong Kong Free Press
      URL: https://hongkongfp.com/2026/04/21/man-city-inter-milan-chelsea-juventus-to-
      ✓ [en] [sports] [neutral]
        Title : Man City, Inter Milan, Chelsea and Juventus to face off pre-season in 
        Author: More Afp | Tags: manchester city, inter milan, chelsea, juventus, hong kong
    
    [52/500] Source: Hong Kong Free Press
      URL: https://hongkongfp.com/2026/04/21/outrage-in-china-after-streaming-site-iqi
      ✓ [en] [entertainment] [negative]
        Title : Outrage in China after streaming site iQIYI debuts AI actor ‘database’
        Author: More Afp | Tags: china, iqiyi, ai, actors, entertainment
    
    [53/500] Source: Hong Kong Free Press
      URL: https://hongkongfp.com/2026/04/21/hong-kong-to-launch-public-consultation-o
      ✓ [en] [politics] [neutral]
        Title : HK to launch public consultation on first 5-year plan this quarter
        Author: null | Tags: hong kong, china, five-year plan, public consultation
    
    [54/500] Source: Hong Kong Free Press
      URL: https://hongkongfp.com/2026/04/21/govt-failed-to-carry-out-due-diligence-de
      ✓ [en] [politics] [negative]
        Title : Gov’t agencies failed 'in their duties' despite complaints: ex-board m
        Author: null | Tags: wang fuk court, renovation project, deadly fire
    
    [55/500] Source: Sixth Tone China
      URL: https://www.sixthtone.com/news/1018411/The Pagoda Puzzle: What Can Save Chi
    

    /usr/local/lib/python3.12/dist-packages/dateutil/parser/_parser.py:1207: UnknownTimezoneWarning: tzname PDT identified but not understood.  Pass `tzinfos` argument in order to correctly return a timezone-aware datetime.  In a future version, this will raise an exception.
      warnings.warn("tzname {tzname} identified but not understood.  "
    

      ✓ [en] [general] [neutral]
        Title : The Pagoda Puzzle: What Can Save China’s Oldest Wooden Tower?
        Author: Sixth Tone | Tags: china, wooden pagoda, restoration, conservation
    
    [56/500] Source: Sixth Tone China
      URL: https://www.sixthtone.com/news/1018441/China’s Latest Season of ‘Ride the W
      ✓ [en] [entertainment] [negative]
        Title : China’s Latest Season of ‘Ride the Wind’ Goes Viral Due to Poor Perfor
        Author: Marianne Gunnarsson | Tags: china, ride the wind, variety show
    
    [57/500] Source: Sixth Tone China
      URL: https://www.sixthtone.com/news/1018446/How China’s Deaf Delivery Riders Fin
      ✓ [en] [technology] [positive]
        Title : How China's Deaf Delivery Riders Find a New Life in Gig Work
        Author: null | Tags: china, deaf, delivery, riders, gig
    
    [58/500] Source: Sixth Tone China
      URL: https://www.sixthtone.com/news/1018442/Chinese Robot Runner Beats Men’s Hal
      ✓ [en] [technology] [positive]
        Title : Chinese Robot Runner Beats Men's Half-Marathon World Record
        Author: Marianne Gunnarsson | Tags: robot, half-marathon, world record, beijing
    
    [59/500] Source: Sixth Tone China
      URL: https://www.sixthtone.com/news/1018429/After Years of Endless Choice, China
      ✓ [en] [business] [neutral]
        Title : After Years of Endless Choice, China’s Shoppers Now Want Trust
        Author: Sixth Tone | Tags: china, shopping, trust, reliability, convenience
    
    [60/500] Source: The Diplomat Asia
      URL: https://thediplomat.com/2026/04/aseans-rules-of-origin-need-a-rethink/
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://thediplomat.com/2026/04/aseans-rules-of-origin-need-a-rethink/ on URL https://thediplomat.com/2026/04/aseans-rules-of-origin-need-a-rethink/
      → Scrape failed, skipping.
    
    [60/500] Source: The Diplomat Asia
      URL: https://thediplomat.com/2026/04/indonesia-u-s-blanket-overflight-access-a-d
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://thediplomat.com/2026/04/indonesia-u-s-blanket-overflight-access-a-door-that-others-will-push/ on URL https://thediplomat.com/2026/04/indonesia-u-s-blanket-overflight-access-a-door-that-others-will-push/
      → Scrape failed, skipping.
    
    [60/500] Source: The Diplomat Asia
      URL: https://thediplomat.com/2026/04/how-myanmars-civil-war-has-slipped-down-the
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://thediplomat.com/2026/04/how-myanmars-civil-war-has-slipped-down-the-global-crisis-hierarchy/ on URL https://thediplomat.com/2026/04/how-myanmars-civil-war-has-slipped-down-the-global-crisis-hierarchy/
      → Scrape failed, skipping.
    
    [60/500] Source: The Diplomat Asia
      URL: https://thediplomat.com/2026/04/thailand-to-accelerate-planning-on-land-bri
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://thediplomat.com/2026/04/thailand-to-accelerate-planning-on-land-bridge-project-minister-says/ on URL https://thediplomat.com/2026/04/thailand-to-accelerate-planning-on-land-bridge-project-minister-says/
      → Scrape failed, skipping.
    
    [60/500] Source: The Diplomat Asia
      URL: https://thediplomat.com/2026/04/philippines-us-kick-off-largest-ever-balika
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://thediplomat.com/2026/04/philippines-us-kick-off-largest-ever-balikatan-exercises-close-to-regional-flashpoints/ on URL https://thediplomat.com/2026/04/philippines-us-kick-off-largest-ever-balikatan-exercises-close-to-regional-flashpoints/
      → Scrape failed, skipping.
    
    [60/500] Source: Asia Times
      URL: https://asiatimes.com/2026/04/japans-takaichi-chooses-guns-over-butter-at-h
      ✓ [en] [politics] [negative]
        Title : Japan’s Takaichi chooses guns over butter — at her peril
        Author: William Pesek | Tags: japan, takaichi, military, economy, reform
    
    [61/500] Source: Asia Times
      URL: https://asiatimes.com/2026/04/iran-war-leaves-asian-nations-weighing-their-
      ✓ [en] [politics] [neutral]
        Title : Iran war leaves Asian nations weighing their nuclear options
        Author: Miles Pomper | Tags: iran, nuclear, asia, war, energy
    
    [62/500] Source: Asia Times
      URL: https://asiatimes.com/2026/04/southeast-asia-holds-the-key-to-unlocking-kor
      ✓ [en] [politics] [neutral]
        Title : Southeast Asia holds the key to unlocking Korean impasse
        Author: Ki-ho Han, PhD | Tags: korea, diplomacy, south east asia
    
    [63/500] Source: Asia Times
      URL: https://asiatimes.com/2026/04/in-jab-at-taiwan-china-ramps-up-military-supp
      ✓ [en] [politics] [neutral]
        Title : In jab at Taiwan, China ramps up military support for Somalia
        Author: Brendon J. Cannon | Tags: china, somalia, military, taiwan, al-shabaab
    
    [64/500] Source: Asia Times
      URL: https://asiatimes.com/2026/04/iran-war-is-turbocharging-chinas-africa-pivot
      ✓ [en] [business] [neutral]
        Title : Iran war is turbocharging China’s Africa pivot
        Author: Lauren Johnston | Tags: china, africa, hunan, investment, trade
    
    [65/500] Source: Nikkei Asia
      URL: https://asia.nikkei.com/politics/international-relations/taiwan-tensions/ta
      ✓ [en] [politics] [negative]
        Title : taiwan president scraps africa trip due to chinese coercion
        Author: Thompson Chau | Tags: taiwan, china, africa
    
    [66/500] Source: Nikkei Asia
      URL: https://asia.nikkei.com/business/technology/chinese-lidar-maker-building-fi
      ✓ [en] [technology] [neutral]
        Title : chinese lidar maker building first overseas plant in southeast asia
        Author: Nikkei Staff Writers | Tags: lidar, factory, southeast asia
    
    [67/500] Source: Nikkei Asia
      URL: https://asia.nikkei.com/business/markets/ipo/malaysia-s-mtt-shipping-shares
      ✓ [en] [business] [negative]
        Title : malaysia's mtt shipping shares close lower in stock market debut
        Author: Ahmad Mustakim, Norman Goh | Tags: malaysia, shipping, stockmarket
    
    [68/500] Source: Nikkei Asia
      URL: https://asia.nikkei.com/business/energy/china-cuts-gasoline-price-for-1st-t
      ✓ [en] [business] [neutral]
        Title : china cuts gasoline price for 1st time this year despite iran war
        Author: Wataru Suzuki | Tags: china, gasoline, iran, oil
    
    [69/500] Source: Nikkei Asia
      URL: https://asia.nikkei.com/politics/defense/ihi-mitsubishi-heavy-to-boost-prod
      ✓ [en] [politics] [neutral]
        Title : ihi, mitsubishi heavy to boost production as japan eases arms export r
        Author: Taito Kurose, Yuta Adachi, Eisaku Nitta | Tags: japan, defense, exports
    
    [70/500] Source: Japan Times
      URL: https://www.japantimes.co.jp/news/2026/04/21/world/chernobyl-40-years-on/
      ✓ [en] [general] [neutral]
        Title : chernobyl first responder says few survive 40 years on
        Author: No Author, Daria Smetanko | Tags: chernobyl, nuclear, disaster
    
    [71/500] Source: Japan Times
      URL: https://www.japantimes.co.jp/business/2026/04/21/economy/new-bank-of-korea-
      ✓ [en] [business] [neutral]
        Title : Taking Bank of Korea helm, crisis-era veteran pursues ambitious won ov
        Author: Cynthia Kim | Tags: bank of korea, shin hyun song, won
    
    [72/500] Source: Japan Times
      URL: https://www.japantimes.co.jp/news/2026/04/21/japan/recycled-resources-inves
      ✓ [en] [technology] [neutral]
        Title : japan to invest ¥1 trillion to secure recycled resources
        Author: No Author | Tags: japan, recycling, resources
    
    [73/500] Source: Japan Times
      URL: https://www.japantimes.co.jp/news/2026/04/21/japan/politics/japan-pm-takaic
      ✓ [en] [politics] [neutral]
        Title : takaichi to deliver foreign policy address in vietnam
        Author: No Author | Tags: japan, foreign policy, economy
    
    [74/500] Source: Japan Times
      URL: https://www.japantimes.co.jp/news/2026/04/21/japan/japan-showa-era-commemor
      ✓ [en] [business] [neutral]
        Title : japan to issue coins marking 100th anniversary of showa era
        Author: No Author | Tags: japan, coins, showa era
    
    [75/500] Source: Times of India
      URL: https://timesofindia.indiatimes.com/india/i-never-said-pm-is-a-terrorist-kh
        ✗ Validation error: 1 validation error for NewsArticle
    description
      Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
        For further information visit https://errors.pydantic.dev/2.12/v/string_type
      → Validation failed, skipping.
    
    [75/500] Source: Times of India
      URL: https://timesofindia.indiatimes.com/india/90-of-women-cant-enter-politics-u
      ✓ [en] [politics] [negative]
        Title : pappu yadav's 'bedroom' slur stirs big row; bjp seeks action
        Author: N/A | Tags: pappu yadav, politics, controversy
    
      ── Auto-save checkpoint at 75 articles ──
      💾 Saved 75 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    
    [76/500] Source: Times of India
      URL: https://timesofindia.indiatimes.com/sports/cricket/ipl/ipl-2026/ipl-2026-ze
      ✓ [en] [sports] [negative]
        Title : ipl 2026: 'zero impact' - ex-india captain roasts riyan parag, drags r
        Author: N/A | Tags: ipl, india, cricket
    
    [77/500] Source: Times of India
      URL: https://timesofindia.indiatimes.com/world/us/tim-cook-called-to-kiss-my-a-t
      ✓ [en] [politics] [negative]
        Title : trump praises tim cook: tim cook called to 'kiss my a**': trump's post
        Author: N/A | Tags: trump, tim cook, apple, ceo
    
    [78/500] Source: Times of India
      URL: https://timesofindia.indiatimes.com/technology/tech-news/tim-cook-in-memo-t
      ✓ [en] [technology] [positive]
        Title : tim cook in memo to employees on his exit as apple ceo: i have never b
        Author: tim cook | Tags: tim cook, apple, john ternus
    
    [79/500] Source: BBC Top Stories
      URL: https://www.bbc.com/news/articles/c895jpwl9gpo?at_medium=RSS&at_campaign=rs
      ✓ [en] [politics] [negative]
        Title : Olly Robbins's revelations are a dangerous moment for Keir Starmer
        Author: N/A | Tags: labour, mps, prime minister
    
    [80/500] Source: BBC Top Stories
      URL: https://www.bbc.com/news/articles/cjd84pkkjgpo?at_medium=RSS&at_campaign=rs
      ✓ [en] [business] [neutral]
        Title : unemployment rate unexpectedly falls as fewer students look for work
        Author: N/A | Tags: unemployment, economy, students
    
    [81/500] Source: BBC Top Stories
      URL: https://www.bbc.com/news/articles/ckgw0xzk1jvo?at_medium=RSS&at_campaign=rs
      ✓ [en] [politics] [neutral]
        Title : eight more arrests made following london arson attacks
        Author: N/A | Tags: arson, london, attacks
    
    [82/500] Source: BBC Top Stories
      URL: https://www.bbc.com/news/articles/cn08jy6w0l5o?at_medium=RSS&at_campaign=rs
      ✓ [en] [health] [neutral]
        Title : smoking ban for people born after 2008 in the uk agreed
        Author: N/A | Tags: smoking, ban, uk
    
    [83/500] Source: BBC Top Stories
      URL: https://www.bbc.com/news/articles/crm19j48wnno?at_medium=RSS&at_campaign=rs
      ✓ [en] [entertainment] [neutral]
        Title : madonna offers reward for return of missing coachella costume
        Author: N/A | Tags: madonna, coachella, costume
    
    [84/500] Source: BBC World
      URL: https://www.bbc.com/news/articles/cd9v420y190o?at_medium=RSS&at_campaign=rs
      ✓ [en] [politics] [negative]
        Title : zelensky says failure of us envoys to visit kyiv is 'disrespectful'
        Author: N/A | Tags: zelensky, us envoys, kyiv
    
    [85/500] Source: BBC World
      URL: https://www.bbc.com/news/articles/cddqvyr0yjro?at_medium=RSS&at_campaign=rs
      ✓ [en] [politics] [neutral]
        Title : unprecedented ruling finds hungary's anti-lgbtq laws in breach of eu v
        Author: N/A | Tags: hungary, eu, lgbtq
    
    [86/500] Source: BBC World
      URL: https://www.bbc.com/news/articles/clyx4vlqy4vo?at_medium=RSS&at_campaign=rs
        ✗ Validation error: 1 validation error for NewsArticle
    sentiment
      Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
        For further information visit https://errors.pydantic.dev/2.12/v/string_type
      → Validation failed, skipping.
    
    [86/500] Source: BBC World
      URL: https://www.bbc.com/news/articles/cn784g76v63o?at_medium=RSS&at_campaign=rs
      ✓ [en] [politics] [neutral]
        Title : Fannie Masemola: South Africa's police boss charged in connection with
        Author: N/A | Tags: south africa, police, corruption
    
    [87/500] Source: BBC World
      URL: https://www.bbc.com/news/articles/c86expy881qo?at_medium=RSS&at_campaign=rs
      ✓ [en] [politics] [neutral]
        Title : role of us officials killed in mexico crash under scrutiny
        Author: N/A | Tags: us officials, mexico crash, drugs operation
    
    [88/500] Source: BBC Technology
      URL: https://www.bbc.com/news/articles/c4gxj049wljo?at_medium=RSS&at_campaign=rs
      ✓ [en] [technology] [neutral]
        Title : ofcom probing telegram over child sexual abuse material concerns
        Author: N/A | Tags: telegram, child, abuse
    
    [89/500] Source: BBC Technology
      URL: https://www.bbc.com/news/articles/cn4vkye71ypo?at_medium=RSS&at_campaign=rs
      ✓ [en] [technology] [neutral]
        Title : john ternus' challenges as new apple boss
        Author: N/A | Tags: apple, john ternus, smartphone
    
    [90/500] Source: BBC Technology
      URL: https://www.bbc.com/news/articles/c1kr19lry18o?at_medium=RSS&at_campaign=rs
      ✓ [en] [technology] [neutral]
        Title : john ternus named as apple chief executive to replace tim cook
        Author: N/A | Tags: apple, john ternus, tim cook
    
    [91/500] Source: BBC Technology
      URL: https://www.bbc.com/news/articles/c5yvm11xrn6o?at_medium=RSS&at_campaign=rs
      ✓ [en] [science] [neutral]
        Title : dumb machine promising a clean energy breakthrough
        Author: N/A | Tags: fusion, energy, breakthrough
    
    [92/500] Source: BBC Technology
      URL: https://www.bbc.com/news/articles/cjr9vwz48npo?at_medium=RSS&at_campaign=rs
      ✓ [en] [technology] [neutral]
        Title : blue origin rocket grounded after satellite mishap
        Author: N/A | Tags: blue origin, rocket, satellite
    
    [93/500] Source: BBC Business
      URL: https://www.bbc.com/news/articles/c98m048d441o?at_medium=RSS&at_campaign=rs
      ✓ [en] [business] [negative]
        Title : royal mail to ask part-time posties to work more to meet letter target
        Author: N/A | Tags: royal mail, posties, letter targets
    
    [94/500] Source: BBC Business
      URL: https://www.bbc.com/news/articles/cx2drmm1mglo?at_medium=RSS&at_campaign=rs
      ✓ [en] [general] [neutral]
        Title : Spike in petrol thefts after Iran war pushed up fuel prices
        Author: N/A | Tags: petrol, theft, fuel, prices
    
    [95/500] Source: BBC Business
      URL: https://www.bbc.com/news/articles/c79jg43vd8no?at_medium=RSS&at_campaign=rs
      ✓ [en] [general] [negative]
        Title : electricity bills targeted in planned shakeup to energy pricing
        Author: N/A | Tags: electricity, energy, pricing
    
    [96/500] Source: BBC Health
      URL: https://www.bbc.com/news/articles/cdrmv48d43jo?at_medium=RSS&at_campaign=rs
      ✓ [en] [health] [negative]
        Title : disgraced mesh surgeon costs nhs £20m in compensation
        Author: N/A | Tags: mesh, surgeon, nhs
    
    [97/500] Source: BBC Health
      URL: https://www.bbc.com/news/articles/ce8lp0pz3y9o?at_medium=RSS&at_campaign=rs
      ✓ [en] [health] [neutral]
        Title : health visitors call for limits on 'impossible' 1,000-family caseloads
        Author: N/A | Tags: health, visitors, caseloads
    
    [98/500] Source: BBC Health
      URL: https://www.bbc.com/news/articles/clyepyy82kxo?at_medium=RSS&at_campaign=rs
      ✓ [en] [technology] [neutral]
        Title : can i trust health advice from an ai chatbot
        Author: N/A | Tags: health, ai, chatbots
    
    [99/500] Source: BBC Health
      URL: https://www.bbc.com/news/articles/c4g84nxwz8wo?at_medium=RSS&at_campaign=rs
      ✓ [en] [health] [neutral]
        Title : pregnancy vaccine reduces baby hospital admissions for rsv by 80%
        Author: N/A | Tags: pregnancy, vaccine, rsv
    
    [100/500] Source: The Guardian World
      URL: https://www.theguardian.com/film/2026/apr/20/charlize-theron-timothee-chala
      ✓ [en] [entertainment] [negative]
        Title : Charlize Theron joins chorus of disapproval over Timothée Chalamet’s b
        Author: null | Tags: charlize theron, timothée chalamet, ballet, opera
    
      ── Auto-save checkpoint at 100 articles ──
      💾 Saved 100 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    
    [101/500] Source: The Guardian World
      URL: https://www.theguardian.com/world/2026/apr/20/madagascar-gen-z-protesters-f
      ✓ [en] [politics] [negative]
        Title : Arrests fuel fears among Madagascar’s gen Z protesters that new regime
        Author: Rachel Savage | Tags: madagascar, protests, regime, arrests, gen z
    
    [102/500] Source: The Guardian World
      URL: https://www.theguardian.com/us-news/2026/apr/19/woman-arrested-la-arms-traf
      ✓ [en] [politics] [negative]
        Title : Iranian American woman arrested in Los Angeles for alleged arms traffi
        Author: Gloria Oladipo | Tags: iran, arms trafficking, los angeles, arrest
    
    [103/500] Source: The Guardian World
      URL: https://www.theguardian.com/technology/2026/apr/17/kenyan-outsourcing-compa
      ✓ [en] [technology] [negative]
        Title : Kenyan firm sacks more than 1,000 workers after losing Meta contract
        Author: Robert Booth | Tags: meta, sama, content moderation, ai training, tech jobs
    
    [104/500] Source: The Guardian World
      URL: https://www.theguardian.com/environment/2026/apr/17/weather-tracker-hail-co
      ✓ [en] [general] [neutral]
        Title : Weather tracker: hail covers parts of Tunisia and Algeria like snow
        Author: N/A | Tags: weather, thunderstorms, hail, tunisia, algeria
    
    [105/500] Source: The Guardian Tech
      URL: https://www.theguardian.com/technology/2026/apr/21/palantir-manifesto-uk-co
      ✓ [en] [politics] [negative]
        Title : Palantir manifesto described as ‘ramblings of a supervillain’ amid UK 
        Author: Aisha Down, Robert Booth | Tags: palantir, uk, contract, manifesto
    
    [106/500] Source: The Guardian Tech
      URL: https://www.theguardian.com/technology/2026/apr/20/tim-cook-apple-ceo-repla
      ✓ [en] [technology] [neutral]
        Title : tim cook to step down as apple chief as john ternus named replacement
        Author: Blake Montgomery, Nick Robins-Early | Tags: apple, tim cook, john ternus, ceo
    
    [107/500] Source: The Guardian Tech
      URL: https://www.theguardian.com/technology/2026/apr/20/french-prosecutors-summo
      ✓ [en] [technology] [negative]
        Title : Elon Musk snubs Paris legal summons over alleged child abuse images on
        Author: N/A | Tags: elon musk, x, grok, child abuse, paris
    
    [108/500] Source: The Guardian Tech
      URL: https://www.theguardian.com/science/audio/2026/apr/21/mythos-are-fears-over
      ✓ [en] [technology] [neutral]
        Title : mythos: are fears over new ai model panic or pr?
        Author: Ian Sample, Aisha Down, Madeleine Finlay, Joel Cox, Ellie Bury | Tags: ai, anthropic, mythos
    
    [109/500] Source: The Guardian Tech
      URL: https://www.theguardian.com/technology/2026/apr/18/sam-altman-house-attack-
      ✓ [en] [technology] [negative]
        Title : How a fiery attack on Sam Altman’s home unfolded
        Author: Nick Robins-Early | Tags: sam altman, openai, molotov cocktail, artificial intelligence, attack
    
    [110/500] Source: The Guardian Business
      URL: https://www.theguardian.com/business/2026/apr/21/kevin-warsh-trump-federal-
      ✓ [en] [politics] [neutral]
        Title : Kevin Warsh: Trump’s ideal choice to push Fed to cut interest rates
        Author: Lauren Aratani | Tags: trump, fed, interest rates, warsh, economy
    
    [111/500] Source: The Guardian Business
      URL: https://www.theguardian.com/us-news/2026/apr/21/healthcare-nurses-gig-work-
      ✓ [en] [business] [negative]
        Title : Uber for nurses’: gig-work apps lobby to deregulate healthcare, report
        Author: Michael Sainato | Tags: gig-work, nursing, deregulation, healthcare
    
    [112/500] Source: The Guardian Business
      URL: https://www.theguardian.com/us-news/2026/apr/20/trump-tariffs-refund-claims
      ✓ [en] [politics] [neutral]
        Title : Trump administration begins refunding more than $166bn in tariffs
        Author: Joseph Gedeon | Tags: trump, tariffs, refund, business
    
    [113/500] Source: The Guardian Business
      URL: https://www.theguardian.com/business/2026/apr/20/oil-prices-rise-markets-fa
      ✓ [en] [business] [negative]
        Title : Oil prices rise and markets fall after US seizure of ship hits Iran pe
        Author: Lauren Almeida | Tags: oil, prices, markets, iran, peace
    
    [114/500] Source: The Guardian Environment
      URL: https://www.theguardian.com/us-news/2026/apr/20/lawsuit-new-bp-oil-project-
      ✓ [en] [environment] [negative]
        Title : Climate groups sue US government over approval of new BP project in Gu
        Author: Oliver Milman | Tags: climate, environment, oil, drilling, gulf
    
    [115/500] Source: The Guardian Environment
      URL: https://www.theguardian.com/environment/2026/apr/20/democrats-clean-energy-
      ✓ [en] [politics] [neutral]
        Title : Democrats urged to link clean energy to affordability as Iran war hike
        Author: null | Tags: iran, war, clean, energy, affordability
    
    [116/500] Source: The Guardian Environment
      URL: https://www.theguardian.com/us-news/2026/apr/19/lahaina-maui-rebuild-locals
      ✓ [en] [general] [positive]
        Title : Maui residents are rebuilding Lahaina for locals, not tourists: ‘In Ha
        Author: N/A | Tags: lahaina, maui, hawaii, rebuilding, locals
    
    [117/500] Source: The Guardian Environment
      URL: https://www.theguardian.com/us-news/2026/apr/17/supreme-court-oil-and-gas-l
      ✓ [en] [politics] [neutral]
        Title : Supreme court sides with oil and gas firms in Louisiana coastal damage
        Author: N/A | Tags: supreme court, oil and gas, louisiana, coastal damage, environmental degradation
    
    [118/500] Source: The Guardian Environment
      URL: https://www.theguardian.com/us-news/2026/apr/17/senate-overturn-biden-era-m
      ✓ [en] [politics] [negative]
        Title : US Senate repeals Biden-era ban on mining near Minnesota wilderness ar
        Author: Anna Betts | Tags: us senate, minnesota, mining, boundary waters
    
    [119/500] Source: TechCrunch
      URL: https://techcrunch.com/2026/04/21/whats-the-key-to-better-vegan-cheese-micr
      ✓ [en] [technology] [neutral]
        Title : What’s the key to better vegan cheese? Microbreweries, one startup say
        Author: Tim De Chant, Senior Reporter, Amanda Silberling, Sean O'Kane, Anthony Ha, Tim Fernholz, Aisha Malik, Sarah Perez, --C-Author-Card-Image-Size Align-Items Center Display Flex Gap Var, Media | Tags: vegan cheese, microbreweries, startup
    
    [120/500] Source: TechCrunch
      URL: https://techcrunch.com/2026/04/21/cash-app-is-targeting-a-new-kind-of-custo
      ✓ [en] [technology] [neutral]
        Title : Cash App targets 6-12 year olds with new youth-focused services
        Author: Lucas Ropek, Senior Writer, Amanda Silberling, Sean O'Kane, Anthony Ha, Tim Fernholz, Aisha Malik, Sarah Perez, --C-Author-Card-Image-Size Align-Items Center Display Flex Gap Var, Media | Tags: cash app, fintech, children, financial literacy
    
    [121/500] Source: TechCrunch
      URL: https://techcrunch.com/2026/04/21/grai-believes-ai-can-make-music-more-soci
      ✓ [en] [technology] [neutral]
        Title : GRAI believes AI can make music more social, not replace artists
        Author: Sarah Perez, Consumer News Editor, Amanda Silberling, Sean O'Kane, Anthony Ha, Tim Fernholz, Aisha Malik, --C-Author-Card-Image-Size Align-Items Center Display Flex Gap Var, Media, Min-Width | Tags: music, ai, social, remix
    
    [122/500] Source: TechCrunch
      URL: https://techcrunch.com/2026/04/21/yelps-updated-ai-assistant-can-answer-que
      ✓ [en] [technology] [neutral]
        Title : Yelp’s updated AI assistant can answer questions and book a restaurant
        Author: Ivan Mehta, Amanda Silberling, Sean O'Kane, Anthony Ha, Tim Fernholz, Aisha Malik, Sarah Perez, --C-Author-Card-Image-Size Align-Items Center Display Flex Gap Var, Media, Min-Width | Tags: yelp, ai, assistant, restaurant, service
    
    [123/500] Source: TechCrunch
      URL: https://techcrunch.com/2026/04/21/blue-energy-raises-380m-to-build-grid-sca
      ✓ [en] [technology] [neutral]
        Title : Blue Energy raises $380M to build grid-scale nuclear reactors in shipy
        Author: Tim De Chant, Senior Reporter, Amanda Silberling, Sean O'Kane, Anthony Ha, Tim Fernholz, Aisha Malik, Sarah Perez, --C-Author-Card-Image-Size Align-Items Center Display Flex Gap Var, Media | Tags: blue energy, nuclear reactors, shipyards
    
    [124/500] Source: TechCrunch AI
      URL: https://techcrunch.com/2026/04/20/anthropic-takes-5b-from-amazon-and-pledge
      ✓ [en] [technology] [neutral]
        Title : anthropic takes $5b from amazon and pledges $100b in cloud spending in
        Author: Julie Bort, Zack Whittaker, Anthony Ha, Kirsten Korosec, Sarah Perez, Ivan Mehta, .Post-Authors-List__Authors --Font-Size Var, Align-Items Center Display Flex Gap Var, .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Display Flex Flex-Shrink Margin Padding .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Li List-Style None Margin-Left Margin-Top Important .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Li First-Child Margin-Left .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs .Post-Authors-List__Author-Thumb Background-Color Var, Border Solid Var --Wp--Custom--Color--White | Tags: anthropic, amazon, aws, cloud, funding
    
    [125/500] Source: TechCrunch AI
      URL: https://techcrunch.com/2026/04/20/google-rolls-out-gemini-in-chrome-in-seve
      ✓ [en] [technology] [neutral]
        Title : google rolls out gemini in chrome in 7 new countries
        Author: Ivan Mehta, Sarah Perez, .Post-Authors-List__Authors --Font-Size Var, Align-Items Center Display Flex Gap Var, .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Display Flex Flex-Shrink Margin Padding .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Li List-Style None Margin-Left Margin-Top Important .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Li First-Child Margin-Left .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs .Post-Authors-List__Author-Thumb Background-Color Var, Border Solid Var --Wp--Custom--Color--White, Border-Radius, Height -O-Object-Fit Cover Object-Fit Cover Width .Post-Authors-List__Authors .Post-Authors-List__Author-List Display Flex Flex-Wrap Wrap Gap Var, List-Style-Type None Margin-Bottom Margin-Top Padding .Post-Authors-List__Authors .Post-Authors-List__Author-List Li List-Style None Margin-Top .Post-Authors-List__Authors .Post-Authors-List__Author-List Li Not, Last-Child | Tags: google, chrome, gemini
    
      ── Auto-save checkpoint at 125 articles ──
      💾 Saved 125 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    
    [126/500] Source: TechCrunch AI
      URL: https://techcrunch.com/2026/04/20/ai-writing-its-not-just-this-its-that-bar
      ✓ [en] [technology] [negative]
        Title : AI-generated writing is becoming an epidemic in corporate communicatio
        Author: Amanda Silberling, Senior Writer, Sean O'Kane, Anthony Ha, Tim Fernholz, Aisha Malik, Sarah Perez, --C-Author-Card-Image-Size Align-Items Center Display Flex Gap Var, Media, Min-Width | Tags: ai, writing, corporate, communications
    
    [127/500] Source: TechCrunch AI
      URL: https://techcrunch.com/2026/04/20/nsa-spies-are-reportedly-using-anthropics
      ✓ [en] [technology] [neutral]
        Title : NSA reportedly using Anthropic's Mythos despite Pentagon feud
        Author: Rebecca Bellan, Zack Whittaker, Anthony Ha, .Post-Authors-List__Authors --Font-Size Var, Align-Items Center Display Flex Gap Var, .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Display Flex Flex-Shrink Margin Padding .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Li List-Style None Margin-Left Margin-Top Important .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Li First-Child Margin-Left .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs .Post-Authors-List__Author-Thumb Background-Color Var, Border Solid Var --Wp--Custom--Color--White, Border-Radius, Height -O-Object-Fit Cover Object-Fit Cover Width .Post-Authors-List__Authors .Post-Authors-List__Author-List Display Flex Flex-Wrap Wrap Gap Var, List-Style-Type None Margin-Bottom Margin-Top Padding .Post-Authors-List__Authors .Post-Authors-List__Author-List Li List-Style None Margin-Top .Post-Authors-List__Authors .Post-Authors-List__Author-List Li Not | Tags: nsa, anthropic, mythos, cybersecurity
    
    [128/500] Source: TechCrunch AI
      URL: https://techcrunch.com/2026/04/20/fermi-ceo-and-cfo-depart-texas-nuclear-po
      ✓ [en] [technology] [negative]
        Title : CEO and CFO suddenly depart AI nuclear power upstart Fermi
        Author: Kirsten Korosec, Amanda Silberling, Anthony Ha, Tim De Chant, .Post-Authors-List__Authors --Font-Size Var, Align-Items Center Display Flex Gap Var, .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Display Flex Flex-Shrink Margin Padding .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Li List-Style None Margin-Left Margin-Top Important .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs Li First-Child Margin-Left .Post-Authors-List__Authors .Post-Authors-List__Author-Thumbs .Post-Authors-List__Author-Thumb Background-Color Var, Border Solid Var --Wp--Custom--Color--White, Border-Radius, Height -O-Object-Fit Cover Object-Fit Cover Width .Post-Authors-List__Authors .Post-Authors-List__Author-List Display Flex Flex-Wrap Wrap Gap Var | Tags: fermi, ai, nuclear, power
    
    [129/500] Source: The Verge
      URL: https://www.theverge.com/science/915244/spacex-ipo-trillion-dollar-commerci
      ✓ [en] [technology] [neutral]
        Title : The SpaceX IPO is a trillion-dollar gamble on the future of space
        Author: Georgina Torbet | Tags: space, spacex, ipo, elon musk, space economy
    
    [130/500] Source: The Verge
      URL: https://www.theverge.com/tech/915388/apple-ceo-john-ternus-tim-cook
      ✓ [en] [technology] [neutral]
        Title : Apple to have product guy as CEO again
        Author: Jay Peters, Stevie Bonifield, Jay Peters Stevie Bonifield | Tags: apple, john ternus, ceo
    
    [131/500] Source: The Verge
      URL: https://www.theverge.com/ai-artificial-intelligence/915626/yelp-ai-assistan
      ✓ [en] [technology] [neutral]
        Title : yelp is making its ai chatbot way more useful
        Author: is a london-based reporter at the verge covering all things ai and a senior tarbell fellow | Tags: yelp, ai, chatbot, assistant
    
    [132/500] Source: The Verge
      URL: https://www.theverge.com/tech/915586/microsoft-teams-accidental-hand-raisin
      ✓ [en] [technology] [neutral]
        Title : microsoft teams redesign aims to reduce accidental hand-raising
        Author: Jess Weatherbed | Tags: microsoft, teams, redesign, hand-raising, meeting
    
    [133/500] Source: The Verge
      URL: https://www.theverge.com/tech/915560/ikea-and-samsung-promise-glitch-free-s
      ✓ [en] [technology] [neutral]
        Title : Ikea and Samsung promise glitch-free Matter integration
        Author: Casey Newton | Tags: samsung, ikea, matter, smartthings, home automation
    
    [134/500] Source: Wired
      URL: https://www.wired.com/story/best-gaming-laptops/
      ✓ [en] [technology] [neutral]
        Title : Best Gaming Laptops (2026): Razer, Asus, Dell, and More
        Author: Luke Larsen, Scott Gilbertson, Julian Chokkattu, Ryan Waniata, Matt Kamen, Molly Higgins, Brad Bourque | Tags: gaming, laptops, lenovo, acer, nvidia
    
    [135/500] Source: Wired
      URL: https://www.wired.com/story/ai-generated-maga-girls/
      ✓ [en] [technology] [negative]
        Title : This Scammer Used an AI-Generated MAGA Girl to Grift ‘Super Dumb’ Men
        Author: Ej Dickson, Jason Parham, Matt Burgess, Miles Klee, Kat Tenbarge, Ashwin Rodrigues, Tiffany Ng, Kate Knibbs, Katie Drummond, Boone Ashworth | Tags: scammer, ai-generated, maga, influencer, social media
    
    [136/500] Source: Wired
      URL: https://www.wired.com/review/h2o-audio-tri-run-workout-headphones/
      ✓ [en] [technology] [neutral]
        Title : H2O Audio Tri Run Workout Headphones Review: A Little Underwhelming
        Author: Michael Sawh | Tags: h2o audio, tri run, workout headphones, review
    
    [137/500] Source: Wired
      URL: https://www.wired.com/story/the-big-interview-podcast-legal-eagle-devin-sto
      ✓ [en] [politics] [neutral]
        Title : The Internet’s Favorite Lawyer Says We’re Living Through ‘Multiple Wat
        Author: Katie Drummond | Tags: devin stone, legal eagle, youtube, trump presidency
    
    [138/500] Source: Wired
      URL: https://www.wired.com/story/they-built-privacy-tool-grapheneos-now-sworn-en
      ✓ [en] [technology] [neutral]
        Title : They Built a Legendary Privacy Tool. Now They’re Sworn Enemies
        Author: Tiffany Ng, Andy Greenberg, Dell Cameron, Paresh Dave, Jason Parham, Andrew Couts, Maxwell Zeff, Robert Silverman, Boone Ashworth, Vittoria Elliott | Tags: daniel micay, grapheneos, copperheados, android hardening, privacy tool
    
    [139/500] Source: Ars Technica
      URL: https://arstechnica.com/science/2026/04/global-growth-in-solar-the-largest-
      ✓ [en] [technology] [positive]
        Title : Global growth in solar 'the largest ever observed for any source'
        Author: N/A | Tags: solar, energy, renewables
    
    [140/500] Source: Ars Technica
      URL: https://arstechnica.com/space/2026/04/pentagon-pulls-the-plug-on-one-of-the
      ✓ [en] [technology] [negative]
        Title : Pentagon pulls the plug on one of the military’s most troubled space p
        Author: N/A | Tags: pentagon, gps, space
    
    [141/500] Source: Ars Technica
      URL: https://arstechnica.com/apple/2026/04/john-ternus-will-replace-tim-cook-as-
      ✓ [en] [technology] [neutral]
        Title : john ternus to replace tim cook as apple ceo
        Author: N/A | Tags: apple, ceo, tim cook, john ternus
    
    [142/500] Source: Ars Technica
      URL: https://arstechnica.com/health/2026/04/absurdly-bad-study-spurs-headlines-l
      ✓ [en] [health] [negative]
        Title : Absurd study suggests eating fruits and vegetables leads to cancer
        Author: N/A | Tags: cancer, fruits, vegetables, study, nutrition
    
    [143/500] Source: Ars Technica
      URL: https://arstechnica.com/tech-policy/2026/04/us-opens-refund-portal-to-start
      ✓ [en] [politics] [neutral]
        Title : US opens refund portal to start paying back Trump’s illegal tariffs
        Author: N/A | Tags: us, tariffs, trump, refund, portal
    
    [144/500] Source: MIT Tech Review
      URL: https://www.technologyreview.com/2026/04/21/1136246/the-download-human-nois
      ✓ [en] [technology] [neutral]
        Title : The Download: turning down human noise, and LA’s stunning subway upgra
        Author: MIKE MCQUADE | Tags: apple, anthropic, ai, tech
    
    [145/500] Source: MIT Tech Review
      URL: https://www.technologyreview.com/2026/04/21/1135231/digging-for-truth-north
      ✓ [en] [science] [neutral]
        Title : Digging for clues about the North Pole’s past
        Author: Tim Kalvelage | Tags: north pole, climate change, arctic
    
    [146/500] Source: MIT Tech Review
      URL: https://www.technologyreview.com/2026/04/20/1136154/the-download-murderous-
      ✓ [en] [technology] [neutral]
        Title : murderous ‘mirror’ bacteria, and Chinese workers fighting AI doubles
        Author: Stephen Ornes | Tags: mirror bacteria, ai doubles, automation
    
    [147/500] Source: MIT Tech Review
      URL: https://www.technologyreview.com/2026/04/20/1135222/red-wolves-colossal-bio
      ✓ [en] [science] [neutral]
        Title : Colossal Biosciences said it cloned red wolves. Is it for real?
        Author: TRISTAN SPINSKI | Tags: colossal biosciences, red wolves, cloning, conservation
    
    [148/500] Source: MIT Tech Review
      URL: https://www.technologyreview.com/2026/04/20/1136149/chinese-tech-workers-ai
      ✓ [en] [technology] [neutral]
        Title : Chinese tech workers are starting to train their AI doubles–and pushin
        Author: Caiwei Chen | Tags: ai, china, tech, workers
    
    [149/500] Source: VentureBeat
      URL: https://venturebeat.com/security/adversaries-hijacked-ai-security-tools-at-
        ✗ Scrape failed: Article `download()` failed with 429 Client Error: Too Many Requests for url: https://venturebeat.com/security/adversaries-hijacked-ai-security-tools-at-90-organizations-the-next-wave-has-write-access-to-the-firewall on URL https://venturebeat.com/security/adversaries-hijacked-ai-security-tools-at-90-organizations-the-next-wave-has-write-access-to-the-firewall
      → Scrape failed, skipping.
    
    [149/500] Source: VentureBeat
      URL: https://venturebeat.com/orchestration/train-to-test-scaling-explained-how-t
        ✗ Scrape failed: Article `download()` failed with 429 Client Error: Too Many Requests for url: https://venturebeat.com/orchestration/train-to-test-scaling-explained-how-to-optimize-your-end-to-end-ai-compute-budget-for-inference on URL https://venturebeat.com/orchestration/train-to-test-scaling-explained-how-to-optimize-your-end-to-end-ai-compute-budget-for-inference
      → Scrape failed, skipping.
    
    [149/500] Source: VentureBeat
      URL: https://venturebeat.com/security/most-enterprises-cant-stop-stage-three-ai-
        ✗ Scrape failed: Article `download()` failed with 429 Client Error: Too Many Requests for url: https://venturebeat.com/security/most-enterprises-cant-stop-stage-three-ai-agent-threats-venturebeat-survey-finds on URL https://venturebeat.com/security/most-enterprises-cant-stop-stage-three-ai-agent-threats-venturebeat-survey-finds
      → Scrape failed, skipping.
    
    [149/500] Source: VentureBeat
      URL: https://venturebeat.com/technology/anthropic-just-launched-claude-design-an
        ✗ Scrape failed: Article `download()` failed with 429 Client Error: Too Many Requests for url: https://venturebeat.com/technology/anthropic-just-launched-claude-design-an-ai-tool-that-turns-prompts-into-prototypes-and-challenges-figma on URL https://venturebeat.com/technology/anthropic-just-launched-claude-design-an-ai-tool-that-turns-prompts-into-prototypes-and-challenges-figma
      → Scrape failed, skipping.
    
    [149/500] Source: VentureBeat
      URL: https://venturebeat.com/orchestration/should-my-enterprise-ai-agent-do-that
        ✗ Scrape failed: Article `download()` failed with 429 Client Error: Too Many Requests for url: https://venturebeat.com/orchestration/should-my-enterprise-ai-agent-do-that-nanoclaw-and-vercel-launch-easier-agentic-policy-setting-and-approval-dialogs-across-15-messaging-apps on URL https://venturebeat.com/orchestration/should-my-enterprise-ai-agent-do-that-nanoclaw-and-vercel-launch-easier-agentic-policy-setting-and-approval-dialogs-across-15-messaging-apps
      → Scrape failed, skipping.
    
    [149/500] Source: ZDNet
      URL: https://www.zdnet.com/article/how-to-easily-encrypt-files-on-android-with-o
      ✓ [en] [technology] [positive]
        Title : I found the easiest way to encrypt files on an Android phone - and it'
        Author: Jack Wallen/ZDNET | Tags: android, encryption, security, openkeychain
    
    [150/500] Source: ZDNet
      URL: https://www.zdnet.com/article/free-apple-iphone-17-deal-t-mobile/
      ✓ [en] [technology] [neutral]
        Title : t-mobile will give you an iphone 17 basically for free - here's how to
        Author: Kayla Solino, April, At A.M. Pt | Tags: t-mobile, iphone, free
    
      ── Auto-save checkpoint at 150 articles ──
      💾 Saved 150 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    
    [151/500] Source: ZDNet
      URL: https://www.zdnet.com/article/does-walmart-price-match-faq/
      ✓ [en] [technology] [neutral]
        Title : does walmart price match what to know about online and in-store price 
        Author: Kayla Solino, April, At A.M. Pt | Tags: price match, walmart, online shopping
    
    [152/500] Source: ZDNet
      URL: https://www.zdnet.com/article/best-mini-gaming-pcs/
      ✓ [en] [technology] [neutral]
        Title : The best mini gaming PCs of 2026: Expert tested and reviewed
        Author: Adrian Kingsley-Hughes, Senior Contributing Editor, Taylor Clemons, Staff Writer, Allison Murray | Tags: gaming, pc, mini, hp, dell
    
    [153/500] Source: ZDNet
      URL: https://www.zdnet.com/article/best-settings-to-change-on-your-sony-bravia-t
      ✓ [en] [technology] [neutral]
        Title : Own a Sony TV? 3 quick settings I'd change to meaningfully improve the
        Author: Adam Breeden | Tags: sony, tv, picture quality, settings
    
    [154/500] Source: Engadget
      URL: https://www.engadget.com/computing/tim-cook-will-step-down-as-204959434.htm
      ✓ [en] [technology] [positive]
        Title : John Ternus to be CEO of Apple when Tim Cook steps down this fall
        Author: Tim Cook | Tags: apple, tim cook, john ternus, ceo
    
    [155/500] Source: Engadget
      URL: https://www.engadget.com/big-tech/amazon-allegedly-pressured-companies-to-r
      ✓ [en] [business] [negative]
        Title : Amazon allegedly pressured companies to raise product prices with othe
        Author: N/A | Tags: amazon, price fixing, lawsuit
    
    [156/500] Source: Engadget
      URL: https://www.engadget.com/general/the-morning-after-engadget-newsletter-1115
      ✓ [en] [technology] [neutral]
        Title : Apple Names Hardware Exec John Ternus as Next CEO
        Author: Mat Smith | Tags: apple, john ternus, tim cook, ceo
    
    [157/500] Source: Engadget
      URL: https://www.engadget.com/apps/yelps-ai-chatbot-can-now-make-your-dinner-res
      ✓ [en] [technology] [neutral]
        Title : yelp's ai chatbot can now make your dinner reservation
        Author: N/A | Tags: yelp, ai, chatbot, reservation
    
    [158/500] Source: Engadget
      URL: https://www.engadget.com/wearables/homeland-security-reportedly-wants-to-de
      ✓ [en] [politics] [negative]
        Title : Homeland Security reportedly wants to develop smart glasses for ICE
        Author: Ken Klippenstein | Tags: homeland security, ice, smart glasses, surveillance
    
    [159/500] Source: Mashable Tech
      URL: https://mashable.com/article/apple-wwdc-ai-siri-tease
      ✓ [en] [technology] [neutral]
        Title : Apple may have given us a big hint about AI Siri
        Author: null | Tags: apple, siri, wwdc, ai
    
    [160/500] Source: Mashable Tech
      URL: https://mashable.com/article/april-21-samsung-odyssey-g6-gaming-monitor-dea
      ✓ [en] [technology] [positive]
        Title : Save $300 on Samsung 27-inch Odyssey OLED G6 gaming monitor
        Author: Hannah Hoolihan | Tags: samsung, gaming, monitor, amazon, resident evil
    
    [161/500] Source: Mashable Tech
      URL: https://mashable.com/article/april-21-samsung-galaxy-watch-ultra-gift-card-
      ✓ [en] [technology] [positive]
        Title : Amazon is offering a free $100 gift card with the Samsung Galaxy Watch
        Author: Hannah Hoolihan | Tags: amazon, samsung, galaxy watch ultra, gift card, smartwatch
    
    [162/500] Source: Mashable Tech
      URL: https://mashable.com/article/whatsapp-plus-paid-subscription
      ✓ [en] [technology] [neutral]
        Title : whatsapp tests plus subscription but what do you actually get
        Author: N/A | Tags: whatsapp, plus, subscription, meta
    
    [163/500] Source: Mashable Tech
      URL: https://mashable.com/article/soundcore-space-2-release-price-specs
      ✓ [en] [technology] [positive]
        Title : Soundcore Space 2 headphones: Specs, price, where to buy
        Author: Bethany Allard | Tags: soundcore, space 2, headphones, budget, noise cancellation
    
    [164/500] Source: Bloomberg Technology
      URL: https://www.bloomberg.com/news/articles/2026-04-21/moody-s-lifts-thai-outlo
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.bloomberg.com/news/articles/2026-04-21/moody-s-lifts-thai-outlook-to-stable-on-easing-us-tariff-shocks on URL https://www.bloomberg.com/news/articles/2026-04-21/moody-s-lifts-thai-outlook-to-stable-on-easing-us-tariff-shocks
      → Scrape failed, skipping.
    
    [164/500] Source: Bloomberg Technology
      URL: https://www.bloomberg.com/news/videos/2026-04-21/bofa-sees-a-moment-to-weig
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.bloomberg.com/news/videos/2026-04-21/bofa-sees-a-moment-to-weigh-positive-negative-surprises-video on URL https://www.bloomberg.com/news/videos/2026-04-21/bofa-sees-a-moment-to-weigh-positive-negative-surprises-video
      → Scrape failed, skipping.
    
    [164/500] Source: Bloomberg Technology
      URL: https://www.bloomberg.com/news/articles/2026-04-21/us-stock-futures-today-3
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.bloomberg.com/news/articles/2026-04-21/us-stock-futures-today-3m-alaska-air-amazon-apple-unitedhealth on URL https://www.bloomberg.com/news/articles/2026-04-21/us-stock-futures-today-3m-alaska-air-amazon-apple-unitedhealth
      → Scrape failed, skipping.
    
    [164/500] Source: Bloomberg Technology
      URL: https://www.bloomberg.com/news/videos/2026-04-21/daybreak-europe-4-21-2026-
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.bloomberg.com/news/videos/2026-04-21/daybreak-europe-4-21-2026-video on URL https://www.bloomberg.com/news/videos/2026-04-21/daybreak-europe-4-21-2026-video
      → Scrape failed, skipping.
    
    [164/500] Source: Bloomberg Technology
      URL: https://www.bloomberg.com/news/newsletters/2026-04-21/apple-ceo-tim-cook-wr
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.bloomberg.com/news/newsletters/2026-04-21/apple-ceo-tim-cook-wrote-a-playbook-for-success-in-china on URL https://www.bloomberg.com/news/newsletters/2026-04-21/apple-ceo-tim-cook-wrote-a-playbook-for-success-in-china
      → Scrape failed, skipping.
    
    [164/500] Source: CNBC World
      URL: https://www.cnbc.com/2026/04/21/trump-iran-war-ceasefire-peace-talks.html
      ✓ [en] [politics] [positive]
        Title : trump expects great deal with iran
        Author: null | Tags: trump, iran, peace negotiations
    
    [165/500] Source: CNBC World
      URL: https://www.cnbc.com/2026/04/21/uk-uae-iran-war-dubai-expat-appeal-middle-e
      ✓ [en] [business] [neutral]
        Title : Brits fled to Dubai for low taxes — now war is making some rethink the
        Author: Emma Graham Sawdah Bhaimiya, Emma Graham, Sawdah Bhaimiya | Tags: dubai, uk, tax, war, expats
    
    [166/500] Source: CNBC World
      URL: https://www.cnbc.com/2026/04/21/global-stocks-iran-conflict-ai-rally.html
      ✓ [en] [business] [positive]
        Title : Global stocks recoup Iran war losses to hit fresh records
        Author: Lee Ying Shan, In Ying-Shan-Lee | Tags: iran, stocks, economy
    
    [167/500] Source: CNBC World
      URL: https://www.cnbc.com/2026/04/21/unitedhealth-group-unh-earnings-q1-2026.htm
      ✓ [en] [business] [positive]
        Title : UnitedHealth tops quarterly estimates, hikes profit outlook as insurer
        Author: Annika Kim Constantino | Tags: unitedhealth, medical costs, profit outlook
    
    [168/500] Source: CNBC World
      URL: https://www.cnbc.com/2026/04/21/volkswagen-voice-ai-chinese-cars-automaker.
      ✓ [en] [technology] [neutral]
        Title : Volkswagen announces voice AI in its Chinese cars from later this year
        Author: Evelyn Cheng | Tags: volkswagen, ai, voice, commands, china
    
    [169/500] Source: CNBC Finance
      URL: https://www.cnbc.com/2026/04/21/kevin-warshs-senate-hearing-what-to-expect.
      ✓ [en] [politics] [neutral]
        Title : Fed chair nominee Kevin Warsh faces Senate hearing on independence
        Author: Jeff Cox | Tags: kevin warsh, federal reserve, monetary policy, independence
    
    [170/500] Source: CNBC Finance
      URL: https://www.cnbc.com/2026/04/21/jpmorgan-chase-security-defense-spending-ai
      ✓ [en] [business] [neutral]
        Title : JPMorgan expands $1.5 trillion economic security splurge into Europe
        Author: null | Tags: jpmorgan, economy, security, investment
    
    [171/500] Source: CNBC Finance
      URL: https://www.cnbc.com/2026/04/20/ast-falls-after-bezos-blue-origin-places-sa
      ✓ [en] [technology] [negative]
        Title : ast spacemobile shares drop after its satellite is placed in wrong orb
        Author: Davis Giangiulio, In | Tags: ast spacemobile, blue origin, rocket launch
    
    [172/500] Source: CNBC Finance
      URL: https://www.cnbc.com/2026/04/19/cursor-ai-2-billion-funding-round.html
      ✓ [en] [technology] [neutral]
        Title : cursor in talks to raise $2 billion funding round at valuation of over
        Author: Deirdre Bosa Jonathan Vanian, Deirdre Bosa, Jonathan Vanian, In | Tags: cursor, ai, funding, startup
    
    [173/500] Source: Financial Times World
      URL: https://www.ft.com/content/877411bf-c810-473c-a4f5-d0468d81bbd1
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.ft.com/content/877411bf-c810-473c-a4f5-d0468d81bbd1 on URL https://www.ft.com/content/877411bf-c810-473c-a4f5-d0468d81bbd1
      → Scrape failed, skipping.
    
    [173/500] Source: Financial Times World
      URL: https://www.ft.com/content/a72963c3-c5ca-4eb4-9971-ba44118b1af3
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.ft.com/content/a72963c3-c5ca-4eb4-9971-ba44118b1af3 on URL https://www.ft.com/content/a72963c3-c5ca-4eb4-9971-ba44118b1af3
      → Scrape failed, skipping.
    
    [173/500] Source: Financial Times World
      URL: https://www.ft.com/content/6d006c95-2934-4340-82b0-05b18ec161e0
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.ft.com/content/6d006c95-2934-4340-82b0-05b18ec161e0 on URL https://www.ft.com/content/6d006c95-2934-4340-82b0-05b18ec161e0
      → Scrape failed, skipping.
    
    [173/500] Source: Financial Times World
      URL: https://www.ft.com/content/5b5a466c-fc48-429d-b505-2c81d87e3615
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.ft.com/content/5b5a466c-fc48-429d-b505-2c81d87e3615 on URL https://www.ft.com/content/5b5a466c-fc48-429d-b505-2c81d87e3615
      → Scrape failed, skipping.
    
    [173/500] Source: Financial Times World
      URL: https://www.ft.com/content/55e5927c-caf7-489f-829f-da00998e6ffd
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.ft.com/content/55e5927c-caf7-489f-829f-da00998e6ffd on URL https://www.ft.com/content/55e5927c-caf7-489f-829f-da00998e6ffd
      → Scrape failed, skipping.
    
    [173/500] Source: Forbes Business
      URL: https://www.forbes.com/sites/davidblackmon/2026/04/21/americas-lng-dominanc
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Max restarts limit reached for url: https://www.forbes.com/sites/davidblackmon/2026/04/21/americas-lng-dominance-anchors-global-energy-security/ on URL https://www.forbes.com/sites/davidblackmon/2026/04/21/americas-lng-dominance-anchors-global-energy-security/
      → Scrape failed, skipping.
    
    [173/500] Source: Forbes Business
      URL: https://www.forbes.com/sites/hughmcintyre/2026/04/21/lady-gaga-charts-anoth
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Max restarts limit reached for url: https://www.forbes.com/sites/hughmcintyre/2026/04/21/lady-gaga-charts-another-new-top-10-hit-and-shes-not-alone/ on URL https://www.forbes.com/sites/hughmcintyre/2026/04/21/lady-gaga-charts-another-new-top-10-hit-and-shes-not-alone/
      → Scrape failed, skipping.
    
    [173/500] Source: Forbes Business
      URL: https://www.forbes.com/sites/garyocchiogrosso/2026/04/21/5-reasons-to-focus
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Max restarts limit reached for url: https://www.forbes.com/sites/garyocchiogrosso/2026/04/21/5-reasons-to-focus-on-technology-for-restaurant-success-in-2026/ on URL https://www.forbes.com/sites/garyocchiogrosso/2026/04/21/5-reasons-to-focus-on-technology-for-restaurant-success-in-2026/
      → Scrape failed, skipping.
    
    [173/500] Source: Forbes Business
      URL: https://www.forbes.com/sites/hughmcintyre/2026/04/21/elvis-presley-returns-
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Max restarts limit reached for url: https://www.forbes.com/sites/hughmcintyre/2026/04/21/elvis-presley-returns-to-no-1-as-his-recent-album-surges/ on URL https://www.forbes.com/sites/hughmcintyre/2026/04/21/elvis-presley-returns-to-no-1-as-his-recent-album-surges/
      → Scrape failed, skipping.
    
    [173/500] Source: Forbes Business
      URL: https://www.forbes.com/sites/siladityaray/2026/04/21/trump-says-tim-cook-ca
        ✗ Scrape failed: Article `download()` failed with 403 Client Error: Max restarts limit reached for url: https://www.forbes.com/sites/siladityaray/2026/04/21/trump-says-tim-cook-called-to-kiss-my-ass-in-long-post-about-apple-ceo/ on URL https://www.forbes.com/sites/siladityaray/2026/04/21/trump-says-tim-cook-called-to-kiss-my-ass-in-long-post-about-apple-ceo/
      → Scrape failed, skipping.
    
    [173/500] Source: Business Insider
      URL: https://www.businessinsider.com/ai-boom-exhausting-energizing-tech-workers-
      ✓ [en] [technology] [neutral]
        Title : AI boom energizing and exhausting tech product managers at once
        Author: Thibault Spirlet, Every Time | Tags: ai, tech, product managers, boom
    
    [174/500] Source: Business Insider
      URL: https://www.businessinsider.com/tim-cook-memes-jokes-stepping-down-apple-ce
      ✓ [en] [technology] [neutral]
        Title : 10 best memes about Tim Cook stepping down as Apple CEO
        Author: Hugh Langley, Every Time | Tags: tim cook, apple, memes
    
    [175/500] Source: Business Insider
      URL: https://www.businessinsider.com/us-air-force-a-10s-new-life-heavy-use-iran-
      ✓ [en] [technology] [neutral]
        Title : US military extends service life of A-10 'Warthog' until 2030
        Author: Jake Epstein, Every Time | Tags: a-10, warthog, us-air-force, iran
    
      ── Auto-save checkpoint at 175 articles ──
      💾 Saved 175 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    
    [176/500] Source: Business Insider
      URL: https://www.businessinsider.com/trump-praises-tim-cook-apple-references-vir
      ✓ [en] [politics] [neutral]
        Title : Trump praises 'Tim Apple' in a nod to his infamous 2019 name slip-up
        Author: null | Tags: trump, apple, tim cook
    
    [177/500] Source: Business Insider
      URL: https://www.businessinsider.com/smart-people-comments-tim-cook-legacy-apple
      ✓ [en] [technology] [neutral]
        Title : what smart people are saying about tim cook's legacy at apple
        Author: Kelsey Vlamis, Aditi Bharade, Every Time | Tags: tim cook, apple, ceo, legacy
    
    [178/500] Source: MarketWatch
      URL: https://www.marketwatch.com/story/the-blue-sky-scenario-that-could-take-the
        ✗ Scrape failed: Article `download()` failed with 401 Client Error: HTTP Forbidden for url: https://www.marketwatch.com/story/the-blue-sky-scenario-that-could-take-the-s-p-500-to-8-000-by-years-end-according-to-jpmorgan-10138b80?mod=mw_rss_topstories on URL https://www.marketwatch.com/story/the-blue-sky-scenario-that-could-take-the-s-p-500-to-8-000-by-years-end-according-to-jpmorgan-10138b80?mod=mw_rss_topstories
      → Scrape failed, skipping.
    
    [178/500] Source: MarketWatch
      URL: https://www.marketwatch.com/story/retail-sales-jump-to-3-year-high-but-its-
        ✗ Scrape failed: Article `download()` failed with 401 Client Error: HTTP Forbidden for url: https://www.marketwatch.com/story/retail-sales-jump-to-3-year-high-but-its-due-to-high-gas-prices-0dbfc66b?mod=mw_rss_topstories on URL https://www.marketwatch.com/story/retail-sales-jump-to-3-year-high-but-its-due-to-high-gas-prices-0dbfc66b?mod=mw_rss_topstories
      → Scrape failed, skipping.
    
    [178/500] Source: MarketWatch
      URL: https://www.marketwatch.com/story/i-will-retire-in-my-early-50s-i-have-3-2-
        ✗ Scrape failed: Article `download()` failed with 401 Client Error: HTTP Forbidden for url: https://www.marketwatch.com/story/i-will-retire-in-my-early-50s-i-have-3-2-million-only-200-000-is-in-a-traditional-ira-have-i-beaten-the-irs-3ab5df98?mod=mw_rss_topstories on URL https://www.marketwatch.com/story/i-will-retire-in-my-early-50s-i-have-3-2-million-only-200-000-is-in-a-traditional-ira-have-i-beaten-the-irs-3ab5df98?mod=mw_rss_topstories
      → Scrape failed, skipping.
    
    [178/500] Source: MarketWatch
      URL: https://www.marketwatch.com/story/ges-profit-beats-by-wide-margin-sending-i
        ✗ Scrape failed: Article `download()` failed with 401 Client Error: HTTP Forbidden for url: https://www.marketwatch.com/story/ges-profit-beats-by-wide-margin-sending-its-stock-into-positive-territory-for-the-year-8463b635?mod=mw_rss_topstories on URL https://www.marketwatch.com/story/ges-profit-beats-by-wide-margin-sending-its-stock-into-positive-territory-for-the-year-8463b635?mod=mw_rss_topstories
      → Scrape failed, skipping.
    
    [178/500] Source: MarketWatch
      URL: https://www.marketwatch.com/story/this-is-unbelievable-my-adviser-made-300-
        ✗ Scrape failed: Article `download()` failed with 401 Client Error: HTTP Forbidden for url: https://www.marketwatch.com/story/this-is-unbelievable-my-adviser-made-300-000-trading-options-now-im-being-killed-by-taxes-do-i-complain-e30873b7?mod=mw_rss_topstories on URL https://www.marketwatch.com/story/this-is-unbelievable-my-adviser-made-300-000-trading-options-now-im-being-killed-by-taxes-do-i-complain-e30873b7?mod=mw_rss_topstories
      → Scrape failed, skipping.
    
    [178/500] Source: CoinDesk Crypto
      URL: https://www.coindesk.com/markets/2026/04/21/almost-80-of-japanese-instituti
      ✓ [en] [business] [positive]
        Title : Almost 80% of Japanese institutional investors are eyeing crypto for t
        Author: Helene Braun, Ai Boost, Helene-Braun | Tags: japan, crypto, investors, portfolios
    
    [179/500] Source: CoinDesk Crypto
      URL: https://www.coindesk.com/daybook-us/2026/04/21/bitcoin-trades-above-a-make-
      ✓ [en] [technology] [neutral]
        Title : Bitcoin (BTC) price holds above a make-or-break level before Warsh con
        Author: Omkar Godbole | Tags: bitcoin, btc, warsh, ceasefire, cryptocurrency
    
    [180/500] Source: CoinDesk Crypto
      URL: https://www.coindesk.com/markets/2026/04/21/bitcoin-climbs-as-risk-sentimen
      ✓ [en] [technology] [neutral]
        Title : crypto market strength led by bitcoin as altcoin sentiment stays fragi
        Author: Oliver Knight, Omkar Godbole, Oliver-Knight | Tags: crypto, bitcoin, altcoin, market
    
    [181/500] Source: CoinDesk Crypto
      URL: https://www.coindesk.com/business/2026/04/21/crypto-scammers-offer-safe-pas
      ✓ [en] [technology] [negative]
        Title : Bitcoin, USDT 'safe passage' scam hits Hormuz as one ship reportedly d
        Author: Olivier Acuna | Tags: bitcoin, scam, hormuz
    
    [182/500] Source: CoinDesk Crypto
      URL: https://www.coindesk.com/policy/2026/04/21/bank-of-korea-s-new-governor-sig
      ✓ [en] [business] [neutral]
        Title : Bank of Korea's new governor signals CBDC and bank token push, skips s
        Author: null | Tags: bank, korea, cbdc, stablecoins, crypto
    
    [183/500] Source: WHO News
      URL: https://www.who.int/news/item/14-04-2026-after-three-years-of-conflict--sud
      ✓ [en] [general] [negative]
        Title : Sudan faces deeper health crisis after three years of conflict
        Author: N/A | Tags: sudan, health, crisis, conflict, aid
    
    [184/500] Source: WHO News
      URL: https://www.who.int/news/item/09-04-2026-first-ever-who-forum-unites-800--c
      ✓ [en] [health] [positive]
        Title : First-ever WHO Forum unites 800+ Collaborating Centres for stronger sc
        Author: N/A | Tags: who, global health, scientific collaboration
    
    [185/500] Source: WHO News
      URL: https://www.who.int/news/item/07-04-2026-who-and-france-shift-one-health-vi
      ✓ [en] [health] [positive]
        Title : WHO and France shift One Health vision to action with new high-impact 
        Author: null | Tags: one health, world health organization, france, global health, sustainability
    
    [186/500] Source: WHO News
      URL: https://www.who.int/news/item/06-04-2026-who-calls-for-action---together-fo
      ✓ [en] [health] [neutral]
        Title : WHO calls for action: “Together for health. Stand with science.” to ma
        Author: N/A | Tags: world health organization, science, health, world health day
    
    [187/500] Source: WHO News
      URL: https://www.who.int/news/item/28-03-2026-who-member-states-agree-to-extend-
      ✓ [en] [health] [neutral]
        Title : WHO Member States agree to extend negotiations on key annex to the Pan
        Author: N/A | Tags: who, negotiations, pandemic, agreement
    
    [188/500] Source: Science Daily
      URL: https://www.sciencedaily.com/releases/2026/04/260420233930.htm
      ✓ [en] [science] [neutral]
        Title : Scientists Find Cheaper Way to Kill Western Drywood Termites
        Author: N/A | Tags: termites, insecticide, science
    
    [189/500] Source: Science Daily
      URL: https://www.sciencedaily.com/releases/2026/04/260420015840.htm
        ✗ JSON parse error (attempt 1): Expecting ',' delimiter: line 3 column 100 (char 179)
        ✗ JSON parse error (attempt 2): Expecting ',' delimiter: line 3 column 90 (char 169)
      ✓ [en] [science] [neutral]
        Title : Scientists finally crack the “dolomite problem”
        Author: null | Tags: science, technology, geology
    
    [190/500] Source: Science Daily
      URL: https://www.sciencedaily.com/releases/2026/04/260420014750.htm
      ✓ [en] [environment] [negative]
        Title : Hundreds of millions at risk as river deltas sink faster than rising s
        Author: null | Tags: river deltas, subsidence, sea levels, climate change
    
    [191/500] Source: Science Daily
      URL: https://www.sciencedaily.com/releases/2026/04/260420014748.htm
      ✓ [en] [technology] [negative]
        Title : AI swarms could hijack democracy without anyone noticing
        Author: N/A | Tags: ai, democracy, influence, politics, technology
    
    [192/500] Source: Science Daily
      URL: https://www.sciencedaily.com/releases/2026/04/260420014744.htm
      ✓ [en] [health] [neutral]
        Title : missing vitamin could stop cancer cells in their tracks
        Author: null | Tags: cancer, vitamin b7, glutamine
    
    [193/500] Source: Nature News
      URL: https://www.nature.com/articles/d41586-026-01257-6
      ✓ [en] [technology] [neutral]
        Title : AI doom warnings are getting louder. Are they realistic?
        Author: Gibney, Elizabeth Gibney, Search Author On | Tags: ai, doom, warnings, realistic, risk
    
    [194/500] Source: Nature News
      URL: https://www.nature.com/articles/d41586-026-01243-y
      ✓ [en] [health] [neutral]
        Title : Personalized CRISPR therapies could soon reach thousands — here’s how
        Author: Urnov, Fyodor D., Kassim, Sadik H., Fyodor D. Urnov Is A Professor Of Molecular Therapeutics At The University Of California, Berkeley, California, Usa, Director Of Therapeutic Research, Development At The Innovative Genomics Institute. | Tags: crispr, gene-editing, therapy, fda, approval
    
    [195/500] Source: Nature News
      URL: https://www.nature.com/articles/d41586-026-01255-8
      ✓ [en] [environment] [neutral]
        Title : nuclear disasters are inevitable — plan for them
        Author: Bell, Alexandra Bell Is President, Chief Executive Of The, Search Author On | Tags: nuclear, disasters, energy, renewable, climate
    
    [196/500] Source: Nature News
      URL: https://www.nature.com/articles/d41586-026-01259-4
      ✓ [en] [science] [neutral]
        Title : Bat feast animal videos at African cave offer clues to how deadly viru
        Author: null | Tags: leopards, bats, viruses, africa, cave
    
    [197/500] Source: Nature News
      URL: https://www.nature.com/articles/d41586-026-01278-1
      ✓ [en] [technology] [neutral]
        Title : No humans allowed: scientific AI agents get their own social network
        Author: Ahart, Jenna Ahart, Search Author On | Tags: ai, science, research, socialnetwork, agents
    
    [198/500] Source: NASA Breaking News
      URL: https://science.nasa.gov/earth/earth-observatory/a-school-of-mud-volcano-is
      ✓ [en] [science] [neutral]
        Title : Azerbaijan's Mud Volcano Islands
        Author: Adam Voiland | Tags: mud volcanoes, azerbaijan, geology
    
    [199/500] Source: NASA Breaking News
      URL: https://www.nasa.gov/missions/nasa-on-track-for-future-missions-with-initia
      ✓ [en] [science] [neutral]
        Title : NASA on Track for Future Missions with Initial Artemis II Assessments
        Author: Lauren E. Low | Tags: nasa, artemis, space, moon, mars
    
    [200/500] Source: NASA Breaking News
      URL: https://www.nasa.gov/news-release/nasa-rolls-out-artemis-iii-moon-rocket-co
      ✓ [en] [science] [neutral]
        Title : NASA Rolls Out Artemis III Moon Rocket Core Stage
        Author: James Gannon | Tags: nasa, artemis, moon, rocket, space
    
      ── Auto-save checkpoint at 200 articles ──
      💾 Saved 200 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    
    [201/500] Source: NASA Breaking News
      URL: https://www.nasa.gov/news-release/nasa-invites-media-to-spacexs-34th-resupp
      ✓ [en] [science] [neutral]
        Title : NASA Invites Media to SpaceX’s 34th Resupply Launch to Space Station
        Author: Josh Finch / Jimi Russell | Tags: nasa, spacex, space station, resupply mission
    
    [202/500] Source: NASA Breaking News
      URL: https://www.nasa.gov/news-release/nasa-welcomes-latvia-as-newest-artemis-ac
      ✓ [en] [science] [neutral]
        Title : NASA Welcomes Latvia as Newest Artemis Accords Signatory
        Author: Camille Gallo / Elizabeth Shaw | Tags: nasa, latvia, space, exploration
    
    [203/500] Source: New Scientist
      URL: https://www.newscientist.com/article/2523443-we-might-finally-know-how-to-u
      ✓ [en] [technology] [neutral]
        Title : We might finally know how to use quantum computers to boost AI
        Author: Author.Fullname | Tags: quantum computers, ai, machine learning, research
    
    [204/500] Source: New Scientist
      URL: https://www.newscientist.com/article/2522362-why-the-right-kind-of-stress-i
      ✓ [en] [health] [neutral]
        Title : Why the right kind of stress is crucial for your health and happiness
        Author: Mojo Wang | Tags: stress, health, happiness, research, science
    
    [205/500] Source: New Scientist
      URL: https://www.newscientist.com/article/2523669-a-whole-new-way-to-prevent-dea
      ✓ [en] [health] [positive]
        Title : New way to prevent death from sepsis shows promise
        Author: Author.Fullname | Tags: sepsis, protein, blood, filtering, treatment
    
    [206/500] Source: New Scientist
      URL: https://www.newscientist.com/article/2523607-diamonds-are-surprisingly-elas
      ✓ [en] [science] [neutral]
        Title : diamonds are surprisingly elastic when you make them tiny
        Author: Author.Fullname | Tags: diamonds, nanotechnology, research
    
    [207/500] Source: New Scientist
      URL: https://www.newscientist.com/article/2522501-can-we-vaccinate-ourselves-aga
      ✓ [en] [health] [neutral]
        Title : Can we ‘vaccinate’ ourselves against stress?
        Author: Mojo Wang | Tags: stress, resilience, vaccine, mental health
    
    [208/500] Source: ESPN Headlines
      URL: https://www.espn.com/nba/story/_/id/48506452/2026-nba-playoffs-western-conf
      ✓ [en] [sports] [neutral]
        Title : 2026 NBA playoffs: Western Conference first-round takeaways
        Author: Nba Insiders, Vincent Goodwill, Michael C. Wright, Anthony Slater, Jamal Collier, Tim Bontemps, Ramona Shelburne, Zach Kram, Ohm Youngmisuk, Brian Windhorst | Tags: nba, playoffs, basketball
    
    [209/500] Source: ESPN Headlines
      URL: https://www.espn.com/nba/story/_/id/48546628/cj-mccollum-leads-late-rally-h
      ✓ [en] [sports] [positive]
        Title : CJ McCollum leads late rally as Hawks stun Knicks to tie series
        Author: Vincent Goodwill, Michael C. Wright, Anthony Slater, Jamal Collier, Tim Bontemps, Ramona Shelburne, Zach Kram, Ohm Youngmisuk, Brian Windhorst, Espn Staff | Tags: atlanta hawks, new york knicks, cj mccollum, nba playoffs
    
    [210/500] Source: ESPN Headlines
      URL: https://www.espn.com/nba/story/_/id/48547786/timberwolves-rally-nuggets-win
      ✓ [en] [sports] [positive]
        Title : Rudy Gobert contains Nuggets' Nikola Jokic as Wolves tie series
        Author: Anthony Slater, Jamal Collier, Tim Bontemps, Ramona Shelburne, Zach Kram, Ohm Youngmisuk, Brian Windhorst, Espn Staff, Multiple Authors, Nba Insiders | Tags: nba, timberwolves, nuggets, rudy gobert, nikola jokic
    
    [211/500] Source: ESPN Headlines
      URL: https://www.espn.com/nhl/story/_/id/48547203/martinook-rescues-hurricanes-2
      ✓ [en] [sports] [positive]
        Title : Martinook rescues Hurricanes in 2OT after overturned goal
        Author: Greg Wyshynski, Brooke Pryor, Ryan Clark, Kristen Shilton, Espn Staff, Alaina Getzenberg, Neil Paine, Sean Allen, Victoria Matiash, Multiple Authors | Tags: hurricanes, ottawa senators, nhl, stanley cup playoffs
    
    [212/500] Source: ESPN Headlines
      URL: https://www.espn.com/nba/story/_/id/48544568/spurs-victor-wembanyama-captur
      ✓ [en] [sports] [positive]
        Title : Spurs star Victor Wembanyama first unanimous DPOY winner
        Author: Michael C. Wright, Anthony Slater, Jamal Collier, Tim Bontemps, Ramona Shelburne, Zach Kram, Ohm Youngmisuk, Brian Windhorst, Espn Staff, Multiple Authors | Tags: nba, victor wembanyama, dpoys
    
    [213/500] Source: BBC Sport
      URL: https://www.bbc.com/sport/football/articles/c33l0gxm2ndo?at_medium=RSS&at_c
      ✓ [en] [sports] [neutral]
        Title : premier league players out of contract this summer
        Author: N/A | Tags: premier league, players, contracts
    
    [214/500] Source: BBC Sport
      URL: https://www.bbc.com/sport/football/articles/c3r3ewyz1e8o?at_medium=RSS&at_c
      ✓ [en] [sports] [neutral]
        Title : Liverpool: Freddie Woodman on life as Reds' third-choice goalkeeper
        Author: Aadam Patel | Tags: freddie woodman, liverpool, third-choice goalkeeper
    
    [215/500] Source: BBC Sport
      URL: https://www.bbc.com/sport/basketball/articles/ce3drn7rwv6o?at_medium=RSS&at
      ✓ [en] [sports] [positive]
        Title : nba: victor wembanyama named defensive player of the year as first una
        Author: N/A | Tags: nba, victor wembanyama, defensive player of the year
    
    [216/500] Source: BBC Sport
      URL: https://www.bbc.com/sport/football/articles/cly7ejx9nx5o?at_medium=RSS&at_c
      ✓ [en] [sports] [neutral]
        Title : baroness karren brady steps down as west ham vice-chair after 16 years
        Author: Simon Stone | Tags: west ham, karren brady, football, sports
    
    [217/500] Source: BBC Sport
      URL: https://www.bbc.com/sport/boxing/articles/c17vjqv5n5zo?at_medium=RSS&at_cam
      ✓ [en] [sports] [neutral]
        Title : british boxer lawrence okolie fails doping test before paris fight wit
        Author: N/A | Tags: lawrence okolie, doping test, tony yoka
    
    [218/500] Source: Sky Sports
      URL: https://www.skysports.com/football/news/12040/13534530/arne-slot-future-liv
      ✓ [en] [sports] [neutral]
        Title : Arne Slot future: Liverpool boss expected to stay at Anfield next seas
        Author: N/A | Tags: liverpool, champions league, arne slot
    
    [219/500] Source: Sky Sports
      URL: https://www.skysports.com/watch/video/13534546/jamie-carragher-from-what-i-
      ✓ [en] [sports] [neutral]
        Title : jamie carragher: arne slot will stay at liverpool next season
        Author: null | Tags: liverpool, football, transfer
    
    [220/500] Source: Sky Sports
      URL: https://www.skysports.com/football/live-blog/12040/12476234/transfer-centre
      ✓ [en] [sports] [neutral]
        Title : Transfer Centre LIVE! Football transfer news, updates and rumours
        Author: N/A | Tags: football, transfer, news
    
    [221/500] Source: Sky Sports
      URL: https://www.skysports.com/athletics/news/12040/13534420/gout-gout-usain-bol
      ✓ [en] [sports] [neutral]
        Title : Usain Bolt urges Australian teenage sprint star Gout Gout to stay focu
        Author: N/A | Tags: usain bolt, gout gout, australian sprint star
    
    [222/500] Source: Sky Sports
      URL: https://www.skysports.com/football/news/12040/13534428/karren-brady-west-ha
      ✓ [en] [sports] [neutral]
        Title : Karren Brady to leave West Ham after 16 years
        Author: N/A | Tags: west ham, karren brady, premier league
    
    [223/500] Source: CNN Travel
      URL: https://www.cnn.com/travel/article/ritz-carlton-superyacht-sets-sail/index.
      ✓ [en] [travel] [neutral]
        Title : Ritz-Carlton’s luxury superyacht cruise has finally set sail
        Author: Tamara Hardingham-Gill | Tags: ritz-carlton, superyacht, cruise
    
    [224/500] Source: CNN Travel
      URL: https://www.cnn.com/travel/article/limone-sul-garda-italy-elixir-wellness/i
      ✓ [en] [health] [neutral]
        Title : Limone sul Garda, Italy’s village with a health ‘elixir’
        Author: Silvia Marchetti | Tags: italy, limone, gene, health, elixir
    
    [225/500] Source: CNN Travel
      URL: https://www.cnn.com/travel/article/virgin-orbit-boeing-747-newquay-scn/inde
      ✓ [en] [technology] [neutral]
        Title : Virgin Boeing 747 to launch rocket into space
        Author: Julia Buckley | Tags: virgin orbit, space launch, boeing 747
    
      ── Auto-save checkpoint at 225 articles ──
      💾 Saved 225 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    
    [226/500] Source: CNN Travel
      URL: https://www.cnn.com/travel/article/famous-missing-shipwrecks-cmd/index.html
      ✓ [en] [travel] [neutral]
        Title : Famous shipwrecks that remain missing – and a few that have been found
        Author: Will Noble | Tags: shipwrecks, travel, history, maritime
    
    [227/500] Source: CNN Travel
      URL: https://www.cnn.com/travel/article/man-builds-plane-garden/index.html
      ✓ [en] [general] [positive]
        Title : This man built a plane for his family in his garden
        Author: null | Tags: plane, garden, family, aviation, uk
    
    [228/500] Source: Variety
      URL: https://variety.com/2026/film/reviews/michael-review-michael-jackson-colman
      ✓ [en] [entertainment] [positive]
        Title : Michael Review: The Thrill Is Not Gone, as a Surprisingly Effective Mi
        Author: Owen Gleiberman, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: michael jackson, biopic, music, pop, culture
    
    [229/500] Source: Variety
      URL: https://variety.com/2026/music/news/toddler-techno-lenny-pearce-disney-musi
      ✓ [en] [entertainment] [positive]
        Title : Toddler Techno Creator Lenny Pearce Signs Disney Music and Content Dev
        Author: Joe Otterson, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: lenny pearce, toddler techno, disney
    
    [230/500] Source: Variety
      URL: https://variety.com/2026/digital/news/webby-awards-2026-winners-announced-v
      ✓ [en] [entertainment] [neutral]
        Title : Webby Awards 2026 Winners Revealed, Variety Among Honorees
        Author: Todd Spangler, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: webby awards, variety, music, film, internet
    
    [231/500] Source: Variety
      URL: https://variety.com/2026/tv/reviews/half-man-review-hbo-richard-gadd-123672
      ✓ [en] [entertainment] [positive]
        Title : Half Man Is Baby Reindeer Creator Richard Gadd’s Outstanding Return to
        Author: Aramide Tinubu, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: half man, baby reindeer, richard gadd, hbo, limited series
    
    [232/500] Source: Variety
      URL: https://variety.com/2026/film/news/cat-on-a-hot-tin-roof-broadway-revival-s
      ✓ [en] [entertainment] [neutral]
        Title : Cat on a Hot Tin Roof Broadway Revival Coming in 2027 From Tony-Winnin
        Author: Brent Lang, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: broadway, cat on a hot tin roof, sam gold, tennessee williams
    
    [233/500] Source: Hollywood Reporter
      URL: https://www.hollywoodreporter.com/business/digital/disney-rivals-the-podcas
      ✓ [en] [entertainment] [neutral]
        Title : Disney+ Sets ‘Rivals: The Podcast’ Return With Pandora Sykes (Exclusiv
        Author: Lily Ford, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: disney, rivals, podcast, pandora-sykes
    
    [234/500] Source: Hollywood Reporter
      URL: https://www.hollywoodreporter.com/business/digital/youtube-ai-deepfake-dete
      ✓ [en] [entertainment] [neutral]
        Title : YouTube Opens Up AI Deepfake Detection Tool to All of Hollywood (Exclu
        Author: Alex Weprin, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: youtube, deepfake, detection, tool, hollywood
    
    [235/500] Source: Hollywood Reporter
      URL: https://www.hollywoodreporter.com/business/business-news/sister-group-after
      ✓ [en] [business] [neutral]
        Title : Sister Group Buys Majority Stake in Digital-First Producer After Party
        Author: null | Tags: sister group, after party studios, digital-first, production company
    
    [236/500] Source: Hollywood Reporter
      URL: https://www.hollywoodreporter.com/movies/movie-news/karlovy-vary-2026-anniv
      ✓ [en] [entertainment] [neutral]
        Title : Karlovy Vary Fest to Celebrate 60th Edition, 80th Anniversary With Pow
        Author: Georg Szalai, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: karlovy-vary, film-festival, anniversary, classics, exhibition
    
    [237/500] Source: Hollywood Reporter
      URL: https://www.hollywoodreporter.com/business/business-news/oliver-jones-apple
      ✓ [en] [entertainment] [neutral]
        Title : Oliver Jones Exits Apple TV to Join Amazon MGM Studios
        Author: Lily Ford, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: oliver jones, apple tv, amazon mgm studios
    
    [238/500] Source: Rolling Stone
      URL: https://www.rollingstone.com/tv-movies/tv-movie-reviews/michael-jackson-bio
      ✓ [en] [entertainment] [negative]
        Title : We Were Never Going to Get a Real Michael Jackson Biopic
        Author: David Fear, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: michael jackson, biopic, music
    
    [239/500] Source: Rolling Stone
      URL: https://www.rollingstone.com/music/music-features/linda-perry-4-non-blondes
      ✓ [en] [entertainment] [positive]
        Title : Linda Perry Talks Cancer Diagnosis and Finally Feeling Inspired to Cre
        Author: null | Tags: linda perry, music, cancer, documentary
    
    [240/500] Source: Rolling Stone
      URL: https://www.rollingstone.com/culture/culture-commentary/clavicular-follower
      ✓ [en] [entertainment] [negative]
        Title : Are Clavicular’s Followers Rethinking His Influence?
        Author: Eli Thompson, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: clavicular, looksmaxxing, influence
    
    [241/500] Source: Rolling Stone
      URL: https://www.rollingstone.com/politics/politics-news/labor-secretary-lori-ch
      ✓ [en] [politics] [negative]
        Title : Trump Labor Secretary Resigns Amid Misconduct Scandal
        Author: Charisma Madarang, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: trump, labor, scandal
    
    [242/500] Source: Rolling Stone
      URL: https://www.rollingstone.com/product-recommendations/books/heated-rivalry-j
      ✓ [en] [entertainment] [neutral]
        Title : New 'Heated Rivalry' Book Teases Backstage Secrets
        Author: Jacob Tierney | Tags: heated rivalry, hbo max, book
    
    [243/500] Source: Pitchfork Music
      URL: https://pitchfork.com/news/brian-eno-massive-attack-sigur-ros-call-for-euro
      ✓ [en] [entertainment] [negative]
        Title : Brian Eno, Massive Attack, Sigur Rós Call for Eurovision 2026 Boycott
        Author: Kiana Mickles, Jazz Monroe | Tags: eurovision, boycott, israel, genocide, music
    
    [244/500] Source: Pitchfork Music
      URL: https://pitchfork.com/news/coachella-2027-dates-announced/
      ✓ [en] [entertainment] [neutral]
        Title : Coachella 2027 Dates Announced
        Author: Nina Corcoran | Tags: coachella, music, festival
    
    [245/500] Source: Pitchfork Music
      URL: https://pitchfork.com/news/grimes-says-she-made-an-album-called-psy-opera/
      ✓ [en] [entertainment] [neutral]
        Title : Grimes Says She Made an Album Called Psy Opera
        Author: Walden Green | Tags: grimes, psy-opera, music, ai
    
    [246/500] Source: Pitchfork Music
      URL: https://pitchfork.com/news/someone-stole-madonna-coachella-outfits/
      ✓ [en] [entertainment] [negative]
        Title : Madonna Calls for Safe Return of Stolen Coachella Outfits
        Author: null | Tags: madonna, coachella, stolen, outfits
    
    [247/500] Source: Pitchfork Music
      URL: https://pitchfork.com/news/shaboozey-returns-with-new-album-the-outlaw-cher
      ✓ [en] [general] [neutral]
        Title : Shaboozey Returns With New Album The Outlaw Cherie Lee & Other Western
        Author: Kiana Mickles | Tags: shaboozey, new album, country music
    
    [248/500] Source: Deadline Hollywood
      URL: https://deadline.com/2026/04/sports-news-doc-emmys-2026-lifetime-achievemen
      ✓ [en] [sports] [neutral]
        Title : Sports & News/Doc Emmys Set 2026 Lifetime Achievement Award Recipients
        Author: Erik Pedersen, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: sports, emmys, awards
    
    [249/500] Source: Deadline Hollywood
      URL: https://deadline.com/2026/04/michael-review-jaafar-jackson-dazzles-feel-goo
      ✓ [en] [entertainment] [positive]
        Title : Michael Review: Jaafar Jackson Dazzles As His King Of Pop Uncle In A F
        Author: Pete Hammond, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: michael jackson, biopic, jaafar jackson, music, drama
    
    [250/500] Source: Deadline Hollywood
      URL: https://deadline.com/2026/04/big-boys-jack-rooke-secret-diary-adrian-mole-s
      ✓ [en] [entertainment] [neutral]
        Title : Big Boys Writer-Creator Jack Rooke Reflects On Hit Series & Talks Next
        Author: Jack Rooke | Tags: big boys, jack rooke, comedy, tv series
    
      ── Auto-save checkpoint at 250 articles ──
      💾 Saved 250 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    
    [251/500] Source: Deadline Hollywood
      URL: https://deadline.com/2026/04/embassy-prime-video-uk-australia-more-more-cas
      ✓ [en] [entertainment] [neutral]
        Title : Prime Video Secures Multi-Territory Rights To Action Series 'Embassy'
        Author: Jesse Whittock, .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow, Class, Wp-Block-Co-Authors-Plus, Display Inline, .Wp-Block-Co-Authors-Plus-Avatar, Where Img, Height Auto Max-Width, Vertical-Align Bottom .Wp-Block-Co-Authors-Plus-Coauthors.Is-Layout-Flow .Wp-Block-Co-Authors-Plus-Avatar, Vertical-Align Middle .Wp-Block-Co-Authors-Plus-Avatar Is .Alignleft .Alignright | Tags: prime video, embassy, action series
    
    [252/500] Source: Deadline Hollywood
      URL: https://deadline.com/2026/04/succession-bugonia-writer-will-tracy-the-onion
      ✓ [en] [entertainment] [neutral]
        Title : Succession & Bugonia Writer Will Tracy On How Working At The Onion Pav
        Author: null | Tags: succession, bugonia, comedy writing, the onion, will tracy
    
    =================================================================
    PIPELINE COMPLETE
      Articles collected : 252
      URLs skipped       : 33
      Groq API calls     : 256
      Quota hits         : 0
    =================================================================
      💾 Saved 252 articles → news_dataset.csv | news_dataset.json | news_dataset.db
    

EDA summary


```python
df = pd.DataFrame(clean_articles)

print("=" * 50)
print(f"Total articles    : {len(df)}")
print(f"Unique sources    : {df['source'].nunique()}")
print(f"Languages         : {df['language'].value_counts().to_dict()}")
print(f"\n── Category distribution ──")
print(df["category"].value_counts().to_string())
print(f"\n── Sentiment distribution ──")
print(df["sentiment"].value_counts().to_string())
print(f"\n── Articles per source (top 20) ──")
print(df["source"].value_counts().head(20).to_string())
print(f"\n── Null counts ──")
print(df.isnull().sum().to_string())
```

    ==================================================
    Total articles    : 252
    Unique sources    : 53
    Languages         : {'en': 252}
    
    ── Category distribution ──
    category
    technology       74
    politics         54
    entertainment    27
    business         27
    sports           18
    general          17
    health           15
    science          12
    environment       4
    travel            4
    
    ── Sentiment distribution ──
    sentiment
    neutral     170
    negative     48
    positive     34
    
    ── Articles per source (top 20) ──
    source
    Al Jazeera English          5
    What's On Dubai             5
    Middle East Eye             5
    CGTN World                  5
    CGTN Business               5
    BBC Technology              5
    Xinhua Top News             5
    Xinhua China                5
    South China Morning Post    5
    Sixth Tone China            5
    Hong Kong Free Press        5
    Nikkei Asia                 5
    Asia Times                  5
    Japan Times                 5
    BBC Top Stories             5
    The Verge                   5
    TechCrunch AI               5
    The Guardian Environment    5
    TechCrunch                  5
    The Guardian Tech           5
    
    ── Null counts ──
    article_id       0
    url              0
    source           0
    title            0
    description      0
    author          69
    tags             0
    category         0
    sentiment        0
    publish_date     8
    language         0
    top_image        6
    scraped_at       0
    


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

