"""
ATR-Based Take Profit Strategy
استراتژی حد سود بر اساس ATR
"""

from typing import Optional, List
import numpy as np

from .base import BaseTPStrategy, TPResult, TradeDirection


class ATRTP(BaseTPStrategy):
    """
    استراتژی Take Profit بر اساس ATR
    
    TP در فاصله‌ای از قیمت ورود قرار می‌گیرد که
    برابر با ضریبی از ATR است.
    
    Attributes:
        atr_period: دوره ATR (پیش‌فرض 14)
        multiplier: ضریب ATR (پیش‌فرض 2.0)
    """
    
    def __init__(
        self,
        atr_period: int = 14,
        multiplier: float = 2.0,
        pip_value: float = 0.0001
    ):
        super().__init__(pip_value)
        self.atr_period = atr_period
        self.multiplier = multiplier
    
    @property
    def name(self) -> str:
        return f"ATR TP (×{self.multiplier})"
    
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
    
    def calculate(self, entry_price: float, sl_price: float,
                  direction: TradeDirection, **kwargs) -> Optional[TPResult]:
        """
        محاسبه Take Profit بر اساس ATR
        
        Args:
            entry_price: قیمت ورود
            sl_price: قیمت SL
            direction: جهت معامله
            candles: لیست کندل‌ها (required in kwargs)
        """
        candles = kwargs.get('candles')
        if not candles:
            return None
        
        atr = self.calculate_atr(candles)
        
        if atr == 0:
            return None
        
        tp_distance = atr * self.multiplier
        
        if direction == TradeDirection.BUY:
            tp_price = entry_price + tp_distance
        else:
            tp_price = entry_price - tp_distance
        
        pips = self.calculate_pips(entry_price, tp_price)
        rr = self.calculate_rr(entry_price, sl_price, tp_price)
        
        return TPResult(
            tp_price=tp_price,
            method=self.name,
            reason=f"ATR({self.atr_period}) = {atr:.5f} × {self.multiplier} = {tp_distance:.5f}",
            risk_reward_ratio=rr,
            pips=pips,
            confidence=75.0
        )
