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
from .sl_strategies import (
    PinBarSL, ATRSL, SwingPointSL, CompositeSL,
    TradeDirection as SLDirection
)
from .tp_strategies import (
    MultiTargetTP, RiskRewardTP, ATRTP, FixedPipsTP, CompositeTP,
    TradeDirection as TPDirection
)


def calculate_lot_size(account_balance: float, risk_percent: float,
                       sl_pips: float, pip_value_per_lot: float = 10.0) -> float:
    """محاسبه حجم معامله"""
    if sl_pips <= 0:
        return 0.01
    risk_amount = account_balance * (risk_percent / 100)
    lot_size = risk_amount / (sl_pips * pip_value_per_lot)
    return max(0.01, min(round(lot_size, 2), 100.0))


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
    - SL بر اساس Pin Bar (ماژول مستقل sl_strategies)
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
        
        # ماژول SL - استفاده از ماژول مستقل
        self._init_sl_strategy()
        
        # ماژول TP - استفاده از MultiTargetTP
        self._init_tp_strategy()
        
        # ذخیره آخرین کندل‌ها برای تشخیص الگو
        self.candles_cache = {}
        
        self.logger.info(
            f"RSI Bot configured: period={rsi_period}, "
            f"oversold={oversold}, overbought={overbought}, "
            f"SL: PinBar, TP: MultiTarget"
        )
    
    def _init_sl_strategy(self):
        """راه‌اندازی استراتژی SL بر اساس تنظیمات"""
        sl_mode = self.config.trade.sl_mode
        buffer = self.config.trade.pin_bar_buffer_pips
        
        if sl_mode == SLMode.PIN_BAR:
            # استفاده از ترکیبی: اول Pin Bar، بعد ATR
            self.sl_strategy = CompositeSL(
                strategies=[PinBarSL(buffer_pips=buffer)],
                fallback_strategy=ATRSL(multiplier=self.config.trade.atr_sl_multiplier)
            )
        elif sl_mode == SLMode.SWING_POINT:
            self.sl_strategy = CompositeSL(
                strategies=[SwingPointSL(buffer_pips=buffer)],
                fallback_strategy=ATRSL(multiplier=self.config.trade.atr_sl_multiplier)
            )
        elif sl_mode == SLMode.ATR_BASED:
            self.sl_strategy = ATRSL(multiplier=self.config.trade.atr_sl_multiplier)
        else:
            # FIXED_PIPS - از ATR با ضریب ثابت استفاده می‌کنیم
            self.sl_strategy = ATRSL(multiplier=1.0)
    
    def _init_tp_strategy(self):
        """راه‌اندازی استراتژی TP - MultiTarget"""
        # تنظیمات Multi-Target TP
        # TP1: R:R 1:1, بستن 50% پوزیشن
        # TP2: R:R 1:2, بستن 30% پوزیشن  
        # TP3: R:R 1:3, بستن 20% پوزیشن
        self.tp_strategy = MultiTargetTP(targets=[
            (1.0, 50),   # TP1
            (2.0, 30),   # TP2
            (3.0, 20),   # TP3
        ])
        
        # ذخیره آخرین نتایج TP برای هر جفت ارز
        self.tp_levels = {}
    
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
        محاسبه قیمت Stop Loss با استفاده از ماژول sl_strategies
        
        Args:
            candles: لیست کندل‌ها
            direction: جهت معامله
            current_price: قیمت فعلی
            atr: مقدار ATR (برای fallback)
            
        Returns:
            قیمت SL
        """
        # تبدیل جهت به فرمت ماژول SL
        sl_direction = SLDirection.BUY if direction == TradeDirection.BUY else SLDirection.SELL
        
        # استفاده از ماژول مستقل SL
        result = self.sl_strategy.calculate(candles, sl_direction, current_price)
        
        self.logger.info(f"SL calculated: {result.sl_price:.5f} (method: {result.method}, reason: {result.reason})")
        
        return result.sl_price
    
    def _calculate_tp_prices(self, pair: str, entry_price: float, sl_price: float, 
                              direction: TradeDirection) -> list:
        """
        محاسبه قیمت‌های Take Profit با استفاده از MultiTargetTP
        
        Args:
            pair: جفت ارز
            entry_price: قیمت ورود
            sl_price: قیمت SL
            direction: جهت معامله
            
        Returns:
            لیست TPResult برای هر سطح
        """
        tp_direction = TPDirection.BUY if direction == TradeDirection.BUY else TPDirection.SELL
        
        # محاسبه همه سطوح TP
        tp_results = self.tp_strategy.calculate_all(entry_price, sl_price, tp_direction)
        
        # ذخیره برای استفاده بعدی
        self.tp_levels[pair] = tp_results
        
        # لاگ
        for i, tp in enumerate(tp_results, 1):
            self.logger.info(f"TP{i}: {tp.tp_price:.5f} (R:R {tp.risk_reward_ratio})")
        
        return tp_results
    
    def _get_primary_tp(self, pair: str, entry_price: float, sl_price: float,
                        direction: TradeDirection) -> float:
        """
        دریافت اولین TP (برای سازگاری با Signal)
        
        Returns:
            قیمت TP اول
        """
        tp_results = self._calculate_tp_prices(pair, entry_price, sl_price, direction)
        return tp_results[0].tp_price if tp_results else entry_price
    
    def _format_tp_info(self, pair: str) -> str:
        """
        فرمت اطلاعات همه سطوح TP برای نمایش
        
        Returns:
            متن فرمت شده TPها
        """
        if pair not in self.tp_levels:
            return ""
        
        lines = ["📊 سطوح حد سود:"]
        for i, tp in enumerate(self.tp_levels[pair], 1):
            lines.append(f"  TP{i}: {tp.tp_price:.5f} (R:R 1:{tp.risk_reward_ratio:.0f}) - بستن {self.tp_strategy.targets[i-1][1]}%")
        
        return "\n".join(lines)
    
    def get_tp_levels(self, pair: str) -> list:
        """
        دریافت همه سطوح TP برای یک جفت ارز
        
        Returns:
            لیست TPResult
        """
        return self.tp_levels.get(pair, [])
    
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
            
            # محاسبه TP با MultiTarget (اولین TP برای Signal)
            tp_price = self._get_primary_tp(pair, current_price, sl_price, direction)
            
            # ساخت reason با اطلاعات همه TPها
            tp_info = self._format_tp_info(pair)
            
            signal = Signal(
                pair=pair,
                direction=direction,
                signal_type=SignalType.INSTANT,
                entry_price=current_price,
                tp_price=tp_price,
                sl_price=sl_price,
                reason=f"RSI خروج از اشباع فروش (RSI: {prev_rsi:.1f} → {current_rsi:.1f})\n{tp_info}",
                probability=65
            )
            self.logger.info(f"BUY Signal: {pair} - Entry: {current_price:.5f}, SL: {sl_price:.5f}")
        
        # === سیگنال SELL ===
        # RSI از بالای overbought به پایین کراس کند
        elif prev_rsi > self.overbought and current_rsi <= self.overbought:
            direction = TradeDirection.SELL
            
            # محاسبه SL بر اساس Pin Bar
            sl_price = self._calculate_sl_price(candles, direction, current_price, atr)
            
            # محاسبه TP با MultiTarget (اولین TP برای Signal)
            tp_price = self._get_primary_tp(pair, current_price, sl_price, direction)
            
            # ساخت reason با اطلاعات همه TPها
            tp_info = self._format_tp_info(pair)
            
            signal = Signal(
                pair=pair,
                direction=direction,
                signal_type=SignalType.INSTANT,
                entry_price=current_price,
                tp_price=tp_price,
                sl_price=sl_price,
                reason=f"RSI خروج از اشباع خرید (RSI: {prev_rsi:.1f} → {current_rsi:.1f})\n{tp_info}",
                probability=65
            )
            self.logger.info(f"SELL Signal: {pair} - Entry: {current_price:.5f}, SL: {sl_price:.5f}")
        
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
