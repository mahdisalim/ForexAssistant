"""
Forex Factory Scraper - Calendar and News
"""
import logging
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, NewsArticle

logger = logging.getLogger(__name__)


class ForexFactoryScraper(BaseScraper):
    """Scraper for ForexFactory.com"""
    
    def __init__(self):
        super().__init__("Forex Factory", "https://www.forexfactory.com")
        self.calendar_url = "/calendar"
        self.news_url = "/news"
    
    async def scrape_news(self, currency_pairs: List[str] = None) -> List[NewsArticle]:
        """Scrape news and calendar from Forex Factory"""
        articles = []
        
        # Scrape news
        news_articles = await self._scrape_news_section(currency_pairs)
        articles.extend(news_articles)
        
        # Scrape calendar events
        calendar_articles = await self._scrape_calendar(currency_pairs)
        articles.extend(calendar_articles)
        
        logger.info(f"Scraped {len(articles)} items from Forex Factory")
        return articles
    
    async def _scrape_news_section(self, currency_pairs: List[str] = None) -> List[NewsArticle]:
        """Scrape news section"""
        articles = []
        url = f"{self.base_url}{self.news_url}"
        html = await self.fetch_page(url)
        
        if not html:
            logger.warning(f"Failed to fetch {url}")
            return articles
        
        soup = self.parse_html(html)
        
        # Find news items
        news_items = soup.select("div.flexposts__item, tr.calendar__row, div.news__item")
        
        for item in news_items[:15]:
            try:
                title_elem = item.select_one("a.flexposts__title, span.news__title, a.calendar__event-title")
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = title_elem.get("href", "")
                
                if link and not link.startswith("http"):
                    link = f"{self.base_url}{link}"
                
                # Get snippet
                snippet_elem = item.select_one("div.flexposts__excerpt, span.news__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                # Detect pairs
                full_text = f"{title} {snippet}"
                detected_pairs = self.detect_currency_pairs(full_text, currency_pairs or [])
                
                article = NewsArticle(
                    title=self.clean_text(title),
                    content=self.truncate_text(self.clean_text(snippet)),
                    url=link or url,
                    source=self.source_name,
                    published_at=datetime.now(),
                    currency_pairs=detected_pairs,
                    importance="medium"
                )
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error parsing FF news item: {e}")
                continue
        
        return articles
    
    async def _scrape_calendar(self, currency_pairs: List[str] = None) -> List[NewsArticle]:
        """Scrape economic calendar"""
        articles = []
        url = f"{self.base_url}{self.calendar_url}"
        html = await self.fetch_page(url)
        
        if not html:
            logger.warning(f"Failed to fetch calendar {url}")
            return articles
        
        soup = self.parse_html(html)
        
        # Find calendar rows
        calendar_rows = soup.select("tr.calendar__row")
        
        for row in calendar_rows[:20]:
            try:
                # Get event details
                currency_elem = row.select_one("td.calendar__currency")
                event_elem = row.select_one("td.calendar__event span.calendar__event-title")
                impact_elem = row.select_one("td.calendar__impact span")
                
                if not event_elem:
                    continue
                
                currency = currency_elem.get_text(strip=True) if currency_elem else ""
                event_title = event_elem.get_text(strip=True)
                
                # Determine importance from impact
                importance = "low"
                if impact_elem:
                    impact_class = impact_elem.get("class", [])
                    if any("high" in c.lower() for c in impact_class):
                        importance = "high"
                    elif any("medium" in c.lower() or "med" in c.lower() for c in impact_class):
                        importance = "medium"
                
                # Map currency to pairs
                detected_pairs = []
                if currency:
                    for pair in (currency_pairs or []):
                        if currency.upper() in pair:
                            detected_pairs.append(pair)
                
                article = NewsArticle(
                    title=f"[Economic Event] {currency} - {event_title}",
                    content=f"Economic calendar event: {event_title} for {currency}. Impact: {importance}",
                    url=url,
                    source=f"{self.source_name} Calendar",
                    published_at=datetime.now(),
                    currency_pairs=detected_pairs,
                    importance=importance
                )
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error parsing calendar row: {e}")
                continue
        
        return articles
    
    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract content from article page"""
        content_elem = soup.select_one("div.body, div.content, article")
        
        if content_elem:
            for unwanted in content_elem.select("script, style, .ad"):
                unwanted.decompose()
            return self.clean_text(content_elem.get_text())
        
        return ""
