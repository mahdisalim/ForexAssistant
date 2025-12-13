"""
Base Trading Robot Module
Provides the foundation for all trading robots with modular SL/TP strategies.

Features:
- Support for all timeframes
- Modular SL/TP strategy selection
- Premium vs Free user handling
- Signal generation interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
import logging

from .sl_tp_strategies import (
    SLTPManager, SLTPResult, SLStrategy, TPStrategy,
    SLTPStrategyFactory
)

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"


class Timeframe(str, Enum):
    """Available timeframes"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN1 = "1M"


@dataclass
class TradeSignal:
    """Trading signal with all necessary information"""
    signal_type: SignalType
    symbol: str
    timeframe: str
    entry_price: float
    stop_loss: float
    take_profit: float
    sl_pips: float
    tp_pips: float
    risk_reward: float
    confidence: float  # 0-100
    robot_name: str
    timestamp: str
    indicators: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type.value,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "sl_pips": self.sl_pips,
            "tp_pips": self.tp_pips,
            "risk_reward": self.risk_reward,
            "confidence": self.confidence,
            "robot_name": self.robot_name,
            "timestamp": self.timestamp,
            "indicators": self.indicators,
            "reason": self.reason
        }


@dataclass
class RobotConfig:
    """Configuration for a trading robot"""
    # Basic settings
    symbol: str = "EURUSD"
    timeframe: Timeframe = Timeframe.H1
    
    # SL/TP settings
    sl_strategy: SLStrategy = SLStrategy.ATR
    tp_strategy: TPStrategy = TPStrategy.RISK_REWARD
    sl_params: Dict[str, Any] = field(default_factory=lambda: {"multiplier": 2.0, "period": 14})
    tp_params: Dict[str, Any] = field(default_factory=lambda: {"ratio": 2.0})
    
    # Risk settings
    risk_percent: float = 1.0
    max_trades: int = 3
    
    # Premium features
    is_premium: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe.value if isinstance(self.timeframe, Timeframe) else self.timeframe,
            "sl_strategy": self.sl_strategy.value if isinstance(self.sl_strategy, SLStrategy) else self.sl_strategy,
            "tp_strategy": self.tp_strategy.value if isinstance(self.tp_strategy, TPStrategy) else self.tp_strategy,
            "sl_params": self.sl_params,
            "tp_params": self.tp_params,
            "risk_percent": self.risk_percent,
            "max_trades": self.max_trades,
            "is_premium": self.is_premium
        }


class BaseRobot(ABC):
    """
    Abstract base class for all trading robots.
    
    All robots must implement:
    - calculate_indicators(): Calculate required indicators
    - generate_signal(): Generate trading signal based on strategy
    
    Built-in features:
    - Modular SL/TP calculation
    - Multi-timeframe support
    - Premium/Free user handling
    """
    
    # Robot metadata - override in subclasses
    ROBOT_NAME = "BaseRobot"
    ROBOT_DESCRIPTION = "Base trading robot"
    ROBOT_VERSION = "1.0.0"
    
    # Default SL/TP for this robot (can be overridden)
    DEFAULT_SL_STRATEGY = SLStrategy.ATR
    DEFAULT_TP_STRATEGY = TPStrategy.RISK_REWARD
    DEFAULT_SL_PARAMS = {"multiplier": 2.0, "period": 14}
    DEFAULT_TP_PARAMS = {"ratio": 2.0}
    
    def __init__(self, config: Optional[RobotConfig] = None):
        self.config = config or RobotConfig()
        self._sltp_manager = SLTPManager(is_premium=self.config.is_premium)
        self._setup_sltp_strategies()
        self._indicators: Dict[str, Any] = {}
    
    def _setup_sltp_strategies(self):
        """Setup SL/TP strategies based on config"""
        # Use config strategies or defaults
        sl_strategy = self.config.sl_strategy or self.DEFAULT_SL_STRATEGY
        tp_strategy = self.config.tp_strategy or self.DEFAULT_TP_STRATEGY
        sl_params = self.config.sl_params or self.DEFAULT_SL_PARAMS
        tp_params = self.config.tp_params or self.DEFAULT_TP_PARAMS
        
        # Set strategies (will fallback to defaults for non-premium if needed)
        self._sltp_manager.set_sl_strategy(sl_strategy, **sl_params)
        self._sltp_manager.set_tp_strategy(tp_strategy, **tp_params)
    
    def update_config(self, **kwargs):
        """Update robot configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self._setup_sltp_strategies()
    
    def set_premium(self, is_premium: bool):
        """Update premium status"""
        self.config.is_premium = is_premium
        self._sltp_manager = SLTPManager(is_premium=is_premium)
        self._setup_sltp_strategies()
    
    @abstractmethod
    def calculate_indicators(self, data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Calculate indicators required for this robot.
        
        Args:
            data: OHLCV data with keys: open, high, low, close, volume
            
        Returns:
            Dictionary of calculated indicators
        """
        pass
    
    @abstractmethod
    def check_entry_conditions(self, indicators: Dict[str, Any]) -> Tuple[SignalType, float, str]:
        """
        Check if entry conditions are met.
        
        Args:
            indicators: Calculated indicators
            
        Returns:
            Tuple of (signal_type, confidence, reason)
        """
        pass
    
    def generate_signal(self, data: Dict[str, np.ndarray]) -> Optional[TradeSignal]:
        """
        Generate trading signal based on current market data.
        
        Args:
            data: OHLCV data with keys: open, high, low, close, volume
            
        Returns:
            TradeSignal if conditions are met, None otherwise
        """
        # Calculate indicators
        self._indicators = self.calculate_indicators(data)
        
        # Check entry conditions
        signal_type, confidence, reason = self.check_entry_conditions(self._indicators)
        
        if signal_type == SignalType.NEUTRAL:
            return None
        
        # Get current price
        close = data.get("close", [])
        if len(close) == 0:
            return None
        
        entry_price = float(close[-1])
        is_buy = signal_type == SignalType.BUY
        
        # Prepare data for SL/TP calculation
        sltp_data = {
            "high": data.get("high", []),
            "low": data.get("low", []),
            "close": data.get("close", []),
            "atr": self._indicators.get("atr", 0),
            "pip_value": self._get_pip_value(self.config.symbol),
            "support_levels": self._indicators.get("support_levels", []),
            "resistance_levels": self._indicators.get("resistance_levels", [])
        }
        
        # Calculate SL/TP
        sltp_result = self._sltp_manager.calculate(entry_price, is_buy, sltp_data)
        
        return TradeSignal(
            signal_type=signal_type,
            symbol=self.config.symbol,
            timeframe=self.config.timeframe.value if isinstance(self.config.timeframe, Timeframe) else self.config.timeframe,
            entry_price=entry_price,
            stop_loss=sltp_result.stop_loss,
            take_profit=sltp_result.take_profit,
            sl_pips=sltp_result.sl_pips,
            tp_pips=sltp_result.tp_pips,
            risk_reward=sltp_result.risk_reward_ratio,
            confidence=confidence,
            robot_name=self.ROBOT_NAME,
            timestamp=datetime.utcnow().isoformat(),
            indicators=self._indicators,
            reason=reason
        )
    
    def _get_pip_value(self, symbol: str) -> float:
        """Get pip value for a symbol"""
        # JPY pairs have different pip value
        if "JPY" in symbol.upper():
            return 0.01
        return 0.0001
    
    def get_info(self) -> Dict[str, Any]:
        """Get robot information"""
        return {
            "name": self.ROBOT_NAME,
            "description": self.ROBOT_DESCRIPTION,
            "version": self.ROBOT_VERSION,
            "config": self.config.to_dict(),
            "available_sl_strategies": SLTPStrategyFactory.get_available_sl_strategies(),
            "available_tp_strategies": SLTPStrategyFactory.get_available_tp_strategies()
        }
    
    @classmethod
    def get_default_config(cls) -> RobotConfig:
        """Get default configuration for this robot"""
        return RobotConfig(
            sl_strategy=cls.DEFAULT_SL_STRATEGY,
            tp_strategy=cls.DEFAULT_TP_STRATEGY,
            sl_params=cls.DEFAULT_SL_PARAMS.copy(),
            tp_params=cls.DEFAULT_TP_PARAMS.copy()
        )


