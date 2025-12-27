"""
Unified Trading Robots Module
یکپارچه‌سازی سیستم‌های مختلف ربات‌های معاملاتی

این ماژول تمام سیستم‌های ربات و استراتژی‌های SL/TP را یکپارچه می‌کند:
1. strategy_bots - سیستم قدیمی با RSI Bot
2. trading - سیستم جدید با Stochastic Robot و Advanced SL/TP

همه ربات‌ها و استراتژی‌ها از طریق این ماژول قابل دسترسی هستند.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from enum import Enum

logger = logging.getLogger(__name__)

# ============== Import from strategy_bots (Legacy) ==============
try:
    from strategy_bots import (
        RSIBot, BaseStrategyBot,
        Signal, Trade, PendingSetup, BotAnalysis,
        SignalType, TradeDirection, TradeStatus,
        AccountConfig, TradeConfig, BotConfig,
        RiskMode, SLMode, TPMode, DEFAULT_CONFIG,
    )
    STRATEGY_BOTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"strategy_bots module not available: {e}")
    STRATEGY_BOTS_AVAILABLE = False

# ============== Import from trading (New System) ==============
try:
    from trading import (
        # Robots
        StochasticRobot, StochasticDivergenceRobot,
        BaseRobot, RobotConfig, TradeSignal, Timeframe,
        # Legacy SL/TP
        SLStrategy, TPStrategy, SLTPManager,
        # Advanced SL Strategies
        AdvancedSLType, AdvancedSLFactory, AdvancedSLManager,
        SL_DISPLAY_NAMES,
        # Advanced TP Strategies
        AdvancedTPType, AdvancedTPFactory, AdvancedTPManager,
        TP_DISPLAY_NAMES,
        # Support/Resistance
        SupportResistanceDetector, LevelStrength,
        # Manager
        RobotManager, UserSubscription, create_robot_manager
    )
    TRADING_MODULE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"trading module not available: {e}")
    TRADING_MODULE_AVAILABLE = False


class RobotType(str, Enum):
    """انواع ربات‌های موجود"""
    RSI = "rsi"
    STOCHASTIC = "stochastic"
    STOCHASTIC_DIVERGENCE = "stochastic_divergence"


# Use AdvancedSLType if available, otherwise define locally
if TRADING_MODULE_AVAILABLE:
    SLType = AdvancedSLType
    TPType = AdvancedTPType
else:
    class SLType(str, Enum):
        """انواع استراتژی‌های SL"""
        FIXED_PIPS = "fixed_pips"
        ATR = "atr"
        PIN_BAR = "pin_bar"
        PREVIOUS_LEG = "previous_leg"
        FVG_START = "fvg_start"
        SESSION_OPEN = "session_open"
        LEG_START_PIN_BAR = "leg_start_pin_bar"
        KEY_LEVELS_NEAREST = "key_levels_nearest"
        KEY_LEVELS_SELECTABLE = "key_levels_selectable"

    class TPType(str, Enum):
        """انواع استراتژی‌های TP"""
        FIXED_PIPS = "fixed_pips"
        ATR_BASED = "atr_based"
        KEY_LEVELS_NEAREST = "key_levels_nearest"
        KEY_LEVELS_SELECTABLE = "key_levels_selectable"
        RISK_REWARD_FIXED = "risk_reward_fixed"
        STEPPED_RR = "stepped_rr"
        LEG_BASED = "leg_based"


# ============== Unified Robot Registry ==============

class UnifiedRobotRegistry:
    """
    رجیستری یکپارچه برای همه ربات‌ها
    """
    
    _robots: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register_all(cls):
        """ثبت همه ربات‌های موجود"""
        
        # RSI Bot from strategy_bots - رایگان
        if STRATEGY_BOTS_AVAILABLE:
            cls._robots["RSI Robot"] = {
                "type": RobotType.RSI,
                "class": RSIBot,
                "module": "strategy_bots",
                "description": "ربات RSI با سیگنال‌های کراس از مناطق اشباع",
                "default_sl": "atr",
                "default_tp": "risk_reward_fixed",
                "premium": False,
                "available_sl": ["atr", "fixed_pips"],
                "available_tp": ["risk_reward_fixed", "fixed_pips"]
            }
        
        # Stochastic Robot from trading - رایگان
        if TRADING_MODULE_AVAILABLE:
            cls._robots["Stochastic Robot"] = {
                "type": RobotType.STOCHASTIC,
                "class": StochasticRobot,
                "module": "trading",
                "description": "ربات Stochastic با سیگنال‌های کراس در مناطق اشباع",
                "default_sl": "atr",
                "default_tp": "risk_reward_fixed",
                "premium": False,
                "available_sl": ["atr", "fixed_pips", "key_levels_nearest"],
                "available_tp": ["risk_reward_fixed", "fixed_pips", "atr_based", "key_levels_nearest"]
            }
            
            # این ربات هنوز ساخته نشده - برای آینده
            # cls._robots["Stochastic Divergence Robot"] = {...}
    
    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        """لیست همه ربات‌ها - همه رایگان هستند"""
        if not cls._robots:
            cls.register_all()
        
        return [
            {
                "name": name,
                "type": info["type"].value,
                "description": info["description"],
                "default_sl": info["default_sl"],
                "default_tp": info["default_tp"],
                "free": True,  # همه ربات‌ها رایگان هستند
                "module": info["module"]
            }
            for name, info in cls._robots.items()
        ]
    
    @classmethod
    def get(cls, name: str) -> Optional[Dict[str, Any]]:
        """دریافت اطلاعات یک ربات"""
        if not cls._robots:
            cls.register_all()
        return cls._robots.get(name)
    
    @classmethod
    def get_free_robots(cls) -> List[str]:
        """لیست ربات‌های رایگان"""
        if not cls._robots:
            cls.register_all()
        return [name for name, info in cls._robots.items() if not info["premium"]]
    
    @classmethod
    def get_premium_robots(cls) -> List[str]:
        """لیست ربات‌های پولی"""
        if not cls._robots:
            cls.register_all()
        return [name for name, info in cls._robots.items() if info["premium"]]


# ============== Unified SL/TP Factory ==============

class UnifiedSLFactory:
    """
    فکتوری یکپارچه برای استراتژی‌های SL
    از سیستم جدید AdvancedSLFactory استفاده می‌کند
    """
    
    @classmethod
    def create(cls, sl_type: SLType, **kwargs) -> Any:
        """ایجاد استراتژی SL"""
        if TRADING_MODULE_AVAILABLE:
            try:
                return AdvancedSLFactory.create(sl_type, **kwargs)
            except Exception as e:
                logger.warning(f"Failed to create SL strategy: {e}")
        return None
    
    @classmethod
    def get_available(cls, premium: bool = False) -> List[Dict[str, Any]]:
        """لیست استراتژی‌های SL موجود"""
        if TRADING_MODULE_AVAILABLE:
            strategies = AdvancedSLFactory.get_available_strategies()
            for s in strategies:
                s["selectable"] = not s.get("premium", False) or premium
                s["display_name"] = SL_DISPLAY_NAMES.get(
                    AdvancedSLType(s["id"]), s["name"]
                ) if s["id"] in [t.value for t in AdvancedSLType] else s["name"]
            return strategies
        
        # Fallback
        return [
            {"id": "fixed_pips", "name": "Smart Shield", "description": "فاصله ثابت", "premium": False, "selectable": True},
            {"id": "atr", "name": "Volatility Guard", "description": "بر اساس نوسانات", "premium": False, "selectable": True},
        ]


class UnifiedTPFactory:
    """
    فکتوری یکپارچه برای استراتژی‌های TP
    از سیستم جدید AdvancedTPFactory استفاده می‌کند
    """
    
    @classmethod
    def create(cls, tp_type: TPType, **kwargs) -> Any:
        """ایجاد استراتژی TP"""
        if TRADING_MODULE_AVAILABLE:
            try:
                return AdvancedTPFactory.create(tp_type, **kwargs)
            except Exception as e:
                logger.warning(f"Failed to create TP strategy: {e}")
        return None
    
    @classmethod
    def get_available(cls, premium: bool = False) -> List[Dict[str, Any]]:
        """لیست استراتژی‌های TP موجود"""
        if TRADING_MODULE_AVAILABLE:
            strategies = AdvancedTPFactory.get_available_strategies()
            for s in strategies:
                s["selectable"] = not s.get("premium", False) or premium
                s["display_name"] = TP_DISPLAY_NAMES.get(
                    AdvancedTPType(s["type"]), s["name"]
                ) if s["type"] in [t.value for t in AdvancedTPType] else s["name"]
            return strategies
        
        # Fallback
        return [
            {"type": "fixed_pips", "name": "Smart Pips", "description": "فاصله ثابت", "premium": False, "selectable": True},
            {"type": "risk_reward_fixed", "name": "Classic R/R", "description": "نسبت ریسک به ریوارد", "premium": False, "selectable": True},
        ]


# ============== Unified Robot Manager ==============

class UnifiedRobotManager:
    """
    مدیر یکپارچه ربات‌ها
    
    این کلاس هر دو نوع ربات (strategy_bots و trading) را مدیریت می‌کند.
    """
    
    def __init__(self, user_id: str, is_premium: bool = False):
        self.user_id = user_id
        self.is_premium = is_premium
        self._active_robots: Dict[str, Any] = {}
        
        # Initialize registry
        UnifiedRobotRegistry.register_all()
    
    def get_available_robots(self) -> List[Dict[str, Any]]:
        """لیست ربات‌های قابل استفاده"""
        all_robots = UnifiedRobotRegistry.get_all()
        
        for robot in all_robots:
            robot["available"] = not robot["premium"] or self.is_premium
        
        return all_robots
    
    def get_available_sl_strategies(self) -> List[Dict[str, Any]]:
        """لیست استراتژی‌های SL قابل استفاده"""
        return UnifiedSLFactory.get_available(self.is_premium)
    
    def get_available_tp_strategies(self) -> List[Dict[str, Any]]:
        """لیست استراتژی‌های TP قابل استفاده"""
        return UnifiedTPFactory.get_available(self.is_premium)
    
    def create_robot(
        self,
        robot_name: str,
        symbol: str = "EURUSD",
        timeframe: str = "H1",
        sl_type: str = None,
        tp_type: str = None,
        sl_params: Dict = None,
        tp_params: Dict = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        ایجاد ربات جدید
        """
        robot_info = UnifiedRobotRegistry.get(robot_name)
        
        if not robot_info:
            return {"success": False, "error": f"Robot not found: {robot_name}"}
        
        if robot_info["premium"] and not self.is_premium:
            return {"success": False, "error": "Premium subscription required"}
        
        try:
            robot_class = robot_info["class"]
            module = robot_info["module"]
            
            if module == "strategy_bots":
                # Create RSI Bot
                robot = robot_class(
                    pairs=[symbol],
                    timeframe=timeframe,
                    **kwargs
                )
                
                # Configure SL/TP if specified
                if sl_type:
                    sl_strategy = UnifiedSLFactory.create(
                        SLType(sl_type), **(sl_params or {})
                    )
                    if sl_strategy:
                        robot.sl_strategy = sl_strategy
                
                if tp_type:
                    tp_strategy = UnifiedTPFactory.create(
                        TPType(tp_type), **(tp_params or {})
                    )
                    if tp_strategy:
                        robot.tp_strategy = tp_strategy
            
            elif module == "trading":
                # Create Stochastic Robot
                from trading import RobotConfig, Timeframe as TF, SLStrategy as SLS, TPStrategy as TPS
                
                config = RobotConfig(
                    symbol=symbol,
                    timeframe=TF(timeframe.lower()),
                    sl_strategy=SLS(sl_type or "atr"),
                    tp_strategy=TPS(tp_type or "risk_reward"),
                    sl_params=sl_params or {},
                    tp_params=tp_params or {},
                    is_premium=self.is_premium
                )
                
                robot = robot_class(config, **kwargs)
            
            else:
                return {"success": False, "error": "Unknown module"}
            
            # Generate ID and store
            robot_id = f"{robot_name.lower().replace(' ', '_')}_{symbol}_{timeframe}"
            self._active_robots[robot_id] = {
                "robot": robot,
                "info": robot_info,
                "symbol": symbol,
                "timeframe": timeframe
            }
            
            return {
                "success": True,
                "robot_id": robot_id,
                "robot_name": robot_name,
                "symbol": symbol,
                "timeframe": timeframe
            }
            
        except Exception as e:
            logger.error(f"Error creating robot: {e}")
            return {"success": False, "error": str(e)}
    
    def get_active_robots(self) -> List[Dict[str, Any]]:
        """لیست ربات‌های فعال"""
        return [
            {
                "robot_id": robot_id,
                "name": data["info"]["type"].value,
                "symbol": data["symbol"],
                "timeframe": data["timeframe"],
                "module": data["info"]["module"]
            }
            for robot_id, data in self._active_robots.items()
        ]
    
    def delete_robot(self, robot_id: str) -> Dict[str, Any]:
        """حذف ربات"""
        if robot_id in self._active_robots:
            del self._active_robots[robot_id]
            return {"success": True}
        return {"success": False, "error": "Robot not found"}
    
    def get_all_options(self) -> Dict[str, Any]:
        """همه گزینه‌های موجود"""
        return {
            "robots": self.get_available_robots(),
            "sl_strategies": self.get_available_sl_strategies(),
            "tp_strategies": self.get_available_tp_strategies(),
            "timeframes": ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN"],
            "is_premium": self.is_premium,
            "can_customize_sl_tp": self.is_premium,  # ویژگی پولی: انتخاب SL/TP
            "active_robots": len(self._active_robots),
            "premium_features": [
                {"id": "custom_sl_tp", "name": "انتخاب روش SL/TP", "description": "امکان انتخاب روش استاپ و حد سود دلخواه"},
                {"id": "more_coming", "name": "ویژگی‌های بیشتر", "description": "به زودی..."}
            ]
        }


# ============== Factory Function ==============

def create_unified_manager(user_id: str, is_premium: bool = False) -> UnifiedRobotManager:
    """ایجاد مدیر یکپارچه ربات‌ها"""
    return UnifiedRobotManager(user_id, is_premium)


# ============== Initialize Registry ==============
UnifiedRobotRegistry.register_all()
