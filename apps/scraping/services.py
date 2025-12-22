"""
Scraping Service - Integration with scrapers module
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from django.conf import settings

# Import scrapers module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.scraper_manager import ScraperManager
from scrapers.base_scraper import NewsArticle as ScraperNewsArticle

from .models import NewsArticle, ScrapeLog

logger = logging.getLogger(__name__)


class ScrapingService:
    """Service for managing news scraping operations"""
    
    def __init__(self):
        self.data_dir = Path(settings.BASE_DIR) / 'data'
        self.data_dir.mkdir(exist_ok=True)
        self.manager = ScraperManager(self.data_dir)
    
    async def scrape_all_sources(
        self,
        pairs: Optional[List[str]] = None,
        save_to_db: bool = True
    ) -> Dict:
        """
        Scrape all news sources
        
        Args:
            pairs: List of currency pairs to filter (e.g., ['EURUSD', 'XAUUSD'])
            save_to_db: Whether to save articles to database
        
        Returns:
            Dict with scraping results
        """
        log = ScrapeLog.objects.create(
            source='all',
            started_at=datetime.now()
        )
        
        try:
            logger.info(f"Starting scraping for pairs: {pairs}")
            
            # Scrape all sources
            articles = await self.manager.scrape_all(pairs)
            
            logger.info(f"Scraped {len(articles)} articles")
            
            # Save to database if requested
            new_count = 0
            if save_to_db:
                new_count = await self._save_articles_to_db(articles)
            
            # Update log
            log.completed_at = datetime.now()
            log.articles_found = len(articles)
            log.articles_new = new_count
            log.success = True
            log.save()
            
            return {
                'success': True,
                'articles_count': len(articles),
                'articles_new': new_count,
                'sources': list(set(a.source for a in articles)),
                'log_id': str(log.id)
            }
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}", exc_info=True)
            log.completed_at = datetime.now()
            log.success = False
            log.error_message = str(e)
            log.save()
            
            return {
                'success': False,
                'error': str(e),
                'log_id': str(log.id)
            }
    
    async def _save_articles_to_db(self, articles: List[ScraperNewsArticle]) -> int:
        """Save scraped articles to database"""
        new_count = 0
        
        for article in articles:
            # Check if article already exists (by URL)
            if NewsArticle.objects.filter(url=article.url).exists():
                continue
            
            # Create new article
            try:
                NewsArticle.objects.create(
                    source=article.source,
                    title=article.title,
                    url=article.url,
                    summary=article.summary or '',
                    content=article.content or '',
                    published_at=article.published_at,
                    related_pairs=article.related_pairs or [],
                    sentiment=article.sentiment,
                    importance=article.importance or 'medium'
                )
                new_count += 1
            except Exception as e:
                logger.error(f"Failed to save article {article.url}: {e}")
                continue
        
        logger.info(f"Saved {new_count} new articles to database")
        return new_count
    
    async def scrape_source(
        self,
        source: str,
        pairs: Optional[List[str]] = None
    ) -> Dict:
        """
        Scrape a specific news source
        
        Args:
            source: Source name (investing, forexfactory, dailyfx, fxstreet, forexlive)
            pairs: List of currency pairs to filter
        
        Returns:
            Dict with scraping results
        """
        log = ScrapeLog.objects.create(
            source=source,
            started_at=datetime.now()
        )
        
        try:
            # Get the specific scraper
            scraper = self.manager.scrapers.get(source)
            if not scraper:
                raise ValueError(f"Unknown source: {source}")
            
            # Scrape
            articles = await scraper.scrape()
            
            # Filter by pairs if provided
            if pairs:
                articles = self.manager.filter_by_pairs(articles, pairs)
            
            # Save to database
            new_count = await self._save_articles_to_db(articles)
            
            # Update log
            log.completed_at = datetime.now()
            log.articles_found = len(articles)
            log.articles_new = new_count
            log.success = True
            log.save()
            
            return {
                'success': True,
                'source': source,
                'articles_count': len(articles),
                'articles_new': new_count,
                'log_id': str(log.id)
            }
            
        except Exception as e:
            logger.error(f"Scraping {source} failed: {e}", exc_info=True)
            log.completed_at = datetime.now()
            log.success = False
            log.error_message = str(e)
            log.save()
            
            return {
                'success': False,
                'source': source,
                'error': str(e),
                'log_id': str(log.id)
            }
    
    def get_recent_articles(
        self,
        pairs: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[NewsArticle]:
        """Get recent articles from database"""
        queryset = NewsArticle.objects.all().order_by('-published_at', '-created_at')
        
        if pairs:
            # Filter by pairs
            from django.db.models import Q
            query = Q()
            for pair in pairs:
                query |= Q(related_pairs__contains=[pair.upper()])
            queryset = queryset.filter(query)
        
        return list(queryset[:limit])
    
    def get_scrape_logs(self, limit: int = 20) -> List[ScrapeLog]:
        """Get recent scrape logs"""
        return list(ScrapeLog.objects.all().order_by('-started_at')[:limit])


# Singleton instance
_scraping_service = None

def get_scraping_service() -> ScrapingService:
    """Get or create scraping service instance"""
    global _scraping_service
    if _scraping_service is None:
        _scraping_service = ScrapingService()
    return _scraping_service
