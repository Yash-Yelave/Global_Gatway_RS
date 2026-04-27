from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url_hash = Column(String(32), unique=True, nullable=False, index=True) # MD5 hash
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    author = Column(String, default="Unknown")
    published_at = Column(DateTime)
    
    # Relationships / Foreign Keys
    category_id = Column(Integer) 
    source_id = Column(Integer)
    
    # Phase 2 Enriched Features
    tags = Column(JSONB) # Storing tags as native JSON
    sentiment_score = Column(Float)
    sentiment_label_vader = Column(String(20))
    top_image = Column(String)
    is_clean = Column(Boolean, default=True)
    word_count = Column(Integer)
    reading_time_mins = Column(Integer)
    keyword_density = Column(Float)
    
    # Named Entity Recognition (NER)
    entities_persons = Column(JSONB)
    entities_organizations = Column(JSONB)
    entities_locations = Column(JSONB)
    
    # Source & Clustering Metrics
    source_region = Column(String(50))
    source_tier = Column(Integer)
    sub_category = Column(String(100))
    story_id = Column(Integer) # For semantic story grouping
    
    # Full-Text Search Vector
    search_vector = Column(TSVECTOR)

    # Database Indexes for Query Optimization
    __table_args__ = (
        Index('ix_articles_published_at', 'published_at'),
        Index('ix_articles_category_id', 'category_id'),
        Index('ix_articles_source_id', 'source_id'),
        # GIN Index for fast full-text search on the tsvector column
        Index('ix_articles_search_vector', 'search_vector', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<Article(title='{self.title}', url_hash='{self.url_hash}')>"