"""
Views for Scraping App
# TODO: PRIORITY_NEXT - Integrate with existing scrapers/ module
"""
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import NewsArticle, ScrapeLog
from .tasks import trigger_scrape_task


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_scrape(request):
    """Trigger news scraping"""
    # TODO: PRIORITY_NEXT - Use Celery task with scrapers/scraper_manager.py
    # trigger_scrape_task.delay()
    
    return Response({
        'message': 'Scraping started in background',
        'note': 'Full scraper integration pending - see TODO comments'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_news(request):
    """Get scraped news articles"""
    pair = request.query_params.get('pair')
    limit = int(request.query_params.get('limit', 50))
    
    articles = NewsArticle.objects.all()
    
    if pair:
        pair = pair.upper()
        articles = articles.filter(related_pairs__contains=[pair])
    
    articles = articles[:limit]
    
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
            }
            for article in articles
        ]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scrape_logs(request):
    """Get scraping logs"""
    logs = ScrapeLog.objects.all()[:20]
    
    return Response({
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
