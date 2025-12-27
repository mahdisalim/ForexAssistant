"""
Admin Configuration for Trading App
"""
from django.contrib import admin
from .models import TradingAccount, TradingRobot


@admin.register(TradingAccount)
class TradingAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'broker', 'login', 'server', 'balance', 'is_connected', 'created_at']
    list_filter = ['broker', 'is_connected', 'created_at']
    search_fields = ['user__email', 'login', 'nickname']
    raw_id_fields = ['user']


@admin.register(TradingRobot)
class TradingRobotAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'robot_type', 'symbol', 'timeframe', 'is_active', 'total_trades']
    list_filter = ['robot_type', 'is_active', 'timeframe']
    search_fields = ['user__email', 'name', 'symbol']
    raw_id_fields = ['user', 'account']
