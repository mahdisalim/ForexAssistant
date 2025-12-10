"""
Candlestick Pattern Detection
تشخیص الگوهای کندلی
"""

import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PatternType(Enum):
    """نوع الگو"""
    PIN_BAR_BULLISH = "pin_bar_bullish"
    PIN_BAR_BEARISH = "pin_bar_bearish"
    ENGULFING_BULLISH = "engulfing_bullish"
    ENGULFING_BEARISH = "engulfing_bearish"
    DOJI = "doji"
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"


@dataclass
class CandlePattern:
    """
    الگوی کندلی شناسایی شده
    """
    pattern_type: PatternType
    index: int                    # اندیس کندل در آرایه
    candle_high: float
    candle_low: float
    candle_open: float
    candle_close: float
    strength: float = 1.0         # قدرت الگو (0-1)
    
    @property
    def is_bullish(self) -> bool:
        return self.pattern_type in [
            PatternType.PIN_BAR_BULLISH,
            PatternType.ENGULFING_BULLISH,
            PatternType.HAMMER
        ]
    
    @property
    def is_bearish(self) -> bool:
        return self.pattern_type in [
            PatternType.PIN_BAR_BEARISH,
            PatternType.ENGULFING_BEARISH,
            PatternType.SHOOTING_STAR
        ]


class PatternDetector:
    """
    کلاس تشخیص الگوهای کندلی
    """
    
    def __init__(self, 
                 pin_bar_ratio: float = 2.0,
                 body_ratio_max: float = 0.3,
                 engulfing_min_ratio: float = 1.2):
        """
        Args:
            pin_bar_ratio: نسبت سایه به بدنه برای پین بار
            body_ratio_max: حداکثر نسبت بدنه به کل کندل برای پین بار
            engulfing_min_ratio: حداقل نسبت پوشش برای انگالفینگ
        """
        self.pin_bar_ratio = pin_bar_ratio
        self.body_ratio_max = body_ratio_max
        self.engulfing_min_ratio = engulfing_min_ratio
    
    def detect_pin_bar(self, candles: list, index: int = -1) -> Optional[CandlePattern]:
        """
        تشخیص الگوی پین بار
        
        پین بار صعودی (Bullish Pin Bar):
        - سایه پایین بلند (حداقل 2 برابر بدنه)
        - بدنه کوچک در بالای کندل
        - سایه بالا کوتاه یا بدون سایه
        
        پین بار نزولی (Bearish Pin Bar):
        - سایه بالا بلند (حداقل 2 برابر بدنه)
        - بدنه کوچک در پایین کندل
        - سایه پایین کوتاه یا بدون سایه
        
        Args:
            candles: لیست کندل‌ها
            index: اندیس کندل مورد بررسی
            
        Returns:
            CandlePattern یا None
        """
        if not candles or len(candles) < abs(index):
            return None
        
        candle = candles[index]
        o = candle['open']
        h = candle['high']
        l = candle['low']
        c = candle['close']
        
        # محاسبه اندازه‌ها
        total_range = h - l
        if total_range == 0:
            return None
        
        body = abs(c - o)
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l
        
        body_ratio = body / total_range
        
        # بررسی پین بار صعودی
        if (lower_shadow >= body * self.pin_bar_ratio and 
            body_ratio <= self.body_ratio_max and
            upper_shadow < lower_shadow * 0.3):
            
            strength = min(lower_shadow / (body + 0.00001), 5) / 5
            return CandlePattern(
                pattern_type=PatternType.PIN_BAR_BULLISH,
                index=index if index >= 0 else len(candles) + index,
                candle_high=h,
                candle_low=l,
                candle_open=o,
                candle_close=c,
                strength=strength
            )
        
        # بررسی پین بار نزولی
        if (upper_shadow >= body * self.pin_bar_ratio and 
            body_ratio <= self.body_ratio_max and
            lower_shadow < upper_shadow * 0.3):
            
            strength = min(upper_shadow / (body + 0.00001), 5) / 5
            return CandlePattern(
                pattern_type=PatternType.PIN_BAR_BEARISH,
                index=index if index >= 0 else len(candles) + index,
                candle_high=h,
                candle_low=l,
                candle_open=o,
                candle_close=c,
                strength=strength
            )
        
        return None
    
    def find_last_pin_bar(self, candles: list, direction: str, 
                          lookback: int = 10) -> Optional[CandlePattern]:
        """
        پیدا کردن آخرین پین بار در جهت مشخص
        
        Args:
            candles: لیست کندل‌ها
            direction: جهت مورد نظر ("bullish" یا "bearish")
            lookback: تعداد کندل‌های اخیر برای بررسی
            
        Returns:
            آخرین پین بار یافت شده یا None
        """
        if not candles:
            return None
        
        target_type = (PatternType.PIN_BAR_BULLISH if direction == "bullish" 
                       else PatternType.PIN_BAR_BEARISH)
        
        # بررسی کندل‌های اخیر از آخر به اول
        start_idx = max(0, len(candles) - lookback)
        for i in range(len(candles) - 1, start_idx - 1, -1):
            pattern = self.detect_pin_bar(candles, i)
            if pattern and pattern.pattern_type == target_type:
                return pattern
        
        return None
    
    def detect_engulfing(self, candles: list, index: int = -1) -> Optional[CandlePattern]:
        """
        تشخیص الگوی انگالفینگ
        
        Args:
            candles: لیست کندل‌ها
            index: اندیس کندل دوم (کندل پوشاننده)
            
        Returns:
            CandlePattern یا None
        """
        if not candles or len(candles) < 2:
            return None
        
        if index == -1:
            index = len(candles) - 1
        
        if index < 1:
            return None
        
        curr = candles[index]
        prev = candles[index - 1]
        
        curr_body = abs(curr['close'] - curr['open'])
        prev_body = abs(prev['close'] - prev['open'])
        
        if prev_body == 0:
            return None
        
        # انگالفینگ صعودی
        if (prev['close'] < prev['open'] and  # کندل قبلی نزولی
            curr['close'] > curr['open'] and  # کندل فعلی صعودی
            curr['open'] <= prev['close'] and  # باز شدن زیر بسته شدن قبلی
            curr['close'] >= prev['open'] and  # بسته شدن بالای باز شدن قبلی
            curr_body >= prev_body * self.engulfing_min_ratio):
            
            return CandlePattern(
                pattern_type=PatternType.ENGULFING_BULLISH,
                index=index,
                candle_high=curr['high'],
                candle_low=curr['low'],
                candle_open=curr['open'],
                candle_close=curr['close'],
                strength=min(curr_body / prev_body, 3) / 3
            )
        
        # انگالفینگ نزولی
        if (prev['close'] > prev['open'] and  # کندل قبلی صعودی
            curr['close'] < curr['open'] and  # کندل فعلی نزولی
            curr['open'] >= prev['close'] and  # باز شدن بالای بسته شدن قبلی
            curr['close'] <= prev['open'] and  # بسته شدن زیر باز شدن قبلی
            curr_body >= prev_body * self.engulfing_min_ratio):
            
            return CandlePattern(
                pattern_type=PatternType.ENGULFING_BEARISH,
                index=index,
                candle_high=curr['high'],
                candle_low=curr['low'],
                candle_open=curr['open'],
                candle_close=curr['close'],
                strength=min(curr_body / prev_body, 3) / 3
            )
        
        return None
    
    def find_swing_high(self, candles: list, lookback: int = 5) -> Optional[float]:
        """
        پیدا کردن آخرین سوینگ های (قله)
        
        Args:
            candles: لیست کندل‌ها
            lookback: تعداد کندل‌ها برای تأیید سوینگ
            
        Returns:
            قیمت سوینگ های یا None
        """
        if len(candles) < lookback * 2 + 1:
            return None
        
        highs = [c['high'] for c in candles]
        
        for i in range(len(highs) - lookback - 1, lookback - 1, -1):
            is_swing = True
            for j in range(1, lookback + 1):
                if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                    is_swing = False
                    break
            if is_swing:
                return highs[i]
        
        return None
    
    def find_swing_low(self, candles: list, lookback: int = 5) -> Optional[float]:
        """
        پیدا کردن آخرین سوینگ لو (دره)
        
        Args:
            candles: لیست کندل‌ها
            lookback: تعداد کندل‌ها برای تأیید سوینگ
            
        Returns:
            قیمت سوینگ لو یا None
        """
        if len(candles) < lookback * 2 + 1:
            return None
        
        lows = [c['low'] for c in candles]
        
        for i in range(len(lows) - lookback - 1, lookback - 1, -1):
            is_swing = True
            for j in range(1, lookback + 1):
                if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                    is_swing = False
                    break
            if is_swing:
                return lows[i]
        
        return None