# ============== Indicator Helpers ==============

class IndicatorCalculator:
    """Helper class for calculating common indicators"""
    
    @staticmethod
    def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(high) < period + 1:
            return 0.0
        
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        
        atr = np.mean(tr[-period:])
        return float(atr)
    
    @staticmethod
    def calculate_rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index"""
        if len(close) < period + 1:
            return np.array([50.0])
        
        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = np.zeros_like(gain)
        avg_loss = np.zeros_like(loss)
        
        avg_gain[period-1] = np.mean(gain[:period])
        avg_loss[period-1] = np.mean(loss[:period])
        
        for i in range(period, len(gain)):
            avg_gain[i] = (avg_gain[i-1] * (period-1) + gain[i]) / period
            avg_loss[i] = (avg_loss[i-1] * (period-1) + loss[i]) / period
        
        rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray, 
                            k_period: int = 14, d_period: int = 3, smooth: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate Stochastic Oscillator (%K and %D)"""
        if len(close) < k_period:
            return np.array([50.0]), np.array([50.0])
        
        # Calculate %K
        stoch_k = np.zeros(len(close))
        for i in range(k_period - 1, len(close)):
            highest_high = np.max(high[i - k_period + 1:i + 1])
            lowest_low = np.min(low[i - k_period + 1:i + 1])
            
            if highest_high != lowest_low:
                stoch_k[i] = ((close[i] - lowest_low) / (highest_high - lowest_low)) * 100
            else:
                stoch_k[i] = 50
        
        # Smooth %K
        if smooth > 1:
            smoothed_k = np.convolve(stoch_k, np.ones(smooth)/smooth, mode='valid')
            stoch_k[-len(smoothed_k):] = smoothed_k
        
        # Calculate %D (SMA of %K)
        stoch_d = np.convolve(stoch_k, np.ones(d_period)/d_period, mode='valid')
        
        # Pad to match length
        full_d = np.zeros(len(close))
        full_d[-len(stoch_d):] = stoch_d
        
        return stoch_k, full_d
    
    @staticmethod
    def calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return data
        
        multiplier = 2 / (period + 1)
        ema = np.zeros(len(data))
        ema[period-1] = np.mean(data[:period])
        
        for i in range(period, len(data)):
            ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    @staticmethod
    def calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        if len(data) < period:
            return data
        
        return np.convolve(data, np.ones(period)/period, mode='valid')
    
    @staticmethod
    def calculate_bollinger_bands(close: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate Bollinger Bands"""
        if len(close) < period:
            return close, close, close
        
        sma = np.convolve(close, np.ones(period)/period, mode='valid')
        
        # Calculate rolling std
        std = np.zeros(len(sma))
        for i in range(len(sma)):
            std[i] = np.std(close[i:i+period])
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, sma, lower
    
    @staticmethod
    def calculate_macd(close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate MACD"""
        if len(close) < slow:
            return np.zeros(len(close)), np.zeros(len(close)), np.zeros(len(close))
        
        ema_fast = IndicatorCalculator.calculate_ema(close, fast)
        ema_slow = IndicatorCalculator.calculate_ema(close, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = IndicatorCalculator.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
