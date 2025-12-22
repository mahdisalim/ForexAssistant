"""
Admin Configuration for Analysis App
"""
from django.contrib import admin
from .models import CurrencyPair, MarketAnalysis, DailySummary


@admin.register(CurrencyPair)
class CurrencyPairAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'volatility', 'default_sl_pips', 'default_tp_pips', 'is_active']
    list_filter = ['volatility', 'is_active']
    search_fields = ['symbol']


@admin.register(MarketAnalysis)
class MarketAnalysisAdmin(admin.ModelAdmin):
    list_display = ['pair', 'timeframe', 'sentiment', 'recommendation', 'confidence', 'created_at']
    list_filter = ['timeframe', 'sentiment', 'recommendation', 'created_at']
    search_fields = ['pair__symbol']
    raw_id_fields = ['pair']


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ['date', 'asset', 'lang', 'articles_count', 'created_at']
    list_filter = ['asset', 'lang', 'date']
