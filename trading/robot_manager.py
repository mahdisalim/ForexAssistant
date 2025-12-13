"""
Robot Manager Module
Central management system for all trading robots.

Features:
- Robot registration and discovery
- Premium/Free user handling
- Configuration management
- Signal generation coordination
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional, Type
from datetime import datetime
from pathlib import Path

from .base_robot import BaseRobot, RobotConfig, TradeSignal, Timeframe
from .sl_tp_strategies import SLStrategy, TPStrategy, SLTPStrategyFactory
from .stochastic_robot import StochasticRobot, StochasticDivergenceRobot

logger = logging.getLogger(__name__)


class RobotRegistry:
    """Registry of all available trading robots"""
    
    _robots: Dict[str, Type[BaseRobot]] = {}
    
    @classmethod
    def register(cls, robot_class: Type[BaseRobot]):
        """Register a robot class"""
        cls._robots[robot_class.ROBOT_NAME] = robot_class
        return robot_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseRobot]]:
        """Get robot class by name"""
        return cls._robots.get(name)
    
    @classmethod
    def list_all(cls) -> List[Dict[str, Any]]:
        """List all registered robots"""
        return [
            {
                "name": robot.ROBOT_NAME,
                "description": robot.ROBOT_DESCRIPTION,
                "version": robot.ROBOT_VERSION,
                "default_sl": robot.DEFAULT_SL_STRATEGY.value,
                "default_tp": robot.DEFAULT_TP_STRATEGY.value,
            }
            for robot in cls._robots.values()
        ]
    
    @classmethod
    def get_robot_names(cls) -> List[str]:
        """Get list of robot names"""
        return list(cls._robots.keys())


# Register built-in robots
RobotRegistry.register(StochasticRobot)
RobotRegistry.register(StochasticDivergenceRobot)


class UserSubscription:
    """User subscription management"""
    
    PLANS = {
        "free": {
            "name": "Free",
            "robots": ["Stochastic Robot"],
            "sl_strategies": ["atr", "fixed_pips"],
            "tp_strategies": ["risk_reward", "fixed_pips"],
            "max_active_robots": 1,
            "features": []
        },
        "basic": {
            "name": "Basic",
            "robots": ["Stochastic Robot", "RSI Robot"],
            "sl_strategies": ["atr", "fixed_pips", "swing"],
            "tp_strategies": ["risk_reward", "fixed_pips", "atr"],
            "max_active_robots": 3,
            "features": ["multi_timeframe"]
        },
        "premium": {
            "name": "Premium",
            "robots": "all",
            "sl_strategies": "all",
            "tp_strategies": "all",
            "max_active_robots": 10,
            "features": ["multi_timeframe", "divergence", "custom_indicators", "backtesting"]
        }
    }
    
    def __init__(self, plan: str = "free"):
        self.plan = plan
        self._plan_data = self.PLANS.get(plan, self.PLANS["free"])
    
    @property
    def is_premium(self) -> bool:
        return self.plan == "premium"
    
    def can_use_robot(self, robot_name: str) -> bool:
        """Check if user can use a specific robot"""
        allowed = self._plan_data.get("robots", [])
        if allowed == "all":
            return True
        return robot_name in allowed
    
    def can_use_sl_strategy(self, strategy: str) -> bool:
        """Check if user can use a specific SL strategy"""
        allowed = self._plan_data.get("sl_strategies", [])
        if allowed == "all":
            return True
        return strategy in allowed
    
    def can_use_tp_strategy(self, strategy: str) -> bool:
        """Check if user can use a specific TP strategy"""
        allowed = self._plan_data.get("tp_strategies", [])
        if allowed == "all":
            return True
        return strategy in allowed
    
    def get_available_robots(self) -> List[str]:
        """Get list of available robots for this subscription"""
        allowed = self._plan_data.get("robots", [])
        if allowed == "all":
            return RobotRegistry.get_robot_names()
        return allowed
    
    def get_available_sl_strategies(self) -> List[Dict[str, Any]]:
        """Get available SL strategies with premium info"""
        all_strategies = SLTPStrategyFactory.get_available_sl_strategies()
        allowed = self._plan_data.get("sl_strategies", [])
        
        if allowed == "all":
            return all_strategies
        
        for strategy in all_strategies:
            strategy["available"] = strategy["id"] in allowed
        
        return all_strategies
    
    def get_available_tp_strategies(self) -> List[Dict[str, Any]]:
        """Get available TP strategies with premium info"""
        all_strategies = SLTPStrategyFactory.get_available_tp_strategies()
        allowed = self._plan_data.get("tp_strategies", [])
        
        if allowed == "all":
            return all_strategies
        
        for strategy in all_strategies:
            strategy["available"] = strategy["id"] in allowed
        
        return all_strategies
    
    def has_feature(self, feature: str) -> bool:
        """Check if subscription includes a feature"""
        return feature in self._plan_data.get("features", [])


class RobotManager:
    """
    Central manager for trading robots.
    Handles robot lifecycle, configuration, and signal generation.
    """
    
    def __init__(self, user_id: str, subscription: Optional[UserSubscription] = None,
                 config_dir: str = "data/robot_configs"):
        self.user_id = user_id
        self.subscription = subscription or UserSubscription("free")
        self.config_dir = Path(config_dir)
        self._active_robots: Dict[str, BaseRobot] = {}
        self._ensure_config_dir()
        self._load_user_configs()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_config_file(self) -> Path:
        """Get path to user's config file"""
        return self.config_dir / f"{self.user_id}_robots.json"
    
    def _load_user_configs(self):
        """Load user's robot configurations"""
        config_file = self._get_user_config_file()
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    configs = json.load(f)
                    for robot_id, config_data in configs.items():
                        self._create_robot_from_config(robot_id, config_data)
            except Exception as e:
                logger.error(f"Error loading robot configs: {e}")
    
    def _save_user_configs(self):
        """Save user's robot configurations"""
        config_file = self._get_user_config_file()
        try:
            configs = {}
            for robot_id, robot in self._active_robots.items():
                configs[robot_id] = {
                    "robot_name": robot.ROBOT_NAME,
                    "config": robot.config.to_dict()
                }
            with open(config_file, 'w') as f:
                json.dump(configs, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving robot configs: {e}")
    
    def _create_robot_from_config(self, robot_id: str, config_data: Dict[str, Any]) -> Optional[BaseRobot]:
        """Create robot instance from saved config"""
        robot_name = config_data.get("robot_name")
        robot_class = RobotRegistry.get(robot_name)
        
        if not robot_class:
            logger.warning(f"Unknown robot: {robot_name}")
            return None
        
        if not self.subscription.can_use_robot(robot_name):
            logger.warning(f"User cannot use robot: {robot_name}")
            return None
        
        config_dict = config_data.get("config", {})
        config = RobotConfig(
            symbol=config_dict.get("symbol", "EURUSD"),
            timeframe=Timeframe(config_dict.get("timeframe", "1h")),
            sl_strategy=SLStrategy(config_dict.get("sl_strategy", "atr")),
            tp_strategy=TPStrategy(config_dict.get("tp_strategy", "risk_reward")),
            sl_params=config_dict.get("sl_params", {}),
            tp_params=config_dict.get("tp_params", {}),
            risk_percent=config_dict.get("risk_percent", 1.0),
            is_premium=self.subscription.is_premium
        )
        
        robot = robot_class(config)
        self._active_robots[robot_id] = robot
        return robot
    
    def create_robot(self, robot_name: str, symbol: str = "EURUSD",
                    timeframe: str = "1h", **kwargs) -> Dict[str, Any]:
        """
        Create a new robot instance.
        
        Args:
            robot_name: Name of the robot to create
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            **kwargs: Additional configuration
            
        Returns:
            Result dict with robot_id or error
        """
        # Check subscription
        if not self.subscription.can_use_robot(robot_name):
            return {
                "success": False,
                "error": f"Your subscription does not include {robot_name}. Upgrade to access."
            }
        
        # Check max robots
        max_robots = self.subscription._plan_data.get("max_active_robots", 1)
        if len(self._active_robots) >= max_robots:
            return {
                "success": False,
                "error": f"Maximum {max_robots} active robots allowed. Upgrade for more."
            }
        
        # Get robot class
        robot_class = RobotRegistry.get(robot_name)
        if not robot_class:
            return {"success": False, "error": f"Unknown robot: {robot_name}"}
        
        # Validate SL/TP strategies
        sl_strategy = kwargs.get("sl_strategy", robot_class.DEFAULT_SL_STRATEGY.value)
        tp_strategy = kwargs.get("tp_strategy", robot_class.DEFAULT_TP_STRATEGY.value)
        
        if not self.subscription.can_use_sl_strategy(sl_strategy):
            sl_strategy = "atr"  # Fallback to default
        if not self.subscription.can_use_tp_strategy(tp_strategy):
            tp_strategy = "risk_reward"  # Fallback to default
        
        # Create config
        config = RobotConfig(
            symbol=symbol,
            timeframe=Timeframe(timeframe),
            sl_strategy=SLStrategy(sl_strategy),
            tp_strategy=TPStrategy(tp_strategy),
            sl_params=kwargs.get("sl_params", robot_class.DEFAULT_SL_PARAMS.copy()),
            tp_params=kwargs.get("tp_params", robot_class.DEFAULT_TP_PARAMS.copy()),
            risk_percent=kwargs.get("risk_percent", 1.0),
            is_premium=self.subscription.is_premium
        )
        
        # Create robot
        robot = robot_class(config)
        
        # Generate unique ID
        robot_id = f"{robot_name.lower().replace(' ', '_')}_{symbol}_{timeframe}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self._active_robots[robot_id] = robot
        self._save_user_configs()
        
        return {
            "success": True,
            "robot_id": robot_id,
            "robot_info": robot.get_info()
        }
    
    def delete_robot(self, robot_id: str) -> Dict[str, Any]:
        """Delete a robot"""
        if robot_id not in self._active_robots:
            return {"success": False, "error": "Robot not found"}
        
        del self._active_robots[robot_id]
        self._save_user_configs()
        
        return {"success": True, "message": f"Robot {robot_id} deleted"}
    
    def update_robot_config(self, robot_id: str, **kwargs) -> Dict[str, Any]:
        """Update robot configuration"""
        if robot_id not in self._active_robots:
            return {"success": False, "error": "Robot not found"}
        
        robot = self._active_robots[robot_id]
        
        # Validate strategies if being updated
        if "sl_strategy" in kwargs:
            if not self.subscription.can_use_sl_strategy(kwargs["sl_strategy"]):
                return {"success": False, "error": "SL strategy not available in your plan"}
        
        if "tp_strategy" in kwargs:
            if not self.subscription.can_use_tp_strategy(kwargs["tp_strategy"]):
                return {"success": False, "error": "TP strategy not available in your plan"}
        
        robot.update_config(**kwargs)
        self._save_user_configs()
        
        return {"success": True, "config": robot.config.to_dict()}
    
    def get_robot(self, robot_id: str) -> Optional[BaseRobot]:
        """Get robot by ID"""
        return self._active_robots.get(robot_id)
    
    def get_active_robots(self) -> List[Dict[str, Any]]:
        """Get list of active robots"""
        return [
            {
                "robot_id": robot_id,
                "name": robot.ROBOT_NAME,
                "symbol": robot.config.symbol,
                "timeframe": robot.config.timeframe.value if isinstance(robot.config.timeframe, Timeframe) else robot.config.timeframe,
                "sl_strategy": robot.config.sl_strategy.value if isinstance(robot.config.sl_strategy, SLStrategy) else robot.config.sl_strategy,
                "tp_strategy": robot.config.tp_strategy.value if isinstance(robot.config.tp_strategy, TPStrategy) else robot.config.tp_strategy,
            }
            for robot_id, robot in self._active_robots.items()
        ]
    
    def generate_signal(self, robot_id: str, data: Dict[str, Any]) -> Optional[TradeSignal]:
        """Generate signal from a specific robot"""
        robot = self._active_robots.get(robot_id)
        if not robot:
            return None
        
        return robot.generate_signal(data)
    
    def generate_all_signals(self, market_data: Dict[str, Dict[str, Any]]) -> List[TradeSignal]:
        """
        Generate signals from all active robots.
        
        Args:
            market_data: Dict of symbol -> OHLCV data
            
        Returns:
            List of generated signals
        """
        signals = []
        
        for robot_id, robot in self._active_robots.items():
            symbol = robot.config.symbol
            if symbol in market_data:
                signal = robot.generate_signal(market_data[symbol])
                if signal:
                    signals.append(signal)
        
        return signals
    
    def get_available_options(self) -> Dict[str, Any]:
        """Get all available options for the user's subscription"""
        return {
            "robots": [
                {
                    "name": robot_name,
                    "available": self.subscription.can_use_robot(robot_name)
                }
                for robot_name in RobotRegistry.get_robot_names()
            ],
            "sl_strategies": self.subscription.get_available_sl_strategies(),
            "tp_strategies": self.subscription.get_available_tp_strategies(),
            "timeframes": [tf.value for tf in Timeframe],
            "max_active_robots": self.subscription._plan_data.get("max_active_robots", 1),
            "current_active": len(self._active_robots),
            "subscription": self.subscription.plan
        }


# Factory function for easy creation
def create_robot_manager(user_id: str, subscription_plan: str = "free") -> RobotManager:
    """Create a robot manager for a user"""
    subscription = UserSubscription(subscription_plan)
    return RobotManager(user_id, subscription)
