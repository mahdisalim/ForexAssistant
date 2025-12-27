"""
Models for Scraping App
"""
from django.db import models


class NewsArticle(models.Model):
    """Scraped news article"""
    
    SOURCE_CHOICES = [
        ('investing', 'Investing.com'),
        ('forexfactory', 'Forex Factory'),
        ('dailyfx', 'DailyFX'),
        ('fxstreet', 'FXStreet'),
        ('forexlive', 'ForexLive'),
    ]
    
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, unique=True)
    content = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    
    published_at = models.DateTimeField(null=True, blank=True)
    scraped_at = models.DateTimeField(auto_now_add=True)
    
    # Related pairs
    related_pairs = models.JSONField(default=list)
    
    class Meta:
        ordering = ['-published_at', '-scraped_at']
        indexes = [
            models.Index(fields=['source', '-published_at']),
            models.Index(fields=['-scraped_at']),
        ]
    
    def __str__(self):
        return f"{self.source}: {self.title[:50]}"


class ScrapeLog(models.Model):
    """Log of scraping operations"""
    
    source = models.CharField(max_length=50)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    articles_found = models.IntegerField(default=0)
    articles_new = models.IntegerField(default=0)
    
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.source} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
