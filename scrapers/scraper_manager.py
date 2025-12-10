"""
Scraper Manager - Orchestrates all scrapers
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from .base_scraper import NewsArticle
from .investing_scraper import InvestingScraper
from .forexfactory_scraper import ForexFactoryScraper
from .dailyfx_scraper import DailyFXScraper
from .fxstreet_scraper import FXStreetScraper
from .forexlive_scraper import ForexLiveScraper

logger = logging.getLogger(__name__)


class ScraperManager:
    """Manages all news scrapers"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.scrapers = {
            "investing": InvestingScraper(),
            "forexfactory": ForexFactoryScraper(),
            "dailyfx": DailyFXScraper(),
            "fxstreet": FXStreetScraper(),
            "forexlive": ForexLiveScraper()
        }
    
    async def scrape_all(self, currency_pairs: List[str] = None) -> List[NewsArticle]:
        """Run all scrapers concurrently"""
        all_articles = []
        
        # Run scrapers concurrently
        tasks = [
            scraper.scrape_news(currency_pairs)
            for scraper in self.scrapers.values()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            scraper_name = list(self.scrapers.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Scraper {scraper_name} failed: {result}")
            else:
                all_articles.extend(result)
        
        # Remove duplicates based on title similarity
        unique_articles = self._deduplicate_articles(all_articles)
        
        # Save to file
        await self._save_articles(unique_articles)
        
        logger.info(f"Total unique articles scraped: {len(unique_articles)}")
        return unique_articles
    
    async def scrape_source(self, source_name: str, currency_pairs: List[str] = None) -> List[NewsArticle]:
        """Scrape a specific source"""
        if source_name not in self.scrapers:
            logger.error(f"Unknown source: {source_name}")
            return []
        
        scraper = self.scrapers[source_name]
        articles = await scraper.scrape_news(currency_pairs)
        
        await self._save_articles(articles, f"{source_name}_news.json")
        
        return articles
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on title similarity"""
        seen_titles = set()
        unique = []
        
        for article in articles:
            # Normalize title for comparison
            normalized = article.title.lower().strip()[:50]
            
            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(article)
        
        return unique
    
    async def _save_articles(self, articles: List[NewsArticle], filename: str = "all_news.json"):
        """Save articles to JSON file"""
        filepath = self.data_dir / filename
        
        # Convert to dict
        data = {
            "scraped_at": datetime.now().isoformat(),
            "count": len(articles),
            "articles": [article.model_dump() for article in articles]
        }
        
        # Convert datetime objects to strings
        for article in data["articles"]:
            if article.get("published_at"):
                article["published_at"] = article["published_at"].isoformat() if isinstance(article["published_at"], datetime) else article["published_at"]
            if article.get("scraped_at"):
                article["scraped_at"] = article["scraped_at"].isoformat() if isinstance(article["scraped_at"], datetime) else article["scraped_at"]
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(articles)} articles to {filepath}")
    
    async def load_articles(self, filename: str = "all_news.json") -> List[NewsArticle]:
        """Load articles from JSON file"""
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            return []
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        articles = []
        for article_data in data.get("articles", []):
            try:
                articles.append(NewsArticle(**article_data))
            except Exception as e:
                logger.error(f"Error loading article: {e}")
        
        return articles
    
    def filter_by_pair(self, articles: List[NewsArticle], pair: str) -> List[NewsArticle]:
        """Filter articles by currency pair"""
        return [a for a in articles if pair in a.currency_pairs]
    
    def filter_by_importance(self, articles: List[NewsArticle], min_importance: str = "medium") -> List[NewsArticle]:
        """Filter articles by minimum importance"""
        importance_order = {"low": 0, "medium": 1, "high": 2}
        min_level = importance_order.get(min_importance, 1)
        
        return [a for a in articles if importance_order.get(a.importance, 0) >= min_level]
