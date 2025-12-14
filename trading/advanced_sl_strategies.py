"""
Advanced Stop Loss Strategies Module
Provides sophisticated stop loss calculation methods based on price patterns and market structure.

Available Strategies:
1. Fixed Pips - Simple fixed pip distance
2. ATR-Based - Dynamic based on volatility (ATR multiplier)
3. Pin Bar - Behind the last pin bar in trade direction
4. Previous Leg - Behind the previous swing leg
5. FVG Start - Behind the candle that starts the FVG zone
6. Session Open - Behind the session opening candle (NY, London, Tokyo)
7. Leg Start Pin Bar - Behind the pin bar that started the current leg

All strategies are modular and can be used with any trading robot.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from datetime import datetime

from .pattern_detection import (
    PatternManager, PinBarDetector, LegDetector, FVGDetector, SwingPointDetector,
    Pattern, Leg, FVG, PatternType
)
from .market_sessions import MarketSessionDetector, MarketSession, SessionCandle


class AdvancedSLType(str, Enum):
    """Advanced Stop Loss calculation strategies"""
    FIXED_PIPS = "fixed_pips"
    ATR = "atr"
    PIN_BAR = "pin_bar"
    PREVIOUS_LEG = "previous_leg"
    FVG_START = "fvg_start"
    SESSION_OPEN = "session_open"
    LEG_START_PIN_BAR = "leg_start_pin_bar"


@dataclass
class SLCalculationResult:
    """Result of stop loss calculation"""
    stop_loss: float
    sl_pips: float
    strategy_used: AdvancedSLType
    confidence: float  # 0-1, how confident we are in this SL level
    pattern_info: Optional[Dict[str, Any]] = None
    fallback_used: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stop_loss": self.stop_loss,
            "sl_pips": self.sl_pips,
            "strategy_used": self.strategy_used.value,
            "confidence": self.confidence,
            "pattern_info": self.pattern_info,
            "fallback_used": self.fallback_used
        }


class BaseAdvancedSLStrategy(ABC):
    """Base class for advanced stop loss strategies"""
    
    STRATEGY_TYPE: AdvancedSLType = None
    
    def __init__(self, buffer_pips: float = 5.0):
        """
        Initialize strategy.
        
        Args:
            buffer_pips: Additional buffer in pips to add beyond the pattern level
        """
        self.buffer_pips = buffer_pips
    
    @abstractmethod
    def calculate(
        self,
        entry_price: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> SLCalculationResult:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Entry price of the trade
            is_buy: True for buy orders, False for sell
            data: Market data including OHLC, timestamps, etc.
            pip_value: Pip value for the symbol
            
        Returns:
            SLCalculationResult with stop loss details
        """
        pass
    
    def _add_buffer(self, sl_price: float, is_buy: bool, pip_value: float) -> float:
        """Add buffer to stop loss price."""
        buffer = self.buffer_pips * pip_value
        if is_buy:
            return sl_price - buffer
        else:
            return sl_price + buffer
    
    def _calculate_pips(self, entry_price: float, sl_price: float, pip_value: float) -> float:
        """Calculate pips between entry and stop loss."""
        return abs(entry_price - sl_price) / pip_value


# ============== Strategy Implementations ==============

