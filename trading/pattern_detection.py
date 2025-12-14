"""
Pattern Detection Module
Provides detection for various price patterns used in stop loss strategies.

Patterns Detected:
- Pin Bar (Bullish/Bearish)
- Price Legs (Swing structure)
- Fair Value Gaps (FVG/Imbalance)
- Swing Points (Highs/Lows)
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from datetime import datetime


class PatternType(str, Enum):
    """Types of detected patterns"""
    PIN_BAR_BULLISH = "pin_bar_bullish"
    PIN_BAR_BEARISH = "pin_bar_bearish"
    SWING_HIGH = "swing_high"
    SWING_LOW = "swing_low"
    FVG_BULLISH = "fvg_bullish"
    FVG_BEARISH = "fvg_bearish"
    LEG_BULLISH = "leg_bullish"
    LEG_BEARISH = "leg_bearish"


@dataclass
class Pattern:
    """Detected pattern information"""
    pattern_type: PatternType
    index: int  # Index in the data array
    price_level: float  # Key price level (e.g., shadow tip for pin bar)
    high: float
    low: float
    strength: float  # Pattern strength/quality (0-1)
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "index": self.index,
            "price_level": self.price_level,
            "high": self.high,
            "low": self.low,
            "strength": self.strength,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {}
        }


@dataclass
class Leg:
    """Price leg (swing structure) information"""
    direction: str  # "bullish" or "bearish"
    start_index: int
    end_index: int
    start_price: float
    end_price: float
    high: float
    low: float
    size_pips: float
    candle_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "start_price": self.start_price,
            "end_price": self.end_price,
            "high": self.high,
            "low": self.low,
            "size_pips": self.size_pips,
            "candle_count": self.candle_count
        }


@dataclass
class FVG:
    """Fair Value Gap (Imbalance) information"""
    direction: str  # "bullish" or "bearish"
    index: int  # Index of the middle candle
    gap_high: float
    gap_low: float
    gap_size: float
    start_candle_index: int  # First candle before gap
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "index": self.index,
            "gap_high": self.gap_high,
            "gap_low": self.gap_low,
            "gap_size": self.gap_size,
            "start_candle_index": self.start_candle_index
        }


class PinBarDetector:
    """
    Pin Bar Detection
    
    Pin Bar Definition (based on shadow importance):
    - Bullish Pin Bar: Long lower shadow (wick pointing down), small body
      The shadow should be at least 2x the body size
    - Bearish Pin Bar: Long upper shadow (wick pointing up), small body
      The shadow should be at least 2x the body size
    
    Note: Body direction is NOT important, shadow direction determines the type
    """
    
    def __init__(
        self,
        min_shadow_ratio: float = 2.0,  # Shadow should be at least 2x body
        max_body_ratio: float = 0.35,   # Body should be max 35% of total range
        min_range_pips: float = 10.0    # Minimum candle range in pips
    ):
        self.min_shadow_ratio = min_shadow_ratio
        self.max_body_ratio = max_body_ratio
        self.min_range_pips = min_range_pips
    
    def detect(
        self,
        open_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        pip_value: float = 0.0001,
        lookback: int = 50
    ) -> List[Pattern]:
        """
        Detect pin bars in price data.
        
        Returns list of detected pin bar patterns.
        """
        patterns = []
        
        # Ensure we have enough data
        data_len = len(close_prices)
        if data_len < 3:
            return patterns
        
        start_idx = max(0, data_len - lookback)
        
        for i in range(start_idx, data_len):
            pin_bar = self._check_pin_bar(
                open_prices[i], high_prices[i], low_prices[i], close_prices[i],
                pip_value
            )
            
            if pin_bar:
                pattern_type, price_level, strength = pin_bar
                patterns.append(Pattern(
                    pattern_type=pattern_type,
                    index=i,
                    price_level=price_level,
                    high=high_prices[i],
                    low=low_prices[i],
                    strength=strength,
                    metadata={
                        "open": open_prices[i],
                        "close": close_prices[i],
                        "body_size": abs(close_prices[i] - open_prices[i]),
                        "upper_shadow": high_prices[i] - max(open_prices[i], close_prices[i]),
                        "lower_shadow": min(open_prices[i], close_prices[i]) - low_prices[i]
                    }
                ))
        
        return patterns
    
    def _check_pin_bar(
        self,
        open_price: float,
        high: float,
        low: float,
        close: float,
        pip_value: float
    ) -> Optional[Tuple[PatternType, float, float]]:
        """
        Check if a single candle is a pin bar.
        
        Returns: (pattern_type, key_price_level, strength) or None
        """
        total_range = high - low
        
        # Check minimum range
        if total_range < self.min_range_pips * pip_value:
            return None
        
        body = abs(close - open_price)
        body_top = max(open_price, close)
        body_bottom = min(open_price, close)
        
        upper_shadow = high - body_top
        lower_shadow = body_bottom - low
        
        # Body ratio check
        body_ratio = body / total_range if total_range > 0 else 1
        if body_ratio > self.max_body_ratio:
            return None
        
        # Check for Bullish Pin Bar (long lower shadow)
        if lower_shadow > 0 and body > 0:
            shadow_to_body = lower_shadow / body
            if shadow_to_body >= self.min_shadow_ratio and lower_shadow > upper_shadow * 1.5:
                # Strength based on shadow ratio and position
                strength = min(1.0, shadow_to_body / (self.min_shadow_ratio * 2))
                return (PatternType.PIN_BAR_BULLISH, low, strength)
        
        # Check for Bearish Pin Bar (long upper shadow)
        if upper_shadow > 0 and body > 0:
            shadow_to_body = upper_shadow / body
            if shadow_to_body >= self.min_shadow_ratio and upper_shadow > lower_shadow * 1.5:
                strength = min(1.0, shadow_to_body / (self.min_shadow_ratio * 2))
                return (PatternType.PIN_BAR_BEARISH, high, strength)
        
        return None
    
    def find_last_pin_bar(
        self,
        open_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        direction: str,  # "bullish" or "bearish"
        pip_value: float = 0.0001,
        lookback: int = 50
    ) -> Optional[Pattern]:
        """
        Find the most recent pin bar in the specified direction.
        """
        patterns = self.detect(open_prices, high_prices, low_prices, close_prices, pip_value, lookback)
        
        target_type = PatternType.PIN_BAR_BULLISH if direction == "bullish" else PatternType.PIN_BAR_BEARISH
        
        # Filter by direction and return most recent
        matching = [p for p in patterns if p.pattern_type == target_type]
        
        if matching:
            return max(matching, key=lambda p: p.index)
        return None


class LegDetector:
    """
    Price Leg Detection
    
    A leg is a directional price movement between swing points.
    - Bullish Leg: Price moves from swing low to swing high
    - Bearish Leg: Price moves from swing high to swing low
    
    Used for:
    - Stop loss behind previous leg
    - Identifying market structure
    """
    
    def __init__(
        self,
        swing_lookback: int = 5,      # Bars to look back/forward for swing detection
        min_leg_pips: float = 20.0,   # Minimum leg size in pips
        min_leg_candles: int = 3      # Minimum candles in a leg
    ):
        self.swing_lookback = swing_lookback
        self.min_leg_pips = min_leg_pips
        self.min_leg_candles = min_leg_candles
    
    def detect_swings(
        self,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        lookback: int = 5
    ) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
        """
        Detect swing highs and swing lows.
        
        Returns: (swing_highs, swing_lows) as lists of (index, price) tuples
        """
        swing_highs = []
        swing_lows = []
        
        data_len = len(high_prices)
        
        for i in range(lookback, data_len - lookback):
            # Check for swing high
            is_swing_high = True
            for j in range(1, lookback + 1):
                if high_prices[i] <= high_prices[i - j] or high_prices[i] <= high_prices[i + j]:
                    is_swing_high = False
                    break
            if is_swing_high:
                swing_highs.append((i, high_prices[i]))
            
            # Check for swing low
            is_swing_low = True
            for j in range(1, lookback + 1):
                if low_prices[i] >= low_prices[i - j] or low_prices[i] >= low_prices[i + j]:
                    is_swing_low = False
                    break
            if is_swing_low:
                swing_lows.append((i, low_prices[i]))
        
        return swing_highs, swing_lows
    
    def detect_legs(
        self,
        open_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        pip_value: float = 0.0001
    ) -> List[Leg]:
        """
        Detect price legs based on swing structure.
        
        Returns list of detected legs.
        """
        legs = []
        
        swing_highs, swing_lows = self.detect_swings(high_prices, low_prices, self.swing_lookback)
        
        # Combine and sort swings by index
        all_swings = []
        for idx, price in swing_highs:
            all_swings.append(("high", idx, price))
        for idx, price in swing_lows:
            all_swings.append(("low", idx, price))
        
        all_swings.sort(key=lambda x: x[1])
        
        # Build legs from consecutive swings
        for i in range(len(all_swings) - 1):
            swing1_type, swing1_idx, swing1_price = all_swings[i]
            swing2_type, swing2_idx, swing2_price = all_swings[i + 1]
            
            # Skip if same type (shouldn't happen but safety check)
            if swing1_type == swing2_type:
                continue
            
            candle_count = swing2_idx - swing1_idx
            if candle_count < self.min_leg_candles:
                continue
            
            # Determine leg direction
            if swing1_type == "low" and swing2_type == "high":
                direction = "bullish"
                start_price = swing1_price
                end_price = swing2_price
                leg_high = swing2_price
                leg_low = swing1_price
            else:  # high to low
                direction = "bearish"
                start_price = swing1_price
                end_price = swing2_price
                leg_high = swing1_price
                leg_low = swing2_price
            
            size_pips = abs(end_price - start_price) / pip_value
            
            if size_pips < self.min_leg_pips:
                continue
            
            legs.append(Leg(
                direction=direction,
                start_index=swing1_idx,
                end_index=swing2_idx,
                start_price=start_price,
                end_price=end_price,
                high=leg_high,
                low=leg_low,
                size_pips=size_pips,
                candle_count=candle_count
            ))
        
        return legs
    
    def find_previous_leg(
        self,
        open_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        current_direction: str,  # Direction of current trade
        pip_value: float = 0.0001
    ) -> Optional[Leg]:
        """
        Find the previous leg in the same direction as the current trade.
        
        For a bullish trade, find the previous bullish leg (before correction).
        For a bearish trade, find the previous bearish leg (before correction).
        """
        legs = self.detect_legs(open_prices, high_prices, low_prices, close_prices, pip_value)
        
        if len(legs) < 2:
            return None
        
        # Find legs in the same direction
        same_direction_legs = [leg for leg in legs if leg.direction == current_direction]
        
        if len(same_direction_legs) < 2:
            # Return the only one if exists
            return same_direction_legs[0] if same_direction_legs else None
        
        # Return the second to last leg (the one before the current move)
        return same_direction_legs[-2]
    
    def find_current_leg(
        self,
        open_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        direction: str,
        pip_value: float = 0.0001
    ) -> Optional[Leg]:
        """
        Find the current/most recent leg in the specified direction.
        """
        legs = self.detect_legs(open_prices, high_prices, low_prices, close_prices, pip_value)
        
        same_direction_legs = [leg for leg in legs if leg.direction == direction]
        
        if same_direction_legs:
            return same_direction_legs[-1]
        return None


class FVGDetector:
    """
    Fair Value Gap (FVG) / Imbalance Detection
    
    FVG is a 3-candle pattern where there's a gap between:
    - Bullish FVG: Candle 1's high and Candle 3's low (gap in between)
    - Bearish FVG: Candle 1's low and Candle 3's high (gap in between)
    
    The middle candle (Candle 2) creates the imbalance.
    """
    
    def __init__(
        self,
        min_gap_pips: float = 5.0,  # Minimum gap size in pips
    ):
        self.min_gap_pips = min_gap_pips
    
    def detect(
        self,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        pip_value: float = 0.0001,
        lookback: int = 50
    ) -> List[FVG]:
        """
        Detect Fair Value Gaps in price data.
        
        Returns list of detected FVGs.
        """
        fvgs = []
        
        data_len = len(high_prices)
        if data_len < 3:
            return fvgs
        
        start_idx = max(2, data_len - lookback)
        
        for i in range(start_idx, data_len):
            # Candle indices: i-2 (first), i-1 (middle), i (third)
            candle1_high = high_prices[i - 2]
            candle1_low = low_prices[i - 2]
            candle3_high = high_prices[i]
            candle3_low = low_prices[i]
            
            # Check for Bullish FVG
            # Gap exists when candle 3's low is above candle 1's high
            if candle3_low > candle1_high:
                gap_size = (candle3_low - candle1_high) / pip_value
                if gap_size >= self.min_gap_pips:
                    fvgs.append(FVG(
                        direction="bullish",
                        index=i - 1,  # Middle candle index
                        gap_high=candle3_low,
                        gap_low=candle1_high,
                        gap_size=gap_size,
                        start_candle_index=i - 2
                    ))
            
            # Check for Bearish FVG
            # Gap exists when candle 3's high is below candle 1's low
            if candle3_high < candle1_low:
                gap_size = (candle1_low - candle3_high) / pip_value
                if gap_size >= self.min_gap_pips:
                    fvgs.append(FVG(
                        direction="bearish",
                        index=i - 1,
                        gap_high=candle1_low,
                        gap_low=candle3_high,
                        gap_size=gap_size,
                        start_candle_index=i - 2
                    ))
        
        return fvgs
    
    def find_last_fvg(
        self,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        direction: str,  # "bullish" or "bearish"
        pip_value: float = 0.0001,
        lookback: int = 50
    ) -> Optional[FVG]:
        """
        Find the most recent FVG in the specified direction.
        """
        fvgs = self.detect(high_prices, low_prices, pip_value, lookback)
        
        matching = [fvg for fvg in fvgs if fvg.direction == direction]
        
        if matching:
            return max(matching, key=lambda f: f.index)
        return None


class SwingPointDetector:
    """
    Swing Point Detection
    
    Detects significant swing highs and lows in price data.
    """
    
    def __init__(self, lookback: int = 5):
        self.lookback = lookback
    
    def detect(
        self,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        max_results: int = 20
    ) -> Tuple[List[Pattern], List[Pattern]]:
        """
        Detect swing highs and swing lows.
        
        Returns: (swing_highs, swing_lows) as lists of Pattern objects
        """
        swing_highs = []
        swing_lows = []
        
        data_len = len(high_prices)
        
        for i in range(self.lookback, data_len - self.lookback):
            # Check for swing high
            is_swing_high = all(
                high_prices[i] > high_prices[i - j] and high_prices[i] > high_prices[i + j]
                for j in range(1, self.lookback + 1)
            )
            if is_swing_high:
                swing_highs.append(Pattern(
                    pattern_type=PatternType.SWING_HIGH,
                    index=i,
                    price_level=high_prices[i],
                    high=high_prices[i],
                    low=low_prices[i],
                    strength=1.0
                ))
            
            # Check for swing low
            is_swing_low = all(
                low_prices[i] < low_prices[i - j] and low_prices[i] < low_prices[i + j]
                for j in range(1, self.lookback + 1)
            )
            if is_swing_low:
                swing_lows.append(Pattern(
                    pattern_type=PatternType.SWING_LOW,
                    index=i,
                    price_level=low_prices[i],
                    high=high_prices[i],
                    low=low_prices[i],
                    strength=1.0
                ))
        
        # Return most recent ones
        return swing_highs[-max_results:], swing_lows[-max_results:]
    
    def find_nearest_swing(
        self,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        is_buy: bool,
        current_price: float
    ) -> Optional[Pattern]:
        """
        Find the nearest swing point for stop loss placement.
        
        For buy: Find nearest swing low below current price
        For sell: Find nearest swing high above current price
        """
        swing_highs, swing_lows = self.detect(high_prices, low_prices)
        
        if is_buy:
            # Find swing lows below current price
            valid_swings = [s for s in swing_lows if s.price_level < current_price]
            if valid_swings:
                return max(valid_swings, key=lambda s: s.price_level)
        else:
            # Find swing highs above current price
            valid_swings = [s for s in swing_highs if s.price_level > current_price]
            if valid_swings:
                return min(valid_swings, key=lambda s: s.price_level)
        
        return None


class PatternManager:
    """
    Unified manager for all pattern detection.
    Provides easy access to all pattern detectors.
    """
    
    def __init__(
        self,
        pin_bar_config: Optional[Dict[str, Any]] = None,
        leg_config: Optional[Dict[str, Any]] = None,
        fvg_config: Optional[Dict[str, Any]] = None,
        swing_config: Optional[Dict[str, Any]] = None
    ):
        self.pin_bar_detector = PinBarDetector(**(pin_bar_config or {}))
        self.leg_detector = LegDetector(**(leg_config or {}))
        self.fvg_detector = FVGDetector(**(fvg_config or {}))
        self.swing_detector = SwingPointDetector(**(swing_config or {}))
    
    def detect_all(
        self,
        open_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        pip_value: float = 0.0001,
        lookback: int = 50
    ) -> Dict[str, Any]:
        """
        Detect all patterns in the data.
        
        Returns dictionary with all detected patterns.
        """
        return {
            "pin_bars": self.pin_bar_detector.detect(
                open_prices, high_prices, low_prices, close_prices, pip_value, lookback
            ),
            "legs": self.leg_detector.detect_legs(
                open_prices, high_prices, low_prices, close_prices, pip_value
            ),
            "fvgs": self.fvg_detector.detect(high_prices, low_prices, pip_value, lookback),
            "swing_highs": self.swing_detector.detect(high_prices, low_prices)[0],
            "swing_lows": self.swing_detector.detect(high_prices, low_prices)[1]
        }
