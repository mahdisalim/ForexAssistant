"""
Base Take Profit Strategy
کلاس پایه برای استراتژی‌های حد سود
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class TradeDirection(Enum):
    """جهت معامله"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class TPResult:
    """
    نتیجه محاسبه Take Profit
    
    Attributes:
        tp_price: قیمت حد سود
        method: روش محاسبه
        reason: دلیل انتخاب این قیمت
        risk_reward_ratio: نسبت ریسک به ریوارد واقعی
        pips: فاصله TP به پیپ
        confidence: میزان اطمینان (0-100)
    """
    tp_price: float
    method: str
    reason: str
    risk_reward_ratio: Optional[float] = None
    pips: Optional[float] = None
    confidence: float = 80.0
    
    def to_dict(self) -> dict:
        return {
            "tp_price": self.tp_price,
            "method": self.method,
            "reason": self.reason,
            "risk_reward_ratio": self.risk_reward_ratio,
            "pips": self.pips,
            "confidence": self.confidence
        }


class BaseTPStrategy(ABC):
    """
    کلاس پایه برای استراتژی‌های Take Profit
    
    هر استراتژی TP باید از این کلاس ارث‌بری کند و
    متد calculate را پیاده‌سازی کند.
    """
    
    def __init__(self, pip_value: float = 0.0001):
        """
        Args:
            pip_value: ارزش هر پیپ (0.0001 برای اکثر جفت‌ها، 0.01 برای JPY)
        """
        self.pip_value = pip_value
    
    @property
    @abstractmethod
    def name(self) -> str:
        """نام استراتژی"""
        pass
    
    @abstractmethod
    def calculate(self, entry_price: float, sl_price: float,
                  direction: TradeDirection, **kwargs) -> Optional[TPResult]:
        """
        محاسبه قیمت Take Profit
        
        Args:
            entry_price: قیمت ورود
            sl_price: قیمت Stop Loss
            direction: جهت معامله (BUY یا SELL)
            **kwargs: پارامترهای اضافی (مثل candles برای ATR)
            
        Returns:
            TPResult یا None اگر نتوانست محاسبه کند
        """
        pass
    
    def calculate_pips(self, price1: float, price2: float) -> float:
        """محاسبه فاصله به پیپ"""
        return abs(price1 - price2) / self.pip_value
    
    def calculate_rr(self, entry_price: float, sl_price: float, 
                     tp_price: float) -> float:
        """محاسبه نسبت ریسک به ریوارد"""
        risk = abs(entry_price - sl_price)
        reward = abs(tp_price - entry_price)
        if risk == 0:
            return 0
        return reward / risk
    
    def validate_tp(self, tp_price: float, direction: TradeDirection,
                    entry_price: float) -> bool:
        """
        اعتبارسنجی قیمت TP
        
        Args:
            tp_price: قیمت TP محاسبه شده
            direction: جهت معامله
            entry_price: قیمت ورود
            
        Returns:
            True اگر TP معتبر باشد
        """
        if direction == TradeDirection.BUY:
            # برای BUY، TP باید بالای قیمت ورود باشد
            return tp_price > entry_price
        else:
            # برای SELL، TP باید زیر قیمت ورود باشد
            return tp_price < entry_price
