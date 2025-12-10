"""
Pin Bar Stop Loss Strategy
استراتژی استاپ لاس بر اساس پین بار

پین بار یک الگوی کندلی است که نشان‌دهنده برگشت احتمالی قیمت است.
- پین بار صعودی: سایه پایین بلند، بدنه کوچک در بالا
- پین بار نزولی: سایه بالا بلند، بدنه کوچک در پایین

استاپ لاس پشت آخرین پین بار در جهت معامله قرار می‌گیرد.
"""

from typing import List, Optional
from dataclasses import dataclass

from .base import BaseSLStrategy, SLResult, TradeDirection


@dataclass
class PinBar:
    """
    ساختار داده پین بار
    
    Attributes:
        index: اندیس کندل در لیست
        high: بالاترین قیمت
        low: پایین‌ترین قیمت
        open: قیمت باز شدن
        close: قیمت بسته شدن
        is_bullish: آیا پین بار صعودی است
        strength: قدرت الگو (0-1)
        body_ratio: نسبت بدنه به کل کندل
        shadow_ratio: نسبت سایه اصلی به بدنه
    """
    index: int
    high: float
    low: float
    open: float
    close: float
    is_bullish: bool
    strength: float
    body_ratio: float
    shadow_ratio: float
    
    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def total_range(self) -> float:
        return self.high - self.low
    
    @property
    def upper_shadow(self) -> float:
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> float:
        return min(self.open, self.close) - self.low


