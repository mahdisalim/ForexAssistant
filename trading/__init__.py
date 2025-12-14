"""
Trading Module
Provides trading robots with modular SL/TP strategies.

Available Robots:
- StochasticRobot: Basic Stochastic Oscillator robot
- StochasticDivergenceRobot: Advanced with divergence detection (Premium)

SL/TP Strategies:
- ATR-based
- Fixed Pips
- Swing Points (Premium)
- Risk/Reward Ratio
- Support/Resistance (Premium)

Advanced SL Strategies:
- Fixed Pips
- ATR-Based
- Pin Bar
- Previous Leg
- FVG Start
- Session Open (NY/London/Tokyo)
- Leg Start Pin Bar

Pattern Detection:
- Pin Bar Detection
- Leg Detection
- FVG Detection
- Swing Point Detection

Market Sessions:
- Tokyo, London, New York session detection
"""

from .sl_tp_strategies import (
    SLStrategy,
    TPStrategy,
    SLTPResult,
    SLTPManager,
    SLTPStrategyFactory,
    BaseSLStrategy,
    BaseTPStrategy,
    ATRStopLoss,
    FixedPipsStopLoss,
    SwingStopLoss,
    PercentageStopLoss,
    SupportResistanceStopLoss,
    RiskRewardTakeProfit,
    ATRTakeProfit,
    FixedPipsTakeProfit,
    SwingTakeProfit,
    PercentageTakeProfit,
    SupportResistanceTakeProfit,
)

from .pattern_detection import (
    PatternType,
    Pattern,
    Leg,
    FVG,
    PinBarDetector,
    LegDetector,
    FVGDetector,
    SwingPointDetector,
    PatternManager,
)

from .market_sessions import (
    MarketSession,
    SessionInfo,
    SessionCandle,
    MarketSessionDetector,
    get_session_times_iran,
)

from .advanced_sl_strategies import (
    AdvancedSLType,
    SLCalculationResult,
    SL_DISPLAY_NAMES,
    BaseAdvancedSLStrategy,
    FixedPipsSL,
    ATRBasedSL,
    PinBarSL,
    PreviousLegSL,
    FVGStartSL,
    SessionOpenSL,
    LegStartPinBarSL,
    KeyLevelsNearestSL,
    KeyLevelsSelectableSL,
    AdvancedSLFactory,
    AdvancedSLManager,
)

from .support_resistance import (
    LevelType,
    LevelStrength,
    TimeframeContext,
    SRLevel,
    WeeklyMapLevels,
    SupportResistanceDetector,
    detect_sr_levels,
)

from .advanced_tp_strategies import (
    AdvancedTPType,
    TP_DISPLAY_NAMES,
    TPCalculationResult,
    SteppedExitLevel,
    BaseAdvancedTPStrategy,
    FixedPipsTP,
    ATRBasedTP,
    KeyLevelsNearestTP,
    KeyLevelsSelectableTP,
    RiskRewardFixedTP,
    SteppedRRTP,
    LegBasedTP,
    AdvancedTPFactory,
    AdvancedTPManager,
)

from .base_robot import (
    BaseRobot,
    RobotConfig,
    TradeSignal,
    SignalType,
    Timeframe,
    IndicatorCalculator,
)

from .stochastic_robot import (
    StochasticRobot,
    StochasticDivergenceRobot,
)

from .robot_manager import (
    RobotRegistry,
    RobotManager,
    UserSubscription,
    create_robot_manager,
)

__all__ = [
    # SL/TP
    "SLStrategy",
    "TPStrategy", 
    "SLTPResult",
    "SLTPManager",
    "SLTPStrategyFactory",
    "BaseSLStrategy",
    "BaseTPStrategy",
    "ATRStopLoss",
    "FixedPipsStopLoss",
    "SwingStopLoss",
    "PercentageStopLoss",
    "SupportResistanceStopLoss",
    "RiskRewardTakeProfit",
    "ATRTakeProfit",
    "FixedPipsTakeProfit",
    "SwingTakeProfit",
    "PercentageTakeProfit",
    "SupportResistanceTakeProfit",
    # Pattern Detection
    "PatternType",
    "Pattern",
    "Leg",
    "FVG",
    "PinBarDetector",
    "LegDetector",
    "FVGDetector",
    "SwingPointDetector",
    "PatternManager",
    # Market Sessions
    "MarketSession",
    "SessionInfo",
    "SessionCandle",
    "MarketSessionDetector",
    "get_session_times_iran",
    # Advanced SL Strategies
    "AdvancedSLType",
    "SLCalculationResult",
    "SL_DISPLAY_NAMES",
    "BaseAdvancedSLStrategy",
    "FixedPipsSL",
    "ATRBasedSL",
    "PinBarSL",
    "PreviousLegSL",
    "FVGStartSL",
    "SessionOpenSL",
    "LegStartPinBarSL",
    "KeyLevelsNearestSL",
    "KeyLevelsSelectableSL",
    "AdvancedSLFactory",
    "AdvancedSLManager",
    # Support/Resistance
    "LevelType",
    "LevelStrength",
    "TimeframeContext",
    "SRLevel",
    "WeeklyMapLevels",
    "SupportResistanceDetector",
    "detect_sr_levels",
    # Advanced TP Strategies
    "AdvancedTPType",
    "TP_DISPLAY_NAMES",
    "TPCalculationResult",
    "SteppedExitLevel",
    "BaseAdvancedTPStrategy",
    "FixedPipsTP",
    "ATRBasedTP",
    "KeyLevelsNearestTP",
    "KeyLevelsSelectableTP",
    "RiskRewardFixedTP",
    "SteppedRRTP",
    "LegBasedTP",
    "AdvancedTPFactory",
    "AdvancedTPManager",
    # Base
    "BaseRobot",
    "RobotConfig",
    "TradeSignal",
    "SignalType",
    "Timeframe",
    "IndicatorCalculator",
    # Robots
    "StochasticRobot",
    "StochasticDivergenceRobot",
    # Manager
    "RobotRegistry",
    "RobotManager",
    "UserSubscription",
    "create_robot_manager",
]
