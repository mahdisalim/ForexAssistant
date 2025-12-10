"""
DailyFX Scraper
"""
import logging
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, NewsArticle

logger = logging.getLogger(__name__)


class DailyFXScraper(BaseScraper):
    """Scraper for DailyFX.com"""
    
    def __init__(self):
        super().__init__("DailyFX", "https://www.dailyfx.com")
        self.news_urls = {
            "forex": "/forex",
            "technical": "/technical-analysis",
            "market-news": "/market-news"
        }
    
    async def scrape_news(self, currency_pairs: List[str] = None) -> List[NewsArticle]:
        """Scrape news from DailyFX"""
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
        
        logger.info(f"Scraped {len(articles)} articles from DailyFX")
        return articles
    
    async def _parse_news_list(self, soup: BeautifulSoup, currency_pairs: List[str], category: str) -> List[NewsArticle]:
        """Parse news list page"""
        articles = []
        
        # Find article containers
        article_elements = soup.select("article, div.dfx-articleList a, a.dfx-article")
        
        if not article_elements:
            article_elements = soup.select("div.article-list article, div.content-list a")
        
        for element in article_elements[:15]:
            try:
                # Extract title
                title_elem = element.select_one("h3, h2, span.title, div.title")
                if not title_elem:
                    title_elem = element.select_one("a")
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Extract link
                link_elem = element if element.name == 'a' else element.select_one("a")
                link = link_elem.get("href", "") if link_elem else ""
                
                if link and not link.startswith("http"):
                    link = f"{self.base_url}{link}"
                
                # Extract summary
                summary_elem = element.select_one("p, div.summary, span.description")
                summary = summary_elem.get_text(strip=True) if summary_elem else ""
                
                # Detect currency pairs
                full_text = f"{title} {summary}"
                detected_pairs = self.detect_currency_pairs(full_text, currency_pairs or [])
                
                # Determine importance based on category
                importance = "high" if category == "technical" else "medium"
                
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
                logger.error(f"Error parsing DailyFX article: {e}")
                continue
        
        return articles
    
    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from article page"""
        content_elem = soup.select_one("div.dfx-articleBody, article.content, div.article-content")
        
        if content_elem:
            for unwanted in content_elem.select("script, style, .ad, .related, .sidebar"):
                unwanted.decompose()
            return self.clean_text(content_elem.get_text())
        
        return ""
