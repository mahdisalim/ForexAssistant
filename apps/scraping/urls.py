"""
URL Configuration for Scraping App
"""
from django.urls import path
from . import views

urlpatterns = [
    path('scrape/', views.trigger_scrape, name='trigger_scrape'),
    path('news/', views.get_news, name='get_news'),
    path('scrape-logs/', views.get_scrape_logs, name='scrape_logs'),
]
