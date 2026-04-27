import os
import sys
import sqlite3
import pandas as pd
from scraper import run_scraper
from cleaner import run_cleaner
from nlp_pipeline import run_nlp
from recommender import run_recommender
from database import init_db, engine
from config import config

def run_pipeline(nlp_choice: str):
    print("\n" + "="*50)
    print("STARTING AUTONOMOUS NEWS PIPELINE")
    print("="*50)
    
    # 1. Scrape
    raw_data = run_scraper(nlp_choice=nlp_choice, max_articles=100)
    
    # 2. Clean
    cleaned_df = run_cleaner(raw_data)
    
    # 3. NLP Enrich
    nlp_df = run_nlp(cleaned_df, nlp_choice=nlp_choice)
    
    # 4. Calculate Recommendations
    tables = run_recommender(nlp_df)
    if not tables:
        print("Pipeline aborted: no data processed.")
        return

    # 5. Save to Database
    print("\n--- Saving to SQLite ---")
    conn = sqlite3.connect(config.DATABASE_URI.replace("sqlite:///", ""))
    
    # Save the DataFrames directly via pandas to_sql (similar to old colab flow)
    tables["master"].to_sql("articles", conn, if_exists="replace", index=False)
    tables["trending"].to_sql("trending_articles", conn, if_exists="replace", index=False)
    tables["similar"].to_sql("similar_articles", conn, if_exists="replace", index=False)
    tables["category_rankings"].to_sql("category_rankings", conn, if_exists="replace", index=False)
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*50)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("="*50)

def verify_output():
    print("\n--- Output Verification ---")
    try:
        conn = sqlite3.connect(config.DATABASE_URI.replace("sqlite:///", ""))
        trending_df = pd.read_sql("SELECT * FROM trending_articles LIMIT 10", con=conn)
        similar_df = pd.read_sql("SELECT * FROM similar_articles LIMIT 10", con=conn)
        
        print("\n--- TOP 10 TRENDING ARTICLES ---")
        print(trending_df.to_markdown(index=False))
        
        print("\n--- TOP 10 SIMILAR ARTICLE MAPPINGS (JSON) ---")
        for idx, row in similar_df.iterrows():
            print(f"Article: {row['article_id']} -> {row['similar_articles_json']}")
            
        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}")

if __name__ == "__main__":
    init_db()
    
    print("\n--- Select NLP Pipeline Mode ---")
    print("1. Use Groq LLM (llama-3.1-8b-instant) for Tags & Sentiment")
    print("2. Use Local NLP (spaCy & TextBlob) for Tags & Sentiment")
    print("3. Run Both (Groq first, then override/supplement with Local NLP)")
    
    # Auto-select for headless execution if passed as argument
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        print(f"Choice '{choice}' provided via arguments.")
    else:
        choice = input("Enter choice (1/2/3): ").strip()
        
    if choice not in ["1", "2", "3"]:
        print("Invalid choice. Defaulting to 3 (Run Both).")
        choice = "3"
        
    run_pipeline(choice)
    verify_output()
