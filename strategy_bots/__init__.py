"""
Strategy Bots Module
ربات‌های استراتژی معاملاتی

Example:
    >>> from strategy_bots import RSIBot, BotConfig
    >>> from strategy_bots.sl_strategies import PinBarSL, CompositeSL
    >>> 
    >>> bot = RSIBot(pairs=["EURUSD", "GBPUSD"])
    >>> signal = bot.analyze("EURUSD", candles)
"""

from .models import Signal, Trade, PendingSetup, BotAnalysis, SignalType, TradeDirection, TradeStatus
from .base_bot import BaseStrategyBot
from .rsi_bot import RSIBot
from .config import (
    AccountConfig, TradeConfig, BotConfig,
    RiskMode, SLMode, TPMode, DEFAULT_CONFIG
)
# SL Strategies module
from .sl_strategies import (
    PinBarSL, PinBar, ATRSL, SwingPointSL, CompositeSL, SLResult
)
# TP Strategies module
from .tp_strategies import (
    RiskRewardTP, MultiTargetTP, ATRTP, FixedPipsTP, CompositeTP, TPResult
)

__all__ = [
    # Models
    'Signal', 'Trade', 'PendingSetup', 'BotAnalysis',
    'SignalType', 'TradeDirection', 'TradeStatus',
    # Bots
    'BaseStrategyBot', 'RSIBot',
    # Config
    'AccountConfig', 'TradeConfig', 'BotConfig',
    'RiskMode', 'SLMode', 'TPMode', 'DEFAULT_CONFIG',
    # SL Strategies
    'PinBarSL', 'PinBar', 'ATRSL', 'SwingPointSL', 'CompositeSL', 'SLResult',
    # TP Strategies
    'RiskRewardTP', 'MultiTargetTP', 'ATRTP', 'FixedPipsTP', 'CompositeTP', 'TPResult'
]