class PinBarSL(BaseSLStrategy):
    """
    استراتژی Stop Loss بر اساس Pin Bar
    
    این استراتژی آخرین پین بار در جهت معامله را پیدا کرده
    و SL را پشت آن قرار می‌دهد.
    
    برای BUY: SL زیر کف آخرین پین بار صعودی
    برای SELL: SL بالای سقف آخرین پین بار نزولی
    
    Attributes:
        min_shadow_ratio: حداقل نسبت سایه به بدنه (پیش‌فرض 2.0)
        max_body_ratio: حداکثر نسبت بدنه به کل کندل (پیش‌فرض 0.35)
        lookback: تعداد کندل‌های اخیر برای جستجو (پیش‌فرض 20)
    """
    
    def __init__(
        self,
        buffer_pips: float = 5.0,
        pip_value: float = 0.0001,
        min_shadow_ratio: float = 2.0,
        max_body_ratio: float = 0.35,
        lookback: int = 20
    ):
        """
        Args:
            buffer_pips: فاصله اضافی از پین بار (پیپ)
            pip_value: ارزش هر پیپ
            min_shadow_ratio: حداقل نسبت سایه به بدنه
            max_body_ratio: حداکثر نسبت بدنه به کل کندل
            lookback: تعداد کندل برای جستجو
        """
        super().__init__(buffer_pips, pip_value)
        self.min_shadow_ratio = min_shadow_ratio
        self.max_body_ratio = max_body_ratio
        self.lookback = lookback
    
    @property
    def name(self) -> str:
        return "Pin Bar SL"
    
    def detect_pin_bar(self, candle: dict, index: int) -> Optional[PinBar]:
        """
        تشخیص پین بار در یک کندل
        
        Args:
            candle: دیکشنری کندل
            index: اندیس کندل
            
        Returns:
            PinBar یا None
        """
        o = candle.get('open', 0)
        h = candle.get('high', 0)
        l = candle.get('low', 0)
        c = candle.get('close', 0)
        
        total_range = h - l
        if total_range == 0:
            return None
        
        body = abs(c - o)
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l
        
        body_ratio = body / total_range
        
        # بررسی شرایط پین بار
        if body_ratio > self.max_body_ratio:
            return None
        
        # پین بار صعودی: سایه پایین بلند
        if body > 0:
            shadow_ratio = lower_shadow / body if body > 0 else 0
        else:
            shadow_ratio = lower_shadow / (total_range * 0.1)  # بدنه خیلی کوچک
        
        is_bullish_pin = (
            lower_shadow >= body * self.min_shadow_ratio and
            upper_shadow < lower_shadow * 0.3
        )
        
        # پین بار نزولی: سایه بالا بلند
        if body > 0:
            upper_shadow_ratio = upper_shadow / body
        else:
            upper_shadow_ratio = upper_shadow / (total_range * 0.1)
        
        is_bearish_pin = (
            upper_shadow >= body * self.min_shadow_ratio and
            lower_shadow < upper_shadow * 0.3
        )
        
        if is_bullish_pin:
            strength = min(shadow_ratio / 5, 1.0)
            return PinBar(
                index=index,
                high=h, low=l, open=o, close=c,
                is_bullish=True,
                strength=strength,
                body_ratio=body_ratio,
                shadow_ratio=shadow_ratio
            )
        
        if is_bearish_pin:
            strength = min(upper_shadow_ratio / 5, 1.0)
            return PinBar(
                index=index,
                high=h, low=l, open=o, close=c,
                is_bullish=False,
                strength=strength,
                body_ratio=body_ratio,
                shadow_ratio=upper_shadow_ratio
            )
        
        return None
    
    def find_last_pin_bar(self, candles: List[dict], 
                          direction: TradeDirection) -> Optional[PinBar]:
        """
        پیدا کردن آخرین پین بار در جهت مشخص
        
        Args:
            candles: لیست کندل‌ها
            direction: جهت معامله
            
        Returns:
            آخرین PinBar یافت شده یا None
        """
        if not candles:
            return None
        
        # جستجو از آخر به اول
        start_idx = max(0, len(candles) - self.lookback)
        
        for i in range(len(candles) - 1, start_idx - 1, -1):
            pin_bar = self.detect_pin_bar(candles[i], i)
            
            if pin_bar:
                # برای BUY: پین بار صعودی
                if direction == TradeDirection.BUY and pin_bar.is_bullish:
                    return pin_bar
                # برای SELL: پین بار نزولی
                elif direction == TradeDirection.SELL and not pin_bar.is_bullish:
                    return pin_bar
        
        return None
    
    def find_all_pin_bars(self, candles: List[dict], 
                          direction: Optional[TradeDirection] = None) -> List[PinBar]:
        """
        پیدا کردن همه پین بارها
        
        Args:
            candles: لیست کندل‌ها
            direction: فیلتر جهت (اختیاری)
            
        Returns:
            لیست پین بارها
        """
        pin_bars = []
        
        for i, candle in enumerate(candles):
            pin_bar = self.detect_pin_bar(candle, i)
            
            if pin_bar:
                if direction is None:
                    pin_bars.append(pin_bar)
                elif direction == TradeDirection.BUY and pin_bar.is_bullish:
                    pin_bars.append(pin_bar)
                elif direction == TradeDirection.SELL and not pin_bar.is_bullish:
                    pin_bars.append(pin_bar)
        
        return pin_bars
    
    def calculate(self, candles: List[dict], direction: TradeDirection,
                  current_price: float) -> Optional[SLResult]:
        """
        محاسبه Stop Loss بر اساس آخرین پین بار
        
        Args:
            candles: لیست کندل‌ها
            direction: جهت معامله
            current_price: قیمت فعلی
            
        Returns:
            SLResult یا None
        """
        pin_bar = self.find_last_pin_bar(candles, direction)
        
        if not pin_bar:
            return None
        
        buffer = self.get_buffer()
        
        if direction == TradeDirection.BUY:
            # SL زیر کف پین بار صعودی
            sl_price = pin_bar.low - buffer
            reason = f"زیر کف پین بار صعودی (کندل {pin_bar.index})"
        else:
            # SL بالای سقف پین بار نزولی
            sl_price = pin_bar.high + buffer
            reason = f"بالای سقف پین بار نزولی (کندل {pin_bar.index})"
        
        # اعتبارسنجی
        if not self.validate_sl(sl_price, direction, current_price):
            return None
        
        confidence = 60 + (pin_bar.strength * 40)  # 60-100
        
        return SLResult(
            sl_price=sl_price,
            method=self.name,
            reason=reason,
            confidence=confidence,
            pattern_index=pin_bar.index,
            fallback_used=False
        )
