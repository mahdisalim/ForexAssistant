"""
Candlestick Pattern Detection
تشخیص الگوهای کندلی

NOTE: این فایل برای backward compatibility نگه داشته شده.
برای استفاده جدید از ماژول sl_strategies استفاده کنید:

    from strategy_bots.sl_strategies import PinBarSL, PinBar, CompositeSL
"""

# Re-export from new module for backward compatibility
from .sl_strategies import PinBarSL, PinBar, ATRSL, SwingPointSL, CompositeSL
from .sl_strategies.base import TradeDirection, SLResult


# Legacy function wrappers
def calculate_tp_from_rr(entry_price: float, sl_price: float,
                         risk_reward_ratio: float = 2.0) -> float:
    """محاسبه Take Profit بر اساس نسبت ریسک به ریوارد"""
    risk = abs(entry_price - sl_price)
    reward = risk * risk_reward_ratio
    if entry_price > sl_price:
        return entry_price + reward
    return entry_price - reward


def calculate_lot_size(account_balance: float, risk_percent: float,
                       sl_pips: float, pip_value_per_lot: float = 10.0) -> float:
    """محاسبه حجم معامله بر اساس ریسک"""
    if sl_pips <= 0:
        return 0.01
    risk_amount = account_balance * (risk_percent / 100)
    lot_size = risk_amount / (sl_pips * pip_value_per_lot)
    return max(0.01, min(round(lot_size, 2), 100.0))
