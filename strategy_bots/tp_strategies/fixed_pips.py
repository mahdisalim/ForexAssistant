"""
Fixed Pips Take Profit Strategy
استراتژی حد سود با پیپ ثابت
"""

from typing import Optional
from .base import BaseTPStrategy, TPResult, TradeDirection


class FixedPipsTP(BaseTPStrategy):
    """
    استراتژی Take Profit با تعداد پیپ ثابت
    
    TP در فاصله مشخصی (به پیپ) از قیمت ورود قرار می‌گیرد.
    
    Attributes:
        pips: تعداد پیپ (پیش‌فرض 50)
    """
    
    def __init__(self, pips: float = 50.0, pip_value: float = 0.0001):
        """
        Args:
            pips: تعداد پیپ برای TP
            pip_value: ارزش هر پیپ
        """
        super().__init__(pip_value)
        self.pips = pips
    
    @property
    def name(self) -> str:
        return f"Fixed {self.pips} pips"
    
    def calculate(self, entry_price: float, sl_price: float,
                  direction: TradeDirection, **kwargs) -> Optional[TPResult]:
        """
        محاسبه Take Profit با پیپ ثابت
        """
        tp_distance = self.pips * self.pip_value
        
        if direction == TradeDirection.BUY:
            tp_price = entry_price + tp_distance
        else:
            tp_price = entry_price - tp_distance
        
        rr = self.calculate_rr(entry_price, sl_price, tp_price)
        
        return TPResult(
            tp_price=tp_price,
            method=self.name,
            reason=f"{self.pips} پیپ ثابت",
            risk_reward_ratio=rr,
            pips=self.pips,
            confidence=70.0
        )
