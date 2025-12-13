"""
Stop Loss and Take Profit Strategies Module
Provides various methods for calculating SL/TP levels.

Available Strategies:
- ATR-based: Uses Average True Range for dynamic SL/TP
- Fixed R/R: Fixed Risk/Reward ratio
- Swing Points: Uses recent swing highs/lows
- Fixed Pips: Fixed pip distance
- Percentage: Percentage of price
- Support/Resistance: Based on S/R levels
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import numpy as np


class SLStrategy(str, Enum):
    """Stop Loss calculation strategies"""
    ATR = "atr"
    FIXED_PIPS = "fixed_pips"
    SWING = "swing"
    PERCENTAGE = "percentage"
    SUPPORT_RESISTANCE = "support_resistance"


class TPStrategy(str, Enum):
    """Take Profit calculation strategies"""
    RISK_REWARD = "risk_reward"
    ATR = "atr"
    FIXED_PIPS = "fixed_pips"
    SWING = "swing"
    PERCENTAGE = "percentage"
    SUPPORT_RESISTANCE = "support_resistance"
    TRAILING = "trailing"


@dataclass
class SLTPResult:
    """Result of SL/TP calculation"""
    stop_loss: float
    take_profit: float
    sl_pips: float
    tp_pips: float
    risk_reward_ratio: float
    strategy_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "sl_pips": self.sl_pips,
            "tp_pips": self.tp_pips,
            "risk_reward_ratio": self.risk_reward_ratio,
            "strategy_used": self.strategy_used
        }


class BaseSLStrategy(ABC):
    """Base class for Stop Loss strategies"""
    
    @abstractmethod
    def calculate(self, entry_price: float, is_buy: bool, data: Dict[str, Any]) -> float:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Entry price of the trade
            is_buy: True for buy orders, False for sell
            data: Additional data (OHLC, indicators, etc.)
            
        Returns:
            Stop loss price
        """
        pass


class BaseTPStrategy(ABC):
    """Base class for Take Profit strategies"""
    
    @abstractmethod
    def calculate(self, entry_price: float, stop_loss: float, is_buy: bool, data: Dict[str, Any]) -> float:
        """
        Calculate take profit price.
        
        Args:
            entry_price: Entry price of the trade
            stop_loss: Stop loss price
            is_buy: True for buy orders, False for sell
            data: Additional data (OHLC, indicators, etc.)
            
        Returns:
            Take profit price
        """
        pass


# ============== Stop Loss Strategies ==============

class ATRStopLoss(BaseSLStrategy):
    """ATR-based stop loss calculation"""
    
    def __init__(self, multiplier: float = 2.0, period: int = 14):
        self.multiplier = multiplier
        self.period = period
    
    def calculate(self, entry_price: float, is_buy: bool, data: Dict[str, Any]) -> float:
        atr = data.get("atr", 0)
        if atr == 0:
            # Calculate ATR if not provided
            high = np.array(data.get("high", []))
            low = np.array(data.get("low", []))
            close = np.array(data.get("close", []))
            if len(high) >= self.period:
                atr = self._calculate_atr(high, low, close, self.period)
        
        sl_distance = atr * self.multiplier
        
        if is_buy:
            return entry_price - sl_distance
        else:
            return entry_price + sl_distance
    
    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> float:
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = np.mean(tr[-period:])
        return atr


class FixedPipsStopLoss(BaseSLStrategy):
    """Fixed pips stop loss"""
    
    def __init__(self, pips: float = 50):
        self.pips = pips
    
    def calculate(self, entry_price: float, is_buy: bool, data: Dict[str, Any]) -> float:
        pip_value = data.get("pip_value", 0.0001)
        sl_distance = self.pips * pip_value
        
        if is_buy:
            return entry_price - sl_distance
        else:
            return entry_price + sl_distance


class SwingStopLoss(BaseSLStrategy):
    """Swing high/low based stop loss"""
    
    def __init__(self, lookback: int = 20, buffer_pips: float = 5):
        self.lookback = lookback
        self.buffer_pips = buffer_pips
    
    def calculate(self, entry_price: float, is_buy: bool, data: Dict[str, Any]) -> float:
        high = np.array(data.get("high", []))
        low = np.array(data.get("low", []))
        pip_value = data.get("pip_value", 0.0001)
        buffer = self.buffer_pips * pip_value
        
        if len(high) < self.lookback:
            # Fallback to fixed pips if not enough data
            return entry_price - (50 * pip_value) if is_buy else entry_price + (50 * pip_value)
        
        if is_buy:
            # For buy, SL below recent swing low
            swing_low = np.min(low[-self.lookback:])
            return swing_low - buffer
        else:
            # For sell, SL above recent swing high
            swing_high = np.max(high[-self.lookback:])
            return swing_high + buffer


