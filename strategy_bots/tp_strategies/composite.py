"""
Composite Take Profit Strategy
استراتژی ترکیبی حد سود
"""

from typing import List, Optional

from .base import BaseTPStrategy, TPResult, TradeDirection
from .risk_reward import RiskRewardTP
from .atr_based import ATRTP
from .fixed_pips import FixedPipsTP


class CompositeTP:
    """
    استراتژی ترکیبی Take Profit
    
    این کلاس چند استراتژی را به ترتیب اولویت امتحان می‌کند
    و اولین نتیجه معتبر را برمی‌گرداند.
    
    اولویت پیش‌فرض:
    1. Risk/Reward (همیشه کار می‌کند)
    
    Example:
        >>> tp_calculator = CompositeTP()
        >>> result = tp_calculator.calculate(
        ...     entry_price=1.1000,
        ...     sl_price=1.0950,
        ...     direction=TradeDirection.BUY
        ... )
        >>> print(result.tp_price)  # 1.1100
    """
    
    def __init__(
        self,
        strategies: Optional[List[BaseTPStrategy]] = None,
        fallback_strategy: Optional[BaseTPStrategy] = None
    ):
        """
        Args:
            strategies: لیست استراتژی‌ها به ترتیب اولویت
            fallback_strategy: استراتژی پیش‌فرض
        """
        if strategies is None:
            self.strategies = [
                RiskRewardTP(ratio=2.0)
            ]
        else:
            self.strategies = strategies
        
        self.fallback = fallback_strategy or FixedPipsTP(pips=50)
    
    def calculate(self, entry_price: float, sl_price: float,
                  direction: TradeDirection, **kwargs) -> TPResult:
        """
        محاسبه Take Profit با استفاده از استراتژی‌های ترکیبی
        
        Args:
            entry_price: قیمت ورود
            sl_price: قیمت SL
            direction: جهت معامله
            **kwargs: پارامترهای اضافی
            
        Returns:
            TPResult (همیشه یک نتیجه برمی‌گرداند)
        """
        # امتحان استراتژی‌ها به ترتیب اولویت
        for strategy in self.strategies:
            result = strategy.calculate(entry_price, sl_price, direction, **kwargs)
            if result and strategy.validate_tp(result.tp_price, direction, entry_price):
                return result
        
        # استفاده از fallback
        result = self.fallback.calculate(entry_price, sl_price, direction, **kwargs)
        if result:
            return result
        
        # اگر همه شکست خوردند، یک TP ساده برگردان
        pip_value = 0.0001
        tp_distance = 50 * pip_value
        
        if direction == TradeDirection.BUY:
            tp_price = entry_price + tp_distance
        else:
            tp_price = entry_price - tp_distance
        
        return TPResult(
            tp_price=tp_price,
            method="Fixed Default",
            reason="استراتژی‌های دیگر شکست خوردند - 50 پیپ پیش‌فرض",
            pips=50,
            confidence=50.0
        )
    
    def calculate_all(self, entry_price: float, sl_price: float,
                      direction: TradeDirection, **kwargs) -> List[TPResult]:
        """
        محاسبه TP با همه استراتژی‌ها (برای مقایسه)
        
        Returns:
            لیست همه نتایج
        """
        results = []
        
        for strategy in self.strategies + [self.fallback]:
            result = strategy.calculate(entry_price, sl_price, direction, **kwargs)
            if result:
                results.append(result)
        
        return results
