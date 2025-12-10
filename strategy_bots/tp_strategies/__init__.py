"""
Take Profit Strategies Module
ماژول استراتژی‌های حد سود

این ماژول شامل روش‌های مختلف تعیین Take Profit است که می‌توان
در هر ربات استراتژی از آنها استفاده کرد.

Example:
    >>> from strategy_bots.tp_strategies import RiskRewardTP, CompositeTP, TradeDirection
    >>> 
    >>> # استفاده از R:R
    >>> rr_tp = RiskRewardTP(ratio=2.0)
    >>> result = rr_tp.calculate(entry_price=1.1000, sl_price=1.0950, direction=TradeDirection.BUY)
    >>> print(result.tp_price)  # 1.1100
"""

from .base import BaseTPStrategy, TPResult, TradeDirection
from .risk_reward import RiskRewardTP, MultiTargetTP
from .atr_based import ATRTP
from .fixed_pips import FixedPipsTP
from .composite import CompositeTP

__all__ = [
    # Base
    'BaseTPStrategy',
    'TPResult',
    'TradeDirection',
    # Strategies
    'RiskRewardTP',
    'MultiTargetTP',
    'ATRTP',
    'FixedPipsTP',
    'CompositeTP'
]
