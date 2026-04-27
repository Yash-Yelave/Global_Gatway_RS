import os
import time
import json
import hashlib
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup
from newspaper import Article
from groq import Groq
from pydantic import BaseModel, field_validator
from typing import Optional, List
from config import config

client = Groq(api_key=os.getenv("GROQ_API_KEY", config.NEWS_API_KEY))
GROQ_MODEL = "llama-3.1-8b-instant"
MAX_TOKENS_IN = 2000
RATE_LIMIT_SEC = 2.5
CATEGORIES = ["technology", "politics", "sports", "business", "health", "science", "entertainment", "general"]

RSS_FEEDS = {
    "BBC Top Stories": "http://feeds.bbci.co.uk/news/rss.xml",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
}

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

class NewsArticle(BaseModel):
    article_id: str
    url: str
    source: str
    title: str
    description: str
    author: Optional[str]
    tags: List[str]
    category: str
    sentiment: str
    publish_date: Optional[str]
    top_image: Optional[str]
    scraped_at: str

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

def fetch_rss_urls(feeds: dict, max_per_feed: int = 5) -> list[dict]:
    articles = []
    for source_name, feed_url in feeds.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:max_per_feed]:
                url = entry.get("link", "")
                if url:
                    articles.append({
                        "source": source_name,
                        "url": url,
                        "rss_title": entry.get("title", ""),
                        "published": entry.get("published", ""),
                    })
        except Exception as e:
            print(f"  [ERROR] {source_name}: {e}")
    return articles

def scrape_article(url: str) -> dict | None:
    try:
        art = Article(url, fetch_images=False, request_timeout=10)
        art.download()
        art.parse()

        meta_desc = ""
        try:
            soup = BeautifulSoup(art.html, "html.parser")
            tag = (soup.find("meta", attrs={"name": "description"}) or
                   soup.find("meta", attrs={"property": "og:description"}))
            if tag:
                meta_desc = tag.get("content", "")
        except:
            pass

        return {
            "url": url,
            "scraped_title": art.title or "",
            "raw_text": art.text or "",
            "scraped_author": ", ".join(art.authors) if art.authors else "",
            "scraped_date": str(art.publish_date) if art.publish_date else "",
            "meta_desc": meta_desc,
            "top_image": art.top_image or "",
        }
    except Exception as e:
        print(f"    Scrape failed [{url[:60]}]: {e}")
        return None

def extract_with_groq(scraped: dict) -> dict | None:
    raw_text = scraped.get("raw_text", "") or scraped.get("meta_desc", "")
    if not raw_text.strip(): return None

    truncated = raw_text[:MAX_TOKENS_IN * 4]
    prompt = EXTRACTION_PROMPT.format(title_hint=scraped.get("scraped_title", ""), article_text=truncated)
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.1,
        )
        raw_json = response.choices[0].message.content.strip()
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"): raw_json = raw_json[4:]
        return json.loads(raw_json)
    except Exception as e:
        print(f"    Groq extraction failed: {e}")
        return None

def build_article_id(url: str) -> str:
    return "art_" + hashlib.md5(url.encode()).hexdigest()[:8]

def validate_and_merge(rss_meta: dict, scraped: dict, extracted: dict) -> dict | None:
    try:
        article = NewsArticle(
            article_id=build_article_id(rss_meta["url"]),
            url=rss_meta["url"],
            source=rss_meta["source"],
            title=extracted.get("title") or scraped.get("scraped_title") or rss_meta.get("rss_title", ""),
            description=extracted.get("description") or scraped.get("meta_desc") or "",
            author=extracted.get("author") or scraped.get("scraped_author") or "Unknown",
            tags=extracted.get("tags", []),
            category=extracted.get("category", "general"),
            sentiment=extracted.get("sentiment", "neutral"),
            publish_date=extracted.get("publish_date") or scraped.get("scraped_date") or rss_meta.get("published") or None,
            top_image=scraped.get("top_image") or None,
            scraped_at=datetime.utcnow().isoformat(),
        )
        return article.model_dump()
    except Exception as e:
        print(f"    Validation error: {e}")
        return None

def run_scraper(nlp_choice: str, max_articles: int = 15):
    print("\n--- Running Scraper ---")
    raw_urls = fetch_rss_urls(RSS_FEEDS, max_per_feed=40)
    results = []
    seen = set()
    processed = 0

    for item in raw_urls:
        if processed >= max_articles: break
        url = item["url"]
        if url in seen: continue
        seen.add(url)

        print(f"[{processed+1}/{max_articles}] {url[:60]}")
        scraped = scrape_article(url)
        if not scraped: continue

        # If choice is 1 or 3, use Groq
        if nlp_choice in ["1", "3"]:
            extracted = extract_with_groq(scraped) or {}
            time.sleep(RATE_LIMIT_SEC)
        else:
            extracted = {} # Let local NLP handle it later

        article = validate_and_merge(item, scraped, extracted)
        if article and article["title"] and article["description"]:
            results.append(article)
            processed += 1
            print(f"    [OK] {article['title'][:50]}")

    return results
