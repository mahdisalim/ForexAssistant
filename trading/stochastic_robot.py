"""
Stochastic Trading Robot
Uses Stochastic Oscillator for generating trading signals.

Default Settings:
- SL: ATR-based (2x ATR)
- TP: Risk/Reward ratio (1:2)

Signals:
- BUY: %K crosses above %D in oversold zone (<20)
- SELL: %K crosses below %D in overbought zone (>80)
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np

from .base_robot import (
    BaseRobot, RobotConfig, TradeSignal, SignalType, Timeframe,
    IndicatorCalculator
)
from .sl_tp_strategies import SLStrategy, TPStrategy


class StochasticRobot(BaseRobot):
    """
    Stochastic Oscillator Trading Robot
    
    Uses classic Stochastic signals:
    - Oversold/Overbought zones
    - %K and %D crossovers
    - Divergence detection (premium)
    """
    
    ROBOT_NAME = "Stochastic Robot"
    ROBOT_DESCRIPTION = "Trading robot based on Stochastic Oscillator crossovers"
    ROBOT_VERSION = "1.0.0"
    
    # Default SL/TP strategies for Stochastic
    DEFAULT_SL_STRATEGY = SLStrategy.ATR
    DEFAULT_TP_STRATEGY = TPStrategy.RISK_REWARD
    DEFAULT_SL_PARAMS = {"multiplier": 2.0, "period": 14}
    DEFAULT_TP_PARAMS = {"ratio": 2.0}
    
    # Stochastic parameters
    DEFAULT_K_PERIOD = 14
    DEFAULT_D_PERIOD = 3
    DEFAULT_SMOOTH = 3
    DEFAULT_OVERSOLD = 20
    DEFAULT_OVERBOUGHT = 80
    
    def __init__(self, config: Optional[RobotConfig] = None,
                 k_period: int = None,
                 d_period: int = None,
                 smooth: int = None,
                 oversold: float = None,
                 overbought: float = None):
        super().__init__(config)
        
        # Stochastic settings
        self.k_period = k_period or self.DEFAULT_K_PERIOD
        self.d_period = d_period or self.DEFAULT_D_PERIOD
        self.smooth = smooth or self.DEFAULT_SMOOTH
        self.oversold = oversold or self.DEFAULT_OVERSOLD
        self.overbought = overbought or self.DEFAULT_OVERBOUGHT
    
    def calculate_indicators(self, data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Calculate Stochastic and supporting indicators"""
        high = np.array(data.get("high", []))
        low = np.array(data.get("low", []))
        close = np.array(data.get("close", []))
        
        if len(close) < self.k_period + self.d_period:
            return {"error": "Not enough data"}
        
        # Calculate Stochastic
        stoch_k, stoch_d = IndicatorCalculator.calculate_stochastic(
            high, low, close,
            k_period=self.k_period,
            d_period=self.d_period,
            smooth=self.smooth
        )
        
        # Calculate ATR for SL/TP
        atr = IndicatorCalculator.calculate_atr(high, low, close, period=14)
        
        # Get current and previous values
        current_k = float(stoch_k[-1]) if len(stoch_k) > 0 else 50
        current_d = float(stoch_d[-1]) if len(stoch_d) > 0 else 50
        prev_k = float(stoch_k[-2]) if len(stoch_k) > 1 else 50
        prev_d = float(stoch_d[-2]) if len(stoch_d) > 1 else 50
        
        # Detect crossovers
        bullish_cross = prev_k <= prev_d and current_k > current_d
        bearish_cross = prev_k >= prev_d and current_k < current_d
        
        # Zone detection
        in_oversold = current_k < self.oversold
        in_overbought = current_k > self.overbought
        
        return {
            "stoch_k": current_k,
            "stoch_d": current_d,
            "prev_k": prev_k,
            "prev_d": prev_d,
            "bullish_cross": bullish_cross,
            "bearish_cross": bearish_cross,
            "in_oversold": in_oversold,
            "in_overbought": in_overbought,
            "atr": atr,
            "stoch_k_array": stoch_k,
            "stoch_d_array": stoch_d
        }
    
    def check_entry_conditions(self, indicators: Dict[str, Any]) -> Tuple[SignalType, float, str]:
        """Check Stochastic entry conditions"""
        
        if "error" in indicators:
            return SignalType.NEUTRAL, 0, indicators["error"]
        
        stoch_k = indicators.get("stoch_k", 50)
        stoch_d = indicators.get("stoch_d", 50)
        bullish_cross = indicators.get("bullish_cross", False)
        bearish_cross = indicators.get("bearish_cross", False)
        in_oversold = indicators.get("in_oversold", False)
        in_overbought = indicators.get("in_overbought", False)
        
        # BUY Signal: Bullish crossover in oversold zone
        if bullish_cross and in_oversold:
            confidence = self._calculate_confidence(stoch_k, is_buy=True)
            reason = f"Bullish crossover in oversold zone (K={stoch_k:.1f}, D={stoch_d:.1f})"
            return SignalType.BUY, confidence, reason
        
        # SELL Signal: Bearish crossover in overbought zone
        if bearish_cross and in_overbought:
            confidence = self._calculate_confidence(stoch_k, is_buy=False)
            reason = f"Bearish crossover in overbought zone (K={stoch_k:.1f}, D={stoch_d:.1f})"
            return SignalType.SELL, confidence, reason
        
        # Alternative: Strong oversold/overbought without crossover
        if stoch_k < 10 and stoch_d < 15:
            confidence = 60
            reason = f"Extreme oversold (K={stoch_k:.1f}, D={stoch_d:.1f})"
            return SignalType.BUY, confidence, reason
        
        if stoch_k > 90 and stoch_d > 85:
            confidence = 60
            reason = f"Extreme overbought (K={stoch_k:.1f}, D={stoch_d:.1f})"
            return SignalType.SELL, confidence, reason
        
        return SignalType.NEUTRAL, 0, "No signal"
    
    def _calculate_confidence(self, stoch_k: float, is_buy: bool) -> float:
        """Calculate signal confidence based on Stochastic level"""
        if is_buy:
            # Lower K = higher confidence for buy
            if stoch_k < 10:
                return 90
            elif stoch_k < 15:
                return 80
            elif stoch_k < 20:
                return 70
            else:
                return 60
        else:
            # Higher K = higher confidence for sell
            if stoch_k > 90:
                return 90
            elif stoch_k > 85:
                return 80
            elif stoch_k > 80:
                return 70
            else:
                return 60
    
    def get_stochastic_settings(self) -> Dict[str, Any]:
        """Get current Stochastic settings"""
        return {
            "k_period": self.k_period,
            "d_period": self.d_period,
            "smooth": self.smooth,
            "oversold": self.oversold,
            "overbought": self.overbought
        }
    
    def update_stochastic_settings(self, **kwargs):
        """Update Stochastic parameters"""
        if "k_period" in kwargs:
            self.k_period = kwargs["k_period"]
        if "d_period" in kwargs:
            self.d_period = kwargs["d_period"]
        if "smooth" in kwargs:
            self.smooth = kwargs["smooth"]
        if "oversold" in kwargs:
            self.oversold = kwargs["oversold"]
        if "overbought" in kwargs:
            self.overbought = kwargs["overbought"]


