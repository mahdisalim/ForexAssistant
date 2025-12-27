"""
FXStreet Scraper
"""
import logging
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, NewsArticle

logger = logging.getLogger(__name__)


class FXStreetScraper(BaseScraper):
    """Scraper for FXStreet.com"""
    
    def __init__(self):
        super().__init__("FXStreet", "https://www.fxstreet.com")
        self.news_urls = {
            "news": "/news",
            "analysis": "/analysis",
            "technical": "/technical-analysis"
        }
    
    async def scrape_news(self, currency_pairs: List[str] = None) -> List[NewsArticle]:
        """Scrape news from FXStreet"""
        articles = []
        
        for category, path in self.news_urls.items():
            url = f"{self.base_url}{path}"
            html = await self.fetch_page(url)
            
            if not html:
                logger.warning(f"Failed to fetch {url}")
                continue
            
            soup = self.parse_html(html)
            category_articles = await self._parse_news_list(soup, currency_pairs, category)
            articles.extend(category_articles)
        
        logger.info(f"Scraped {len(articles)} articles from FXStreet")
        return articles
    
    async def _parse_news_list(self, soup: BeautifulSoup, currency_pairs: List[str], category: str) -> List[NewsArticle]:
        """Parse news list page"""
        articles = []
        
        # Find article containers
        article_elements = soup.select("article, div.fxs_entry, div.fxs_headline_tiny")
        
        if not article_elements:
            article_elements = soup.select("a.fxs_headline, div.news-item")
        
        for element in article_elements[:15]:
            try:
                # Extract title
                title_elem = element.select_one("h2, h3, h4, a.fxs_headline_tiny_title, span.title")
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Extract link
                link_elem = element.select_one("a") if element.name != 'a' else element
                link = link_elem.get("href", "") if link_elem else ""
                
                if link and not link.startswith("http"):
                    link = f"{self.base_url}{link}"
                
                # Extract summary
                summary_elem = element.select_one("p, div.fxs_entry_summary, span.summary")
                summary = summary_elem.get_text(strip=True) if summary_elem else ""
                
                # Detect currency pairs
                full_text = f"{title} {summary}"
                detected_pairs = self.detect_currency_pairs(full_text, currency_pairs or [])
                
                # Determine importance
                importance = "high" if category in ["analysis", "technical"] else "medium"
                
                article = NewsArticle(
                    title=self.clean_text(title),
                    content=self.truncate_text(self.clean_text(summary)),
                    url=link or self.base_url,
                    source=self.source_name,
                    published_at=datetime.now(),
                    currency_pairs=detected_pairs,
                    importance=importance
                )
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error parsing FXStreet article: {e}")
                continue
        
        return articles
    
    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from article page"""
        content_elem = soup.select_one("div.fxs_article_content, article.content, div.article-body")
        
        if content_elem:
            for unwanted in content_elem.select("script, style, .ad, .related"):
                unwanted.decompose()
            return self.clean_text(content_elem.get_text())
        
        return ""
