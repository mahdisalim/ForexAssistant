"""
Base Stop Loss Strategy
کلاس پایه برای استراتژی‌های استاپ لاس
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
class SLResult:
    """
    نتیجه محاسبه Stop Loss
    
    Attributes:
        sl_price: قیمت استاپ لاس
        method: روش محاسبه
        reason: دلیل انتخاب این قیمت
        confidence: میزان اطمینان (0-100)
        pattern_index: اندیس کندل الگو (اگر وجود داشته باشد)
        fallback_used: آیا از روش جایگزین استفاده شده
    """
    sl_price: float
    method: str
    reason: str
    confidence: float = 80.0
    pattern_index: Optional[int] = None
    fallback_used: bool = False
    
    def to_dict(self) -> dict:
        return {
            "sl_price": self.sl_price,
            "method": self.method,
            "reason": self.reason,
            "confidence": self.confidence,
            "pattern_index": self.pattern_index,
            "fallback_used": self.fallback_used
        }


class BaseSLStrategy(ABC):
    """
    کلاس پایه برای استراتژی‌های Stop Loss
    
    هر استراتژی SL باید از این کلاس ارث‌بری کند و
    متد calculate را پیاده‌سازی کند.
    """
    
    def __init__(self, buffer_pips: float = 5.0, pip_value: float = 0.0001):
        """
        Args:
            buffer_pips: فاصله اضافی از نقطه SL (به پیپ)
            pip_value: ارزش هر پیپ (0.0001 برای اکثر جفت‌ها، 0.01 برای JPY)
        """
        self.buffer_pips = buffer_pips
        self.pip_value = pip_value
    
    @property
    @abstractmethod
    def name(self) -> str:
        """نام استراتژی"""
        pass
    
    @abstractmethod
    def calculate(self, candles: List[dict], direction: TradeDirection, 
                  current_price: float) -> Optional[SLResult]:
        """
        محاسبه قیمت Stop Loss
        
        Args:
            candles: لیست کندل‌ها (هر کندل: {'open', 'high', 'low', 'close', 'time'})
            direction: جهت معامله (BUY یا SELL)
            current_price: قیمت فعلی
            
        Returns:
            SLResult یا None اگر نتوانست محاسبه کند
        """
        pass
    
    def get_buffer(self) -> float:
        """محاسبه فاصله بافر به واحد قیمت"""
        return self.buffer_pips * self.pip_value
    
    def validate_sl(self, sl_price: float, direction: TradeDirection, 
                    current_price: float) -> bool:
        """
        اعتبارسنجی قیمت SL
        
        Args:
            sl_price: قیمت SL محاسبه شده
            direction: جهت معامله
            current_price: قیمت فعلی
            
        Returns:
            True اگر SL معتبر باشد
        """
        if direction == TradeDirection.BUY:
            # برای BUY، SL باید زیر قیمت فعلی باشد
            return sl_price < current_price
        else:
            # برای SELL، SL باید بالای قیمت فعلی باشد
            return sl_price > current_price
