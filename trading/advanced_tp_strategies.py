"""
Advanced Take Profit Strategies Module
ماژول استراتژی‌های پیشرفته حد سود

Strategies:
===========

FREE Strategies:
1. Fixed Pips (پیپ ثابت) - Simple fixed pip target
2. ATR-Based (ضرایب ATR) - Dynamic TP based on ATR multiplier
3. Key Levels - Nearest (نزدیک‌ترین سطح) - TP at nearest S/R level
4. Risk/Reward Fixed (R/R ثابت) - Fixed R/R ratio

PREMIUM Strategies:
5. Key Levels - Selectable (انتخاب سطح) - User selects level from chart
6. Stepped R/R (R/R پلکانی) - Multiple TPs at different R/R levels
7. Leg-Based (بر اساس لگ) - TP based on equal leg projection

Display Names for UI:
- "Smart Pips" - Fixed Pips
- "Volatility Target" - ATR-Based
- "Level Hunter" - Key Levels (Nearest)
- "Level Selector Pro" - Key Levels (Selectable) [PREMIUM]
- "Classic R/R" - Risk/Reward Fixed
- "Ladder Exit" - Stepped R/R [PREMIUM]
- "Leg Projection" - Leg-Based [PREMIUM]
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import numpy as np

try:
    from .pattern_detection import LegDetector, Leg
    from .support_resistance import SupportResistanceDetector, SRLevel, LevelStrength
except ImportError:
    from pattern_detection import LegDetector, Leg
    from support_resistance import SupportResistanceDetector, SRLevel, LevelStrength


class AdvancedTPType(str, Enum):
    """Types of advanced take profit strategies"""
    FIXED_PIPS = "fixed_pips"
    ATR_BASED = "atr_based"
    KEY_LEVELS_NEAREST = "key_levels_nearest"
    KEY_LEVELS_SELECTABLE = "key_levels_selectable"
    RISK_REWARD_FIXED = "risk_reward_fixed"
    STEPPED_RR = "stepped_rr"
    LEG_BASED = "leg_based"


# Display names for UI
TP_DISPLAY_NAMES = {
    AdvancedTPType.FIXED_PIPS: "Smart Pips",
    AdvancedTPType.ATR_BASED: "Volatility Target",
    AdvancedTPType.KEY_LEVELS_NEAREST: "Level Hunter",
    AdvancedTPType.KEY_LEVELS_SELECTABLE: "Level Selector Pro",
    AdvancedTPType.RISK_REWARD_FIXED: "Classic R/R",
    AdvancedTPType.STEPPED_RR: "Ladder Exit",
    AdvancedTPType.LEG_BASED: "Leg Projection",
}


@dataclass
class TPCalculationResult:
    """Result of take profit calculation"""
    take_profit: float
    tp_pips: float
    strategy_used: AdvancedTPType
    fallback_used: bool = False
    
    # For stepped exits
    is_stepped: bool = False
    exit_levels: List[Dict[str, Any]] = field(default_factory=list)
    # Format: [{"price": 1.1050, "percentage": 50, "rr_ratio": 2.0}, ...]
    
    # Additional info
    level_info: Optional[Dict[str, Any]] = None
    leg_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "take_profit": self.take_profit,
            "tp_pips": self.tp_pips,
            "strategy_used": self.strategy_used.value,
            "fallback_used": self.fallback_used,
            "is_stepped": self.is_stepped,
            "exit_levels": self.exit_levels,
            "level_info": self.level_info,
            "leg_info": self.leg_info
        }


@dataclass
class SteppedExitLevel:
    """A single exit level in stepped R/R strategy"""
    price: float
    percentage: float  # Percentage of position to close (e.g., 50%)
    rr_ratio: float    # R/R ratio for this level


class BaseAdvancedTPStrategy(ABC):
    """Base class for all advanced TP strategies"""
    
    STRATEGY_TYPE: AdvancedTPType
    DISPLAY_NAME: str
    DESCRIPTION: str
    IS_PREMIUM: bool = False
    
    @abstractmethod
    def calculate(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> TPCalculationResult:
        """Calculate take profit level(s)"""
        pass
    
    def _calculate_pips(
        self,
        price1: float,
        price2: float,
        pip_value: float
    ) -> float:
        """Calculate pip distance between two prices"""
        return abs(price1 - price2) / pip_value


class FixedPipsTP(BaseAdvancedTPStrategy):
    """
    Fixed Pips Take Profit
    حد سود بر اساس پیپ ثابت
    
    Display Name: "Smart Pips"
    """
    
    STRATEGY_TYPE = AdvancedTPType.FIXED_PIPS
    DISPLAY_NAME = "Smart Pips"
    DESCRIPTION = "Simple fixed pip distance target from entry"
    IS_PREMIUM = False
    
    def __init__(self, pips: float = 50.0):
        self.pips = pips
    
    def calculate(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> TPCalculationResult:
        
        if is_buy:
            take_profit = entry_price + (self.pips * pip_value)
        else:
            take_profit = entry_price - (self.pips * pip_value)
        
        return TPCalculationResult(
            take_profit=take_profit,
            tp_pips=self.pips,
            strategy_used=self.STRATEGY_TYPE,
            fallback_used=False
        )


class ATRBasedTP(BaseAdvancedTPStrategy):
    """
    ATR-Based Take Profit
    حد سود بر اساس ضرایب ATR
    
    Display Name: "Volatility Target"
    """
    
    STRATEGY_TYPE = AdvancedTPType.ATR_BASED
    DISPLAY_NAME = "Volatility Target"
    DESCRIPTION = "Dynamic TP based on market volatility (ATR x multiplier)"
    IS_PREMIUM = False
    
    def __init__(self, multiplier: float = 3.0, period: int = 14):
        self.multiplier = multiplier
        self.period = period
    
    def calculate(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> TPCalculationResult:
        
        high = data.get("high", np.array([]))
        low = data.get("low", np.array([]))
        close = data.get("close", np.array([]))
        
        # Calculate ATR
        atr = self._calculate_atr(high, low, close)
        
        tp_distance = atr * self.multiplier
        
        if is_buy:
            take_profit = entry_price + tp_distance
        else:
            take_profit = entry_price - tp_distance
        
        tp_pips = tp_distance / pip_value
        
        return TPCalculationResult(
            take_profit=take_profit,
            tp_pips=tp_pips,
            strategy_used=self.STRATEGY_TYPE,
            fallback_used=False,
            level_info={"atr": atr, "multiplier": self.multiplier}
        )
    
    def _calculate_atr(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> float:
        """Calculate Average True Range"""
        if len(close) < self.period + 1:
            return float(np.mean(high - low)) if len(high) > 0 else 0.001
        
        tr = np.zeros(len(close))
        tr[0] = high[0] - low[0]
        
        for i in range(1, len(close)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, hc, lc)
        
        return float(np.mean(tr[-self.period:]))


class KeyLevelsNearestTP(BaseAdvancedTPStrategy):
    """
    Key Levels - Nearest Take Profit
    حد سود بر اساس نزدیک‌ترین سطح مهم
    
    Display Name: "Level Hunter"
    """
    
    STRATEGY_TYPE = AdvancedTPType.KEY_LEVELS_NEAREST
    DISPLAY_NAME = "Level Hunter"
    DESCRIPTION = "TP at the nearest significant support/resistance level"
    IS_PREMIUM = False
    
    def __init__(
        self,
        min_distance_pips: float = 10.0,
        buffer_pips: float = 5.0
    ):
        self.min_distance_pips = min_distance_pips
        self.buffer_pips = buffer_pips
        self.sr_detector = SupportResistanceDetector()
    
    def calculate(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> TPCalculationResult:
        
        open_prices = data.get("open", np.array([]))
        high = data.get("high", np.array([]))
        low = data.get("low", np.array([]))
        close = data.get("close", np.array([]))
        
        if len(close) < 20:
            return self._fallback_tp(entry_price, stop_loss, is_buy, pip_value)
        
        # Detect S/R levels
        levels = self.sr_detector.detect_all_levels(
            open_prices, high, low, close,
            pip_value=pip_value,
            current_price=entry_price
        )
        
        # For buy: find nearest resistance above entry
        # For sell: find nearest support below entry
        target_level = self._find_nearest_target(
            levels, entry_price, is_buy, pip_value
        )
        
        if target_level is None:
            return self._fallback_tp(entry_price, stop_loss, is_buy, pip_value)
        
        # Apply buffer (don't set TP exactly at level)
        if is_buy:
            take_profit = target_level.price - (self.buffer_pips * pip_value)
        else:
            take_profit = target_level.price + (self.buffer_pips * pip_value)
        
        tp_pips = self._calculate_pips(entry_price, take_profit, pip_value)
        
        return TPCalculationResult(
            take_profit=take_profit,
            tp_pips=tp_pips,
            strategy_used=self.STRATEGY_TYPE,
            fallback_used=False,
            level_info={
                "level_price": target_level.price,
                "level_type": target_level.level_type.value,
                "strength": target_level.strength_class.value,
                "strength_score": target_level.strength_score
            }
        )
    
    def _find_nearest_target(
        self,
        levels: List[SRLevel],
        entry_price: float,
        is_buy: bool,
        pip_value: float
    ) -> Optional[SRLevel]:
        """Find the nearest valid target level"""
        min_distance = self.min_distance_pips * pip_value
        
        if is_buy:
            # Find resistance levels above entry
            candidates = [
                l for l in levels 
                if not l.is_support 
                and l.price > entry_price + min_distance
            ]
            if candidates:
                return min(candidates, key=lambda x: x.price)
        else:
            # Find support levels below entry
            candidates = [
                l for l in levels 
                if l.is_support 
                and l.price < entry_price - min_distance
            ]
            if candidates:
                return max(candidates, key=lambda x: x.price)
        
        return None
    
    def _fallback_tp(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        pip_value: float
    ) -> TPCalculationResult:
        """Fallback to 2:1 R/R if no level found"""
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * 2
        
        if is_buy:
            take_profit = entry_price + tp_distance
        else:
            take_profit = entry_price - tp_distance
        
        return TPCalculationResult(
            take_profit=take_profit,
            tp_pips=tp_distance / pip_value,
            strategy_used=self.STRATEGY_TYPE,
            fallback_used=True
        )


class KeyLevelsSelectableTP(BaseAdvancedTPStrategy):
    """
    Key Levels - Selectable Take Profit (PREMIUM)
    حد سود با قابلیت انتخاب سطح از روی چارت
    
    Display Name: "Level Selector Pro"
    """
    
    STRATEGY_TYPE = AdvancedTPType.KEY_LEVELS_SELECTABLE
    DISPLAY_NAME = "Level Selector Pro"
    DESCRIPTION = "Select your TP level from chart based on strength"
    IS_PREMIUM = True
    
    def __init__(
        self,
        selected_level_price: Optional[float] = None,
        min_strength: LevelStrength = LevelStrength.MODERATE,
        buffer_pips: float = 5.0
    ):
        self.selected_level_price = selected_level_price
        self.min_strength = min_strength
        self.buffer_pips = buffer_pips
        self.sr_detector = SupportResistanceDetector()
    
    def get_available_levels(
        self,
        data: Dict[str, Any],
        entry_price: float,
        is_buy: bool,
        pip_value: float = 0.0001
    ) -> List[Dict[str, Any]]:
        """
        Get list of available levels for user selection.
        Returns levels formatted for UI display.
        """
        open_prices = data.get("open", np.array([]))
        high = data.get("high", np.array([]))
        low = data.get("low", np.array([]))
        close = data.get("close", np.array([]))
        
        if len(close) < 20:
            return []
        
        levels = self.sr_detector.detect_all_levels(
            open_prices, high, low, close,
            pip_value=pip_value,
            current_price=entry_price
        )
        
        # Filter by direction and minimum strength
        strength_order = {
            LevelStrength.WEAK: 0,
            LevelStrength.MODERATE: 1,
            LevelStrength.STRONG: 2,
            LevelStrength.VERY_STRONG: 3
        }
        min_strength_val = strength_order[self.min_strength]
        
        if is_buy:
            # Resistance levels above entry
            filtered = [
                l for l in levels 
                if not l.is_support 
                and l.price > entry_price
                and strength_order[l.strength_class] >= min_strength_val
            ]
        else:
            # Support levels below entry
            filtered = [
                l for l in levels 
                if l.is_support 
                and l.price < entry_price
                and strength_order[l.strength_class] >= min_strength_val
            ]
        
        # Sort by distance from entry
        filtered.sort(key=lambda x: abs(x.price - entry_price))
        
        # Format for UI
        return [
            {
                "price": l.price,
                "display_name": l.display_name,
                "strength": l.strength_class.value,
                "strength_score": l.strength_score,
                "distance_pips": abs(l.price - entry_price) / pip_value,
                "level_type": l.level_type.value,
                "touches": l.touches
            }
            for l in filtered[:10]  # Max 10 levels
        ]
    
    def calculate(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> TPCalculationResult:
        
        if self.selected_level_price is None:
            # If no level selected, use nearest strong level
            return KeyLevelsNearestTP(buffer_pips=self.buffer_pips).calculate(
                entry_price, stop_loss, is_buy, data, pip_value
            )
        
        # Use selected level
        if is_buy:
            take_profit = self.selected_level_price - (self.buffer_pips * pip_value)
        else:
            take_profit = self.selected_level_price + (self.buffer_pips * pip_value)
        
        tp_pips = self._calculate_pips(entry_price, take_profit, pip_value)
        
        return TPCalculationResult(
            take_profit=take_profit,
            tp_pips=tp_pips,
            strategy_used=self.STRATEGY_TYPE,
            fallback_used=False,
            level_info={
                "selected_price": self.selected_level_price,
                "buffer_pips": self.buffer_pips
            }
        )


class RiskRewardFixedTP(BaseAdvancedTPStrategy):
    """
    Fixed Risk/Reward Take Profit
    حد سود بر اساس نسبت ریسک به ریوارد ثابت
    
    Display Name: "Classic R/R"
    """
    
    STRATEGY_TYPE = AdvancedTPType.RISK_REWARD_FIXED
    DISPLAY_NAME = "Classic R/R"
    DESCRIPTION = "TP based on fixed risk-to-reward ratio"
    IS_PREMIUM = False
    
    def __init__(self, rr_ratio: float = 2.0):
        self.rr_ratio = rr_ratio
    
    def calculate(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> TPCalculationResult:
        
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * self.rr_ratio
        
        if is_buy:
            take_profit = entry_price + tp_distance
        else:
            take_profit = entry_price - tp_distance
        
        tp_pips = tp_distance / pip_value
        
        return TPCalculationResult(
            take_profit=take_profit,
            tp_pips=tp_pips,
            strategy_used=self.STRATEGY_TYPE,
            fallback_used=False,
            level_info={"rr_ratio": self.rr_ratio}
        )


class SteppedRRTP(BaseAdvancedTPStrategy):
    """
    Stepped Risk/Reward Take Profit (PREMIUM)
    حد سود پلکانی با چند مرحله خروج
    
    Display Name: "Ladder Exit"
    
    Default: 50% at R/R 2, 30% at R/R 3, 20% at R/R 4
    """
    
    STRATEGY_TYPE = AdvancedTPType.STEPPED_RR
    DISPLAY_NAME = "Ladder Exit"
    DESCRIPTION = "Multiple exit levels at different R/R ratios"
    IS_PREMIUM = True
    
    def __init__(
        self,
        exit_steps: Optional[List[Tuple[float, float]]] = None
    ):
        """
        Args:
            exit_steps: List of (percentage, rr_ratio) tuples
                       Default: [(50, 2.0), (30, 3.0), (20, 4.0)]
        """
        if exit_steps is None:
            self.exit_steps = [(50.0, 2.0), (30.0, 3.0), (20.0, 4.0)]
        else:
            self.exit_steps = exit_steps
        
        # Validate percentages sum to 100
        total_pct = sum(step[0] for step in self.exit_steps)
        if abs(total_pct - 100.0) > 0.01:
            # Normalize
            self.exit_steps = [
                (step[0] * 100 / total_pct, step[1]) 
                for step in self.exit_steps
            ]
    
    def calculate(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> TPCalculationResult:
        
        sl_distance = abs(entry_price - stop_loss)
        
        exit_levels = []
        for percentage, rr_ratio in self.exit_steps:
            tp_distance = sl_distance * rr_ratio
            
            if is_buy:
                level_price = entry_price + tp_distance
            else:
                level_price = entry_price - tp_distance
            
            exit_levels.append({
                "price": level_price,
                "percentage": percentage,
                "rr_ratio": rr_ratio,
                "pips": tp_distance / pip_value
            })
        
        # Primary TP is the first exit level
        primary_tp = exit_levels[0]["price"]
        primary_pips = exit_levels[0]["pips"]
        
        return TPCalculationResult(
            take_profit=primary_tp,
            tp_pips=primary_pips,
            strategy_used=self.STRATEGY_TYPE,
            fallback_used=False,
            is_stepped=True,
            exit_levels=exit_levels,
            level_info={"steps": len(exit_levels)}
        )


class LegBasedTP(BaseAdvancedTPStrategy):
    """
    Leg-Based Take Profit (PREMIUM)
    حد سود بر اساس لگ‌های حرکتی هم‌اندازه
    
    Display Name: "Leg Projection"
    
    Logic:
    - Find the last valid leg in trade direction
    - Leg must be larger than its correction
    - Leg must have at least 3 candles
    - Project equal distance from correction end
    """
    
    STRATEGY_TYPE = AdvancedTPType.LEG_BASED
    DISPLAY_NAME = "Leg Projection"
    DESCRIPTION = "TP based on equal leg projection from correction"
    IS_PREMIUM = True
    
    def __init__(
        self,
        min_leg_candles: int = 3,
        min_leg_pips: float = 15.0,
        projection_ratio: float = 1.0  # 1.0 = equal leg, 1.618 = fib extension
    ):
        self.min_leg_candles = min_leg_candles
        self.min_leg_pips = min_leg_pips
        self.projection_ratio = projection_ratio
        self.leg_detector = LegDetector(
            min_leg_pips=min_leg_pips,
            min_leg_candles=min_leg_candles
        )
    
    def calculate(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> TPCalculationResult:
        
        open_prices = data.get("open", np.array([]))
        high = data.get("high", np.array([]))
        low = data.get("low", np.array([]))
        close = data.get("close", np.array([]))
        
        if len(close) < 20:
            return self._fallback_tp(entry_price, stop_loss, is_buy, pip_value)
        
        # Detect legs
        legs = self.leg_detector.detect_legs(
            open_prices, high, low, close, pip_value
        )
        
        if not legs:
            return self._fallback_tp(entry_price, stop_loss, is_buy, pip_value)
        
        # Find valid leg in trade direction
        target_direction = "bullish" if is_buy else "bearish"
        valid_leg = self._find_valid_leg(legs, target_direction, pip_value)
        
        if valid_leg is None:
            return self._fallback_tp(entry_price, stop_loss, is_buy, pip_value)
        
        # Calculate projection
        leg_size = valid_leg.size_pips * pip_value
        projected_distance = leg_size * self.projection_ratio
        
        # Project from current price (assuming we're at correction end)
        if is_buy:
            take_profit = entry_price + projected_distance
        else:
            take_profit = entry_price - projected_distance
        
        tp_pips = projected_distance / pip_value
        
        return TPCalculationResult(
            take_profit=take_profit,
            tp_pips=tp_pips,
            strategy_used=self.STRATEGY_TYPE,
            fallback_used=False,
            leg_info={
                "leg_size_pips": valid_leg.size_pips,
                "leg_direction": valid_leg.direction,
                "leg_start_index": valid_leg.start_index,
                "leg_end_index": valid_leg.end_index,
                "projection_ratio": self.projection_ratio
            }
        )
    
    def _find_valid_leg(
        self,
        legs: List[Leg],
        direction: str,
        pip_value: float
    ) -> Optional[Leg]:
        """
        Find a valid leg for projection.
        
        Valid leg criteria:
        1. In the correct direction
        2. Has at least min_leg_candles
        3. Larger than its correction (if correction exists)
        """
        # Filter by direction
        direction_legs = [l for l in legs if l.direction == direction]
        
        if not direction_legs:
            return None
        
        # Find legs with valid corrections
        for i in range(len(direction_legs) - 1, -1, -1):
            leg = direction_legs[i]
            
            # Check minimum candles
            leg_candles = leg.end_index - leg.start_index + 1
            if leg_candles < self.min_leg_candles:
                continue
            
            # Check minimum size
            if leg.size_pips < self.min_leg_pips:
                continue
            
            # Check if leg is larger than correction
            # Find the next leg (correction) if exists
            leg_idx = legs.index(leg)
            if leg_idx + 1 < len(legs):
                correction = legs[leg_idx + 1]
                # Correction should be smaller
                if correction.size_pips < leg.size_pips:
                    return leg
            else:
                # No correction found, use this leg
                return leg
        
        # Return most recent valid leg if no correction check passed
        for leg in reversed(direction_legs):
            if (leg.end_index - leg.start_index + 1) >= self.min_leg_candles:
                return leg
        
        return None
    
    def _fallback_tp(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        pip_value: float
    ) -> TPCalculationResult:
        """Fallback to 2:1 R/R if no valid leg found"""
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * 2
        
        if is_buy:
            take_profit = entry_price + tp_distance
        else:
            take_profit = entry_price - tp_distance
        
        return TPCalculationResult(
            take_profit=take_profit,
            tp_pips=tp_distance / pip_value,
            strategy_used=self.STRATEGY_TYPE,
            fallback_used=True
        )


# ============================================================
# Factory and Manager
# ============================================================

class AdvancedTPFactory:
    """Factory for creating TP strategy instances"""
    
    STRATEGIES = {
        AdvancedTPType.FIXED_PIPS: FixedPipsTP,
        AdvancedTPType.ATR_BASED: ATRBasedTP,
        AdvancedTPType.KEY_LEVELS_NEAREST: KeyLevelsNearestTP,
        AdvancedTPType.KEY_LEVELS_SELECTABLE: KeyLevelsSelectableTP,
        AdvancedTPType.RISK_REWARD_FIXED: RiskRewardFixedTP,
        AdvancedTPType.STEPPED_RR: SteppedRRTP,
        AdvancedTPType.LEG_BASED: LegBasedTP,
    }
    
    PREMIUM_STRATEGIES = {
        AdvancedTPType.KEY_LEVELS_SELECTABLE,
        AdvancedTPType.STEPPED_RR,
        AdvancedTPType.LEG_BASED,
    }
    
    @classmethod
    def create(
        cls,
        strategy_type: AdvancedTPType,
        **kwargs
    ) -> BaseAdvancedTPStrategy:
        """Create a TP strategy instance"""
        if strategy_type not in cls.STRATEGIES:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        return cls.STRATEGIES[strategy_type](**kwargs)
    
    @classmethod
    def is_premium(cls, strategy_type: AdvancedTPType) -> bool:
        """Check if a strategy requires premium access"""
        return strategy_type in cls.PREMIUM_STRATEGIES
    
    @classmethod
    def get_available_strategies(cls) -> List[Dict[str, Any]]:
        """Get list of all available strategies with metadata"""
        strategies = []
        for tp_type, strategy_class in cls.STRATEGIES.items():
            strategies.append({
                "type": tp_type.value,
                "name": strategy_class.DISPLAY_NAME,
                "description": strategy_class.DESCRIPTION,
                "premium": strategy_class.IS_PREMIUM,
                "display_name": TP_DISPLAY_NAMES.get(tp_type, tp_type.value)
            })
        return strategies


class AdvancedTPManager:
    """
    Manager for advanced TP strategies with premium access control.
    """
    
    def __init__(self, is_premium: bool = False):
        self.is_premium = is_premium
        self._strategy: BaseAdvancedTPStrategy = RiskRewardFixedTP(rr_ratio=2.0)
    
    def set_strategy(
        self,
        strategy_type: AdvancedTPType,
        **kwargs
    ) -> bool:
        """
        Set the active TP strategy.
        
        Returns True if successful, False if premium required.
        """
        if AdvancedTPFactory.is_premium(strategy_type) and not self.is_premium:
            # Fallback to default for non-premium users
            self._strategy = RiskRewardFixedTP(rr_ratio=2.0)
            return False
        
        self._strategy = AdvancedTPFactory.create(strategy_type, **kwargs)
        return True
    
    def calculate(
        self,
        entry_price: float,
        stop_loss: float,
        is_buy: bool,
        data: Dict[str, Any],
        pip_value: float = 0.0001
    ) -> TPCalculationResult:
        """Calculate take profit using current strategy"""
        return self._strategy.calculate(
            entry_price, stop_loss, is_buy, data, pip_value
        )
    
    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """Get strategies available for current user"""
        all_strategies = AdvancedTPFactory.get_available_strategies()
        
        for strategy in all_strategies:
            strategy["available"] = not strategy["premium"] or self.is_premium
        
        return all_strategies
    
    def get_current_strategy_info(self) -> Dict[str, Any]:
        """Get info about current strategy"""
        return {
            "type": self._strategy.STRATEGY_TYPE.value,
            "name": self._strategy.DISPLAY_NAME,
            "description": self._strategy.DESCRIPTION,
            "is_premium": self._strategy.IS_PREMIUM
        }


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":
    np.random.seed(42)
    n = 200
    
    base_price = 1.1000
    returns = np.random.randn(n) * 0.001
    close = base_price + np.cumsum(returns)
    high = close + np.abs(np.random.randn(n) * 0.0005)
    low = close - np.abs(np.random.randn(n) * 0.0005)
    open_prices = close - returns + np.random.randn(n) * 0.0002
    
    data = {
        "open": open_prices,
        "high": high,
        "low": low,
        "close": close
    }
    
    entry_price = float(close[-1])
    stop_loss = entry_price - 0.0030  # 30 pips SL
    pip_value = 0.0001
    
    print("=" * 60)
    print("ADVANCED TAKE PROFIT STRATEGIES")
    print("=" * 60)
    print(f"\nEntry: {entry_price:.5f}, SL: {stop_loss:.5f}")
    print(f"SL Distance: {(entry_price - stop_loss) / pip_value:.1f} pips")
    print("\nTesting BUY trade:\n")
    
    # Test all strategies
    strategies = [
        ("Smart Pips", FixedPipsTP(pips=50)),
        ("Volatility Target", ATRBasedTP(multiplier=3.0)),
        ("Level Hunter", KeyLevelsNearestTP()),
        ("Classic R/R", RiskRewardFixedTP(rr_ratio=2.0)),
        ("Ladder Exit", SteppedRRTP()),
        ("Leg Projection", LegBasedTP()),
    ]
    
    for name, strategy in strategies:
        result = strategy.calculate(entry_price, stop_loss, True, data, pip_value)
        print(f"{name}:")
        print(f"  TP: {result.take_profit:.5f} ({result.tp_pips:.1f} pips)")
        print(f"  Fallback: {result.fallback_used}")
        if result.is_stepped:
            print(f"  Exit Levels:")
            for level in result.exit_levels:
                print(f"    - {level['percentage']}% @ {level['price']:.5f} (R/R {level['rr_ratio']})")
        print()
    
    print("\n" + "=" * 60)
    print("AVAILABLE STRATEGIES")
    print("=" * 60)
    for s in AdvancedTPFactory.get_available_strategies():
        tag = " [PREMIUM]" if s["premium"] else " [FREE]"
        print(f"- {s['display_name']}{tag}: {s['description']}")
