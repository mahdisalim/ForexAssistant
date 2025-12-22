"""
Models for Trading App
# TODO: PRIORITY_NEXT - Integrate with existing trading/ module for robot management
"""
from django.db import models
from django.conf import settings


class TradingAccount(models.Model):
    """User's trading account with broker"""
    
    BROKER_CHOICES = [
        ('mt4', 'MetaTrader 4'),
        ('mt5', 'MetaTrader 5'),
        ('ctrader', 'cTrader'),
        ('oanda', 'OANDA'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trading_accounts'
    )
    
    broker = models.CharField(max_length=20, choices=BROKER_CHOICES)
    login = models.CharField(max_length=100)
    server = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100, blank=True)
    
    # Encrypted password stored separately
    password_encrypted = models.TextField(blank=True)
    
    # Account info
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    equity = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='USD')
    leverage = models.IntegerField(default=100)
    
    # Risk settings
    risk_percent = models.FloatField(default=2.0)
    
    # Status
    is_connected = models.BooleanField(default=False)
    last_connected = models.DateTimeField(null=True, blank=True)
    connection_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'broker', 'login', 'server']
    
    def __str__(self):
        return f"{self.nickname or self.login} ({self.broker})"


class TradingRobot(models.Model):
    """User's trading robot configuration"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trading_robots'
    )
    account = models.ForeignKey(
        TradingAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='robots'
    )
    
    name = models.CharField(max_length=100)
    robot_type = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20, default='EURUSD')
    timeframe = models.CharField(max_length=10, default='H1')
    
    # Strategy settings
    sl_strategy = models.CharField(max_length=50, default='atr')
    tp_strategy = models.CharField(max_length=50, default='risk_reward')
    sl_params = models.JSONField(default=dict)
    tp_params = models.JSONField(default=dict)
    risk_percent = models.FloatField(default=1.0)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_signal = models.DateTimeField(null=True, blank=True)
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.symbol}"