class PercentageStopLoss(BaseSLStrategy):
    """Percentage-based stop loss"""
    
    def __init__(self, percentage: float = 1.0):
        self.percentage = percentage / 100
    
    def calculate(self, entry_price: float, is_buy: bool, data: Dict[str, Any]) -> float:
        sl_distance = entry_price * self.percentage
        
        if is_buy:
            return entry_price - sl_distance
        else:
            return entry_price + sl_distance


class SupportResistanceStopLoss(BaseSLStrategy):
    """Support/Resistance based stop loss"""
    
    def __init__(self, buffer_pips: float = 10):
        self.buffer_pips = buffer_pips
    
    def calculate(self, entry_price: float, is_buy: bool, data: Dict[str, Any]) -> float:
        pip_value = data.get("pip_value", 0.0001)
        buffer = self.buffer_pips * pip_value
        
        support_levels = data.get("support_levels", [])
        resistance_levels = data.get("resistance_levels", [])
        
        if is_buy:
            # Find nearest support below entry
            valid_supports = [s for s in support_levels if s < entry_price]
            if valid_supports:
                return max(valid_supports) - buffer
            # Fallback
            return entry_price - (50 * pip_value)
        else:
            # Find nearest resistance above entry
            valid_resistances = [r for r in resistance_levels if r > entry_price]
            if valid_resistances:
                return min(valid_resistances) + buffer
            # Fallback
            return entry_price + (50 * pip_value)


# ============== Take Profit Strategies ==============

class RiskRewardTakeProfit(BaseTPStrategy):
    """Fixed Risk/Reward ratio take profit"""
    
    def __init__(self, ratio: float = 2.0):
        self.ratio = ratio
    
    def calculate(self, entry_price: float, stop_loss: float, is_buy: bool, data: Dict[str, Any]) -> float:
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * self.ratio
        
        if is_buy:
            return entry_price + tp_distance
        else:
            return entry_price - tp_distance


class ATRTakeProfit(BaseTPStrategy):
    """ATR-based take profit"""
    
    def __init__(self, multiplier: float = 3.0, period: int = 14):
        self.multiplier = multiplier
        self.period = period
    
    def calculate(self, entry_price: float, stop_loss: float, is_buy: bool, data: Dict[str, Any]) -> float:
        atr = data.get("atr", 0)
        if atr == 0:
            high = np.array(data.get("high", []))
            low = np.array(data.get("low", []))
            close = np.array(data.get("close", []))
            if len(high) >= self.period:
                tr1 = high - low
                tr2 = np.abs(high - np.roll(close, 1))
                tr3 = np.abs(low - np.roll(close, 1))
                tr = np.maximum(tr1, np.maximum(tr2, tr3))
                atr = np.mean(tr[-self.period:])
        
        tp_distance = atr * self.multiplier
        
        if is_buy:
            return entry_price + tp_distance
        else:
            return entry_price - tp_distance


class FixedPipsTakeProfit(BaseTPStrategy):
    """Fixed pips take profit"""
    
    def __init__(self, pips: float = 100):
        self.pips = pips
    
    def calculate(self, entry_price: float, stop_loss: float, is_buy: bool, data: Dict[str, Any]) -> float:
        pip_value = data.get("pip_value", 0.0001)
        tp_distance = self.pips * pip_value
        
        if is_buy:
            return entry_price + tp_distance
        else:
            return entry_price - tp_distance


class SwingTakeProfit(BaseTPStrategy):
    """Swing high/low based take profit"""
    
    def __init__(self, lookback: int = 50):
        self.lookback = lookback
    
    def calculate(self, entry_price: float, stop_loss: float, is_buy: bool, data: Dict[str, Any]) -> float:
        high = np.array(data.get("high", []))
        low = np.array(data.get("low", []))
        pip_value = data.get("pip_value", 0.0001)
        
        if len(high) < self.lookback:
            # Fallback to R/R
            sl_distance = abs(entry_price - stop_loss)
            return entry_price + (sl_distance * 2) if is_buy else entry_price - (sl_distance * 2)
        
        if is_buy:
            # For buy, TP at recent swing high
            return np.max(high[-self.lookback:])
        else:
            # For sell, TP at recent swing low
            return np.min(low[-self.lookback:])


