"""
Composite Stop Loss Strategy
استراتژی ترکیبی استاپ لاس

این کلاس چند استراتژی SL را ترکیب می‌کند و
بهترین نتیجه را انتخاب می‌کند.
"""

from typing import List, Optional

from .base import BaseSLStrategy, SLResult, TradeDirection
from .pin_bar import PinBarSL
from .atr_based import ATRSL
from .swing_point import SwingPointSL


class CompositeSL:
    """
    استراتژی ترکیبی Stop Loss
    
    این کلاس چند استراتژی را به ترتیب اولویت امتحان می‌کند
    و اولین نتیجه معتبر را برمی‌گرداند.
    
    اولویت پیش‌فرض:
    1. Pin Bar (اگر پین بار وجود داشته باشد)
    2. Swing Point (اگر سوینگ پوینت وجود داشته باشد)
    3. ATR (همیشه کار می‌کند - fallback)
    
    Example:
        >>> sl_calculator = CompositeSL()
        >>> result = sl_calculator.calculate(candles, TradeDirection.BUY, 1.1000)
        >>> print(result.sl_price, result.method)
    """
    
    def __init__(
        self,
        strategies: Optional[List[BaseSLStrategy]] = None,
        fallback_strategy: Optional[BaseSLStrategy] = None
    ):
        """
        Args:
            strategies: لیست استراتژی‌ها به ترتیب اولویت
            fallback_strategy: استراتژی پیش‌فرض (اگر همه شکست بخورند)
        """
        if strategies is None:
            # استراتژی‌های پیش‌فرض
            self.strategies = [
                PinBarSL(),
                SwingPointSL()
            ]
        else:
            self.strategies = strategies
        
        self.fallback = fallback_strategy or ATRSL()
    
    def calculate(self, candles: List[dict], direction: TradeDirection,
                  current_price: float) -> SLResult:
        """
        محاسبه Stop Loss با استفاده از استراتژی‌های ترکیبی
        
        Args:
            candles: لیست کندل‌ها
            direction: جهت معامله
            current_price: قیمت فعلی
            
        Returns:
            SLResult (همیشه یک نتیجه برمی‌گرداند)
        """
        # امتحان استراتژی‌ها به ترتیب اولویت
        for strategy in self.strategies:
            result = strategy.calculate(candles, direction, current_price)
            if result:
                return result
        
        # استفاده از fallback
        result = self.fallback.calculate(candles, direction, current_price)
        if result:
            result.fallback_used = True
            return result
        
        # اگر همه شکست خوردند، یک SL ساده برگردان
        pip_value = 0.0001
        sl_distance = 30 * pip_value  # 30 پیپ پیش‌فرض
        
        if direction == TradeDirection.BUY:
            sl_price = current_price - sl_distance
        else:
            sl_price = current_price + sl_distance
        
        return SLResult(
            sl_price=sl_price,
            method="Fixed Default",
            reason="استراتژی‌های دیگر شکست خوردند - 30 پیپ پیش‌فرض",
            confidence=50.0,
            fallback_used=True
        )
    
    def calculate_all(self, candles: List[dict], direction: TradeDirection,
                      current_price: float) -> List[SLResult]:
        """
        محاسبه SL با همه استراتژی‌ها (برای مقایسه)
        
        Returns:
            لیست همه نتایج
        """
        results = []
        
        for strategy in self.strategies + [self.fallback]:
            result = strategy.calculate(candles, direction, current_price)
            if result:
                results.append(result)
        
        return results
