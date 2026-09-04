import sys
from app.tools.news_api import fetch_news_articles
from app.tools.scraper import extract_article_content
from app.models.article import Article, ArticleSource

def run_test():
    print("==================================================")
    print("    NEWS PLATFORM: COLLECTION & SCRAPING TEST     ")
    print("==================================================")
    
    # 1. Test News API Fetching
    query = "AetherCorp"
    print(f"\n[1] Fetching article metadata for query: '{query}'...")
    articles_data = fetch_news_articles(query, page_size=2)
    print(f"-> Fetched {len(articles_data)} articles metadata.")
    
    # 2. Test Pydantic Validation & Schema Storage
    print(f"\n[2] Validating article schemas against Pydantic models:")
    validated_articles = []
    for idx, art_data in enumerate(articles_data, 1):
        print(f"\n--- Article #{idx} ---")
        print(f"Title:       {art_data.get('title')}")
        print(f"Source:      {art_data.get('source', {}).get('name')}")
        print(f"URL:         {art_data.get('url')}")
        
        try:
            # Map dictionary to Pydantic structures
            source_obj = ArticleSource(
                id=art_data['source'].get('id'),
                name=art_data['source'].get('name'),
                domain=art_data['source'].get('domain'),
                url=art_data['source'].get('url')
            )
            article_obj = Article(
                id=str(hash(art_data['url'])),
                title=art_data['title'],
                author=art_data.get('author'),
                source=source_obj,
                published_at=art_data.get('published_at'),
                url=art_data['url'],
                content=art_data['content'],
                description=art_data.get('description'),
                url_to_image=art_data.get('url_to_image'),
                language=art_data.get('language') or "en"
            )
            validated_articles.append(article_obj)
            print("Pydantic Validation: SUCCESS")
        except Exception as e:
            print(f"Pydantic Validation: FAILED. Error: {e}")
            
    # 3. Test Full-Text Scraper with a live URL
    print("\n[3] Testing Scraper Content Extraction:")
    # We will test using a known stable public article URL, or let the user try a custom one
    test_url = "https://www.wikipedia.org"
    print(f"Attempting to extract content from: {test_url}")
    
    scraped_data = extract_article_content(test_url)
    if scraped_data:
        print("\nExtraction Result:")
        print(f"Title:   {scraped_data.get('title')}")
        print(f"Author:  {scraped_data.get('author')}")
        print(f"Snippet: {scraped_data.get('content')[:300].strip()}...")
        print("\nScraper check: SUCCESS")
    else:
        print("\nScraper check: FAILED to extract body text.")
        
    print("\n==================================================")
    print("Test finished successfully!")
    print("To test a live news article URL, run this script with:")
    print("uv run python test_collection.py <url>")
    print("==================================================")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # User supplied a custom URL to scrape
        url = sys.argv[1]
        print(f"\nScraping custom URL: {url}")
        res = extract_article_content(url)
        if res:
            print("\n--- Scrape Success ---")
            print(f"Title:   {res.get('title')}")
            print(f"Author:  {res.get('author')}")
            print(f"Date:    {res.get('published_at')}")
            print(f"Snippet:\n{res.get('content')[:600]}...")
        else:
            print("\nFailed to scrape content from that URL.")
    else:
        run_test()
