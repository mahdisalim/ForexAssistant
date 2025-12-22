"""
Models for Analysis App
"""
from django.db import models
from django.conf import settings


class CurrencyPair(models.Model):
    """Currency pair configuration"""
    
    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    tradingview_symbol = models.CharField(max_length=50, blank=True, null=True, help_text="TradingView symbol format (e.g., FX:EURUSD, TVC:GOLD)")
    volatility = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    default_sl_pips = models.IntegerField(default=30)
    default_tp_pips = models.IntegerField(default=60)
    keywords = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['symbol']
        verbose_name = 'Currency Pair'
        verbose_name_plural = 'Currency Pairs'
    
    def __str__(self):
        return self.symbol


class MarketAnalysis(models.Model):
    """Stored market analysis results"""
    
    pair = models.ForeignKey(CurrencyPair, on_delete=models.CASCADE, related_name='analyses')
    timeframe = models.CharField(max_length=10, default='H1')
    trading_style = models.CharField(max_length=20, default='day')
    
    sentiment = models.CharField(max_length=20)
    sentiment_score = models.FloatField(default=0)
    key_factors = models.JSONField(default=list)
    support_levels = models.JSONField(default=list)
    resistance_levels = models.JSONField(default=list)
    
    recommendation = models.CharField(max_length=20)
    confidence = models.IntegerField(default=0)
    entry_price = models.FloatField(null=True, blank=True)
    stop_loss = models.JSONField(default=dict)
    take_profit = models.JSONField(default=dict)
    
    raw_analysis = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Market Analysis'
        verbose_name_plural = 'Market Analyses'
    
    def __str__(self):
        return f"{self.pair.symbol} - {self.timeframe} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class DailySummary(models.Model):
    """Daily market summary"""
    
    date = models.DateField(db_index=True)
    asset = models.CharField(max_length=10, default='USD')
    lang = models.CharField(max_length=5, default='fa')
    
    summary_text = models.TextField()
    articles_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['date', 'asset', 'lang']
    
    def __str__(self):
        return f"Summary {self.date} - {self.asset}"


class ChartAnalysis(models.Model):
    """Chart image analysis results from AI"""
    
    pair = models.ForeignKey(CurrencyPair, on_delete=models.CASCADE, related_name='chart_analyses')
    timeframe = models.CharField(max_length=10, default='H1')
    trading_style = models.CharField(max_length=20, default='day')
    
    # Chart image data
    chart_image_url = models.URLField(blank=True, null=True)
    chart_snapshot_time = models.DateTimeField(auto_now_add=True)
    
    # AI Analysis results
    sentiment = models.CharField(max_length=20, default='Neutral')
    sentiment_score = models.IntegerField(default=0)
    trend = models.CharField(max_length=20, default='sideways')
    
    # Trade recommendation
    recommendation = models.CharField(max_length=10, default='WAIT')
    confidence = models.IntegerField(default=0)
    
    # Entry/Exit levels
    entry_min = models.CharField(max_length=50, blank=True)
    entry_max = models.CharField(max_length=50, blank=True)
    stop_loss_price = models.CharField(max_length=50, blank=True)
    stop_loss_pips = models.IntegerField(default=0)
    take_profit_price = models.CharField(max_length=50, blank=True)
    take_profit_pips = models.IntegerField(default=0)
    risk_reward_ratio = models.FloatField(default=0)
    
    # Analysis details
    key_factors = models.JSONField(default=list)
    support_levels = models.JSONField(default=list)
    resistance_levels = models.JSONField(default=list)
    reasoning = models.TextField(blank=True)
    invalidation = models.TextField(blank=True)
    
    # Raw response
    raw_response = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chart Analysis'
        verbose_name_plural = 'Chart Analyses'
    
    def __str__(self):
        return f"{self.pair.symbol} - {self.timeframe} - {self.recommendation} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
