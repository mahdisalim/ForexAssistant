"""
Base Strategy Bot
کلاس پایه برای همه ربات‌های استراتژی
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
import logging

from .models import (
    Signal, Trade, PendingSetup, BotAnalysis,
    SignalType, TradeDirection, TradeStatus
)


class BaseStrategyBot(ABC):
    """
    کلاس پایه برای همه ربات‌های استراتژی
    
    هر ربات استراتژی باید از این کلاس ارث‌بری کند و
    متدهای abstract را پیاده‌سازی کند.
    
    Attributes:
        name: نام ربات
        pairs: لیست جفت ارزهای مورد نظر
        timeframe: تایم‌فریم اصلی
        active_trades: معاملات باز
        pending_setups: سیگنال‌های در انتظار
        signal_history: تاریخچه سیگنال‌ها
        trade_history: تاریخچه معاملات
    """
    
    def __init__(self, name: str, pairs: List[str], timeframe: str = "H1"):
        self.name = name
        self.pairs = pairs
        self.timeframe = timeframe
        self.active_trades: Dict[str, Trade] = {}
        self.pending_setups: Dict[str, List[PendingSetup]] = {}
        self.signal_history: List[Signal] = []
        self.trade_history: List[Trade] = []
        self.logger = logging.getLogger(f"Bot.{name}")
        
        # تنظیمات پیش‌فرض
        self.default_tp_pips = 60
        self.default_sl_pips = 30
        self.max_trades_per_pair = 1
        
        self.logger.info(f"Bot '{name}' initialized with pairs: {pairs}")
    
    @abstractmethod
    def analyze(self, pair: str, candles: list) -> Optional[Signal]:
        """
        تحلیل و تولید سیگنال فوری
        
        Args:
            pair: جفت ارز
            candles: لیست کندل‌ها
            
        Returns:
            Signal اگر سیگنال وجود داشته باشد، در غیر این صورت None
        """
        pass
    
    @abstractmethod
    def find_pending_setups(self, pair: str, candles: list) -> List[PendingSetup]:
        """
        پیدا کردن نقاط چرخش احتمالی برای هر دو جهت
        
        Args:
            pair: جفت ارز
            candles: لیست کندل‌ها
            
        Returns:
            لیست سیگنال‌های در انتظار
        """
        pass
    
    @abstractmethod
    def calculate_indicators(self, candles: list) -> dict:
        """
        محاسبه اندیکاتورها
        
        Args:
            candles: لیست کندل‌ها
            
        Returns:
            دیکشنری شامل مقادیر اندیکاتورها
        """
        pass
    
    def get_market_bias(self, indicators: dict) -> str:
        """
        تشخیص جهت کلی بازار
        
        Args:
            indicators: دیکشنری اندیکاتورها
            
        Returns:
            "bullish", "bearish", یا "neutral"
        """
        return "neutral"
    
    def open_trade(self, signal: Signal) -> Trade:
        """
        باز کردن معامله جدید
        
        Args:
            signal: سیگنال معاملاتی
            
        Returns:
            معامله ایجاد شده
        """
        import uuid
        
        # بررسی آیا معامله‌ای برای این جفت ارز باز است
        if signal.pair in self.active_trades:
            existing = self.active_trades[signal.pair]
            if existing.status == TradeStatus.OPEN:
                self.logger.warning(f"Trade already open for {signal.pair}")
                return existing
        
        trade = Trade(
            id=str(uuid.uuid4())[:8],
            pair=signal.pair,
            direction=signal.direction,
            entry_price=signal.entry_price,
            current_price=signal.entry_price,
            tp_price=signal.tp_price,
            sl_price=signal.sl_price,
            status=TradeStatus.OPEN,
            pnl_pips=0,
            open_time=datetime.now()
        )
        
        self.active_trades[signal.pair] = trade
        self.signal_history.append(signal)
        
        self.logger.info(
            f"Trade OPENED: {trade.pair} {trade.direction.value} @ {trade.entry_price:.5f} "
            f"TP: {trade.tp_price:.5f} SL: {trade.sl_price:.5f}"
        )
        
        return trade
    
    def close_trade(self, pair: str, reason: TradeStatus = TradeStatus.CLOSED_MANUAL) -> Optional[Trade]:
        """
        بستن معامله
        
        Args:
            pair: جفت ارز
            reason: دلیل بستن
            
        Returns:
            معامله بسته شده یا None
        """
        if pair not in self.active_trades:
            return None
        
        trade = self.active_trades[pair]
        trade.status = reason
        trade.close_time = datetime.now()
        
        # انتقال به تاریخچه
        self.trade_history.append(trade)
        del self.active_trades[pair]
        
        self.logger.info(
            f"Trade CLOSED: {trade.pair} {trade.direction.value} "
            f"PnL: {trade.pnl_pips:+.1f} pips ({reason.value})"
        )
        
        return trade
    
    def update_trade_status(self, pair: str, current_price: float) -> Optional[Trade]:
        """
        بروزرسانی وضعیت معامله باز
        
        Args:
            pair: جفت ارز
            current_price: قیمت فعلی
            
        Returns:
            معامله بروزرسانی شده یا None
        """
        if pair not in self.active_trades:
            return None
        
        trade = self.active_trades[pair]
        trade.current_price = current_price
        
        # محاسبه PnL
        if trade.direction == TradeDirection.BUY:
            trade.pnl_pips = (current_price - trade.entry_price) * 10000
        else:
            trade.pnl_pips = (trade.entry_price - current_price) * 10000
        
        # بررسی TP/SL
        hit_tp = False
        hit_sl = False
        
        if trade.direction == TradeDirection.BUY:
            hit_tp = current_price >= trade.tp_price
            hit_sl = current_price <= trade.sl_price
        else:
            hit_tp = current_price <= trade.tp_price
            hit_sl = current_price >= trade.sl_price
        
        if hit_tp:
            self.close_trade(pair, TradeStatus.CLOSED_TP)
        elif hit_sl:
            self.close_trade(pair, TradeStatus.CLOSED_SL)
        
        return trade
    
    def check_pending_triggers(self, pair: str, current_price: float) -> Optional[Signal]:
        """
        بررسی فعال شدن سیگنال‌های در انتظار
        
        Args:
            pair: جفت ارز
            current_price: قیمت فعلی
            
        Returns:
            سیگنال فعال شده یا None
        """
        if pair not in self.pending_setups:
            return None
        
        for setup in self.pending_setups[pair]:
            if setup.is_triggered(current_price):
                signal = Signal(
                    pair=pair,
                    direction=setup.direction,
                    signal_type=SignalType.INSTANT,
                    entry_price=setup.entry_price,
                    tp_price=setup.tp_price,
                    sl_price=setup.sl_price,
                    reason=f"Pending triggered: {setup.reason}",
                    probability=setup.probability
                )
                
                # حذف از لیست در انتظار
                self.pending_setups[pair].remove(setup)
                
                self.logger.info(f"Pending setup TRIGGERED: {pair} {setup.direction.value}")
                
                return signal
        
        return None
    
    def get_full_analysis(self, pair: str, candles: list) -> BotAnalysis:
        """
        تحلیل کامل شامل سیگنال فوری + در انتظار + وضعیت معامله
        
        Args:
            pair: جفت ارز
            candles: لیست کندل‌ها
            
        Returns:
            تحلیل کامل
        """
        # محاسبه اندیکاتورها
        indicators = self.calculate_indicators(candles)
        current_price = candles[-1]['close'] if candles else 0
        
        # بروزرسانی معامله باز
        if pair in self.active_trades:
            self.update_trade_status(pair, current_price)
        
        # بررسی سیگنال‌های در انتظار
        triggered_signal = self.check_pending_triggers(pair, current_price)
        if triggered_signal:
            self.open_trade(triggered_signal)
        
        # تحلیل برای سیگنال جدید
        instant_signal = self.analyze(pair, candles)
        if instant_signal and pair not in self.active_trades:
            self.open_trade(instant_signal)
        
        # پیدا کردن سیگنال‌های در انتظار
        pending_setups = self.find_pending_setups(pair, candles)
        
        # تشخیص جهت بازار
        market_bias = self.get_market_bias(indicators)
        
        return BotAnalysis(
            pair=pair,
            timestamp=datetime.now(),
            current_price=current_price,
            indicators=indicators,
            market_bias=market_bias,
            instant_signal=instant_signal,
            pending_setups=pending_setups,
            active_trade=self.active_trades.get(pair)
        )
    
    def get_status(self) -> dict:
        """
        وضعیت کلی ربات
        
        Returns:
            دیکشنری وضعیت
        """
        total_pnl = sum(t.pnl_pips for t in self.active_trades.values())
        
        return {
            "name": self.name,
            "pairs": self.pairs,
            "timeframe": self.timeframe,
            "active_trades": len(self.active_trades),
            "pending_setups": sum(len(s) for s in self.pending_setups.values()),
            "total_signals": len(self.signal_history),
            "total_trades": len(self.trade_history),
            "current_pnl_pips": round(total_pnl, 1),
            "trades": {pair: t.to_dict() for pair, t in self.active_trades.items()}
        }
    
    def get_statistics(self) -> dict:
        """
        آمار عملکرد ربات
        
        Returns:
            دیکشنری آمار
        """
        if not self.trade_history:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_win": 0,
                "avg_loss": 0
            }
        
        wins = [t for t in self.trade_history if t.status == TradeStatus.CLOSED_TP]
        losses = [t for t in self.trade_history if t.status == TradeStatus.CLOSED_SL]
        
        total_pnl = sum(t.pnl_pips for t in self.trade_history)
        win_rate = len(wins) / len(self.trade_history) * 100 if self.trade_history else 0
        avg_win = sum(t.pnl_pips for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.pnl_pips for t in losses) / len(losses) if losses else 0
        
        return {
            "total_trades": len(self.trade_history),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "total_pnl": round(total_pnl, 1),
            "avg_win": round(avg_win, 1),
            "avg_loss": round(avg_loss, 1)
        }
