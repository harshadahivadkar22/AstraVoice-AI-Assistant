import logging
import requests
import config
from typing import Optional
from services.models import NewsArticle

# Get module-specific logger
logger = logging.getLogger("AstraVoice.NewsService")

class NewsService:
    """
    NewsService interacts with the NewsAPI to retrieve the top 5 articles
    for a chosen category (Technology, Business, Sports, or General).
    If the API key is not configured, it generates realistic mock news headlines.
    """
    def __init__(self) -> None:
        """
        Initializes the News Service with settings from config.py.
        """
        self.api_key: str = config.NEWS_API_KEY
        self.base_url: str = "https://newsapi.org/v2/top-headlines"
        logger.info("NewsService initialized.")

    def is_api_key_configured(self) -> bool:
        """
        Checks if the configured API key is valid (not the placeholder).

        Returns:
            bool: True if key is set and is not the default placeholder.
        """
        is_configured = bool(self.api_key and self.api_key != "your_newsapi_key_here")
        logger.info(f"NewsService: API Key configured checks returned: {is_configured}")
        return is_configured

    def get_top_headlines(self, category: str = "general", limit: int = 5) -> Optional[list[dict]]:
        """
        Fetches the top headlines for a given category.

        Args:
            category (str): News category (e.g., 'technology', 'business', 'sports', 'general').
            limit (int): Number of headlines to retrieve. Default is 5.

        Returns:
            Optional[list[dict]]: List of articles, where each article is a dict containing 'title' and 'source'.
                                  Returns None if fetch fails.
        """
        # Sanitize category input: alphanumeric only, limit length to 20
        import re
        sanitized_category = re.sub(r'[^a-zA-Z0-9]', '', category).lower().strip()[:20]
        if not sanitized_category:
            sanitized_category = "general"

        # If API key is not set, run in mock fallback mode
        if not self.is_api_key_configured():
            logger.info(f"News API Key is placeholder. Falling back to mock headlines for category '{sanitized_category}'.")
            return self._get_mock_headlines(sanitized_category, limit)

        try:
            params = {
                'category': sanitized_category,
                'pageSize': limit,
                'language': 'en',
                'apiKey': self.api_key
            }
            
            logger.info(f"Sending headlines request to NewsAPI for category: '{sanitized_category}'.")
            response = requests.get(self.base_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                parsed_articles = []
                for art in articles[:limit]:
                    source_obj = art.get('source')
                    source_name = 'Unknown Source'
                    if isinstance(source_obj, dict):
                        source_name = source_obj.get('name', 'Unknown Source')
                        
                    parsed_articles.append(NewsArticle(
                        title=art.get('title', 'Unknown Headline'),
                        source=source_name
                    ))
                logger.info(f"Successfully retrieved and parsed {len(parsed_articles)} headlines for '{sanitized_category}'.")
                return parsed_articles
            elif response.status_code == 401:
                print("News API Error: Invalid API Key. Falling back to mock news.")
                logger.error("News query failed: Invalid NewsAPI Key. Falling back to mock headlines.")
                return self._get_mock_headlines(sanitized_category, limit)
            else:
                print(f"News API Error: Received status code {response.status_code}.")
                logger.error(f"News query failed: API returned status {response.status_code}.")
                return None
                
        except requests.RequestException as e:
            # Redact API key if it is leaked in exception details or URLs
            err_str = str(e)
            if self.api_key and self.api_key in err_str:
                err_str = err_str.replace(self.api_key, "[REDACTED_API_KEY]")
            print(f"News API connection error. (Details suppressed for security)")
            logger.error(f"News query failed due to network exception: {err_str}")
            return None

    def _get_mock_headlines(self, category: str, limit: int) -> list[dict]:
        """
        Generates realistic mock news headlines based on the category for testing.

        Args:
            category (str): News category.
            limit (int): Number of headlines to return.

        Returns:
            list[dict]: Mocked news articles list.
        """
        cat_clean = category.lower().strip()
        
        mock_database = {
            "technology": [
                {"title": "OpenAI Launches Advanced AI Search Engine Integrated into ChatGPT", "source": "TechCrunch"},
                {"title": "Google Announces Next-Generation Quantum Computing Prototype with Higher Qubits", "source": "The Verge"},
                {"title": "Apple Previews Major Hardware Redesign for Next-Generation MacBook Pros", "source": "MacRumors"},
                {"title": "New Web Standards Group Formed to Regulate VR and AR Browsing Architectures", "source": "Wired"},
                {"title": "Major Cybersecurity Patch Released for Critical OpenSSL Vulnerability", "source": "InfoSec News"}
            ],
            "business": [
                {"title": "Federal Reserve Holds Interest Rates Steady Amid Persistent Inflation Metrics", "source": "Wall Street Journal"},
                {"title": "Global Logistics Hub Reports 12% Rise in Container Trade Shipping Volumes", "source": "Bloomberg"},
                {"title": "Tech Stocks Rally Drives Major Indices to Record-High Closing Marks", "source": "Reuters"},
                {"title": "Automotive Giant Details $15 Billion Expansion into Solid-State Battery Facilities", "source": "CNBC"},
                {"title": "New Startup Secures Landmark Funding to Revolutionize Agricultural Supply Chains", "source": "Forbes"}
            ],
            "sports": [
                {"title": "Championship Finals: Underdog Team Pulls Off Thrilling Overtime Victory", "source": "ESPN"},
                {"title": "Star Striker Signs Record-Breaking Five-Year Deal in Premier League Transfer", "source": "Sky Sports"},
                {"title": "World Tennis Seed Advances to Semi-Finals in Straight Sets", "source": "Sports Illustrated"},
                {"title": "Olympic Committee Approves Three New Dynamic Sports for Upcoming Games", "source": "BBC Sport"},
                {"title": "National Athletics Championship Records New Historical Sprint Benchmark", "source": "Athletics Weekly"}
            ],
            "general": [
                {"title": "Global Conservation Agreement Declares 20% More Protected Marine Zones", "source": "National Geographic"},
                {"title": "Transit Authority Unveils Ambitious High-Speed Rail Corridor Integration Plans", "source": "Metro Transit News"},
                {"title": "New Archaeological Excavation Unearths Ancient Settlement in Mediterranean Region", "source": "Archaeology Journal"},
                {"title": "Deep Ocean Expedition Discovers Five Previously Unknown Marine Species", "source": "Science Daily"},
                {"title": "Civic Union Highlights New Community Integration and Green Space Developments", "source": "City News"}
            ]
        }
        
        # Select matching category list or fallback to general
        articles = mock_database.get(cat_clean, mock_database["general"])
        
        print(f"[OFFLINE/MOCK MODE] Synthesizing mock news headlines for category '{cat_clean}'...")
        logger.info(f"Synthesizing offline mock headlines for category: '{cat_clean}'")
        
        return [NewsArticle(title=art["title"], source=art["source"]) for art in articles[:limit]]

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Testing NewsService...")
    service = NewsService()
    print(service.get_top_headlines("technology"))
