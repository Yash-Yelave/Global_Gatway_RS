# Old Code: repository.py

This file contains the data access layer for interacting with the database using SQLAlchemy, structured via a repository pattern.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import Base, Article

# Database Connection String
# Format: postgresql://username:password@host:port/database_name
DATABASE_URL = "postgresql://pipeline_user:secure_password123@localhost:5432/global_gateway_db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ArticleRepository:
    def __init__(self):
        self.session = SessionLocal()

    def insert_article(self, article_data: dict):
        """Inserts a new article. Fails silently or handles duplicates via url_hash."""
        try:
            article = Article(**article_data)
            self.session.add(article)
            self.session.commit()
            self.session.refresh(article)
            return article
        except IntegrityError:
            self.session.rollback()
            print(f"Article with URL hash {article_data.get('url_hash')} already exists.")
            return None
        except Exception as e:
            self.session.rollback()
            print(f"Error inserting article: {e}")
            return None

    def get_article_by_hash(self, url_hash: str):
        """Retrieves an article by its unique URL hash."""
        return self.session.query(Article).filter(Article.url_hash == url_hash).first()

    def update_article(self, url_hash: str, update_data: dict):
        """Updates specific fields of an existing article."""
        article = self.get_article_by_hash(url_hash)
        if not article:
            print("Article not found for update.")
            return None

        for key, value in update_data.items():
            if hasattr(article, key):
                setattr(article, key, value)
        
        self.session.commit()
        self.session.refresh(article)
        return article

    def delete_article(self, url_hash: str):
        """Deletes an article by its URL hash."""
        article = self.get_article_by_hash(url_hash)
        if article:
            self.session.delete(article)
            self.session.commit()
            print(f"Deleted article: {url_hash}")
            return True
        return False

    def close(self):
        self.session.close()
```
