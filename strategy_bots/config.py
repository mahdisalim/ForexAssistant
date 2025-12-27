"""
Strategy Bot Configuration
تنظیمات ربات‌های استراتژی
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class RiskMode(Enum):
    """حالت محاسبه ریسک"""
    FIXED_LOT = "fixed_lot"          # لات ثابت
    PERCENT_BALANCE = "percent_balance"  # درصدی از موجودی
    FIXED_AMOUNT = "fixed_amount"    # مبلغ ثابت


class SLMode(Enum):
    """حالت تعیین Stop Loss"""
    FIXED_PIPS = "fixed_pips"        # پیپ ثابت
    ATR_BASED = "atr_based"          # بر اساس ATR
    PIN_BAR = "pin_bar"              # پشت آخرین پین بار
    SWING_POINT = "swing_point"      # پشت آخرین سوینگ


class TPMode(Enum):
    """حالت تعیین Take Profit"""
    FIXED_PIPS = "fixed_pips"        # پیپ ثابت
    RISK_REWARD = "risk_reward"      # بر اساس نسبت ریسک به ریوارد
    ATR_BASED = "atr_based"          # بر اساس ATR


@dataclass
class AccountConfig:
    """
    تنظیمات حساب کاربر
    این تنظیمات در آینده از منوی حساب کاربری پر می‌شوند
    """
    balance: float = 10000.0         # موجودی حساب
    currency: str = "USD"            # ارز حساب
    leverage: int = 100              # لوریج
    risk_percent: float = 1.0        # درصد ریسک هر معامله (1% = 1.0)
    max_daily_risk: float = 5.0      # حداکثر ریسک روزانه
    max_open_trades: int = 5         # حداکثر معاملات باز همزمان
    
    def calculate_risk_amount(self) -> float:
        """محاسبه مبلغ ریسک بر اساس درصد"""
        return self.balance * (self.risk_percent / 100)
    
    def to_dict(self) -> dict:
        return {
            "balance": self.balance,
            "currency": self.currency,
            "leverage": self.leverage,
            "risk_percent": self.risk_percent,
            "max_daily_risk": self.max_daily_risk,
            "max_open_trades": self.max_open_trades,
            "risk_amount": self.calculate_risk_amount()
        }


@dataclass
class TradeConfig:
    """
    تنظیمات معاملات
    """
    # حالت‌های محاسبه
    sl_mode: SLMode = SLMode.PIN_BAR
    tp_mode: TPMode = TPMode.RISK_REWARD
    risk_mode: RiskMode = RiskMode.PERCENT_BALANCE
    
    # مقادیر پیش‌فرض
    default_sl_pips: float = 30.0
    default_tp_pips: float = 60.0
    risk_reward_ratio: float = 2.0   # نسبت ریسک به ریوارد (1:2)
    
    # ATR settings
    atr_sl_multiplier: float = 1.5
    atr_tp_multiplier: float = 3.0
    
    # Pin Bar settings
    pin_bar_buffer_pips: float = 5.0  # فاصله اضافی از پین بار
    
    # Fixed lot (اگر risk_mode = FIXED_LOT)
    fixed_lot_size: float = 0.01
    
    # Fixed amount (اگر risk_mode = FIXED_AMOUNT)
    fixed_risk_amount: float = 100.0
    
    def to_dict(self) -> dict:
        return {
            "sl_mode": self.sl_mode.value,
            "tp_mode": self.tp_mode.value,
            "risk_mode": self.risk_mode.value,
            "default_sl_pips": self.default_sl_pips,
            "default_tp_pips": self.default_tp_pips,
            "risk_reward_ratio": self.risk_reward_ratio,
            "atr_sl_multiplier": self.atr_sl_multiplier,
            "atr_tp_multiplier": self.atr_tp_multiplier,
            "pin_bar_buffer_pips": self.pin_bar_buffer_pips,
            "fixed_lot_size": self.fixed_lot_size,
            "fixed_risk_amount": self.fixed_risk_amount
        }


@dataclass
class BotConfig:
    """
    تنظیمات کلی ربات
    """
    account: AccountConfig = field(default_factory=AccountConfig)
    trade: TradeConfig = field(default_factory=TradeConfig)
    
    # تنظیمات عمومی
    enabled: bool = True
    paper_trading: bool = True       # معاملات آزمایشی (بدون پول واقعی)
    auto_trade: bool = False         # معامله خودکار
    send_notifications: bool = True  # ارسال نوتیفیکیشن
    
    def to_dict(self) -> dict:
        return {
            "account": self.account.to_dict(),
            "trade": self.trade.to_dict(),
            "enabled": self.enabled,
            "paper_trading": self.paper_trading,
            "auto_trade": self.auto_trade,
            "send_notifications": self.send_notifications
        }


# تنظیمات پیش‌فرض
DEFAULT_CONFIG = BotConfig()
