from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from config import config

# Using SQLite for local testing as per phase requirements
engine = create_engine(config.DATABASE_URI, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    url = Column(String, unique=True, index=True)
    published_at = Column(DateTime)
    source = Column(String)

class TrendingArticle(Base):
    __tablename__ = "trending_articles"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer)
    trending_score = Column(Float)

class SimilarArticle(Base):
    __tablename__ = "similar_articles"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer)
    similar_article_id = Column(Integer)
    similarity_score = Column(Float)

class CategoryRanking(Base):
    __tablename__ = "category_rankings"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)
    rank_score = Column(Float)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()
