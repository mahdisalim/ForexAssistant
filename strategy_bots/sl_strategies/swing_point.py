"""
Swing Point Stop Loss Strategy
استراتژی استاپ لاس بر اساس سوینگ پوینت
"""

from typing import List, Optional

from .base import BaseSLStrategy, SLResult, TradeDirection


class SwingPointSL(BaseSLStrategy):
    """
    استراتژی Stop Loss بر اساس Swing Point
    
    SL پشت آخرین سوینگ های/لو قرار می‌گیرد.
    
    Attributes:
        swing_strength: تعداد کندل برای تأیید سوینگ (پیش‌فرض 3)
        lookback: تعداد کندل برای جستجو (پیش‌فرض 50)
    """
    
    def __init__(
        self,
        buffer_pips: float = 5.0,
        pip_value: float = 0.0001,
        swing_strength: int = 3,
        lookback: int = 50
    ):
        super().__init__(buffer_pips, pip_value)
        self.swing_strength = swing_strength
        self.lookback = lookback
    
    @property
    def name(self) -> str:
        return "Swing Point SL"
    
    def find_swing_low(self, candles: List[dict]) -> Optional[tuple]:
        """
        پیدا کردن آخرین سوینگ لو
        
        Returns:
            (قیمت, اندیس) یا None
        """
        if len(candles) < self.swing_strength * 2 + 1:
            return None
        
        start = max(0, len(candles) - self.lookback)
        
        for i in range(len(candles) - self.swing_strength - 1, 
                       start + self.swing_strength - 1, -1):
            low = candles[i]['low']
            is_swing = True
            
            for j in range(1, self.swing_strength + 1):
                if low >= candles[i - j]['low'] or low >= candles[i + j]['low']:
                    is_swing = False
                    break
            
            if is_swing:
                return (low, i)
        
        return None
    
    def find_swing_high(self, candles: List[dict]) -> Optional[tuple]:
        """
        پیدا کردن آخرین سوینگ های
        
        Returns:
            (قیمت, اندیس) یا None
        """
        if len(candles) < self.swing_strength * 2 + 1:
            return None
        
        start = max(0, len(candles) - self.lookback)
        
        for i in range(len(candles) - self.swing_strength - 1,
                       start + self.swing_strength - 1, -1):
            high = candles[i]['high']
            is_swing = True
            
            for j in range(1, self.swing_strength + 1):
                if high <= candles[i - j]['high'] or high <= candles[i + j]['high']:
                    is_swing = False
                    break
            
            if is_swing:
                return (high, i)
        
        return None
    
    def calculate(self, candles: List[dict], direction: TradeDirection,
                  current_price: float) -> Optional[SLResult]:
        """
        محاسبه Stop Loss بر اساس سوینگ پوینت
        """
        buffer = self.get_buffer()
        
        if direction == TradeDirection.BUY:
            result = self.find_swing_low(candles)
            if not result:
                return None
            
            swing_price, index = result
            sl_price = swing_price - buffer
            reason = f"زیر سوینگ لو (کندل {index})"
        else:
            result = self.find_swing_high(candles)
            if not result:
                return None
            
            swing_price, index = result
            sl_price = swing_price + buffer
            reason = f"بالای سوینگ های (کندل {index})"
        
        if not self.validate_sl(sl_price, direction, current_price):
            return None
        
        return SLResult(
            sl_price=sl_price,
            method=self.name,
            reason=reason,
            confidence=70.0,
            pattern_index=index,
            fallback_used=False
        )
