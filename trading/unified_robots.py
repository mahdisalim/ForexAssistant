"""
Unified Trading Robots Module
یکپارچه‌سازی سیستم‌های مختلف ربات‌های معاملاتی

این ماژول دو سیستم را به هم متصل می‌کند:
1. strategy_bots - سیستم قدیمی با RSI Bot و SL/TP strategies
2. trading - سیستم جدید با Stochastic Robot

همه ربات‌ها از طریق این ماژول قابل دسترسی هستند.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from enum import Enum

logger = logging.getLogger(__name__)

# ============== Import from strategy_bots ==============
try:
    from strategy_bots import (
        # Bots
        RSIBot, BaseStrategyBot,
        # Models
        Signal, Trade, PendingSetup, BotAnalysis,
        SignalType, TradeDirection, TradeStatus,
        # Config
        AccountConfig, TradeConfig, BotConfig,
        RiskMode, SLMode, TPMode, DEFAULT_CONFIG,
        # SL Strategies
        PinBarSL, ATRSL, SwingPointSL, CompositeSL, SLResult,
        # TP Strategies
        RiskRewardTP, MultiTargetTP, ATRTP, FixedPipsTP, CompositeTP, TPResult
    )
    STRATEGY_BOTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"strategy_bots module not available: {e}")
    STRATEGY_BOTS_AVAILABLE = False

# ============== Import from trading ==============
try:
    from trading import (
        # Robots
        StochasticRobot, StochasticDivergenceRobot,
        # Base
        BaseRobot, RobotConfig, TradeSignal, Timeframe,
        # SL/TP
        SLStrategy, TPStrategy, SLTPManager,
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


class SLType(str, Enum):
    """انواع استراتژی‌های SL"""
    ATR = "atr"
    PIN_BAR = "pin_bar"
    SWING_POINT = "swing_point"
    FIXED_PIPS = "fixed_pips"
    COMPOSITE = "composite"


class TPType(str, Enum):
    """انواع استراتژی‌های TP"""
    RISK_REWARD = "risk_reward"
    MULTI_TARGET = "multi_target"
    ATR = "atr"
    FIXED_PIPS = "fixed_pips"
    COMPOSITE = "composite"


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
                "default_sl": SLType.ATR,
                "default_tp": TPType.RISK_REWARD,
                "premium": False,  # ربات رایگان
                "available_sl": [SLType.ATR, SLType.FIXED_PIPS],  # SL های رایگان
                "available_tp": [TPType.RISK_REWARD, TPType.FIXED_PIPS]  # TP های رایگان
            }
        
        # Stochastic Robot from trading - رایگان
        if TRADING_MODULE_AVAILABLE:
            cls._robots["Stochastic Robot"] = {
                "type": RobotType.STOCHASTIC,
                "class": StochasticRobot,
                "module": "trading",
                "description": "ربات Stochastic با سیگنال‌های کراس در مناطق اشباع",
                "default_sl": SLType.ATR,
                "default_tp": TPType.RISK_REWARD,
                "premium": False,  # ربات رایگان
                "available_sl": [SLType.ATR, SLType.FIXED_PIPS],  # SL های رایگان
                "available_tp": [TPType.RISK_REWARD, TPType.FIXED_PIPS]  # TP های رایگان
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
                "default_sl": info["default_sl"].value,
                "default_tp": info["default_tp"].value,
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
    """
    
    @classmethod
    def create(cls, sl_type: SLType, **kwargs) -> Any:
        """ایجاد استراتژی SL"""
        if not STRATEGY_BOTS_AVAILABLE:
            logger.warning("strategy_bots not available, using fallback")
            return None
        
        if sl_type == SLType.ATR:
            return ATRSL(
                atr_period=kwargs.get("atr_period", 14),
                multiplier=kwargs.get("multiplier", 1.5)
            )
        elif sl_type == SLType.PIN_BAR:
            return PinBarSL(
                buffer_pips=kwargs.get("buffer_pips", 5.0),
                min_shadow_ratio=kwargs.get("min_shadow_ratio", 2.0)
            )
        elif sl_type == SLType.SWING_POINT:
            return SwingPointSL(
                buffer_pips=kwargs.get("buffer_pips", 5.0),
                lookback=kwargs.get("lookback", 20)
            )
        elif sl_type == SLType.COMPOSITE:
            return CompositeSL(
                strategies=[PinBarSL(), SwingPointSL()],
                fallback_strategy=ATRSL()
            )
        else:
            return ATRSL()
    
    @classmethod
    def get_available(cls, premium: bool = False) -> List[Dict[str, Any]]:
        """
        لیست استراتژی‌های SL موجود
        
        در حالت رایگان: فقط پیش‌فرض ربات استفاده می‌شود
        در حالت پولی: کاربر می‌تواند هر کدام را انتخاب کند
        """
        strategies = [
            {"id": "atr", "name": "ATR-Based", "description": "بر اساس نوسانات بازار"},
            {"id": "fixed_pips", "name": "Fixed Pips", "description": "فاصله ثابت"},
            {"id": "pin_bar", "name": "Pin Bar", "description": "پشت آخرین پین بار"},
            {"id": "swing_point", "name": "Swing Point", "description": "پشت آخرین سوینگ"},
            {"id": "composite", "name": "Composite", "description": "ترکیبی از چند روش"},
        ]
        
        # در حالت پولی همه قابل انتخاب هستند
        # در حالت رایگان فقط نمایش داده می‌شوند ولی قابل انتخاب نیستند
        for s in strategies:
            s["selectable"] = premium  # فقط کاربران پولی می‌توانند انتخاب کنند
        
        return strategies


