"""
Admin Configuration for Scraping App
"""
from django.contrib import admin
from .models import NewsArticle, ScrapeLog


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['source', 'title', 'published_at', 'scraped_at']
    list_filter = ['source', 'published_at', 'scraped_at']
    search_fields = ['title', 'content']
    readonly_fields = ['scraped_at']


@admin.register(ScrapeLog)
class ScrapeLogAdmin(admin.ModelAdmin):
    list_display = ['source', 'started_at', 'completed_at', 'articles_found', 'articles_new', 'success']
    list_filter = ['source', 'success', 'started_at']
