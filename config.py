import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── 1. Database Connections ────────────────────────────────────────────────
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///recommendations.db")
    RAW_DATA_URL = os.getenv("RAW_DATA_URL", "sqlite:///raw_data.db")

    # ── 2. API Keys ────────────────────────────────────────────────────────────
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    # ── 3. Pipeline Thresholds & Parameters ───────────────────────────────────
    MAX_ARTICLES_PER_FEED  = int(os.getenv("MAX_ARTICLES_PER_FEED",  50))
    MIN_WORD_COUNT         = int(os.getenv("MIN_WORD_COUNT",          15))
    TFIDF_MAX_FEATURES     = int(os.getenv("TFIDF_MAX_FEATURES",    5000))
    # Backward‑compatible aliases for legacy code
    DATABASE_URI = DATABASE_URL
    RAW_DATA_URI = RAW_DATA_URL

    # ── 4. Centralized Category Mappings ──────────────────────────────────────
    CATEGORY_MAPPING = {
        "technology": ["ai", "software", "apple", "google", "cybersecurity", "tech", "startup"],
        "business":   ["economy", "stock", "market", "ceo", "funding", "revenue", "investor"],
        "politics":   ["government", "election", "president", "senate", "law", "policy"],
        "sports":     ["football", "basketball", "nba", "fifa", "olympics"],
        "health":     ["vaccine", "covid", "fda", "hospital", "nutrition"],
    }

    # ── 5. RSS Feeds (103 sources — keyed by human-readable name) ─────────────
    RSS_FEEDS = {
        # ── UAE / Gulf / Arabic ───────────────────────────────────────────────
        "Khaleej Times"             : "https://www.khaleejtimes.com/rss",
        "Gulf News"                 : "https://gulfnews.com/rss",
        "The National UAE"          : "https://www.thenationalnews.com/rss",
        "Gulf Business"             : "https://gulfbusiness.com/feed/",
        "Emirates 24/7"             : "https://www.emirates247.com/rss",
        "Arabian Business"          : "https://www.arabianbusiness.com/rss",
        "Al Arabiya English"        : "https://english.alarabiya.net/tools/rss",
        "Al Jazeera English"        : "https://www.aljazeera.com/xml/rss/all.xml",
        "Zawya UAE"                 : "https://www.zawya.com/rss/uae/",
        "Dubai Eye News"            : "https://www.dubaieye1038.com/feed/",
        "Al Khaleej (Arabic)"       : "https://www.alkhaleej.ae/rss.xml",
        "Al Bayan (Arabic)"         : "https://albayan.ae/rss",
        "WAM UAE State News"        : "https://wam.ae/rss.xml",
        "Time Out Dubai"            : "https://www.timeoutdubai.com/rss",
        "What's On Dubai"           : "https://whatson.ae/feed/",
        "Construction Week Online"  : "https://www.constructionweekonline.com/rss",
        "MEED Middle East"          : "https://www.meed.com/rss/",
        "Arab News"                 : "https://www.arabnews.com/rss.xml",
        "Saudi Gazette"             : "https://saudigazette.com.sa/rss",
        "Oman Observer"             : "https://www.omanobserver.om/feed/",
        "Kuwait Times"              : "https://www.kuwaittimes.com/feed/",
        "Bahrain News Agency"       : "https://www.bna.bh/rss.xml",
        "Qatar Tribune"             : "https://www.qatar-tribune.com/rss",
        "Middle East Eye"           : "https://www.middleeasteye.net/rss",
        "Roya News Jordan"          : "https://en.royanews.tv/rss.xml",

        # ── China / Hong Kong / Asia ──────────────────────────────────────────
        "China Daily"               : "https://www.chinadaily.com.cn/rss/china_rss.xml",
        "China Daily Business"      : "https://www.chinadaily.com.cn/rss/bizChina_rss.xml",
        "CGTN World"                : "https://www.cgtn.com/subscribe/rss/section/world.xml",
        "CGTN Business"             : "https://www.cgtn.com/subscribe/rss/section/business.xml",
        "CGTN Science"              : "https://www.cgtn.com/subscribe/rss/section/sci-tech.xml",
        "Xinhua Top News"           : "https://www.xinhuanet.com/english/rss/worldrss.xml",
        "Xinhua China"              : "https://www.xinhuanet.com/english/rss/chinarss.xml",
        "South China Morning Post"  : "https://www.scmp.com/rss/2/feed",
        "SCMP Business"             : "https://www.scmp.com/rss/92/feed",
        "SCMP Tech"                 : "https://www.scmp.com/rss/36/feed",
        "Hong Kong Free Press"      : "https://hongkongfp.com/feed/",
        "Caixin Global"             : "https://www.caixinglobal.com/rss/index.xml",
        "Sixth Tone China"          : "https://www.sixthtone.com/rss",
        "The Diplomat Asia"         : "https://thediplomat.com/feed/",
        "Asia Times"                : "https://asiatimes.com/feed/",
        "Nikkei Asia"               : "https://asia.nikkei.com/rss/feed/nar",
        "Japan Times"               : "https://www.japantimes.co.jp/feed/",
        "Korea Herald"              : "http://www.koreaherald.com/rss/050000000000.xml",
        "Times of India"            : "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "Straits Times Singapore"   : "https://www.straitstimes.com/global/rss.xml",

        # ── International / Global ────────────────────────────────────────────
        "BBC Top Stories"           : "http://feeds.bbci.co.uk/news/rss.xml",
        "BBC World"                 : "http://feeds.bbci.co.uk/news/world/rss.xml",
        "BBC Technology"            : "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "BBC Business"              : "http://feeds.bbci.co.uk/news/business/rss.xml",
        "BBC Health"                : "http://feeds.bbci.co.uk/news/health/rss.xml",
        "Reuters Top News"          : "https://feeds.reuters.com/reuters/topNews",
        "Reuters World"             : "https://feeds.reuters.com/Reuters/worldNews",
        "Reuters Business"          : "https://feeds.reuters.com/reuters/businessNews",
        "Reuters Technology"        : "https://feeds.reuters.com/reuters/technologyNews",
        "AP Top News"               : "https://feeds.apnews.com/rss/apf-topnews",
        "AP World"                  : "https://feeds.apnews.com/rss/apf-WorldNews",
        "AP Business"               : "https://feeds.apnews.com/rss/apf-business",
        "The Guardian World"        : "https://www.theguardian.com/world/rss",
        "The Guardian Tech"         : "https://www.theguardian.com/uk/technology/rss",
        "The Guardian Business"     : "https://www.theguardian.com/business/rss",
        "The Guardian Environment"  : "https://www.theguardian.com/environment/rss",

        # ── Technology ────────────────────────────────────────────────────────
        "TechCrunch"                : "https://techcrunch.com/feed/",
        "TechCrunch AI"             : "https://techcrunch.com/category/artificial-intelligence/feed/",
        "The Verge"                 : "https://www.theverge.com/rss/index.xml",
        "Wired"                     : "https://www.wired.com/feed/rss",
        "Ars Technica"              : "http://feeds.arstechnica.com/arstechnica/index",
        "MIT Tech Review"           : "https://www.technologyreview.com/feed/",
        "VentureBeat"               : "https://venturebeat.com/feed/",
        "ZDNet"                     : "https://www.zdnet.com/news/rss.xml",
        "Engadget"                  : "https://www.engadget.com/rss.xml",
        "Mashable Tech"             : "https://mashable.com/feeds/rss/tech",

        # ── Business / Finance ────────────────────────────────────────────────
        "Bloomberg Technology"      : "https://feeds.bloomberg.com/technology/news.rss",
        "CNBC World"                : "https://www.cnbc.com/id/100727362/device/rss/rss.html",
        "CNBC Finance"              : "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "Financial Times World"     : "https://www.ft.com/world?format=rss",
        "Forbes Business"           : "https://www.forbes.com/business/feed/",
        "Forbes Tech"               : "https://www.forbes.com/technology/feed/",
        "Business Insider"          : "https://feeds.businessinsider.com/custom/all",
        "MarketWatch"               : "https://feeds.marketwatch.com/marketwatch/topstories/",
        "Investopedia"              : "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline",
        "CoinDesk Crypto"           : "https://www.coindesk.com/arc/outboundfeeds/rss/",

        # ── Health & Science ──────────────────────────────────────────────────
        "WHO News"                  : "https://www.who.int/rss-feeds/news-english.xml",
        "Harvard Health"            : "https://www.health.harvard.edu/blog/feed",
        "Science Daily"             : "https://www.sciencedaily.com/rss/all.xml",
        "Nature News"               : "https://www.nature.com/nature.rss",
        "NASA Breaking News"        : "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "New Scientist"             : "https://www.newscientist.com/feed/home/",
        "Medical News Today"        : "https://www.medicalnewstoday.com/rss",

        # ── Sports ────────────────────────────────────────────────────────────
        "ESPN Headlines"            : "https://www.espn.com/espn/rss/news",
        "BBC Sport"                 : "http://feeds.bbci.co.uk/sport/rss.xml",
        "Sky Sports"                : "https://www.skysports.com/rss/12040",
        "Goal.com Football"         : "https://www.goal.com/feeds/en/news",
        "Sports Illustrated"        : "https://www.si.com/rss/si_topstories.rss",

        # ── Environment / Travel ──────────────────────────────────────────────
        "National Geographic"       : "https://www.nationalgeographic.com/news/rss",
        "BBC Travel"                : "http://feeds.bbci.co.uk/travel/rss.xml",
        "Lonely Planet"             : "https://www.lonelyplanet.com/news/feed",
        "CNN Travel"                : "http://rss.cnn.com/rss/edition_travel.rss",
        "World Wildlife Fund"       : "https://www.worldwildlife.org/magazine/rss",

        # ── Entertainment / Culture ───────────────────────────────────────────
        "Variety"                   : "https://variety.com/feed/",
        "Hollywood Reporter"        : "https://www.hollywoodreporter.com/feed/",
        "Rolling Stone"             : "https://www.rollingstone.com/feed/",
        "Pitchfork Music"           : "https://pitchfork.com/rss/news/",
        "Deadline Hollywood"        : "https://deadline.com/feed/",
    }


# Singleton — import `settings` everywhere instead of instantiating Config directly
settings = Config()
# Backward‑compatibility alias for legacy imports
config = settings
# Alias for historic DATABASE_URI name used in older code
DATABASE_URI = settings.DATABASE_URL
RAW_DATA_URI = settings.RAW_DATA_URL
