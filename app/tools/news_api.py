import os
import logging
import requests
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Check for NewsAPI key in environment variables (kept for backward compatibility, but we now default to web search)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


def extract_source_info(url: str) -> Dict[str, Any]:
    """
    Extracts cleaner domain name and resolves a human-readable publisher name.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        domain = "unknown"
        
    domain_mapping = {
        "indiatoday.in": "India Today",
        "indianexpress.com": "Indian Express",
        "ndtv.com": "NDTV",
        "republicworld.com": "Republic World",
        "thestatesman.com": "The Statesman",
        "gulfnews.com": "Gulf News",
        "news18.com": "News18",
        "abplive.com": "ABP Live",
        "reuters.com": "Reuters",
        "apnews.com": "AP News",
        "bloomberg.com": "Bloomberg",
        "nytimes.com": "The New York Times",
        "theguardian.com": "The Guardian",
        "bbc.co.uk": "BBC News",
        "bbc.com": "BBC News",
        "cnn.com": "CNN",
        "aljazeera.com": "Al Jazeera",
        "wsj.com": "The Wall Street Journal",
        "ft.com": "Financial Times",
        "economist.com": "The Economist",
        "cnbc.com": "CNBC",
        "independent.co.uk": "The Independent",
    }
    
    name = domain_mapping.get(domain)
    if not name:
        parts = domain.split('.')
        if len(parts) >= 2:
            name = parts[-2].title()
        else:
            name = domain.title()
            
    return {
        "id": domain.replace(".", "-"),
        "name": name,
        "domain": domain,
        "url": f"{parsed.scheme}://{parsed.netloc}" if hasattr(parsed, 'scheme') and parsed.scheme else f"https://{domain}"
    }


def search_duckduckgo(query: str, page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Searches DuckDuckGo HTML version for the query and returns formatted articles.
    """
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
    }
    logger.info(f"Querying DuckDuckGo: {url}")
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = soup.find_all('div', class_='result')
    articles = []
    for res in results:
        title_link = res.find('a', class_='result__a')
        snippet_div = res.find('a', class_='result__snippet')
        
        if title_link:
            title = title_link.get_text().strip()
            href = title_link.get('href', '')
            
            # Clean DuckDuckGo redirect link
            if "/l/?kh=" in href or "uddg=" in href:
                parsed = urllib.parse.urlparse(href)
                queries = urllib.parse.parse_qs(parsed.query)
                if 'uddg' in queries:
                    href = queries['uddg'][0]
            
            if not href.startswith('http') or 'duckduckgo.com' in href:
                continue
                
            snippet = snippet_div.get_text().strip() if snippet_div else ""
            source_info = extract_source_info(href)
            
            articles.append({
                "title": title,
                "author": None,
                "source": source_info,
                "published_at": None,
                "url": href,
                "content": snippet,
                "description": snippet,
                "url_to_image": None,
                "language": "en"
            })
            if len(articles) >= page_size:
                break
    return articles


def search_yahoo(query: str, page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Searches Yahoo Search and returns formatted articles.
    """
    url = f"https://search.yahoo.com/search?p={urllib.parse.quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    logger.info(f"Querying Yahoo Search (Fallback): {url}")
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    h3s = soup.find_all('h3', class_='title')
    articles = []
    for h3 in h3s:
        a_tag = None
        if h3.parent.name == 'a':
            a_tag = h3.parent
        else:
            a_tag = h3.find('a')
            
        if a_tag:
            title = h3.get_text().strip()
            href = a_tag.get('href', '')
            
            # Unpack Yahoo redirect link (uses RU parameter or raw url split)
            if "/RU=" in href or "RU=" in href:
                parsed = urllib.parse.urlparse(href)
                queries = urllib.parse.parse_qs(parsed.query)
                if 'RU' in queries:
                    href = queries['RU'][0]
                else:
                    parts = parsed.path.split('/RU=')
                    if len(parts) > 1:
                        target = parts[1].split('/RK=')[0]
                        href = urllib.parse.unquote(target)
            
            if not href.startswith('http') or 'yahoo.com' in href:
                continue
                
            snippet = ""
            sibling = h3.parent.find_next_sibling('div', class_='compText')
            if sibling:
                snippet = sibling.get_text().strip()
                
            source_info = extract_source_info(href)
            
            articles.append({
                "title": title,
                "author": None,
                "source": source_info,
                "published_at": None,
                "url": href,
                "content": snippet,
                "description": snippet,
                "url_to_image": None,
                "language": "en"
            })
            if len(articles) >= page_size:
                break
    return articles


def fetch_news_articles(query: str, page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Performs web search via DuckDuckGo with a Yahoo fallback.
    If no search engines return results, falls back to generating mock articles.
    """
    logger.info(f"Searching web articles for query: '{query}'")
    articles = []
    try:
        articles = search_duckduckgo(query, page_size)
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}. Trying Yahoo fallback.")
        
    if not articles:
        try:
            articles = search_yahoo(query, page_size)
        except Exception as e:
            logger.error(f"Yahoo Search fallback failed: {e}")
            
    if articles:
        logger.info(f"Web search successfully gathered {len(articles)} article metadata results.")
        return articles
        
    logger.warning("All web search engines returned 0 results. Falling back to mock database articles.")
    return get_mock_articles(query, page_size)


