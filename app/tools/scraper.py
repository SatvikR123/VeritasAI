import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from datetime import datetime
import json
import re
import nltk

# Pre-emptively download NLTK punkt quietly
try:
    nltk.download('punkt', quiet=True)
except Exception:
    pass

logger = logging.getLogger(__name__)

def parse_date(date_str: str) -> Optional[datetime]:
    """
    Attempts to parse standard ISO and standard news publication date strings.
    """
    if not date_str:
        return None
    
    # Try common formats first
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
            
    # Try dateutil parser if present (installed with dependencies)
    try:
        from dateutil.parser import parse as date_parse
        return date_parse(date_str)
    except Exception:
        return None

def extract_metadata_and_json_ld(html_content: str) -> Dict[str, Any]:
    """
    Parses structured JSON-LD and HTML meta tags to extract authors,
    publication dates, and full article bodies.
    This helps bypass client-side 'Read More' wrappers and retrieve full content.
    """
    metadata = {}
    soup = BeautifulSoup(html_content, "lxml")
    
    # Track candidate authors found in Person schemas
    person_authors = []
    
    # 1. Parse JSON-LD structures
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            # Using strict=False allows parsing control characters (newlines/tabs) inside JSON strings
            data = json.loads(script.string.strip(), strict=False)
            items = data if isinstance(data, list) else [data]
            for item in items:
                graph_items = item.get("@graph", [item]) if isinstance(item, dict) else [item]
                for g_item in graph_items:
                    if not isinstance(g_item, dict):
                        continue
                    
                    # Extract author from any standalone Person schema
                    if g_item.get("@type") == "Person" and g_item.get("name"):
                        person_authors.append(g_item["name"])
                        
                    # Target schemas representing news articles or blog content
                    if g_item.get("@type") in ["NewsArticle", "Article", "BlogPosting", "WebPage"]:
                        # Extract Author
                        author = g_item.get("author")
                        if author:
                            if isinstance(author, list):
                                names = [a.get("name") for a in author if isinstance(a, dict) and a.get("name")]
                                if names:
                                    metadata["author"] = ", ".join(names)
                            elif isinstance(author, dict) and author.get("name"):
                                metadata["author"] = author.get("name")
                            elif isinstance(author, str):
                                metadata["author"] = author
                                
                        # Extract Publication Date
                        pub_date = g_item.get("datePublished") or g_item.get("dateCreated")
                        if pub_date:
                            metadata["published_at"] = parse_date(str(pub_date))
                            
                        # Extract full article text if embedded in schema
                        art_body = g_item.get("articleBody")
                        if art_body and len(art_body.strip()) > 200:
                            metadata["json_ld_content"] = art_body.strip()
        except Exception as e:
            logger.debug(f"JSON-LD parsing issue: {e}")
            continue

    # Use first Person name as author if no author was extracted via NewsArticle/Article tags
    if not metadata.get("author") and person_authors:
        metadata["author"] = person_authors[0]

    # 2. Extract from HTML Meta Tags (fallback)
    if not metadata.get("author") or metadata["author"].startswith("@"):
        for attr in ["name", "property"]:
            for val in ["author", "twitter:creator", "citation_author", "dc.creator", "creator"]:
                tag = soup.find("meta", attrs={attr: val})
                if tag and tag.get("content"):
                    val_str = tag["content"].strip()
                    # Skip generic twitter handles starting with '@' if we have a real person name
                    if val_str.startswith("@") and person_authors:
                        continue
                    metadata["author"] = val_str
                    break
            if metadata.get("author"):
                break
                
    if not metadata.get("published_at"):
        for attr in ["name", "property"]:
            for val in [
                "article:published_time", "pubdate", "publishdate", "dc.date", 
                "dc.date.issued", "citation_publication_date", "og:article:published_time",
                "date"
            ]:
                tag = soup.find("meta", attrs={attr: val})
                if tag and tag.get("content"):
                    parsed = parse_date(tag["content"].strip())
                    if parsed:
                        metadata["published_at"] = parsed
                        break
            if metadata.get("published_at"):
                break
                
    return metadata

