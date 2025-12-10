"""
ATR-Based Stop Loss Strategy
استراتژی استاپ لاس بر اساس ATR
"""

from typing import List, Optional
import numpy as np

from .base import BaseSLStrategy, SLResult, TradeDirection


class ATRSL(BaseSLStrategy):
    """
    استراتژی Stop Loss بر اساس ATR
    
    SL در فاصله‌ای از قیمت فعلی قرار می‌گیرد که
    برابر با ضریبی از ATR است.
    
    Attributes:
        atr_period: دوره ATR (پیش‌فرض 14)
        multiplier: ضریب ATR (پیش‌فرض 1.5)
    """
    
    def __init__(
        self,
        atr_period: int = 14,
        multiplier: float = 1.5,
        buffer_pips: float = 0,  # معمولاً برای ATR بافر نمی‌خواهیم
        pip_value: float = 0.0001
    ):
        super().__init__(buffer_pips, pip_value)
        self.atr_period = atr_period
        self.multiplier = multiplier
    
    @property
    def name(self) -> str:
        return "ATR SL"
    
    def calculate_atr(self, candles: List[dict]) -> float:
        """
        محاسبه ATR
        
        Args:
            candles: لیست کندل‌ها
            
        Returns:
            مقدار ATR
        """
        if len(candles) < self.atr_period + 1:
            return 0.0
        
        highs = np.array([c['high'] for c in candles])
        lows = np.array([c['low'] for c in candles])
        closes = np.array([c['close'] for c in candles])
        
        tr = np.zeros(len(candles))
        tr[0] = highs[0] - lows[0]
        
        for i in range(1, len(candles)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr[i] = max(hl, hc, lc)
        
        atr = np.mean(tr[-self.atr_period:])
        return float(atr)
    
    def calculate(self, candles: List[dict], direction: TradeDirection,
                  current_price: float) -> Optional[SLResult]:
        """
        محاسبه Stop Loss بر اساس ATR
        """
        atr = self.calculate_atr(candles)
        
        if atr == 0:
            return None
        
        sl_distance = atr * self.multiplier
        
        if direction == TradeDirection.BUY:
            sl_price = current_price - sl_distance
            reason = f"ATR({self.atr_period}) × {self.multiplier} = {sl_distance:.5f}"
        else:
            sl_price = current_price + sl_distance
            reason = f"ATR({self.atr_period}) × {self.multiplier} = {sl_distance:.5f}"
        
        return SLResult(
            sl_price=sl_price,
            method=self.name,
            reason=reason,
            confidence=75.0,
            fallback_used=False
        )