def calculate_sl_from_pin_bar(pattern: CandlePattern, 
                               direction: str,
                               buffer_pips: float = 5.0,
                               pip_value: float = 0.0001) -> float:
    """
    محاسبه Stop Loss بر اساس پین بار
    
    برای BUY: SL زیر کف پین بار صعودی
    برای SELL: SL بالای سقف پین بار نزولی
    
    Args:
        pattern: الگوی پین بار
        direction: جهت معامله ("BUY" یا "SELL")
        buffer_pips: فاصله اضافی به پیپ
        pip_value: ارزش هر پیپ
        
    Returns:
        قیمت Stop Loss
    """
    buffer = buffer_pips * pip_value
    
    if direction == "BUY":
        return pattern.candle_low - buffer
    else:  # SELL
        return pattern.candle_high + buffer


def calculate_tp_from_rr(entry_price: float, 
                         sl_price: float,
                         risk_reward_ratio: float = 2.0) -> float:
    """
    محاسبه Take Profit بر اساس نسبت ریسک به ریوارد
    
    Args:
        entry_price: قیمت ورود
        sl_price: قیمت Stop Loss
        risk_reward_ratio: نسبت ریسک به ریوارد
        
    Returns:
        قیمت Take Profit
    """
    risk = abs(entry_price - sl_price)
    reward = risk * risk_reward_ratio
    
    if entry_price > sl_price:  # BUY
        return entry_price + reward
    else:  # SELL
        return entry_price - reward


def calculate_lot_size(account_balance: float,
                       risk_percent: float,
                       sl_pips: float,
                       pip_value_per_lot: float = 10.0) -> float:
    """
    محاسبه حجم معامله بر اساس ریسک
    
    Args:
        account_balance: موجودی حساب
        risk_percent: درصد ریسک (مثلاً 1.0 برای 1%)
        sl_pips: فاصله SL به پیپ
        pip_value_per_lot: ارزش هر پیپ برای 1 لات
        
    Returns:
        حجم معامله (لات)
    """
    if sl_pips <= 0:
        return 0.01  # حداقل لات
    
    risk_amount = account_balance * (risk_percent / 100)
    lot_size = risk_amount / (sl_pips * pip_value_per_lot)
    
    # گرد کردن به 2 رقم اعشار
    lot_size = round(lot_size, 2)
    
    # حداقل و حداکثر لات
    lot_size = max(0.01, min(lot_size, 100.0))
    
    return lot_size
