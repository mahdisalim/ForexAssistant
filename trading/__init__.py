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
