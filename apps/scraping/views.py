"""
Views for Scraping App
Integrated with scrapers/ module
"""
import asyncio
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import NewsArticle, ScrapeLog
from .tasks import trigger_scrape_task
from .services import get_scraping_service


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_scrape(request):
    """Trigger news scraping"""
    pairs = request.data.get('pairs', None)
    source = request.data.get('source', None)  # Optional: specific source
    background = request.data.get('background', True)
    
    if background:
        # Use Celery task for async scraping
        trigger_scrape_task.delay(pairs=pairs, source=source)
        return Response({
            'message': 'Scraping started in background',
            'pairs': pairs,
            'source': source
        })
    else:
        # Synchronous scraping (for testing)
        service = get_scraping_service()
        
        if source:
            result = asyncio.run(service.scrape_source(source, pairs))
        else:
            result = asyncio.run(service.scrape_all_sources(pairs))
        
        return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_news(request):
    """Get scraped news articles"""
    pair = request.query_params.get('pair')
    pairs = request.query_params.getlist('pairs')  # Support multiple pairs
    limit = int(request.query_params.get('limit', 50))
    source = request.query_params.get('source')  # Filter by source
    
    # Use service for better query handling
    service = get_scraping_service()
    
    # Build pairs list
    if pair:
        pairs = [pair.upper()]
    elif pairs:
        pairs = [p.upper() for p in pairs]
    else:
        pairs = None
    
    # Get articles
    articles = service.get_recent_articles(pairs=pairs, limit=limit)
    
    # Filter by source if provided
    if source:
        articles = [a for a in articles if a.source == source]
    
    return Response({
        'count': len(articles),
        'articles': [
            {
                'id': str(article.id),
                'source': article.source,
                'title': article.title,
                'url': article.url,
                'summary': article.summary,
                'published_at': article.published_at.isoformat() if article.published_at else None,
                'related_pairs': article.related_pairs,
                'sentiment': article.sentiment,
                'importance': article.importance,
            }
            for article in articles
        ]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scrape_logs(request):
    """Get scraping logs"""
    limit = int(request.query_params.get('limit', 20))
    
    service = get_scraping_service()
    logs = service.get_scrape_logs(limit=limit)
    
    return Response({
        'count': len(logs),
        'logs': [
            {
                'id': str(log.id),
                'source': log.source,
                'started_at': log.started_at.isoformat(),
                'completed_at': log.completed_at.isoformat() if log.completed_at else None,
                'articles_found': log.articles_found,
                'articles_new': log.articles_new,
                'success': log.success,
                'error_message': log.error_message,
            }
            for log in logs
        ]
    })
