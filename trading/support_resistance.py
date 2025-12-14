"""
Support & Resistance Levels Detection Module
ماژول تشخیص سطوح حمایت و مقاومت

This module provides comprehensive support/resistance level detection with:
- Multiple timeframe analysis (hourly, daily, weekly)
- Level strength/validity scoring based on:
  - Number of touches
  - ATR-based significance
  - Pin bar formations at level
  - Leg structure around level
  - Volume (if available)
  - Time proximity
- Weekly Map integration (pivot points, fibonacci levels)
- Last level vs Most Important level detection

Level Types:
- Swing Highs/Lows
- Pivot Points (Daily, Weekly, Monthly)
- Fibonacci Retracements
- Round Numbers (Psychological levels)
- Volume Profile levels (if volume data available)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np

try:
    from .pattern_detection import PinBarDetector, LegDetector, SwingPointDetector, PatternType
except ImportError:
    from pattern_detection import PinBarDetector, LegDetector, SwingPointDetector, PatternType


class LevelType(str, Enum):
    """Types of support/resistance levels"""
    SWING_HIGH = "swing_high"
    SWING_LOW = "swing_low"
    PIVOT_POINT = "pivot_point"
    PIVOT_R1 = "pivot_r1"
    PIVOT_R2 = "pivot_r2"
    PIVOT_R3 = "pivot_r3"
    PIVOT_S1 = "pivot_s1"
    PIVOT_S2 = "pivot_s2"
    PIVOT_S3 = "pivot_s3"
    FIBONACCI = "fibonacci"
    ROUND_NUMBER = "round_number"
    WEEKLY_HIGH = "weekly_high"
    WEEKLY_LOW = "weekly_low"
    DAILY_HIGH = "daily_high"
    DAILY_LOW = "daily_low"
    SESSION_HIGH = "session_high"
    SESSION_LOW = "session_low"


class LevelStrength(str, Enum):
    """Strength classification of levels"""
    WEAK = "weak"           # 0-30 score
    MODERATE = "moderate"   # 30-60 score
    STRONG = "strong"       # 60-80 score
    VERY_STRONG = "very_strong"  # 80-100 score


class TimeframeContext(str, Enum):
    """Timeframe context for level detection"""
    HOURLY = "hourly"       # Last hour
    DAILY = "daily"         # Last day (24h)
    WEEKLY = "weekly"       # Last week


@dataclass
class SRLevel:
    """Support/Resistance Level with metadata"""
    price: float
    level_type: LevelType
    is_support: bool  # True = Support, False = Resistance
    strength_score: float  # 0-100
    strength_class: LevelStrength
    touches: int  # Number of times price touched this level
    first_touch_index: int
    last_touch_index: int
    timeframe_context: TimeframeContext
    
    # Additional metadata
    has_pin_bar: bool = False
    has_leg_rejection: bool = False
    atr_significance: float = 0.0  # How significant relative to ATR
    distance_from_current: float = 0.0  # Pips from current price
    
    # Display name for UI
    display_name: str = ""
    
    def __post_init__(self):
        if not self.display_name:
            direction = "Support" if self.is_support else "Resistance"
            self.display_name = f"{direction} @ {self.price:.5f} ({self.strength_class.value})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "price": self.price,
            "level_type": self.level_type.value,
            "is_support": self.is_support,
            "strength_score": self.strength_score,
            "strength_class": self.strength_class.value,
            "touches": self.touches,
            "timeframe_context": self.timeframe_context.value,
            "has_pin_bar": self.has_pin_bar,
            "has_leg_rejection": self.has_leg_rejection,
            "atr_significance": self.atr_significance,
            "distance_from_current": self.distance_from_current,
            "display_name": self.display_name
        }


@dataclass
class WeeklyMapLevels:
    """Weekly Map levels (Pivot Points + Fibonacci)"""
    pivot: float
    r1: float
    r2: float
    r3: float
    s1: float
    s2: float
    s3: float
    
    # Fibonacci levels
    fib_236: float = 0.0
    fib_382: float = 0.0
    fib_500: float = 0.0
    fib_618: float = 0.0
    fib_786: float = 0.0
    
    weekly_high: float = 0.0
    weekly_low: float = 0.0
    weekly_open: float = 0.0
    weekly_close: float = 0.0


class SupportResistanceDetector:
    """
    Advanced Support/Resistance Level Detector
    
    Features:
    - Multi-timeframe level detection
    - Strength scoring based on multiple factors
    - Weekly Map integration
    - Pin bar and leg structure analysis
    """
    
    def __init__(
        self,
        swing_lookback: int = 5,
        level_tolerance_pips: float = 5.0,
        min_touches: int = 2,
        atr_period: int = 14
    ):
        """
        Initialize detector.
        
        Args:
            swing_lookback: Lookback for swing point detection
            level_tolerance_pips: Tolerance for grouping similar levels
            min_touches: Minimum touches to consider a valid level
            atr_period: Period for ATR calculation
        """
        self.swing_lookback = swing_lookback
        self.level_tolerance_pips = level_tolerance_pips
        self.min_touches = min_touches
        self.atr_period = atr_period
        
        # Sub-detectors
        self.swing_detector = SwingPointDetector(lookback=swing_lookback)
        self.pin_bar_detector = PinBarDetector()
        self.leg_detector = LegDetector(swing_lookback=swing_lookback)
    
    def detect_all_levels(
        self,
        open_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        timestamps: Optional[List[datetime]] = None,
        pip_value: float = 0.0001,
        current_price: Optional[float] = None,
        include_weekly_map: bool = True
    ) -> List[SRLevel]:
        """
        Detect all support/resistance levels.
        
        Returns list of SRLevel objects sorted by strength (strongest first).
        """
        if current_price is None:
            current_price = float(close_prices[-1])
        
        all_levels = []
        
        # Calculate ATR for significance scoring
        atr = self._calculate_atr(high_prices, low_prices, close_prices)
        
        # 1. Detect swing-based levels
        swing_levels = self._detect_swing_levels(
            high_prices, low_prices, close_prices, timestamps, pip_value, atr
        )
        all_levels.extend(swing_levels)
        
        # 2. Detect pivot point levels (if we have enough data)
        if len(close_prices) >= 24:  # At least 1 day of hourly data
            pivot_levels = self._detect_pivot_levels(
                open_prices, high_prices, low_prices, close_prices, timestamps, pip_value, atr
            )
            all_levels.extend(pivot_levels)
        
        # 3. Detect round number levels
        round_levels = self._detect_round_numbers(
            current_price, pip_value, atr
        )
        all_levels.extend(round_levels)
        
        # 4. Weekly Map levels
        if include_weekly_map and len(close_prices) >= 168:  # At least 1 week of hourly data
            weekly_levels = self._detect_weekly_map_levels(
                open_prices, high_prices, low_prices, close_prices, timestamps, pip_value, atr
            )
            all_levels.extend(weekly_levels)
        
        # Merge similar levels
        merged_levels = self._merge_similar_levels(all_levels, pip_value)
        
        # Calculate strength scores
        scored_levels = self._calculate_strength_scores(
            merged_levels, open_prices, high_prices, low_prices, close_prices,
            pip_value, atr, current_price
        )
        
        # Update distance from current price
        for level in scored_levels:
            level.distance_from_current = abs(level.price - current_price) / pip_value
        
        # Sort by strength (strongest first)
        scored_levels.sort(key=lambda x: x.strength_score, reverse=True)
        
        return scored_levels
    
    def get_nearest_level(
        self,
        levels: List[SRLevel],
        current_price: float,
        is_support: bool,
        pip_value: float = 0.0001
    ) -> Optional[SRLevel]:
        """
        Get the nearest support or resistance level.
        
        Args:
            levels: List of detected levels
            current_price: Current price
            is_support: True for support, False for resistance
            pip_value: Pip value for distance calculation
        """
        filtered = [l for l in levels if l.is_support == is_support]
        
        if is_support:
            # Support levels should be below current price
            below = [l for l in filtered if l.price < current_price]
            if not below:
                return None
            return max(below, key=lambda x: x.price)
        else:
            # Resistance levels should be above current price
            above = [l for l in filtered if l.price > current_price]
            if not above:
                return None
            return min(above, key=lambda x: x.price)
    
    def get_most_important_level(
        self,
        levels: List[SRLevel],
        current_price: float,
        is_support: bool,
        max_distance_pips: float = 100.0,
        pip_value: float = 0.0001
    ) -> Optional[SRLevel]:
        """
        Get the most important (strongest) support or resistance level within range.
        
        Args:
            levels: List of detected levels
            current_price: Current price
            is_support: True for support, False for resistance
            max_distance_pips: Maximum distance in pips to consider
            pip_value: Pip value
        """
        filtered = [l for l in levels if l.is_support == is_support]
        
        if is_support:
            # Support levels should be below current price
            candidates = [
                l for l in filtered 
                if l.price < current_price 
                and (current_price - l.price) / pip_value <= max_distance_pips
            ]
        else:
            # Resistance levels should be above current price
            candidates = [
                l for l in filtered 
                if l.price > current_price 
                and (l.price - current_price) / pip_value <= max_distance_pips
            ]
        
        if not candidates:
            return None
        
        # Return the one with highest strength score
        return max(candidates, key=lambda x: x.strength_score)
    
    def get_levels_by_timeframe(
        self,
        levels: List[SRLevel],
        timeframe: TimeframeContext
    ) -> List[SRLevel]:
        """Get levels filtered by timeframe context."""
        return [l for l in levels if l.timeframe_context == timeframe]
    
    def get_levels_for_chart(
        self,
        levels: List[SRLevel],
        current_price: float,
        max_levels: int = 10,
        pip_value: float = 0.0001
    ) -> List[Dict[str, Any]]:
        """
        Get levels formatted for chart display.
        
        Returns list of dicts with price, color, label, and strength info.
        """
        # Get top levels by strength
        top_levels = sorted(levels, key=lambda x: x.strength_score, reverse=True)[:max_levels]
        
        chart_levels = []
        for level in top_levels:
            color = self._get_level_color(level)
            chart_levels.append({
                "price": level.price,
                "color": color,
                "label": level.display_name,
                "is_support": level.is_support,
                "strength": level.strength_class.value,
                "strength_score": level.strength_score,
                "touches": level.touches,
                "distance_pips": level.distance_from_current
            })
        
        return chart_levels
    
    def _calculate_atr(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> float:
        """Calculate Average True Range."""
        if len(close) < self.atr_period + 1:
            return float(np.mean(high - low))
        
        tr = np.zeros(len(close))
        tr[0] = high[0] - low[0]
        
        for i in range(1, len(close)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, hc, lc)
        
        return float(np.mean(tr[-self.atr_period:]))
    
    def _detect_swing_levels(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        timestamps: Optional[List[datetime]],
        pip_value: float,
        atr: float
    ) -> List[SRLevel]:
        """Detect levels based on swing highs/lows."""
        levels = []
        
        swing_highs, swing_lows = self.swing_detector.detect(high, low)
        
        # Process swing highs (resistance) - swing_highs is list of Pattern objects
        for pattern in swing_highs:
            idx = pattern.index
            price = float(pattern.price_level)
            timeframe = self._determine_timeframe(idx, len(close), timestamps)
            
            levels.append(SRLevel(
                price=price,
                level_type=LevelType.SWING_HIGH,
                is_support=False,
                strength_score=0.0,  # Will be calculated later
                strength_class=LevelStrength.WEAK,
                touches=1,
                first_touch_index=idx,
                last_touch_index=idx,
                timeframe_context=timeframe
            ))
        
        # Process swing lows (support) - swing_lows is list of Pattern objects
        for pattern in swing_lows:
            idx = pattern.index
            price = float(pattern.price_level)
            timeframe = self._determine_timeframe(idx, len(close), timestamps)
            
            levels.append(SRLevel(
                price=price,
                level_type=LevelType.SWING_LOW,
                is_support=True,
                strength_score=0.0,
                strength_class=LevelStrength.WEAK,
                touches=1,
                first_touch_index=idx,
                last_touch_index=idx,
                timeframe_context=timeframe
            ))
        
        return levels
    
    def _detect_pivot_levels(
        self,
        open_prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        timestamps: Optional[List[datetime]],
        pip_value: float,
        atr: float
    ) -> List[SRLevel]:
        """Detect pivot point levels (daily)."""
        levels = []
        
        # Use last 24 candles for daily pivot (assuming hourly data)
        lookback = min(24, len(close) - 1)
        
        daily_high = float(np.max(high[-lookback:]))
        daily_low = float(np.min(low[-lookback:]))
        daily_close = float(close[-1])
        
        # Standard Pivot Point calculation
        pivot = (daily_high + daily_low + daily_close) / 3
        r1 = 2 * pivot - daily_low
        r2 = pivot + (daily_high - daily_low)
        r3 = daily_high + 2 * (pivot - daily_low)
        s1 = 2 * pivot - daily_high
        s2 = pivot - (daily_high - daily_low)
        s3 = daily_low - 2 * (daily_high - pivot)
        
        pivot_data = [
            (pivot, LevelType.PIVOT_POINT, None),  # Pivot can be both
            (r1, LevelType.PIVOT_R1, False),
            (r2, LevelType.PIVOT_R2, False),
            (r3, LevelType.PIVOT_R3, False),
            (s1, LevelType.PIVOT_S1, True),
            (s2, LevelType.PIVOT_S2, True),
            (s3, LevelType.PIVOT_S3, True),
        ]
        
        current_price = float(close[-1])
        
        for price, level_type, is_support in pivot_data:
            if is_support is None:
                is_support = price < current_price
            
            levels.append(SRLevel(
                price=price,
                level_type=level_type,
                is_support=is_support,
                strength_score=0.0,
                strength_class=LevelStrength.MODERATE,
                touches=0,
                first_touch_index=len(close) - lookback,
                last_touch_index=len(close) - 1,
                timeframe_context=TimeframeContext.DAILY
            ))
        
        return levels
    
    def _detect_round_numbers(
        self,
        current_price: float,
        pip_value: float,
        atr: float
    ) -> List[SRLevel]:
        """Detect psychological round number levels."""
        levels = []
        
        # Determine round number interval based on price
        if current_price > 100:  # JPY pairs
            interval = 1.0
        elif current_price > 10:
            interval = 0.5
        else:
            interval = 0.01  # Standard pairs
        
        # Find nearby round numbers
        base = round(current_price / interval) * interval
        
        for i in range(-3, 4):
            price = base + i * interval
            is_support = price < current_price
            
            levels.append(SRLevel(
                price=price,
                level_type=LevelType.ROUND_NUMBER,
                is_support=is_support,
                strength_score=0.0,
                strength_class=LevelStrength.WEAK,
                touches=0,
                first_touch_index=0,
                last_touch_index=0,
                timeframe_context=TimeframeContext.DAILY
            ))
        
        return levels
    
    def _detect_weekly_map_levels(
        self,
        open_prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        timestamps: Optional[List[datetime]],
        pip_value: float,
        atr: float
    ) -> List[SRLevel]:
        """
        Detect Weekly Map levels.
        
        Weekly Map includes:
        - Weekly Pivot Points
        - Weekly High/Low
        - Fibonacci retracements of weekly range
        """
        levels = []
        
        # Use last 168 candles for weekly data (assuming hourly)
        lookback = min(168, len(close) - 1)
        
        weekly_high = float(np.max(high[-lookback:]))
        weekly_low = float(np.min(low[-lookback:]))
        weekly_open = float(open_prices[-lookback])
        weekly_close = float(close[-1])
        weekly_range = weekly_high - weekly_low
        
        current_price = float(close[-1])
        
        # Weekly Pivot
        weekly_pivot = (weekly_high + weekly_low + weekly_close) / 3
        
        # Weekly Pivot levels
        wr1 = 2 * weekly_pivot - weekly_low
        wr2 = weekly_pivot + weekly_range
        wr3 = weekly_high + 2 * (weekly_pivot - weekly_low)
        ws1 = 2 * weekly_pivot - weekly_high
        ws2 = weekly_pivot - weekly_range
        ws3 = weekly_low - 2 * (weekly_high - weekly_pivot)
        
        # Fibonacci levels
        fib_236 = weekly_high - 0.236 * weekly_range
        fib_382 = weekly_high - 0.382 * weekly_range
        fib_500 = weekly_high - 0.500 * weekly_range
        fib_618 = weekly_high - 0.618 * weekly_range
        fib_786 = weekly_high - 0.786 * weekly_range
        
        weekly_levels_data = [
            (weekly_high, LevelType.WEEKLY_HIGH, False, "Weekly High"),
            (weekly_low, LevelType.WEEKLY_LOW, True, "Weekly Low"),
            (weekly_pivot, LevelType.PIVOT_POINT, weekly_pivot < current_price, "Weekly Pivot"),
            (wr1, LevelType.PIVOT_R1, False, "Weekly R1"),
            (wr2, LevelType.PIVOT_R2, False, "Weekly R2"),
            (ws1, LevelType.PIVOT_S1, True, "Weekly S1"),
            (ws2, LevelType.PIVOT_S2, True, "Weekly S2"),
            (fib_236, LevelType.FIBONACCI, fib_236 < current_price, "Fib 23.6%"),
            (fib_382, LevelType.FIBONACCI, fib_382 < current_price, "Fib 38.2%"),
            (fib_500, LevelType.FIBONACCI, fib_500 < current_price, "Fib 50%"),
            (fib_618, LevelType.FIBONACCI, fib_618 < current_price, "Fib 61.8%"),
            (fib_786, LevelType.FIBONACCI, fib_786 < current_price, "Fib 78.6%"),
        ]
        
        for price, level_type, is_support, name in weekly_levels_data:
            levels.append(SRLevel(
                price=price,
                level_type=level_type,
                is_support=is_support,
                strength_score=0.0,
                strength_class=LevelStrength.MODERATE,
                touches=0,
                first_touch_index=len(close) - lookback,
                last_touch_index=len(close) - 1,
                timeframe_context=TimeframeContext.WEEKLY,
                display_name=f"{name} @ {price:.5f}"
            ))
        
        return levels
    
    def _merge_similar_levels(
        self,
        levels: List[SRLevel],
        pip_value: float
    ) -> List[SRLevel]:
        """Merge levels that are within tolerance of each other."""
        if not levels:
            return []
        
        tolerance = self.level_tolerance_pips * pip_value
        
        # Sort by price
        sorted_levels = sorted(levels, key=lambda x: x.price)
        merged = []
        
        current_group = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            if abs(level.price - current_group[0].price) <= tolerance:
                current_group.append(level)
            else:
                # Merge current group
                merged.append(self._merge_level_group(current_group))
                current_group = [level]
        
        # Don't forget the last group
        merged.append(self._merge_level_group(current_group))
        
        return merged
    
    def _merge_level_group(self, group: List[SRLevel]) -> SRLevel:
        """Merge a group of similar levels into one."""
        if len(group) == 1:
            return group[0]
        
        # Average price
        avg_price = np.mean([l.price for l in group])
        
        # Take the strongest level type (prefer swing over pivot over round)
        priority = {
            LevelType.SWING_HIGH: 10, LevelType.SWING_LOW: 10,
            LevelType.WEEKLY_HIGH: 9, LevelType.WEEKLY_LOW: 9,
            LevelType.DAILY_HIGH: 8, LevelType.DAILY_LOW: 8,
            LevelType.PIVOT_POINT: 7,
            LevelType.FIBONACCI: 6,
            LevelType.PIVOT_R1: 5, LevelType.PIVOT_S1: 5,
            LevelType.PIVOT_R2: 4, LevelType.PIVOT_S2: 4,
            LevelType.PIVOT_R3: 3, LevelType.PIVOT_S3: 3,
            LevelType.ROUND_NUMBER: 2,
        }
        
        best_level = max(group, key=lambda x: priority.get(x.level_type, 0))
        
        # Sum touches
        total_touches = sum(l.touches for l in group)
        
        # Combine metadata
        has_pin_bar = any(l.has_pin_bar for l in group)
        has_leg_rejection = any(l.has_leg_rejection for l in group)
        
        # Best timeframe (prefer weekly > daily > hourly)
        timeframe_priority = {
            TimeframeContext.WEEKLY: 3,
            TimeframeContext.DAILY: 2,
            TimeframeContext.HOURLY: 1
        }
        best_timeframe = max(group, key=lambda x: timeframe_priority.get(x.timeframe_context, 0)).timeframe_context
        
        return SRLevel(
            price=float(avg_price),
            level_type=best_level.level_type,
            is_support=best_level.is_support,
            strength_score=0.0,
            strength_class=LevelStrength.WEAK,
            touches=total_touches,
            first_touch_index=min(l.first_touch_index for l in group),
            last_touch_index=max(l.last_touch_index for l in group),
            timeframe_context=best_timeframe,
            has_pin_bar=has_pin_bar,
            has_leg_rejection=has_leg_rejection
        )
    
    def _calculate_strength_scores(
        self,
        levels: List[SRLevel],
        open_prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        pip_value: float,
        atr: float,
        current_price: float
    ) -> List[SRLevel]:
        """Calculate strength scores for all levels."""
        tolerance = self.level_tolerance_pips * pip_value
        
        for level in levels:
            score = 0.0
            
            # 1. Touch count (max 25 points)
            touches = self._count_touches(level.price, high, low, tolerance)
            level.touches = touches
            score += min(touches * 5, 25)
            
            # 2. ATR significance (max 20 points)
            distance_from_current = abs(level.price - current_price)
            atr_ratio = distance_from_current / atr if atr > 0 else 0
            level.atr_significance = atr_ratio
            if 0.5 <= atr_ratio <= 2.0:
                score += 20
            elif 0.25 <= atr_ratio <= 3.0:
                score += 10
            
            # 3. Pin bar at level (max 15 points)
            if self._has_pin_bar_at_level(level.price, open_prices, high, low, close, tolerance, pip_value):
                level.has_pin_bar = True
                score += 15
            
            # 4. Leg rejection at level (max 15 points)
            if self._has_leg_rejection(level.price, high, low, close, tolerance, pip_value):
                level.has_leg_rejection = True
                score += 15
            
            # 5. Level type bonus (max 15 points)
            type_bonus = {
                LevelType.WEEKLY_HIGH: 15, LevelType.WEEKLY_LOW: 15,
                LevelType.DAILY_HIGH: 12, LevelType.DAILY_LOW: 12,
                LevelType.SWING_HIGH: 10, LevelType.SWING_LOW: 10,
                LevelType.PIVOT_POINT: 8,
                LevelType.FIBONACCI: 7,
                LevelType.PIVOT_R1: 6, LevelType.PIVOT_S1: 6,
                LevelType.ROUND_NUMBER: 5,
            }
            score += type_bonus.get(level.level_type, 0)
            
            # 6. Recency bonus (max 10 points)
            recency = (len(close) - level.last_touch_index) / len(close)
            score += max(0, 10 * (1 - recency))
            
            # Normalize to 0-100
            level.strength_score = min(100, score)
            
            # Classify strength
            if level.strength_score >= 80:
                level.strength_class = LevelStrength.VERY_STRONG
            elif level.strength_score >= 60:
                level.strength_class = LevelStrength.STRONG
            elif level.strength_score >= 30:
                level.strength_class = LevelStrength.MODERATE
            else:
                level.strength_class = LevelStrength.WEAK
            
            # Update display name
            direction = "Support" if level.is_support else "Resistance"
            level.display_name = f"{direction} @ {level.price:.5f} ({level.strength_class.value}, {level.touches} touches)"
        
        return levels
    
    def _count_touches(
        self,
        level_price: float,
        high: np.ndarray,
        low: np.ndarray,
        tolerance: float
    ) -> int:
        """Count how many times price touched a level."""
        touches = 0
        
        for i in range(len(high)):
            # Check if candle touched the level
            if low[i] - tolerance <= level_price <= high[i] + tolerance:
                touches += 1
        
        return touches
    
    def _has_pin_bar_at_level(
        self,
        level_price: float,
        open_prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        tolerance: float,
        pip_value: float
    ) -> bool:
        """Check if there's a pin bar formation at the level."""
        pin_bars = self.pin_bar_detector.detect(
            open_prices, high, low, close, pip_value, lookback=50
        )
        
        for pb in pin_bars:
            idx = pb.index
            # Check if pin bar is at the level
            if low[idx] - tolerance <= level_price <= high[idx] + tolerance:
                return True
        
        return False
    
    def _has_leg_rejection(
        self,
        level_price: float,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        tolerance: float,
        pip_value: float
    ) -> bool:
        """Check if there's a leg rejection at the level."""
        # Simple check: price approached level and reversed
        for i in range(5, len(close)):
            # Check if price touched level
            if low[i] - tolerance <= level_price <= high[i] + tolerance:
                # Check for reversal in next few candles
                if i + 3 < len(close):
                    if level_price < close[i]:  # Level is below (support)
                        if close[i+3] > close[i]:  # Price went up
                            return True
                    else:  # Level is above (resistance)
                        if close[i+3] < close[i]:  # Price went down
                            return True
        
        return False
    
    def _determine_timeframe(
        self,
        index: int,
        total_length: int,
        timestamps: Optional[List[datetime]]
    ) -> TimeframeContext:
        """Determine timeframe context based on index position."""
        # Calculate how far back this index is
        bars_back = total_length - index
        
        if bars_back <= 1:  # Last hour
            return TimeframeContext.HOURLY
        elif bars_back <= 24:  # Last day
            return TimeframeContext.DAILY
        else:
            return TimeframeContext.WEEKLY
    
    def _get_level_color(self, level: SRLevel) -> str:
        """Get color for chart display based on level properties."""
        if level.is_support:
            if level.strength_class == LevelStrength.VERY_STRONG:
                return "#00FF00"  # Bright green
            elif level.strength_class == LevelStrength.STRONG:
                return "#32CD32"  # Lime green
            elif level.strength_class == LevelStrength.MODERATE:
                return "#90EE90"  # Light green
            else:
                return "#98FB98"  # Pale green
        else:
            if level.strength_class == LevelStrength.VERY_STRONG:
                return "#FF0000"  # Bright red
            elif level.strength_class == LevelStrength.STRONG:
                return "#DC143C"  # Crimson
            elif level.strength_class == LevelStrength.MODERATE:
                return "#FF6347"  # Tomato
            else:
                return "#FFA07A"  # Light salmon
    
    def calculate_weekly_map(
        self,
        open_prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> WeeklyMapLevels:
        """
        Calculate complete Weekly Map levels.
        
        Returns WeeklyMapLevels dataclass with all pivot and fibonacci levels.
        """
        lookback = min(168, len(close) - 1)
        
        weekly_high = float(np.max(high[-lookback:]))
        weekly_low = float(np.min(low[-lookback:]))
        weekly_open = float(open_prices[-lookback])
        weekly_close = float(close[-1])
        weekly_range = weekly_high - weekly_low
        
        # Pivot calculation
        pivot = (weekly_high + weekly_low + weekly_close) / 3
        r1 = 2 * pivot - weekly_low
        r2 = pivot + weekly_range
        r3 = weekly_high + 2 * (pivot - weekly_low)
        s1 = 2 * pivot - weekly_high
        s2 = pivot - weekly_range
        s3 = weekly_low - 2 * (weekly_high - pivot)
        
        # Fibonacci levels
        fib_236 = weekly_high - 0.236 * weekly_range
        fib_382 = weekly_high - 0.382 * weekly_range
        fib_500 = weekly_high - 0.500 * weekly_range
        fib_618 = weekly_high - 0.618 * weekly_range
        fib_786 = weekly_high - 0.786 * weekly_range
        
        return WeeklyMapLevels(
            pivot=pivot,
            r1=r1, r2=r2, r3=r3,
            s1=s1, s2=s2, s3=s3,
            fib_236=fib_236,
            fib_382=fib_382,
            fib_500=fib_500,
            fib_618=fib_618,
            fib_786=fib_786,
            weekly_high=weekly_high,
            weekly_low=weekly_low,
            weekly_open=weekly_open,
            weekly_close=weekly_close
        )


# Convenience function
def detect_sr_levels(
    open_prices: np.ndarray,
    high_prices: np.ndarray,
    low_prices: np.ndarray,
    close_prices: np.ndarray,
    pip_value: float = 0.0001,
    timestamps: Optional[List[datetime]] = None
) -> List[SRLevel]:
    """
    Convenience function to detect support/resistance levels.
    
    Returns list of SRLevel objects sorted by strength.
    """
    detector = SupportResistanceDetector()
    return detector.detect_all_levels(
        open_prices, high_prices, low_prices, close_prices,
        timestamps=timestamps, pip_value=pip_value
    )


if __name__ == "__main__":
    # Test with sample data
    np.random.seed(42)
    n = 200
    
    base_price = 1.1000
    returns = np.random.randn(n) * 0.001
    close = base_price + np.cumsum(returns)
    high = close + np.abs(np.random.randn(n) * 0.0005)
    low = close - np.abs(np.random.randn(n) * 0.0005)
    open_prices = close - returns + np.random.randn(n) * 0.0002
    
    detector = SupportResistanceDetector()
    levels = detector.detect_all_levels(
        open_prices, high, low, close,
        pip_value=0.0001
    )
    
    print("=" * 60)
    print("SUPPORT & RESISTANCE LEVELS")
    print("=" * 60)
    
    print("\nTop 10 Levels by Strength:")
    for i, level in enumerate(levels[:10], 1):
        print(f"{i}. {level.display_name}")
        print(f"   Type: {level.level_type.value}, Score: {level.strength_score:.1f}")
        print(f"   Pin Bar: {level.has_pin_bar}, Leg Rejection: {level.has_leg_rejection}")
    
    current_price = float(close[-1])
    print(f"\nCurrent Price: {current_price:.5f}")
    
    nearest_support = detector.get_nearest_level(levels, current_price, is_support=True)
    nearest_resistance = detector.get_nearest_level(levels, current_price, is_support=False)
    
    if nearest_support:
        print(f"\nNearest Support: {nearest_support.price:.5f} ({nearest_support.strength_class.value})")
    if nearest_resistance:
        print(f"Nearest Resistance: {nearest_resistance.price:.5f} ({nearest_resistance.strength_class.value})")
    
    most_important_support = detector.get_most_important_level(levels, current_price, is_support=True)
    most_important_resistance = detector.get_most_important_level(levels, current_price, is_support=False)
    
    if most_important_support:
        print(f"\nMost Important Support: {most_important_support.price:.5f} (Score: {most_important_support.strength_score:.1f})")
    if most_important_resistance:
        print(f"Most Important Resistance: {most_important_resistance.price:.5f} (Score: {most_important_resistance.strength_score:.1f})")