def clean_scraped_text(text: str) -> str:
    """
    Cleans up boilerplate phrases like 'read more', 'continue reading', etc.
    """
    if not text:
        return ""
        
    lines = text.split("\n")
    cleaned_lines = []
    
    # Identify common dynamic link prompts/boilerplate patterns (pre-compiled with IGNORECASE)
    boilerplate_patterns = [
        re.compile(r"^\s*(read\s+more|continue\s+reading|subscribe\s+to\s+read|read\s+full\s+(story|article|post|news|report))\b.*$", re.IGNORECASE),
        re.compile(r"^\s*(share\s+this\s+story|follow\s+us\s+on|copyright\s+\d{4})\b.*$", re.IGNORECASE),
        re.compile(r"^\s*(also\s+read|read\s+also|advertisement|promo|newsletter)\b.*$", re.IGNORECASE),
        re.compile(r"^\s*(read\s+full\s+story|read\s+full\s+article|read\s+more\s+news|click\s+here)\b.*$", re.IGNORECASE)
    ]
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            cleaned_lines.append("")
            continue
        if any(pat.match(line_stripped) for pat in boilerplate_patterns):
            continue
        cleaned_lines.append(line)
        
    # Reconstruct text and clean up double blank lines
    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
    return cleaned_text.strip()

def extract_article_content(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetches the article URL and extracts its full text content, title, authors,
    and metadata using newspaper3k as the primary extractor, and BeautifulSoup/JSON-LD as fallback.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }
    
    html_content = ""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        logger.error(f"Failed to download HTML from {url}: {e}")
        return None
        
    # 1. Parse JSON-LD and metadata first (captures hidden article body & structured dates)
    bs_meta = extract_metadata_and_json_ld(html_content)
    
    title_text = "Untitled Article"
    author_text = bs_meta.get("author")
    pub_date = bs_meta.get("published_at")
    content_text = bs_meta.get("json_ld_content", "")
    top_image = None
    description = None

    # 2. Parse using newspaper3k
    try:
        from newspaper import Article as NewspaperArticle
        article = NewspaperArticle(url, keep_article_html=False)
        article.set_html(html_content)
        article.parse()
        
        title_text = article.title or title_text
        author_text = author_text or (", ".join(article.authors) if article.authors else None)
        pub_date = pub_date or article.publish_date
        top_image = article.top_image
        description = article.meta_description
        
        # Prefer the newspaper extracted text only if it's larger than the schema version
        if article.text and len(article.text.strip()) > len(content_text):
            content_text = article.text.strip()
    except Exception as e:
        logger.warning(f"newspaper3k extraction failed for {url}: {e}. Falling back to BeautifulSoup.")

    # 3. BeautifulSoup tag fallback if text content is still empty
    if not content_text or len(content_text.strip()) < 100:
        try:
            soup = BeautifulSoup(html_content, "lxml")
            if title_text == "Untitled Article" and soup.find("title"):
                title_text = soup.find("title").get_text().strip()
                
            paragraphs = []
            for container_tag in ["article", "main"]:
                container = soup.find(container_tag)
                if container:
                    for p in container.find_all("p"):
                        p_text = p.get_text().strip()
                        if len(p_text) > 30:
                            paragraphs.append(p_text)
                    if paragraphs:
                        break
            
            if not paragraphs:
                for p in soup.find_all("p"):
                    p_text = p.get_text().strip()
                    if len(p_text) > 30:
                        paragraphs.append(p_text)
                        
            bs_content = "\n\n".join(paragraphs)
            if len(bs_content) > len(content_text):
                content_text = bs_content
        except Exception as e:
            logger.error(f"BeautifulSoup tag parsing fallback failed: {e}")

    # 4. Clean boilerplate text
    content_text = clean_scraped_text(content_text)
    
    if len(content_text.strip()) > 50:
        return {
            "title": title_text,
            "author": author_text,
            "content": content_text,
            "published_at": pub_date,
            "url_to_image": top_image,
            "description": description,
        }
        
    return None
