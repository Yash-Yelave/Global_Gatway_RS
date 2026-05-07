# Database Schema

Generated: 2026-05-04

# recommendations.db

Tables: articles, category_rankings, raw_articles, similar_articles, trending_articles

## articles

| column | type | not null | default | pk |
|---|---|---:|---|---:|
| `article_id` | `TEXT` | 0 | `NULL` | 0 |
| `url` | `TEXT` | 0 | `NULL` | 0 |
| `source` | `TEXT` | 0 | `NULL` | 0 |
| `title` | `TEXT` | 0 | `NULL` | 0 |
| `description` | `TEXT` | 0 | `NULL` | 0 |
| `author` | `TEXT` | 0 | `NULL` | 0 |
| `tags` | `TEXT` | 0 | `NULL` | 0 |
| `category` | `TEXT` | 0 | `NULL` | 0 |
| `sentiment` | `TEXT` | 0 | `NULL` | 0 |
| `publish_date` | `TEXT` | 0 | `NULL` | 0 |
| `top_image` | `TEXT` | 0 | `NULL` | 0 |
| `scraped_at` | `TEXT` | 0 | `NULL` | 0 |
| `is_clean` | `INTEGER` | 0 | `NULL` | 0 |
| `lang` | `TEXT` | 0 | `NULL` | 0 |
| `freshness_decay_score` | `REAL` | 0 | `NULL` | 0 |
| `view_count` | `INTEGER` | 0 | `NULL` | 0 |
| `trending_score` | `REAL` | 0 | `NULL` | 0 |
| `category_rank` | `REAL` | 0 | `NULL` | 0 |

**Create SQL (from sqlite_master)**

```sql
CREATE TABLE "articles" (
"article_id" TEXT,
  "url" TEXT,
  "source" TEXT,
  "title" TEXT,
  "description" TEXT,
  "author" TEXT,
  "tags" TEXT,
  "category" TEXT,
  "sentiment" TEXT,
  "publish_date" TEXT,
  "top_image" TEXT,
  "scraped_at" TEXT,
  "is_clean" INTEGER,
  "lang" TEXT,
  "freshness_decay_score" REAL,
  "view_count" INTEGER,
  "trending_score" REAL,
  "category_rank" REAL
);
```

## category_rankings

| column | type | not null | default | pk |
|---|---|---:|---|---:|
| `article_id` | `TEXT` | 0 | `NULL` | 0 |
| `title` | `TEXT` | 0 | `NULL` | 0 |
| `category` | `TEXT` | 0 | `NULL` | 0 |
| `category_rank` | `REAL` | 0 | `NULL` | 0 |
| `trending_score` | `REAL` | 0 | `NULL` | 0 |

**Create SQL (from sqlite_master)**

```sql
CREATE TABLE "category_rankings" (
"article_id" TEXT,
  "title" TEXT,
  "category" TEXT,
  "category_rank" REAL,
  "trending_score" REAL
);
```

## raw_articles

| column | type | not null | default | pk |
|---|---|---:|---|---:|
| `article_id` | `VARCHAR` | 1 | `NULL` | 1 |
| `payload_json` | `JSON` | 1 | `NULL` | 0 |
| `scraped_at` | `VARCHAR` | 0 | `NULL` | 0 |

**Indexes**

- `sqlite_autoindex_raw_articles_1` (unique=1, origin=pk, partial=0): `article_id`

**Create SQL (from sqlite_master)**

```sql
CREATE TABLE raw_articles (
	article_id VARCHAR NOT NULL, 
	payload_json JSON NOT NULL, 
	scraped_at VARCHAR, 
	PRIMARY KEY (article_id)
);
```

## similar_articles

| column | type | not null | default | pk |
|---|---|---:|---|---:|
| `article_id` | `TEXT` | 0 | `NULL` | 0 |
| `similar_articles_json` | `TEXT` | 0 | `NULL` | 0 |

**Create SQL (from sqlite_master)**

```sql
CREATE TABLE "similar_articles" (
"article_id" TEXT,
  "similar_articles_json" TEXT
);
```

## trending_articles

| column | type | not null | default | pk |
|---|---|---:|---|---:|
| `article_id` | `TEXT` | 0 | `NULL` | 0 |
| `title` | `TEXT` | 0 | `NULL` | 0 |
| `category` | `TEXT` | 0 | `NULL` | 0 |
| `view_count` | `INTEGER` | 0 | `NULL` | 0 |
| `freshness_decay_score` | `REAL` | 0 | `NULL` | 0 |
| `trending_score` | `REAL` | 0 | `NULL` | 0 |

**Create SQL (from sqlite_master)**

```sql
CREATE TABLE "trending_articles" (
"article_id" TEXT,
  "title" TEXT,
  "category" TEXT,
  "view_count" INTEGER,
  "freshness_decay_score" REAL,
  "trending_score" REAL
);
```


# raw_data.db

Tables: raw_articles

## raw_articles

| column | type | not null | default | pk |
|---|---|---:|---|---:|
| `article_id` | `TEXT` | 0 | `NULL` | 0 |
| `url` | `TEXT` | 0 | `NULL` | 0 |
| `source` | `TEXT` | 0 | `NULL` | 0 |
| `title` | `TEXT` | 0 | `NULL` | 0 |
| `description` | `TEXT` | 0 | `NULL` | 0 |
| `author` | `TEXT` | 0 | `NULL` | 0 |
| `tags` | `TEXT` | 0 | `NULL` | 0 |
| `category` | `TEXT` | 0 | `NULL` | 0 |
| `sentiment` | `TEXT` | 0 | `NULL` | 0 |
| `publish_date` | `TEXT` | 0 | `NULL` | 0 |
| `top_image` | `TEXT` | 0 | `NULL` | 0 |
| `scraped_at` | `TEXT` | 0 | `NULL` | 0 |

**Create SQL (from sqlite_master)**

```sql
CREATE TABLE "raw_articles" (
"article_id" TEXT,
  "url" TEXT,
  "source" TEXT,
  "title" TEXT,
  "description" TEXT,
  "author" TEXT,
  "tags" TEXT,
  "category" TEXT,
  "sentiment" TEXT,
  "publish_date" TEXT,
  "top_image" TEXT,
  "scraped_at" TEXT
);
```

