"""
Investing.com Scraper
"""
import logging
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, NewsArticle

logger = logging.getLogger(__name__)


class InvestingScraper(BaseScraper):
    """Scraper for Investing.com"""
    
    def __init__(self):
        super().__init__("Investing.com", "https://www.investing.com")
        self.news_urls = {
            "forex": "/news/forex-news",
            "commodities": "/news/commodities-news",
            "economic": "/economic-calendar/"
        }
    
    async def scrape_news(self, currency_pairs: List[str] = None) -> List[NewsArticle]:
        """Scrape forex news from Investing.com"""
        articles = []
        
        for category, path in self.news_urls.items():
            if category == "economic":
                continue  # Handle economic calendar separately
            
            url = f"{self.base_url}{path}"
            html = await self.fetch_page(url)
            
            if not html:
                logger.warning(f"Failed to fetch {url}")
                continue
            
            soup = self.parse_html(html)
            category_articles = await self._parse_news_list(soup, currency_pairs)
            articles.extend(category_articles)
        
        logger.info(f"Scraped {len(articles)} articles from Investing.com")
        return articles
    
    async def _parse_news_list(self, soup: BeautifulSoup, currency_pairs: List[str] = None) -> List[NewsArticle]:
        """Parse news list page"""
        articles = []
        
        # Find article containers
        article_elements = soup.select("article.js-article-item, div.largeTitle article, div.mediumTitle1 article")
        
        if not article_elements:
            # Alternative selectors
            article_elements = soup.select("a[data-test='article-title-link']")
        
        for element in article_elements[:15]:  # Limit to 15 articles
            try:
                # Extract title and link
                title_elem = element.select_one("a.title, a[data-test='article-title-link'], h3 a, h2 a")
                if not title_elem:
                    title_elem = element if element.name == 'a' else None
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = title_elem.get("href", "")
                
                if not link.startswith("http"):
                    link = f"{self.base_url}{link}"
                
                # Extract summary/snippet
                summary_elem = element.select_one("p, .textDiv, span.js-article-item-description")
                summary = summary_elem.get_text(strip=True) if summary_elem else ""
                
                # Detect currency pairs
                full_text = f"{title} {summary}"
                detected_pairs = self.detect_currency_pairs(full_text, currency_pairs or [])
                
                # Create article
                article = NewsArticle(
                    title=self.clean_text(title),
                    content=self.truncate_text(self.clean_text(summary)),
                    url=link,
                    source=self.source_name,
                    published_at=datetime.now(),
                    currency_pairs=detected_pairs,
                    importance="medium"
                )
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error parsing article: {e}")
                continue
        
        return articles
    
    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from article page"""
        content_elem = soup.select_one("div.articlePage, div.WYSIWYG, article.article")
        
        if content_elem:
            # Remove unwanted elements
            for unwanted in content_elem.select("script, style, .ad, .advertisement, .related"):
                unwanted.decompose()
            
            return self.clean_text(content_elem.get_text())
        
        return ""
