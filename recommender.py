import pandas as pd
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def run_recommender(df: pd.DataFrame) -> dict:
    print("\n--- Running Recommender Engine ---")
    if df.empty: return {}
    
    # 1. Trending Score Logic
    print("Calculating Trending Scores...")
    np.random.seed(42)
    # Simulate views
    if 'view_count' not in df.columns:
        df['view_count'] = np.random.randint(10, 10000, size=len(df))
    
    df['trending_score'] = np.log1p(df['view_count']) * df['freshness_decay_score']
    
    max_score = df['trending_score'].max()
    if max_score > 0:
        df['trending_score'] = (df['trending_score'] / max_score * 10).round(2)
    else:
        df['trending_score'] = 0.0

    df_trending = df[['article_id', 'title', 'category', 'view_count', 'freshness_decay_score', 'trending_score']]
    df_trending = df_trending.sort_values(by='trending_score', ascending=False)
    
    # 2. TF-IDF Cosine Similarity
    print("Computing Article Similarity Matrix...")
    text_corpus = df['title'].fillna("") + " " + df['description'].fillna("")
    
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(text_corpus)
    cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    similar_articles_data = []
    for idx in range(len(df)):
        art_id = df.iloc[idx]['article_id']
        sim_scores = list(enumerate(cosine_sim_matrix[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]
        top_matches = [{"similar_article_id": df.iloc[i[0]]['article_id'], "similarity_score": round(i[1], 4)} for i in sim_scores]
        similar_articles_data.append({
            "article_id": art_id,
            "similar_articles_json": json.dumps(top_matches)
        })
        
    df_similar = pd.DataFrame(similar_articles_data)
    
    # 3. Category Grouping
    print("Grouping Category Rankings...")
    df['category_rank'] = df.groupby('category')['trending_score'].rank(method='dense', ascending=False)
    df_category_rankings = df[['article_id', 'title', 'category', 'category_rank', 'trending_score']]
    df_category_rankings = df_category_rankings.sort_values(by=['category', 'category_rank'])
    
    return {
        "master": df,
        "trending": df_trending,
        "similar": df_similar,
        "category_rankings": df_category_rankings
    }
