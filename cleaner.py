import re
import pandas as pd
import numpy as np
from dateutil import parser as dateparser
from langdetect import detect, LangDetectException

VALID_CATEGORIES = ["technology", "politics", "sports", "business", "health", "science", "entertainment", "general"]
VALID_SENTIMENTS = ["positive", "neutral", "negative"]

BOILERPLATE_PHRASES = [
    "subscribe to read", "sign in to read", "cookie policy", 
    "privacy policy", "terms of service", "javascript is required"
]

def clean_text(text: str) -> str:
    if not isinstance(text, str): return ""
    text = re.sub(r"<[^>]+>", " ", text) # HTML
    text = re.sub(r"\s+", " ", text)     # Whitespace
    text = re.sub(r"[^\x00-\x7F]+", " ", text) # Non-ASCII
    text = re.sub(r"http\S+", "", text)  # URLs
    return text.strip()

def is_boilerplate(text: str) -> bool:
    if not isinstance(text, str): return True
    text_lower = text.lower()
    hits = sum(1 for phrase in BOILERPLATE_PHRASES if phrase in text_lower)
    return hits >= 1

def run_cleaner(raw_data: list[dict]) -> pd.DataFrame:
    print("\n--- Running Cleaner ---")
    if not raw_data:
        print("No raw data to clean.")
        return pd.DataFrame()
        
    df = pd.DataFrame(raw_data)
    
    # Clean text
    df["title"] = df["title"].apply(clean_text)
    df["description"] = df["description"].apply(clean_text)
    
    # Normalize
    df["category"] = df["category"].str.lower().apply(lambda x: x if x in VALID_CATEGORIES else "general")
    df["sentiment"] = df["sentiment"].str.lower().apply(lambda x: x if x in VALID_SENTIMENTS else "neutral")
    
    # Filtering Logic (Stage 2)
    df["is_clean"] = True
    
    # 1. Description length
    df.loc[df["description"].str.split().str.len().lt(10), "is_clean"] = False
    
    # 2. Boilerplate
    df.loc[df["description"].apply(is_boilerplate), "is_clean"] = False
    
    # 3. Language detection (keep only English)
    def detect_lang(text):
        try: return detect(str(text))
        except: return "unknown"
    
    df["lang"] = df["description"].apply(detect_lang)
    df.loc[df["lang"] != "en", "is_clean"] = False
    
    clean_df = df[df["is_clean"]].copy().reset_index(drop=True)
    print(f"Cleaned data: {len(clean_df)} valid articles out of {len(df)}.")
    return clean_df