def get_mock_articles(query: str, page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Generates realistic, domain-specific mock articles for testing.
    This guarantees that Phase 2-4 run successfully without external credentials.
    """
    # Normalize query for routing
    q = query.lower()
    
    # Pre-prepared mock articles representing a controversial event with multiple angles
    # (great for summarization, clustering, bias, fact-checking, and consensus testing)
    mock_db = [
        {
            "title": "AetherCorp Announces Launch of NeuralLink-V2 with Direct-to-Brain Synapse Mapping",
            "author": "Sarah Jenkins",
            "source": {"id": "tech-chronicle", "name": "The Tech Chronicle"},
            "published_at": "2026-06-25T08:00:00Z",
            "url": "https://techchronicle.mock/aethercorp-neurallink-v2",
            "content": (
                "Tech giant AetherCorp announced the release of NeuralLink-V2, a groundbreaking "
                "neural interface designed for direct-to-brain synapse mapping. The company claims "
                "the interface operates with 99.9% accuracy and causes zero tissue damage. According to CEO "
                "Elena Rostova, the product has passed extensive clinical trials and will launch in late 2026. "
                "Rostova claimed that 'this device will help treat spinal injuries and restore motor function.' "
                "However, independent tech ethics groups have already raised concerns about safety data transparency."
            ),
            "description": "AetherCorp claims its neural interface is 99.9% safe and has passed clinical trials.",
            "url_to_image": "https://images.mock/tech.png",
            "language": "en"
        },
        {
            "title": "Ethics Alert: Inside the Secretive NeuralLink-V2 Trials of AetherCorp",
            "author": "David Vance",
            "source": {"id": "watchdog", "name": "Global Tech Watchdog"},
            "published_at": "2026-06-25T08:15:00Z",
            "url": "https://globalwatchdog.mock/aethercorp-clinical-trials-secret",
            "content": (
                "A scathing report by the Global Tech Watchdog reveals that AetherCorp's NeuralLink-V2 trials "
                "were conducted under intense secrecy in off-shore clinics. Leaked documents suggest "
                "several trial subjects experienced cognitive dissonance and minor neurological hemorrhaging. "
                "Despite CEO Elena Rostova's claims of 99.9% accuracy, the whistleblower alleges "
                "the clinical safety database was modified to delete adverse event logs. Dr. Aris Thorne, "
                "a neurobiologist, warned that 'direct-to-brain synapse mapping carries major long-term risks.'"
            ),
            "description": "Whistleblower documents suggest AetherCorp modified clinical trials to hide adverse events.",
            "url_to_image": "https://images.mock/alert.png",
            "language": "en"
        },
        {
            "title": "AetherCorp Stock Hits Record High Following NeuralLink-V2 Unveiling",
            "author": "Mark Sterling",
            "source": {"id": "financial-times", "name": "Global Market Tribune"},
            "published_at": "2026-06-25T09:00:00Z",
            "url": "https://markettribune.mock/aethercorp-stock-surges",
            "content": (
                "Shares of AetherCorp (AETH) surged 14.5% to hit an all-time high of $420.50 after the "
                "highly anticipated announcement of NeuralLink-V2. Wall Street analysts are bullish, "
                "predicting a market capitalization expansion of over $150 billion. Investors shrugged "
                "off minor criticisms from ethical watchdogs, focusing instead on the immense medical "
                "applications. AetherCorp's neural interface is expected to dominate the brain-machine "
                "interface market, capturing up to 80% share by the end of next year."
            ),
            "description": "AetherCorp stock price surges 14.5% as Wall Street praises neural synapse mapping tech.",
            "url_to_image": "https://images.mock/finance.png",
            "language": "en"
        }
    ]
    
    # Filter or return based on page size
    return mock_db[:page_size]