class UnifiedTPFactory:
    """
    فکتوری یکپارچه برای استراتژی‌های TP
    """
    
    @classmethod
    def create(cls, tp_type: TPType, **kwargs) -> Any:
        """ایجاد استراتژی TP"""
        if not STRATEGY_BOTS_AVAILABLE:
            logger.warning("strategy_bots not available, using fallback")
            return None
        
        if tp_type == TPType.RISK_REWARD:
            return RiskRewardTP(
                ratio=kwargs.get("ratio", 2.0)
            )
        elif tp_type == TPType.MULTI_TARGET:
            return MultiTargetTP(
                targets=kwargs.get("targets", [(1.0, 50), (2.0, 30), (3.0, 20)])
            )
        elif tp_type == TPType.ATR:
            return ATRTP(
                atr_period=kwargs.get("atr_period", 14),
                multiplier=kwargs.get("multiplier", 3.0)
            )
        elif tp_type == TPType.FIXED_PIPS:
            return FixedPipsTP(
                pips=kwargs.get("pips", 100)
            )
        elif tp_type == TPType.COMPOSITE:
            return CompositeTP(
                strategies=[RiskRewardTP(ratio=2.0), MultiTargetTP()]
            )
        else:
            return RiskRewardTP()
    
    @classmethod
    def get_available(cls, premium: bool = False) -> List[Dict[str, Any]]:
        """
        لیست استراتژی‌های TP موجود
        
        در حالت رایگان: فقط پیش‌فرض ربات استفاده می‌شود
        در حالت پولی: کاربر می‌تواند هر کدام را انتخاب کند
        """
        strategies = [
            {"id": "risk_reward", "name": "Risk/Reward", "description": "نسبت ریسک به ریوارد"},
            {"id": "fixed_pips", "name": "Fixed Pips", "description": "فاصله ثابت"},
            {"id": "multi_target", "name": "Multi-Target", "description": "چند هدف با بستن تدریجی"},
            {"id": "atr", "name": "ATR-Based", "description": "بر اساس نوسانات"},
            {"id": "composite", "name": "Composite", "description": "ترکیبی از چند روش"},
        ]
        
        # در حالت پولی همه قابل انتخاب هستند
        # در حالت رایگان فقط نمایش داده می‌شوند ولی قابل انتخاب نیستند
        for s in strategies:
            s["selectable"] = premium  # فقط کاربران پولی می‌توانند انتخاب کنند
        
        return strategies


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
