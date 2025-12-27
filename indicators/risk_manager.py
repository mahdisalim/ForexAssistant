"""
Risk Manager - Position sizing and risk calculations
Phase 3: Trading Algorithm Support
"""
import logging
from typing import Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PositionSize(BaseModel):
    """Position size calculation result"""
    lots: float
    risk_amount: float
    risk_percent: float
    pip_value: float
    sl_pips: int
    tp_pips: int
    potential_profit: float
    potential_loss: float


class RiskManager:
    """
    Risk management for forex trading
    Calculates position sizes based on account balance and risk parameters
    """
    
    # Standard lot sizes
    STANDARD_LOT = 100000
    MINI_LOT = 10000
    MICRO_LOT = 1000
    
    # Pip values for major pairs (per standard lot)
    PIP_VALUES = {
        "EURUSD": 10.0,
        "GBPUSD": 10.0,
        "AUDUSD": 10.0,
        "NZDUSD": 10.0,
        "USDJPY": 9.1,  # Approximate, varies with USD/JPY rate
        "USDCHF": 10.0,
        "USDCAD": 7.5,  # Approximate
        "XAUUSD": 1.0,  # Gold - $1 per 0.01 move per 1 oz
    }
    
    def __init__(
        self,
        account_balance: float = 10000.0,
        risk_percent: float = 1.0,
        max_risk_percent: float = 2.0,
        min_lot_size: float = 0.01,
        max_lot_size: float = 10.0
    ):
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.max_risk_percent = max_risk_percent
        self.min_lot_size = min_lot_size
        self.max_lot_size = max_lot_size
    
    def calculate_position_size(
        self,
        pair: str,
        sl_pips: int,
        tp_pips: int,
        risk_percent: Optional[float] = None
    ) -> PositionSize:
        """
        Calculate optimal position size based on risk parameters
        
        Args:
            pair: Currency pair (e.g., "EURUSD")
            sl_pips: Stop loss in pips
            tp_pips: Take profit in pips
            risk_percent: Risk percentage (optional, uses default if not provided)
        
        Returns:
            PositionSize with calculated values
        """
        risk_pct = risk_percent or self.risk_percent
        
        # Ensure risk doesn't exceed maximum
        if risk_pct > self.max_risk_percent:
            logger.warning(f"Risk {risk_pct}% exceeds max {self.max_risk_percent}%, using max")
            risk_pct = self.max_risk_percent
        
        # Calculate risk amount
        risk_amount = self.account_balance * (risk_pct / 100)
        
        # Get pip value for the pair
        pip_value = self.PIP_VALUES.get(pair.upper(), 10.0)
        
        # Calculate position size in lots
        # Formula: Lots = Risk Amount / (SL Pips * Pip Value)
        if sl_pips > 0:
            lots = risk_amount / (sl_pips * pip_value)
        else:
            lots = self.min_lot_size
        
        # Round to 2 decimal places and apply limits
        lots = round(lots, 2)
        lots = max(self.min_lot_size, min(lots, self.max_lot_size))
        
        # Calculate potential profit/loss
        potential_loss = lots * sl_pips * pip_value
        potential_profit = lots * tp_pips * pip_value
        
        return PositionSize(
            lots=lots,
            risk_amount=risk_amount,
            risk_percent=risk_pct,
            pip_value=pip_value,
            sl_pips=sl_pips,
            tp_pips=tp_pips,
            potential_profit=potential_profit,
            potential_loss=potential_loss
        )
    
    def validate_trade(
        self,
        pair: str,
        sl_pips: int,
        tp_pips: int,
        min_rr_ratio: float = 1.5
    ) -> Dict:
        """
        Validate if a trade meets risk management criteria
        
        Returns:
            Dict with validation result and reasons
        """
        issues = []
        
        # Check minimum SL distance
        min_sl = self._get_min_sl(pair)
        if sl_pips < min_sl:
            issues.append(f"SL too tight: {sl_pips} pips < minimum {min_sl} pips")
        
        # Check risk-reward ratio
        if sl_pips > 0:
            rr_ratio = tp_pips / sl_pips
            if rr_ratio < min_rr_ratio:
                issues.append(f"R:R ratio {rr_ratio:.2f} < minimum {min_rr_ratio}")
        
        # Check maximum SL
        max_sl = self._get_max_sl(pair)
        if sl_pips > max_sl:
            issues.append(f"SL too wide: {sl_pips} pips > maximum {max_sl} pips")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "rr_ratio": tp_pips / sl_pips if sl_pips > 0 else 0
        }
    
    def _get_min_sl(self, pair: str) -> int:
        """Get minimum SL for a pair based on typical spreads"""
        min_sl_map = {
            "EURUSD": 10,
            "GBPUSD": 15,
            "USDJPY": 10,
            "XAUUSD": 50,
            "AUDUSD": 12,
            "USDCAD": 15,
        }
        return min_sl_map.get(pair.upper(), 15)
    
    def _get_max_sl(self, pair: str) -> int:
        """Get maximum recommended SL for a pair"""
        max_sl_map = {
            "EURUSD": 100,
            "GBPUSD": 120,
            "USDJPY": 100,
            "XAUUSD": 300,
            "AUDUSD": 100,
            "USDCAD": 100,
        }
        return max_sl_map.get(pair.upper(), 100)
    
    def update_balance(self, new_balance: float):
        """Update account balance"""
        self.account_balance = new_balance
        logger.info(f"Account balance updated to {new_balance}")
    
    def calculate_max_daily_loss(self, max_daily_risk_percent: float = 5.0) -> float:
        """Calculate maximum daily loss allowed"""
        return self.account_balance * (max_daily_risk_percent / 100)
    
    def should_stop_trading(
        self,
        daily_pnl: float,
        max_daily_risk_percent: float = 5.0
    ) -> bool:
        """Check if trading should stop due to daily loss limit"""
        max_loss = self.calculate_max_daily_loss(max_daily_risk_percent)
        return daily_pnl <= -max_loss
