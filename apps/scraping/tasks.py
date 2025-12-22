"""
Celery Tasks for Scraping App
"""
import asyncio
from celery import shared_task
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


@shared_task
def trigger_scrape_task(pairs: Optional[List[str]] = None, source: Optional[str] = None):
    """
    Trigger news scraping in background
    
    Args:
        pairs: List of currency pairs to filter
        source: Specific source to scrape (optional)
    """
    from .services import get_scraping_service
    
    logger.info(f"Scraping task triggered - pairs: {pairs}, source: {source}")
    
    try:
        service = get_scraping_service()
        
        if source:
            result = asyncio.run(service.scrape_source(source, pairs))
        else:
            result = asyncio.run(service.scrape_all_sources(pairs))
        
        logger.info(f"Scraping completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Scraping task failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task
def scheduled_scrape_task():
    """Scheduled task for periodic scraping"""
    return trigger_scrape_task()


@shared_task
def daily_analysis_task():
    """
    Daily market analysis task
    Scrapes news and generates analysis for all configured pairs
    """
    from apps.analysis.services import AnalysisService
    from apps.analysis.models import CurrencyPair
    
    logger.info("Daily analysis task triggered")
    
    try:
        # First, scrape all news
        scrape_result = trigger_scrape_task()
        logger.info(f"News scraped: {scrape_result.get('articles_count', 0)} articles")
        
        # Get all active pairs
        pairs = CurrencyPair.objects.filter(is_active=True)
        
        # Generate analysis for each pair
        service = AnalysisService()
        results = []
        
        for pair in pairs:
            try:
                analysis = asyncio.run(service.auto_chart_analysis(
                    pair=pair.symbol,
                    timeframe='H4',
                    trading_style='day'
                ))
                results.append({
                    'pair': pair.symbol,
                    'success': True,
                    'sentiment': analysis.get('analysis', {}).get('sentiment')
                })
            except Exception as e:
                logger.error(f"Analysis failed for {pair.symbol}: {e}")
                results.append({
                    'pair': pair.symbol,
                    'success': False,
                    'error': str(e)
                })
        
        logger.info(f"Daily analysis completed for {len(results)} pairs")
        return {
            'success': True,
            'scrape_result': scrape_result,
            'analysis_results': results
        }
        
    except Exception as e:
        logger.error(f"Daily analysis task failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}
