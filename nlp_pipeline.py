import spacy
from textblob import TextBlob
from datetime import datetime
from dateutil import parser as dateparser
import pandas as pd
import json
import math

try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("Warning: en_core_web_sm not found. Run python -m spacy download en_core_web_sm")

CATEGORY_MAPPING = {
    "technology": ["ai", "artificial intelligence", "software", "apple", "google", "cybersecurity", "tech", "app", "cloud", "crypto"],
    "business": ["economy", "stock", "market", "startup", "ceo", "funding", "revenue", "investor", "wall street", "inflation"],
    "politics": ["government", "election", "president", "senate", "law", "policy", "congress", "diplomacy", "minister"],
    "sports": ["football", "basketball", "fifa", "nba", "championship", "tournament", "coach", "league", "olympics"],
    "health": ["vaccine", "covid", "fda", "hospital", "mental health", "nutrition", "disease", "treatment", "research"]
}

DECAY_RATE = 0.1

def extract_keywords(text):
    if not str(text).strip() or pd.isna(text): return []
    doc = nlp(str(text)[:2000])
    keywords = set()
    valid_ents = {'PERSON', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT'}
    for ent in doc.ents:
        if ent.label_ in valid_ents:
            keywords.add(ent.text.lower().strip())
    for chunk in doc.noun_chunks:
        if chunk.root.pos_ != 'PRON' and len(chunk.text) > 2:
            clean_chunk = " ".join([t.text for t in chunk if t.pos_ != 'DET'])
            if clean_chunk:
                keywords.add(clean_chunk.lower().strip())
    return list(keywords)

def get_textblob_sentiment(text):
    if pd.isna(text): return "neutral"
    polarity = TextBlob(str(text)).sentiment.polarity
    if polarity > 0.05: return "positive"
    elif polarity < -0.05: return "negative"
    return "neutral"

def auto_categorize(keywords, current_cat):
    # If using Local NLP, categorize based on keywords
    scores = {cat: 0 for cat in CATEGORY_MAPPING.keys()}
    for kw in keywords:
        for category, target_words in CATEGORY_MAPPING.items():
            if any(target in kw for target in target_words):
                scores[category] += 1
    best_category = max(scores, key=scores.get)
    # If no matches, fallback to general or existing category
    if scores[best_category] == 0:
        return current_cat if current_cat and current_cat != "general" else "general"
    return best_category

def calculate_freshness(date_val):
    if not date_val or pd.isna(date_val): return 0.5
    try:
        today = datetime.utcnow().date()
        pub_date = dateparser.parse(str(date_val)).date()
        days_old = max(0, (today - pub_date).days)
        score = math.exp(-DECAY_RATE * days_old)
        return round(score, 4)
    except:
        return 0.5

def run_nlp(df: pd.DataFrame, nlp_choice: str) -> pd.DataFrame:
    print("\n--- Running NLP Pipeline ---")
    if df.empty: return df

    df['full_text'] = df['title'].fillna("") + ". " + df['description'].fillna("")

    # If Local NLP (2 or 3) is chosen, override or supplement tags/sentiment
    if nlp_choice in ["2", "3"]:
        print("Extracting keywords using spaCy...")
        df['nlp_keywords'] = df['full_text'].apply(extract_keywords)
        
        print("Computing TextBlob sentiment...")
        df['sentiment'] = df['full_text'].apply(get_textblob_sentiment)
        
        print("Auto-categorizing...")
        df['category'] = df.apply(lambda row: auto_categorize(row['nlp_keywords'], row['category']), axis=1)
        
        # Serialize to match the DB
        df['tags'] = df['nlp_keywords']
        df = df.drop(columns=['nlp_keywords'])

    # Always calculate freshness
    print("Calculating freshness decay...")
    df['freshness_decay_score'] = df['publish_date'].apply(calculate_freshness)
    
    # Store tags as json strings for SQLite compatibility
    df['tags'] = df['tags'].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)
    
    df = df.drop(columns=['full_text'])
    return df
