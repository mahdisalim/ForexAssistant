"""
Stop Loss Strategies Module
ماژول استراتژی‌های استاپ لاس

این ماژول شامل روش‌های مختلف تعیین Stop Loss است که می‌توان
در هر ربات استراتژی از آنها استفاده کرد.

Example:
    >>> from strategy_bots.sl_strategies import PinBarSL, CompositeSL, TradeDirection
    >>> 
    >>> # استفاده مستقیم از Pin Bar
    >>> pin_bar_sl = PinBarSL(buffer_pips=5)
    >>> result = pin_bar_sl.calculate(candles, TradeDirection.BUY, 1.1000)
    >>> 
    >>> # استفاده از استراتژی ترکیبی
    >>> composite = CompositeSL()
    >>> result = composite.calculate(candles, TradeDirection.BUY, 1.1000)
"""

from .base import BaseSLStrategy, SLResult, TradeDirection
from .pin_bar import PinBarSL, PinBar
from .atr_based import ATRSL
from .swing_point import SwingPointSL
from .composite import CompositeSL

__all__ = [
    # Base
    'BaseSLStrategy',
    'SLResult',
    'TradeDirection',
    # Strategies
    'PinBarSL',
    'PinBar',
    'ATRSL', 
    'SwingPointSL',
    'CompositeSL'
]