class PercentageTakeProfit(BaseTPStrategy):
    """Percentage-based take profit"""
    
    def __init__(self, percentage: float = 2.0):
        self.percentage = percentage / 100
    
    def calculate(self, entry_price: float, stop_loss: float, is_buy: bool, data: Dict[str, Any]) -> float:
        tp_distance = entry_price * self.percentage
        
        if is_buy:
            return entry_price + tp_distance
        else:
            return entry_price - tp_distance


class SupportResistanceTakeProfit(BaseTPStrategy):
    """Support/Resistance based take profit"""
    
    def calculate(self, entry_price: float, stop_loss: float, is_buy: bool, data: Dict[str, Any]) -> float:
        pip_value = data.get("pip_value", 0.0001)
        
        support_levels = data.get("support_levels", [])
        resistance_levels = data.get("resistance_levels", [])
        
        if is_buy:
            # Find nearest resistance above entry
            valid_resistances = [r for r in resistance_levels if r > entry_price]
            if valid_resistances:
                return min(valid_resistances)
            # Fallback to R/R
            sl_distance = abs(entry_price - stop_loss)
            return entry_price + (sl_distance * 2)
        else:
            # Find nearest support below entry
            valid_supports = [s for s in support_levels if s < entry_price]
            if valid_supports:
                return max(valid_supports)
            # Fallback
            sl_distance = abs(entry_price - stop_loss)
            return entry_price - (sl_distance * 2)


# ============== Strategy Factory ==============

class SLTPStrategyFactory:
    """Factory for creating SL/TP strategy instances"""
    
    SL_STRATEGIES = {
        SLStrategy.ATR: ATRStopLoss,
        SLStrategy.FIXED_PIPS: FixedPipsStopLoss,
        SLStrategy.SWING: SwingStopLoss,
        SLStrategy.PERCENTAGE: PercentageStopLoss,
        SLStrategy.SUPPORT_RESISTANCE: SupportResistanceStopLoss,
    }
    
    TP_STRATEGIES = {
        TPStrategy.RISK_REWARD: RiskRewardTakeProfit,
        TPStrategy.ATR: ATRTakeProfit,
        TPStrategy.FIXED_PIPS: FixedPipsTakeProfit,
        TPStrategy.SWING: SwingTakeProfit,
        TPStrategy.PERCENTAGE: PercentageTakeProfit,
        TPStrategy.SUPPORT_RESISTANCE: SupportResistanceTakeProfit,
    }
    
    @classmethod
    def create_sl_strategy(cls, strategy: SLStrategy, **kwargs) -> BaseSLStrategy:
        """Create a stop loss strategy instance"""
        strategy_class = cls.SL_STRATEGIES.get(strategy)
        if not strategy_class:
            raise ValueError(f"Unknown SL strategy: {strategy}")
        return strategy_class(**kwargs)
    
    @classmethod
    def create_tp_strategy(cls, strategy: TPStrategy, **kwargs) -> BaseTPStrategy:
        """Create a take profit strategy instance"""
        strategy_class = cls.TP_STRATEGIES.get(strategy)
        if not strategy_class:
            raise ValueError(f"Unknown TP strategy: {strategy}")
        return strategy_class(**kwargs)
    
    @classmethod
    def get_available_sl_strategies(cls) -> List[Dict[str, Any]]:
        """Get list of available SL strategies with descriptions"""
        return [
            {"id": "atr", "name": "ATR-Based", "description": "Dynamic SL based on market volatility", "premium": False},
            {"id": "fixed_pips", "name": "Fixed Pips", "description": "Fixed pip distance from entry", "premium": False},
            {"id": "swing", "name": "Swing Points", "description": "Based on recent swing highs/lows", "premium": True},
            {"id": "percentage", "name": "Percentage", "description": "Percentage of entry price", "premium": True},
            {"id": "support_resistance", "name": "Support/Resistance", "description": "Based on S/R levels", "premium": True},
        ]
    
    @classmethod
    def get_available_tp_strategies(cls) -> List[Dict[str, Any]]:
        """Get list of available TP strategies with descriptions"""
        return [
            {"id": "risk_reward", "name": "Risk/Reward Ratio", "description": "Fixed R/R ratio (e.g., 1:2)", "premium": False},
            {"id": "atr", "name": "ATR-Based", "description": "Dynamic TP based on volatility", "premium": True},
            {"id": "fixed_pips", "name": "Fixed Pips", "description": "Fixed pip distance from entry", "premium": False},
            {"id": "swing", "name": "Swing Points", "description": "Target recent swing highs/lows", "premium": True},
            {"id": "percentage", "name": "Percentage", "description": "Percentage of entry price", "premium": True},
            {"id": "support_resistance", "name": "Support/Resistance", "description": "Target S/R levels", "premium": True},
        ]


