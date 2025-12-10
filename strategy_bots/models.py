"""
Data Models for Strategy Bots
مدل‌های داده برای ربات‌های استراتژی
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional, List


class SignalType(Enum):
    """نوع سیگنال"""
    INSTANT = "instant"      # سیگنال فوری - همین الان معامله کن
    PENDING = "pending"      # در انتظار قیمت - وقتی قیمت رسید معامله کن


class TradeDirection(Enum):
    """جهت معامله"""
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(Enum):
    """وضعیت معامله"""
    OPEN = "open"                    # معامله باز است
    CLOSED_TP = "closed_tp"          # بسته شده با سود (Take Profit)
    CLOSED_SL = "closed_sl"          # بسته شده با ضرر (Stop Loss)
    CLOSED_MANUAL = "closed_manual"  # بسته شده دستی


@dataclass
class Signal:
    """
    سیگنال معاملاتی
    
    Attributes:
        pair: جفت ارز (مثل EURUSD)
        direction: جهت معامله (BUY/SELL)
        signal_type: نوع سیگنال (فوری/در انتظار)
        entry_price: قیمت ورود
        tp_price: قیمت Take Profit
        sl_price: قیمت Stop Loss
        trigger_price: قیمت فعال‌سازی (برای سیگنال‌های در انتظار)
        reason: دلیل سیگنال
        probability: درصد احتمال موفقیت
        timestamp: زمان ایجاد سیگنال
    """
    pair: str
    direction: TradeDirection
    signal_type: SignalType
    entry_price: float
    tp_price: float
    sl_price: float
    trigger_price: Optional[float] = None
    reason: str = ""
    probability: int = 50
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """تبدیل به دیکشنری"""
        return {
            "pair": self.pair,
            "direction": self.direction.value,
            "signal_type": self.signal_type.value,
            "entry_price": round(self.entry_price, 5),
            "tp_price": round(self.tp_price, 5),
            "sl_price": round(self.sl_price, 5),
            "trigger_price": round(self.trigger_price, 5) if self.trigger_price else None,
            "reason": self.reason,
            "probability": self.probability,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Trade:
    """
    معامله باز یا بسته شده
    
    Attributes:
        id: شناسه یکتای معامله
        pair: جفت ارز
        direction: جهت معامله
        entry_price: قیمت ورود
        current_price: قیمت فعلی
        tp_price: قیمت Take Profit
        sl_price: قیمت Stop Loss
        status: وضعیت معامله
        pnl_pips: سود/ضرر به پیپ
        open_time: زمان باز شدن
        close_time: زمان بسته شدن
    """
    id: str
    pair: str
    direction: TradeDirection
    entry_price: float
    current_price: float
    tp_price: float
    sl_price: float
    status: TradeStatus = TradeStatus.OPEN
    pnl_pips: float = 0.0
    open_time: datetime = field(default_factory=datetime.now)
    close_time: Optional[datetime] = None
    
    @property
    def is_in_profit(self) -> bool:
        """آیا معامله در سود است؟"""
        return self.pnl_pips > 0
    
    @property
    def tp_distance_pips(self) -> float:
        """فاصله تا TP به پیپ"""
        if self.direction == TradeDirection.BUY:
            return (self.tp_price - self.current_price) * 10000
        else:
            return (self.current_price - self.tp_price) * 10000
    
    @property
    def sl_distance_pips(self) -> float:
        """فاصله تا SL به پیپ"""
        if self.direction == TradeDirection.BUY:
            return (self.current_price - self.sl_price) * 10000
        else:
            return (self.sl_price - self.current_price) * 10000
    
    def to_dict(self) -> dict:
        """تبدیل به دیکشنری"""
        return {
            "id": self.id,
            "pair": self.pair,
            "direction": self.direction.value,
            "entry_price": round(self.entry_price, 5),
            "current_price": round(self.current_price, 5),
            "tp_price": round(self.tp_price, 5),
            "sl_price": round(self.sl_price, 5),
            "status": self.status.value,
            "pnl_pips": round(self.pnl_pips, 1),
            "is_in_profit": self.is_in_profit,
            "tp_distance_pips": round(self.tp_distance_pips, 1),
            "sl_distance_pips": round(self.sl_distance_pips, 1),
            "open_time": self.open_time.isoformat(),
            "close_time": self.close_time.isoformat() if self.close_time else None
        }


@dataclass
class PendingSetup:
    """
    سیگنال در انتظار رسیدن قیمت
    
    این کلاس برای ذخیره سیگنال‌هایی است که هنوز فعال نشده‌اند
    و منتظر رسیدن قیمت به یک سطح خاص هستند.
    
    Attributes:
        pair: جفت ارز
        direction: جهت معامله پس از فعال شدن
        trigger_price: قیمتی که باید به آن برسد تا سیگنال فعال شود
        entry_price: قیمت ورود پس از فعال شدن
        tp_price: قیمت Take Profit
        sl_price: قیمت Stop Loss
        condition: شرط فعال شدن ("price_above" یا "price_below")
        reason: دلیل این سیگنال
        probability: درصد احتمال موفقیت
        created_at: زمان ایجاد
    """
    pair: str
    direction: TradeDirection
    trigger_price: float
    entry_price: float
    tp_price: float
    sl_price: float
    condition: str  # "price_above" or "price_below"
    reason: str = ""
    probability: int = 50
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_triggered(self, current_price: float) -> bool:
        """بررسی آیا شرط فعال شدن برقرار است"""
        if self.condition == "price_above":
            return current_price >= self.trigger_price
        elif self.condition == "price_below":
            return current_price <= self.trigger_price
        return False
    
    def to_dict(self) -> dict:
        """تبدیل به دیکشنری"""
        return {
            "pair": self.pair,
            "direction": self.direction.value,
            "trigger_price": round(self.trigger_price, 5),
            "entry_price": round(self.entry_price, 5),
            "tp_price": round(self.tp_price, 5),
            "sl_price": round(self.sl_price, 5),
            "condition": self.condition,
            "reason": self.reason,
            "probability": self.probability,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class BotAnalysis:
    """
    تحلیل کامل ربات برای یک جفت ارز
    
    شامل:
    - وضعیت فعلی بازار
    - سیگنال فوری (اگر وجود داشته باشد)
    - سیگنال‌های در انتظار
    - معامله باز (اگر وجود داشته باشد)
    """
    pair: str
    timestamp: datetime
    current_price: float
    indicators: dict
    market_bias: str  # "bullish", "bearish", "neutral"
    instant_signal: Optional[Signal] = None
    pending_setups: List[PendingSetup] = field(default_factory=list)
    active_trade: Optional[Trade] = None
    
    def to_dict(self) -> dict:
        """تبدیل به دیکشنری"""
        return {
            "pair": self.pair,
            "timestamp": self.timestamp.isoformat(),
            "current_price": round(self.current_price, 5),
            "indicators": self.indicators,
            "market_bias": self.market_bias,
            "instant_signal": self.instant_signal.to_dict() if self.instant_signal else None,
            "pending_setups": [s.to_dict() for s in self.pending_setups],
            "active_trade": self.active_trade.to_dict() if self.active_trade else None
        }
