"""
RSI Strategy Bot
ربات معاملاتی بر اساس اندیکاتور RSI
"""

import numpy as np
from typing import List, Optional
from datetime import datetime

from .base_bot import BaseStrategyBot
from .models import (
    Signal, PendingSetup,
    SignalType, TradeDirection
)
from .config import BotConfig, SLMode, TPMode, DEFAULT_CONFIG
from .patterns import (
    PatternDetector, 
    calculate_sl_from_pin_bar, 
    calculate_tp_from_rr,
    calculate_lot_size
)


class RSIBot(BaseStrategyBot):
    """
    ربات معاملاتی بر اساس RSI
    
    قوانین سیگنال فوری:
    - RSI از زیر 30 به بالا کراس کند → BUY
    - RSI از بالای 70 به پایین کراس کند → SELL
    
    قوانین سیگنال در انتظار:
    - پیش‌بینی نقاطی که RSI به oversold/overbought می‌رسد
    - بر اساس سطوح حمایت و مقاومت اخیر
    
    ویژگی‌های جدید:
    - SL بر اساس Pin Bar (پشت آخرین پین بار در جهت معامله)
    - TP بر اساس نسبت ریسک به ریوارد
    - پشتیبانی از تنظیمات حساب کاربر
    
    Attributes:
        rsi_period: دوره RSI (پیش‌فرض 14)
        oversold: سطح اشباع فروش (پیش‌فرض 30)
        overbought: سطح اشباع خرید (پیش‌فرض 70)
        config: تنظیمات ربات
    """
    
    def __init__(
        self,
        pairs: List[str],
        timeframe: str = "H1",
        rsi_period: int = 14,
        oversold: int = 30,
        overbought: int = 70,
        config: BotConfig = None
    ):
        super().__init__(name="RSI_Bot", pairs=pairs, timeframe=timeframe)
        
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        
        # تنظیمات ربات
        self.config = config or DEFAULT_CONFIG
        
        # تشخیص‌دهنده الگوها
        self.pattern_detector = PatternDetector()
        
        # ذخیره آخرین کندل‌ها برای تشخیص الگو
        self.candles_cache = {}
        
        self.logger.info(
            f"RSI Bot configured: period={rsi_period}, "
            f"oversold={oversold}, overbought={overbought}, "
            f"SL mode={self.config.trade.sl_mode.value}, "
            f"TP mode={self.config.trade.tp_mode.value}"
        )
    
    def calculate_rsi(self, closes: np.ndarray, period: int = None) -> np.ndarray:
        """
        محاسبه RSI
        
        Args:
            closes: آرایه قیمت‌های بسته شدن
            period: دوره RSI
            
        Returns:
            آرایه مقادیر RSI
        """
        if period is None:
            period = self.rsi_period
        
        if len(closes) < period + 1:
            return np.zeros_like(closes)
        
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        rsi = np.zeros_like(closes)
        
        # اولین میانگین
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            rsi[period] = 100
        else:
            rs = avg_gain / avg_loss
            rsi[period] = 100 - (100 / (1 + rs))
        
        # میانگین‌های بعدی (Smoothed/Wilder)
        for i in range(period + 1, len(closes)):
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
            
            if avg_loss == 0:
                rsi[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_atr(self, highs: np.ndarray, lows: np.ndarray, 
                      closes: np.ndarray, period: int = 14) -> float:
        """
        محاسبه ATR (Average True Range)
        
        Args:
            highs: آرایه قیمت‌های بالا
            lows: آرایه قیمت‌های پایین
            closes: آرایه قیمت‌های بسته شدن
            period: دوره ATR
            
        Returns:
            مقدار ATR
        """
        if len(closes) < period + 1:
            return 0.001  # مقدار پیش‌فرض
        
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )
        
        return np.mean(tr[-period:])
    
    def find_support_resistance(self, highs: np.ndarray, lows: np.ndarray, 
                                 lookback: int = 20) -> tuple:
        """
        پیدا کردن سطوح حمایت و مقاومت اخیر
        
        Args:
            highs: آرایه قیمت‌های بالا
            lows: آرایه قیمت‌های پایین
            lookback: تعداد کندل‌های اخیر
            
        Returns:
            (resistance, support)
        """
        recent_high = np.max(highs[-lookback:])
        recent_low = np.min(lows[-lookback:])
        
        return recent_high, recent_low
    
    def calculate_indicators(self, candles: list) -> dict:
        """
        محاسبه همه اندیکاتورها
        
        Args:
            candles: لیست کندل‌ها
            
        Returns:
            دیکشنری اندیکاتورها
        """
        if not candles or len(candles) < self.rsi_period + 5:
            return {
                "rsi": 50,
                "prev_rsi": 50,
                "current_price": 0,
                "atr": 0.001,
                "resistance": 0,
                "support": 0,
                "rsi_status": "neutral"
            }
        
        closes = np.array([c['close'] for c in candles])
        highs = np.array([c['high'] for c in candles])
        lows = np.array([c['low'] for c in candles])
        
        rsi = self.calculate_rsi(closes)
        atr = self.calculate_atr(highs, lows, closes)
        resistance, support = self.find_support_resistance(highs, lows)
        
        current_rsi = rsi[-1]
        
        # تعیین وضعیت RSI
        if current_rsi < self.oversold:
            rsi_status = "oversold"
        elif current_rsi > self.overbought:
            rsi_status = "overbought"
        else:
            rsi_status = "neutral"
        
        return {
            "rsi": round(current_rsi, 2),
            "prev_rsi": round(rsi[-2], 2) if len(rsi) > 1 else 50,
            "current_price": closes[-1],
            "atr": atr,
            "resistance": resistance,
            "support": support,
            "rsi_status": rsi_status
        }
    
    def get_market_bias(self, indicators: dict) -> str:
        """
        تشخیص جهت کلی بازار
        
        Args:
            indicators: دیکشنری اندیکاتورها
            
        Returns:
            "bullish", "bearish", یا "neutral"
        """
        rsi = indicators.get("rsi", 50)
        
        if rsi < 40:
            return "bearish"
        elif rsi > 60:
            return "bullish"
        else:
            return "neutral"
    
    def _calculate_sl_price(self, candles: list, direction: TradeDirection, 
                             current_price: float, atr: float) -> float:
        """
        محاسبه قیمت Stop Loss بر اساس تنظیمات
        
        Args:
            candles: لیست کندل‌ها
            direction: جهت معامله
            current_price: قیمت فعلی
            atr: مقدار ATR
            
        Returns:
            قیمت SL
        """
        sl_mode = self.config.trade.sl_mode
        
        if sl_mode == SLMode.PIN_BAR:
            # پیدا کردن آخرین پین بار در جهت معامله
            pin_direction = "bullish" if direction == TradeDirection.BUY else "bearish"
            pin_bar = self.pattern_detector.find_last_pin_bar(candles, pin_direction, lookback=15)
            
            if pin_bar:
                sl_price = calculate_sl_from_pin_bar(
                    pin_bar, 
                    direction.value,
                    buffer_pips=self.config.trade.pin_bar_buffer_pips
                )
                self.logger.info(f"SL from Pin Bar: {sl_price:.5f}")
                return sl_price
            else:
                # اگر پین بار پیدا نشد، از ATR استفاده کن
                self.logger.info("No Pin Bar found, using ATR for SL")
                sl_mode = SLMode.ATR_BASED
        
        if sl_mode == SLMode.ATR_BASED:
            sl_distance = atr * self.config.trade.atr_sl_multiplier
            if direction == TradeDirection.BUY:
                return current_price - sl_distance
            else:
                return current_price + sl_distance
        
        # FIXED_PIPS
        pip_value = 0.0001 if "JPY" not in "" else 0.01  # TODO: get from pair
        sl_distance = self.config.trade.default_sl_pips * pip_value
        if direction == TradeDirection.BUY:
            return current_price - sl_distance
        else:
            return current_price + sl_distance
    
    def _calculate_tp_price(self, entry_price: float, sl_price: float, 
                            direction: TradeDirection, atr: float) -> float:
        """
        محاسبه قیمت Take Profit بر اساس تنظیمات
        
        Args:
            entry_price: قیمت ورود
            sl_price: قیمت SL
            direction: جهت معامله
            atr: مقدار ATR
            
        Returns:
            قیمت TP
        """
        tp_mode = self.config.trade.tp_mode
        
        if tp_mode == TPMode.RISK_REWARD:
            return calculate_tp_from_rr(
                entry_price, 
                sl_price, 
                self.config.trade.risk_reward_ratio
            )
        
        if tp_mode == TPMode.ATR_BASED:
            tp_distance = atr * self.config.trade.atr_tp_multiplier
            if direction == TradeDirection.BUY:
                return entry_price + tp_distance
            else:
                return entry_price - tp_distance
        
        # FIXED_PIPS
        pip_value = 0.0001
        tp_distance = self.config.trade.default_tp_pips * pip_value
        if direction == TradeDirection.BUY:
            return entry_price + tp_distance
        else:
            return entry_price - tp_distance
    
    def _calculate_lot_size(self, sl_pips: float) -> float:
        """
        محاسبه حجم معامله بر اساس تنظیمات حساب
        
        Args:
            sl_pips: فاصله SL به پیپ
            
        Returns:
            حجم معامله (لات)
        """
        return calculate_lot_size(
            account_balance=self.config.account.balance,
            risk_percent=self.config.account.risk_percent,
            sl_pips=sl_pips
        )

    def analyze(self, pair: str, candles: list) -> Optional[Signal]:
        """
        تحلیل و تولید سیگنال فوری
        
        شرایط سیگنال BUY:
        - RSI قبلی زیر 30 بود
        - RSI فعلی از 30 به بالا کراس کرده
        
        شرایط سیگنال SELL:
        - RSI قبلی بالای 70 بود
        - RSI فعلی از 70 به پایین کراس کرده
        
        SL: پشت آخرین پین بار در جهت معامله (یا ATR اگر پین بار نباشد)
        TP: بر اساس نسبت ریسک به ریوارد
        
        Args:
            pair: جفت ارز
            candles: لیست کندل‌ها
            
        Returns:
            Signal یا None
        """
        if len(candles) < self.rsi_period + 5:
            return None
        
        # ذخیره کندل‌ها برای استفاده بعدی
        self.candles_cache[pair] = candles
        
        # اگر معامله باز داریم، سیگنال جدید نده
        if pair in self.active_trades:
            return None
        
        indicators = self.calculate_indicators(candles)
        current_rsi = indicators["rsi"]
        prev_rsi = indicators["prev_rsi"]
        current_price = indicators["current_price"]
        atr = indicators["atr"]
        
        signal = None
        
        # === سیگنال BUY ===
        # RSI از زیر oversold به بالا کراس کند
        if prev_rsi < self.oversold and current_rsi >= self.oversold:
            direction = TradeDirection.BUY
            
            # محاسبه SL بر اساس Pin Bar
            sl_price = self._calculate_sl_price(candles, direction, current_price, atr)
            
            # محاسبه TP بر اساس R:R
            tp_price = self._calculate_tp_price(current_price, sl_price, direction, atr)
            
            signal = Signal(
                pair=pair,
                direction=direction,
                signal_type=SignalType.INSTANT,
                entry_price=current_price,
                tp_price=tp_price,
                sl_price=sl_price,
                reason=f"RSI خروج از اشباع فروش (RSI: {prev_rsi:.1f} → {current_rsi:.1f})",
                probability=65
            )
            self.logger.info(f"BUY Signal: {pair} - Entry: {current_price:.5f}, SL: {sl_price:.5f}, TP: {tp_price:.5f}")
        
        # === سیگنال SELL ===
        # RSI از بالای overbought به پایین کراس کند
        elif prev_rsi > self.overbought and current_rsi <= self.overbought:
            direction = TradeDirection.SELL
            
            # محاسبه SL بر اساس Pin Bar
            sl_price = self._calculate_sl_price(candles, direction, current_price, atr)
            
            # محاسبه TP بر اساس R:R
            tp_price = self._calculate_tp_price(current_price, sl_price, direction, atr)
            
            signal = Signal(
                pair=pair,
                direction=direction,
                signal_type=SignalType.INSTANT,
                entry_price=current_price,
                tp_price=tp_price,
                sl_price=sl_price,
                reason=f"RSI خروج از اشباع خرید (RSI: {prev_rsi:.1f} → {current_rsi:.1f})",
                probability=65
            )
            self.logger.info(f"SELL Signal: {pair} - Entry: {current_price:.5f}, SL: {sl_price:.5f}, TP: {tp_price:.5f}")
        
        return signal
    
    def find_pending_setups(self, pair: str, candles: list) -> List[PendingSetup]:
        """
        پیدا کردن نقاط چرخش احتمالی برای هر دو جهت
        
        این متد پیش‌بینی می‌کند که در چه قیمت‌هایی احتمالاً
        RSI به سطوح oversold/overbought می‌رسد.
        
        Args:
            pair: جفت ارز
            candles: لیست کندل‌ها
            
        Returns:
            لیست سیگنال‌های در انتظار
        """
        if len(candles) < self.rsi_period + 5:
            return []
        
        indicators = self.calculate_indicators(candles)
        current_price = indicators["current_price"]
        current_rsi = indicators["rsi"]
        resistance = indicators["resistance"]
        support = indicators["support"]
        atr = indicators["atr"]
        
        setups = []
        
        # === سیگنال BUY در انتظار ===
        # اگر RSI هنوز به oversold نرسیده
        if current_rsi > self.oversold + 10:
            # تخمین قیمتی که RSI به oversold می‌رسد
            # معمولاً نزدیک به سطح حمایت
            buy_trigger = support - (atr * 0.3)
            buy_entry = support
            
            setups.append(PendingSetup(
                pair=pair,
                direction=TradeDirection.BUY,
                trigger_price=buy_trigger,
                entry_price=buy_entry,
                tp_price=buy_entry + (atr * self.atr_multiplier_tp),
                sl_price=buy_entry - (atr * self.atr_multiplier_sl),
                condition="price_below",
                reason=f"انتظار RSI oversold نزدیک حمایت {support:.5f}",
                probability=60,
                created_at=datetime.now()
            ))
        
        # === سیگنال SELL در انتظار ===
        # اگر RSI هنوز به overbought نرسیده
        if current_rsi < self.overbought - 10:
            # تخمین قیمتی که RSI به overbought می‌رسد
            # معمولاً نزدیک به سطح مقاومت
            sell_trigger = resistance + (atr * 0.3)
            sell_entry = resistance
            
            setups.append(PendingSetup(
                pair=pair,
                direction=TradeDirection.SELL,
                trigger_price=sell_trigger,
                entry_price=sell_entry,
                tp_price=sell_entry - (atr * self.atr_multiplier_tp),
                sl_price=sell_entry + (atr * self.atr_multiplier_sl),
                condition="price_above",
                reason=f"انتظار RSI overbought نزدیک مقاومت {resistance:.5f}",
                probability=60,
                created_at=datetime.now()
            ))
        
        # ذخیره در pending_setups
        self.pending_setups[pair] = setups
        
        return setups
    
    def get_analysis_summary(self, pair: str, candles: list) -> dict:
        """
        خلاصه تحلیل برای نمایش در UI
        
        Args:
            pair: جفت ارز
            candles: لیست کندل‌ها
            
        Returns:
            دیکشنری خلاصه تحلیل
        """
        analysis = self.get_full_analysis(pair, candles)
        
        return {
            "pair": pair,
            "timestamp": analysis.timestamp.isoformat(),
            "current_price": round(analysis.current_price, 5),
            "rsi": analysis.indicators.get("rsi", 50),
            "rsi_status": analysis.indicators.get("rsi_status", "neutral"),
            "market_bias": analysis.market_bias,
            "has_instant_signal": analysis.instant_signal is not None,
            "instant_signal": analysis.instant_signal.to_dict() if analysis.instant_signal else None,
            "pending_count": len(analysis.pending_setups),
            "pending_setups": [s.to_dict() for s in analysis.pending_setups],
            "has_active_trade": analysis.active_trade is not None,
            "active_trade": analysis.active_trade.to_dict() if analysis.active_trade else None
        }