# ============== SL/TP Manager ==============

class SLTPManager:
    """
    Manager for calculating SL/TP using selected strategies.
    Handles both free and premium users.
    """
    
    # Default strategies for free users
    DEFAULT_SL_STRATEGY = SLStrategy.ATR
    DEFAULT_TP_STRATEGY = TPStrategy.RISK_REWARD
    
    # Default parameters
    DEFAULT_SL_PARAMS = {"multiplier": 2.0, "period": 14}
    DEFAULT_TP_PARAMS = {"ratio": 2.0}
    
    def __init__(self, is_premium: bool = False):
        self.is_premium = is_premium
        self._sl_strategy: Optional[BaseSLStrategy] = None
        self._tp_strategy: Optional[BaseTPStrategy] = None
    
    def set_sl_strategy(self, strategy: SLStrategy, **kwargs) -> bool:
        """
        Set stop loss strategy.
        Non-premium users can only use default strategies.
        """
        # Check if strategy requires premium
        strategy_info = next(
            (s for s in SLTPStrategyFactory.get_available_sl_strategies() if s["id"] == strategy.value),
            None
        )
        
        if strategy_info and strategy_info.get("premium") and not self.is_premium:
            # Use default for non-premium
            self._sl_strategy = SLTPStrategyFactory.create_sl_strategy(
                self.DEFAULT_SL_STRATEGY, **self.DEFAULT_SL_PARAMS
            )
            return False
        
        self._sl_strategy = SLTPStrategyFactory.create_sl_strategy(strategy, **kwargs)
        return True
    
    def set_tp_strategy(self, strategy: TPStrategy, **kwargs) -> bool:
        """
        Set take profit strategy.
        Non-premium users can only use default strategies.
        """
        strategy_info = next(
            (s for s in SLTPStrategyFactory.get_available_tp_strategies() if s["id"] == strategy.value),
            None
        )
        
        if strategy_info and strategy_info.get("premium") and not self.is_premium:
            self._tp_strategy = SLTPStrategyFactory.create_tp_strategy(
                self.DEFAULT_TP_STRATEGY, **self.DEFAULT_TP_PARAMS
            )
            return False
        
        self._tp_strategy = SLTPStrategyFactory.create_tp_strategy(strategy, **kwargs)
        return True
    
    def calculate(self, entry_price: float, is_buy: bool, data: Dict[str, Any]) -> SLTPResult:
        """
        Calculate SL/TP levels using configured strategies.
        """
        # Ensure strategies are set
        if self._sl_strategy is None:
            self._sl_strategy = SLTPStrategyFactory.create_sl_strategy(
                self.DEFAULT_SL_STRATEGY, **self.DEFAULT_SL_PARAMS
            )
        if self._tp_strategy is None:
            self._tp_strategy = SLTPStrategyFactory.create_tp_strategy(
                self.DEFAULT_TP_STRATEGY, **self.DEFAULT_TP_PARAMS
            )
        
        # Calculate SL
        stop_loss = self._sl_strategy.calculate(entry_price, is_buy, data)
        
        # Calculate TP
        take_profit = self._tp_strategy.calculate(entry_price, stop_loss, is_buy, data)
        
        # Calculate pips
        pip_value = data.get("pip_value", 0.0001)
        sl_pips = abs(entry_price - stop_loss) / pip_value
        tp_pips = abs(entry_price - take_profit) / pip_value
        
        # Calculate R/R
        risk_reward = tp_pips / sl_pips if sl_pips > 0 else 0
        
        return SLTPResult(
            stop_loss=round(stop_loss, 5),
            take_profit=round(take_profit, 5),
            sl_pips=round(sl_pips, 1),
            tp_pips=round(tp_pips, 1),
            risk_reward_ratio=round(risk_reward, 2),
            strategy_used=f"SL: {type(self._sl_strategy).__name__}, TP: {type(self._tp_strategy).__name__}"
        )