class FixedPipsSL(BaseAdvancedSLStrategy):
    """
    Strategy 1: Fixed Pips Stop Loss
    
    Simple fixed pip distance from entry price.
    """
    
    STRATEGY_TYPE = AdvancedSLType.FIXED_PIPS
    
    def __init__(self, pips: float = 50.0, buffer_pips: float = 0.0):
        super().__init__(buffer_pips)
        self.pips = pips
    
    def calculate(
        self,
        entry_price: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> SLCalculationResult:
        sl_distance = self.pips * pip_value
        
        if is_buy:
            sl_price = entry_price - sl_distance
        else:
            sl_price = entry_price + sl_distance
        
        return SLCalculationResult(
            stop_loss=round(sl_price, 5),
            sl_pips=self.pips,
            strategy_used=self.STRATEGY_TYPE,
            confidence=1.0,
            pattern_info={"fixed_pips": self.pips}
        )


class ATRBasedSL(BaseAdvancedSLStrategy):
    """
    Strategy 2: ATR-Based Stop Loss
    
    Dynamic stop loss based on Average True Range.
    SL = Entry ± (ATR × Multiplier)
    """
    
    STRATEGY_TYPE = AdvancedSLType.ATR
    
    def __init__(self, multiplier: float = 2.0, period: int = 14, buffer_pips: float = 0.0):
        super().__init__(buffer_pips)
        self.multiplier = multiplier
        self.period = period
    
    def calculate(
        self,
        entry_price: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> SLCalculationResult:
        # Get or calculate ATR
        atr = data.get("atr", 0)
        
        if atr == 0:
            high = np.array(data.get("high", []))
            low = np.array(data.get("low", []))
            close = np.array(data.get("close", []))
            
            if len(high) >= self.period:
                atr = self._calculate_atr(high, low, close)
            else:
                # Fallback to fixed pips
                return FixedPipsSL(50.0).calculate(entry_price, is_buy, data, pip_value)
        
        sl_distance = atr * self.multiplier
        
        if is_buy:
            sl_price = entry_price - sl_distance
        else:
            sl_price = entry_price + sl_distance
        
        sl_pips = self._calculate_pips(entry_price, sl_price, pip_value)
        
        return SLCalculationResult(
            stop_loss=round(sl_price, 5),
            sl_pips=round(sl_pips, 1),
            strategy_used=self.STRATEGY_TYPE,
            confidence=0.9,
            pattern_info={
                "atr": atr,
                "multiplier": self.multiplier,
                "period": self.period
            }
        )
    
    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> float:
        """Calculate ATR from OHLC data."""
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        return np.mean(tr[-self.period:])


class PinBarSL(BaseAdvancedSLStrategy):
    """
    Strategy 3: Pin Bar Stop Loss
    
    Places stop loss behind the last pin bar in the trade direction.
    - For BUY: Behind the last bullish pin bar (below the lower shadow)
    - For SELL: Behind the last bearish pin bar (above the upper shadow)
    """
    
    STRATEGY_TYPE = AdvancedSLType.PIN_BAR
    
    def __init__(
        self,
        buffer_pips: float = 5.0,
        min_shadow_ratio: float = 2.0,
        lookback: int = 50,
        fallback_pips: float = 50.0
    ):
        super().__init__(buffer_pips)
        self.min_shadow_ratio = min_shadow_ratio
        self.lookback = lookback
        self.fallback_pips = fallback_pips
        self.pin_bar_detector = PinBarDetector(min_shadow_ratio=min_shadow_ratio)
    
    def calculate(
        self,
        entry_price: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> SLCalculationResult:
        open_prices = np.array(data.get("open", []))
        high_prices = np.array(data.get("high", []))
        low_prices = np.array(data.get("low", []))
        close_prices = np.array(data.get("close", []))
        
        if len(high_prices) < 3:
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Find pin bar in trade direction
        direction = "bullish" if is_buy else "bearish"
        pin_bar = self.pin_bar_detector.find_last_pin_bar(
            open_prices, high_prices, low_prices, close_prices,
            direction, pip_value, self.lookback
        )
        
        if pin_bar is None:
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Set SL behind the pin bar shadow
        if is_buy:
            sl_price = self._add_buffer(pin_bar.low, is_buy, pip_value)
        else:
            sl_price = self._add_buffer(pin_bar.high, is_buy, pip_value)
        
        sl_pips = self._calculate_pips(entry_price, sl_price, pip_value)
        
        return SLCalculationResult(
            stop_loss=round(sl_price, 5),
            sl_pips=round(sl_pips, 1),
            strategy_used=self.STRATEGY_TYPE,
            confidence=pin_bar.strength,
            pattern_info={
                "pin_bar_index": pin_bar.index,
                "pin_bar_type": pin_bar.pattern_type.value,
                "pin_bar_high": pin_bar.high,
                "pin_bar_low": pin_bar.low,
                "strength": pin_bar.strength
            }
        )
    
    def _fallback(self, entry_price: float, is_buy: bool, pip_value: float) -> SLCalculationResult:
        """Fallback to fixed pips when no pin bar found."""
        result = FixedPipsSL(self.fallback_pips).calculate(entry_price, is_buy, {}, pip_value)
        result.fallback_used = True
        result.pattern_info = {"reason": "No pin bar found, using fixed pips fallback"}
        return result


class PreviousLegSL(BaseAdvancedSLStrategy):
    """
    Strategy 4: Previous Leg Stop Loss
    
    Places stop loss behind the previous leg in the same direction.
    
    Example for BUY:
    - We had a bullish leg (Leg 1), then correction, now starting Leg 2
    - SL goes behind the low of Leg 1
    """
    
    STRATEGY_TYPE = AdvancedSLType.PREVIOUS_LEG
    
    def __init__(
        self,
        buffer_pips: float = 5.0,
        swing_lookback: int = 5,
        min_leg_pips: float = 20.0,
        fallback_pips: float = 50.0
    ):
        super().__init__(buffer_pips)
        self.swing_lookback = swing_lookback
        self.min_leg_pips = min_leg_pips
        self.fallback_pips = fallback_pips
        self.leg_detector = LegDetector(
            swing_lookback=swing_lookback,
            min_leg_pips=min_leg_pips
        )
    
    def calculate(
        self,
        entry_price: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> SLCalculationResult:
        open_prices = np.array(data.get("open", []))
        high_prices = np.array(data.get("high", []))
        low_prices = np.array(data.get("low", []))
        close_prices = np.array(data.get("close", []))
        
        if len(high_prices) < 20:
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Find previous leg in trade direction
        direction = "bullish" if is_buy else "bearish"
        previous_leg = self.leg_detector.find_previous_leg(
            open_prices, high_prices, low_prices, close_prices,
            direction, pip_value
        )
        
        if previous_leg is None:
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Set SL behind the leg
        if is_buy:
            sl_price = self._add_buffer(previous_leg.low, is_buy, pip_value)
        else:
            sl_price = self._add_buffer(previous_leg.high, is_buy, pip_value)
        
        sl_pips = self._calculate_pips(entry_price, sl_price, pip_value)
        
        return SLCalculationResult(
            stop_loss=round(sl_price, 5),
            sl_pips=round(sl_pips, 1),
            strategy_used=self.STRATEGY_TYPE,
            confidence=0.85,
            pattern_info={
                "leg_direction": previous_leg.direction,
                "leg_start_index": previous_leg.start_index,
                "leg_end_index": previous_leg.end_index,
                "leg_high": previous_leg.high,
                "leg_low": previous_leg.low,
                "leg_size_pips": previous_leg.size_pips
            }
        )
    
    def _fallback(self, entry_price: float, is_buy: bool, pip_value: float) -> SLCalculationResult:
        result = FixedPipsSL(self.fallback_pips).calculate(entry_price, is_buy, {}, pip_value)
        result.fallback_used = True
        result.pattern_info = {"reason": "No previous leg found, using fixed pips fallback"}
        return result


class FVGStartSL(BaseAdvancedSLStrategy):
    """
    Strategy 5: FVG Start Candle Stop Loss
    
    Places stop loss behind the candle that starts the FVG (Fair Value Gap) zone.
    The start candle is the first candle in the 3-candle FVG pattern.
    """
    
    STRATEGY_TYPE = AdvancedSLType.FVG_START
    
    def __init__(
        self,
        buffer_pips: float = 5.0,
        min_gap_pips: float = 5.0,
        lookback: int = 50,
        fallback_pips: float = 50.0
    ):
        super().__init__(buffer_pips)
        self.min_gap_pips = min_gap_pips
        self.lookback = lookback
        self.fallback_pips = fallback_pips
        self.fvg_detector = FVGDetector(min_gap_pips=min_gap_pips)
    
    def calculate(
        self,
        entry_price: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> SLCalculationResult:
        high_prices = np.array(data.get("high", []))
        low_prices = np.array(data.get("low", []))
        
        if len(high_prices) < 5:
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Find FVG in trade direction
        direction = "bullish" if is_buy else "bearish"
        fvg = self.fvg_detector.find_last_fvg(
            high_prices, low_prices, direction, pip_value, self.lookback
        )
        
        if fvg is None:
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Get the start candle (first candle before the gap)
        start_idx = fvg.start_candle_index
        
        if start_idx < 0 or start_idx >= len(high_prices):
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Set SL behind the start candle
        if is_buy:
            sl_price = self._add_buffer(low_prices[start_idx], is_buy, pip_value)
        else:
            sl_price = self._add_buffer(high_prices[start_idx], is_buy, pip_value)
        
        sl_pips = self._calculate_pips(entry_price, sl_price, pip_value)
        
        return SLCalculationResult(
            stop_loss=round(sl_price, 5),
            sl_pips=round(sl_pips, 1),
            strategy_used=self.STRATEGY_TYPE,
            confidence=0.8,
            pattern_info={
                "fvg_direction": fvg.direction,
                "fvg_index": fvg.index,
                "fvg_gap_high": fvg.gap_high,
                "fvg_gap_low": fvg.gap_low,
                "fvg_gap_size": fvg.gap_size,
                "start_candle_index": start_idx,
                "start_candle_high": high_prices[start_idx],
                "start_candle_low": low_prices[start_idx]
            }
        )
    
    def _fallback(self, entry_price: float, is_buy: bool, pip_value: float) -> SLCalculationResult:
        result = FixedPipsSL(self.fallback_pips).calculate(entry_price, is_buy, {}, pip_value)
        result.fallback_used = True
        result.pattern_info = {"reason": "No FVG found, using fixed pips fallback"}
        return result


class SessionOpenSL(BaseAdvancedSLStrategy):
    """
    Strategy 6: Session Opening Candle Stop Loss
    
    Places stop loss behind the candle at session opening.
    Sessions: New York, London, Tokyo (based on stock exchange opening times)
    
    Stock Exchange Opening Times (UTC):
    - Tokyo: 00:00 UTC (09:00 JST)
    - London: 08:00 UTC (08:00 GMT)
    - New York: 14:30 UTC (09:30 EST)
    """
    
    STRATEGY_TYPE = AdvancedSLType.SESSION_OPEN
    
    def __init__(
        self,
        session: MarketSession = MarketSession.NEW_YORK,
        buffer_pips: float = 5.0,
        lookback: int = 100,
        fallback_pips: float = 50.0
    ):
        super().__init__(buffer_pips)
        self.session = session
        self.lookback = lookback
        self.fallback_pips = fallback_pips
        self.session_detector = MarketSessionDetector()
    
    def calculate(
        self,
        entry_price: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> SLCalculationResult:
        timestamps = data.get("timestamps", [])
        high_prices = np.array(data.get("high", []))
        low_prices = np.array(data.get("low", []))
        open_prices = np.array(data.get("open", []))
        close_prices = np.array(data.get("close", []))
        
        if len(timestamps) < 5 or len(high_prices) < 5:
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Find session opening candle
        session_candle = self.session_detector.find_session_opening_candle(
            timestamps, high_prices, low_prices, open_prices, close_prices,
            self.session, self.lookback
        )
        
        if session_candle is None:
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Set SL behind the session candle
        if is_buy:
            sl_price = self._add_buffer(session_candle.low, is_buy, pip_value)
        else:
            sl_price = self._add_buffer(session_candle.high, is_buy, pip_value)
        
        sl_pips = self._calculate_pips(entry_price, sl_price, pip_value)
        
        return SLCalculationResult(
            stop_loss=round(sl_price, 5),
            sl_pips=round(sl_pips, 1),
            strategy_used=self.STRATEGY_TYPE,
            confidence=0.75,
            pattern_info={
                "session": self.session.value,
                "candle_index": session_candle.candle_index,
                "candle_time": session_candle.candle_time.isoformat() if session_candle.candle_time else None,
                "candle_high": session_candle.high,
                "candle_low": session_candle.low
            }
        )
    
    def _fallback(self, entry_price: float, is_buy: bool, pip_value: float) -> SLCalculationResult:
        result = FixedPipsSL(self.fallback_pips).calculate(entry_price, is_buy, {}, pip_value)
        result.fallback_used = True
        result.pattern_info = {"reason": f"No {self.session.value} session candle found, using fixed pips fallback"}
        return result


class LegStartPinBarSL(BaseAdvancedSLStrategy):
    """
    Strategy 7: Leg Start Pin Bar Stop Loss
    
    Places stop loss behind the pin bar that started the current leg.
    This combines leg detection with pin bar detection.
    """
    
    STRATEGY_TYPE = AdvancedSLType.LEG_START_PIN_BAR
    
    def __init__(
        self,
        buffer_pips: float = 5.0,
        min_shadow_ratio: float = 2.0,
        swing_lookback: int = 5,
        fallback_pips: float = 50.0
    ):
        super().__init__(buffer_pips)
        self.min_shadow_ratio = min_shadow_ratio
        self.swing_lookback = swing_lookback
        self.fallback_pips = fallback_pips
        self.pin_bar_detector = PinBarDetector(min_shadow_ratio=min_shadow_ratio)
        self.leg_detector = LegDetector(swing_lookback=swing_lookback)
    
    def calculate(
        self,
        entry_price: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> SLCalculationResult:
        open_prices = np.array(data.get("open", []))
        high_prices = np.array(data.get("high", []))
        low_prices = np.array(data.get("low", []))
        close_prices = np.array(data.get("close", []))
        
        if len(high_prices) < 20:
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Find current leg
        direction = "bullish" if is_buy else "bearish"
        current_leg = self.leg_detector.find_current_leg(
            open_prices, high_prices, low_prices, close_prices,
            direction, pip_value
        )
        
        if current_leg is None:
            return self._fallback(entry_price, is_buy, pip_value)
        
        # Look for pin bar near the leg start
        leg_start = current_leg.start_index
        search_range = min(10, leg_start)  # Search within 10 candles of leg start
        
        # Find pin bars in the search range
        start_idx = max(0, leg_start - search_range)
        end_idx = min(len(high_prices), leg_start + 3)
        
        pin_bars = self.pin_bar_detector.detect(
            open_prices[start_idx:end_idx],
            high_prices[start_idx:end_idx],
            low_prices[start_idx:end_idx],
            close_prices[start_idx:end_idx],
            pip_value,
            lookback=end_idx - start_idx
        )
        
        # Filter for pin bars in trade direction
        target_type = PatternType.PIN_BAR_BULLISH if is_buy else PatternType.PIN_BAR_BEARISH
        matching_pin_bars = [p for p in pin_bars if p.pattern_type == target_type]
        
        if not matching_pin_bars:
            # No pin bar at leg start, use leg start instead
            if is_buy:
                sl_price = self._add_buffer(current_leg.low, is_buy, pip_value)
            else:
                sl_price = self._add_buffer(current_leg.high, is_buy, pip_value)
            
            sl_pips = self._calculate_pips(entry_price, sl_price, pip_value)
            
            return SLCalculationResult(
                stop_loss=round(sl_price, 5),
                sl_pips=round(sl_pips, 1),
                strategy_used=self.STRATEGY_TYPE,
                confidence=0.7,
                pattern_info={
                    "leg_start_index": current_leg.start_index,
                    "leg_direction": current_leg.direction,
                    "pin_bar_found": False,
                    "using_leg_extreme": True
                }
            )
        
        # Use the pin bar closest to leg start
        pin_bar = min(matching_pin_bars, key=lambda p: abs(p.index - (leg_start - start_idx)))
        
        # Adjust index back to original array
        actual_index = start_idx + pin_bar.index
        
        if is_buy:
            sl_price = self._add_buffer(low_prices[actual_index], is_buy, pip_value)
        else:
            sl_price = self._add_buffer(high_prices[actual_index], is_buy, pip_value)
        
        sl_pips = self._calculate_pips(entry_price, sl_price, pip_value)
        
        return SLCalculationResult(
            stop_loss=round(sl_price, 5),
            sl_pips=round(sl_pips, 1),
            strategy_used=self.STRATEGY_TYPE,
            confidence=pin_bar.strength * 0.9,
            pattern_info={
                "leg_start_index": current_leg.start_index,
                "leg_direction": current_leg.direction,
                "pin_bar_found": True,
                "pin_bar_index": actual_index,
                "pin_bar_type": pin_bar.pattern_type.value,
                "pin_bar_high": high_prices[actual_index],
                "pin_bar_low": low_prices[actual_index]
            }
        )
    
    def _fallback(self, entry_price: float, is_buy: bool, pip_value: float) -> SLCalculationResult:
        result = FixedPipsSL(self.fallback_pips).calculate(entry_price, is_buy, {}, pip_value)
        result.fallback_used = True
        result.pattern_info = {"reason": "No leg/pin bar found, using fixed pips fallback"}
        return result


# ============== Strategy Factory ==============

class AdvancedSLFactory:
    """Factory for creating advanced stop loss strategies."""
    
    STRATEGIES = {
        AdvancedSLType.FIXED_PIPS: FixedPipsSL,
        AdvancedSLType.ATR: ATRBasedSL,
        AdvancedSLType.PIN_BAR: PinBarSL,
        AdvancedSLType.PREVIOUS_LEG: PreviousLegSL,
        AdvancedSLType.FVG_START: FVGStartSL,
        AdvancedSLType.SESSION_OPEN: SessionOpenSL,
        AdvancedSLType.LEG_START_PIN_BAR: LegStartPinBarSL,
    }
    
    @classmethod
    def create(cls, strategy_type: AdvancedSLType, **kwargs) -> BaseAdvancedSLStrategy:
        """
        Create a stop loss strategy instance.
        
        Args:
            strategy_type: Type of strategy to create
            **kwargs: Strategy-specific parameters
            
        Returns:
            Strategy instance
        """
        strategy_class = cls.STRATEGIES.get(strategy_type)
        if strategy_class is None:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        return strategy_class(**kwargs)
    
    @classmethod
    def get_available_strategies(cls) -> List[Dict[str, Any]]:
        """Get list of available strategies with descriptions."""
        return [
            {
                "id": AdvancedSLType.FIXED_PIPS.value,
                "name": "Fixed Pips",
                "description": "Simple fixed pip distance from entry",
                "params": ["pips"],
                "premium": False
            },
            {
                "id": AdvancedSLType.ATR.value,
                "name": "ATR-Based",
                "description": "Dynamic SL based on market volatility (ATR × multiplier)",
                "params": ["multiplier", "period"],
                "premium": False
            },
            {
                "id": AdvancedSLType.PIN_BAR.value,
                "name": "Pin Bar",
                "description": "Behind the last pin bar in trade direction",
                "params": ["min_shadow_ratio", "lookback"],
                "premium": True
            },
            {
                "id": AdvancedSLType.PREVIOUS_LEG.value,
                "name": "Previous Leg",
                "description": "Behind the previous swing leg (before correction)",
                "params": ["swing_lookback", "min_leg_pips"],
                "premium": True
            },
            {
                "id": AdvancedSLType.FVG_START.value,
                "name": "FVG Start",
                "description": "Behind the candle that starts the FVG zone",
                "params": ["min_gap_pips", "lookback"],
                "premium": True
            },
            {
                "id": AdvancedSLType.SESSION_OPEN.value,
                "name": "Session Open",
                "description": "Behind the session opening candle (NY/London/Tokyo)",
                "params": ["session"],
                "premium": True
            },
            {
                "id": AdvancedSLType.LEG_START_PIN_BAR.value,
                "name": "Leg Start Pin Bar",
                "description": "Behind the pin bar that started the current leg",
                "params": ["min_shadow_ratio", "swing_lookback"],
                "premium": True
            }
        ]


# ============== Manager Class ==============

class AdvancedSLManager:
    """
    Manager for advanced stop loss calculation.
    Handles strategy selection and premium access control.
    """
    
    # Free strategies
    FREE_STRATEGIES = {AdvancedSLType.FIXED_PIPS, AdvancedSLType.ATR}
    
    def __init__(self, is_premium: bool = False):
        self.is_premium = is_premium
        self._current_strategy: Optional[BaseAdvancedSLStrategy] = None
        self._strategy_type: Optional[AdvancedSLType] = None
    
    def set_strategy(self, strategy_type: AdvancedSLType, **kwargs) -> bool:
        """
        Set the stop loss strategy.
        
        Args:
            strategy_type: Type of strategy
            **kwargs: Strategy parameters
            
        Returns:
            True if strategy was set, False if not allowed (premium required)
        """
        # Check premium access
        if strategy_type not in self.FREE_STRATEGIES and not self.is_premium:
            # Fallback to ATR for non-premium users
            self._current_strategy = AdvancedSLFactory.create(AdvancedSLType.ATR)
            self._strategy_type = AdvancedSLType.ATR
            return False
        
        self._current_strategy = AdvancedSLFactory.create(strategy_type, **kwargs)
        self._strategy_type = strategy_type
        return True
    
    def calculate(
        self,
        entry_price: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> SLCalculationResult:
        """
        Calculate stop loss using the configured strategy.
        """
        if self._current_strategy is None:
            # Default to ATR
            self._current_strategy = AdvancedSLFactory.create(AdvancedSLType.ATR)
            self._strategy_type = AdvancedSLType.ATR
        
        return self._current_strategy.calculate(entry_price, is_buy, data, pip_value)
    
    def get_current_strategy(self) -> Optional[AdvancedSLType]:
        """Get the currently configured strategy type."""
        return self._strategy_type
    
    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """Get available strategies based on premium status."""
        all_strategies = AdvancedSLFactory.get_available_strategies()
        
        for strategy in all_strategies:
            strategy["available"] = (
                strategy["id"] in [s.value for s in self.FREE_STRATEGIES] or
                self.is_premium
            )
        
        return all_strategies