class StochasticDivergenceRobot(StochasticRobot):
    """
    Advanced Stochastic Robot with Divergence Detection (Premium)
    
    Additional signals:
    - Bullish divergence: Price makes lower low, Stochastic makes higher low
    - Bearish divergence: Price makes higher high, Stochastic makes lower high
    """
    
    ROBOT_NAME = "Stochastic Divergence Robot"
    ROBOT_DESCRIPTION = "Advanced Stochastic with divergence detection (Premium)"
    ROBOT_VERSION = "1.0.0"
    
    def __init__(self, config: Optional[RobotConfig] = None, **kwargs):
        # Force premium for this robot
        if config:
            config.is_premium = True
        else:
            config = RobotConfig(is_premium=True)
        
        super().__init__(config, **kwargs)
        self.divergence_lookback = kwargs.get("divergence_lookback", 10)
    
    def calculate_indicators(self, data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Calculate indicators including divergence detection"""
        indicators = super().calculate_indicators(data)
        
        if "error" in indicators:
            return indicators
        
        close = np.array(data.get("close", []))
        stoch_k = indicators.get("stoch_k_array", np.array([]))
        
        if len(close) < self.divergence_lookback or len(stoch_k) < self.divergence_lookback:
            indicators["bullish_divergence"] = False
            indicators["bearish_divergence"] = False
            return indicators
        
        # Detect divergences
        bullish_div = self._detect_bullish_divergence(close, stoch_k)
        bearish_div = self._detect_bearish_divergence(close, stoch_k)
        
        indicators["bullish_divergence"] = bullish_div
        indicators["bearish_divergence"] = bearish_div
        
        return indicators
    
    def _detect_bullish_divergence(self, close: np.ndarray, stoch: np.ndarray) -> bool:
        """Detect bullish divergence (price lower low, stoch higher low)"""
        lookback = self.divergence_lookback
        
        # Find recent lows
        price_recent = close[-lookback:]
        stoch_recent = stoch[-lookback:]
        
        # Simple detection: compare first half vs second half
        mid = lookback // 2
        
        price_first_low = np.min(price_recent[:mid])
        price_second_low = np.min(price_recent[mid:])
        
        stoch_first_low = np.min(stoch_recent[:mid])
        stoch_second_low = np.min(stoch_recent[mid:])
        
        # Bullish: price makes lower low, stoch makes higher low
        if price_second_low < price_first_low and stoch_second_low > stoch_first_low:
            return True
        
        return False
    
    def _detect_bearish_divergence(self, close: np.ndarray, stoch: np.ndarray) -> bool:
        """Detect bearish divergence (price higher high, stoch lower high)"""
        lookback = self.divergence_lookback
        
        price_recent = close[-lookback:]
        stoch_recent = stoch[-lookback:]
        
        mid = lookback // 2
        
        price_first_high = np.max(price_recent[:mid])
        price_second_high = np.max(price_recent[mid:])
        
        stoch_first_high = np.max(stoch_recent[:mid])
        stoch_second_high = np.max(stoch_recent[mid:])
        
        # Bearish: price makes higher high, stoch makes lower high
        if price_second_high > price_first_high and stoch_second_high < stoch_first_high:
            return True
        
        return False
    
    def check_entry_conditions(self, indicators: Dict[str, Any]) -> Tuple[SignalType, float, str]:
        """Check entry conditions including divergence"""
        
        # First check divergence (higher priority)
        bullish_div = indicators.get("bullish_divergence", False)
        bearish_div = indicators.get("bearish_divergence", False)
        stoch_k = indicators.get("stoch_k", 50)
        stoch_d = indicators.get("stoch_d", 50)
        
        if bullish_div and stoch_k < 30:
            confidence = 85
            reason = f"Bullish divergence detected (K={stoch_k:.1f})"
            return SignalType.BUY, confidence, reason
        
        if bearish_div and stoch_k > 70:
            confidence = 85
            reason = f"Bearish divergence detected (K={stoch_k:.1f})"
            return SignalType.SELL, confidence, reason
        
        # Fallback to standard Stochastic signals
        return super().check_entry_conditions(indicators)
