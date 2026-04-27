import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from database import init_db, engine
from scraper import run_scraper
from cleaner import run_cleaner
from nlp_pipeline import run_nlp
from recommender import run_recommender

def run_pipeline():
    """
    Phase 3: The Integrator
    Executes the steps sequentially: Scrape -> Clean -> Store -> NLP Enrich -> Calculate Recommendations.
    """
    print("--- Starting Autonomous News Processing Pipeline ---")
    
    # Step 1: Scrape
    print("[1/5] Scraping data...")
    raw_data = run_scraper()
    
    # Step 2: Clean
    print("[2/5] Cleaning data...")
    cleaned_data = run_cleaner(raw_data)
    
    # Step 3: Store to Database (Raw/Cleaned)
    print("[3/5] Storing to Database...")
    # TODO: Paste logic to use database.get_session() to insert articles
    
    # Step 4: NLP Enrich
    print("[4/5] Enriching with NLP (spaCy NER, TextBlob)...")
    nlp_data = run_nlp(cleaned_data)
    
    # Step 5: Calculate Recommendations
    print("[5/5] Calculating TF-IDF and Recommendations...")
    recommendations = run_recommender(nlp_data)
    
    print("--- Pipeline Completed Successfully ---")

def verify_output():
    """
    Phase 4: Output Verification
    Queries the final database tables and uses pandas to print the first 5 rows to the console.
    """
    print("\n" + "="*50)
    print("PHASE 4: OUTPUT VERIFICATION (SQLite DB)")
    print("="*50)
    
    try:
        # We query the sqlite engine directly using pandas
        trending_query = "SELECT * FROM trending_articles LIMIT 5"
        similar_query = "SELECT * FROM similar_articles LIMIT 5"
        category_query = "SELECT * FROM category_rankings LIMIT 5"
        
        trending_df = pd.read_sql(trending_query, con=engine)
        similar_df = pd.read_sql(similar_query, con=engine)
        category_df = pd.read_sql(category_query, con=engine)

        print("\n--- Top 5 Trending Articles ---")
        if not trending_df.empty:
            print(trending_df.to_markdown(index=False))
        else:
            print("No data found in trending_articles table.")

        print("\n--- Top 5 Similar Articles ---")
        if not similar_df.empty:
            print(similar_df.to_markdown(index=False))
        else:
            print("No data found in similar_articles table.")

        print("\n--- Top 5 Category Rankings ---")
        if not category_df.empty:
            print(category_df.to_markdown(index=False))
        else:
            print("No data found in category_rankings table.")
            
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    print("Initializing Database...")
    # Ensure tables exist
    init_db()
    
    # Run the pipeline once to populate data
    run_pipeline()
    
    # Verify the output by printing pandas dataframes
    verify_output()
    
    # Set up APScheduler to run the pipeline automatically
    # Uncomment the below lines to run scheduling (e.g., every 6 hours)
    
    # print("\nStarting background scheduler (every 6 hours)... Press Ctrl+C to exit.")
    # scheduler = BlockingScheduler()
    # scheduler.add_job(run_pipeline, 'interval', hours=6)
    # try:
    #     scheduler.start()
    # except (KeyboardInterrupt, SystemExit):
    #     pass
