import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///news_engine.db')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')

config = Config()
