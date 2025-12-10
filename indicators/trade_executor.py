"""
Trade Executor - MetaTrader 5 Integration
Phase 3: Algorithmic Trading
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    BUY_STOP = "buy_stop"
    SELL_STOP = "sell_stop"


class TradeResult(BaseModel):
    """Result of a trade execution"""
    success: bool
    order_id: Optional[int] = None
    pair: str
    order_type: str
    lots: float
    entry_price: Optional[float] = None
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    message: str
    timestamp: datetime = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)


class Position(BaseModel):
    """Open position"""
    ticket: int
    pair: str
    order_type: str
    lots: float
    entry_price: float
    current_price: float
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    profit: float
    opened_at: datetime


class TradeExecutor:
    """
    Trade execution via MetaTrader 5
    
    Note: Requires MetaTrader5 package and MT5 terminal installed
    pip install MetaTrader5
    """
    
    def __init__(
        self,
        login: int = 0,
        password: str = "",
        server: str = "",
        demo: bool = True
    ):
        self.login = login
        self.password = password
        self.server = server
        self.demo = demo
        self.connected = False
        self.mt5 = None
    
    def connect(self) -> bool:
        """Connect to MetaTrader 5 terminal"""
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
            
            # Initialize MT5
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Login if credentials provided
            if self.login and self.password:
                authorized = mt5.login(
                    login=self.login,
                    password=self.password,
                    server=self.server
                )
                if not authorized:
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    return False
            
            self.connected = True
            account_info = mt5.account_info()
            logger.info(f"Connected to MT5: {account_info.name} (Balance: {account_info.balance})")
            return True
            
        except ImportError:
            logger.error("MetaTrader5 package not installed. Run: pip install MetaTrader5")
            return False
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5"""
        if self.mt5:
            self.mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        if not self.connected:
            return None
        
        info = self.mt5.account_info()
        if info:
            return {
                "login": info.login,
                "name": info.name,
                "balance": info.balance,
                "equity": info.equity,
                "margin": info.margin,
                "free_margin": info.margin_free,
                "leverage": info.leverage,
                "currency": info.currency
            }
        return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information"""
        if not self.connected:
            return None
        
        info = self.mt5.symbol_info(symbol)
        if info:
            return {
                "symbol": info.name,
                "bid": info.bid,
                "ask": info.ask,
                "spread": info.spread,
                "digits": info.digits,
                "point": info.point,
                "trade_mode": info.trade_mode,
                "volume_min": info.volume_min,
                "volume_max": info.volume_max,
                "volume_step": info.volume_step
            }
        return None
    
    def execute_trade(
        self,
        pair: str,
        order_type: OrderType,
        lots: float,
        sl_pips: int = 0,
        tp_pips: int = 0,
        comment: str = "AI Trade"
    ) -> TradeResult:
        """
        Execute a trade
        
        Args:
            pair: Currency pair symbol
            order_type: Type of order
            lots: Position size in lots
            sl_pips: Stop loss in pips
            tp_pips: Take profit in pips
            comment: Trade comment
        
        Returns:
            TradeResult with execution details
        """
        if not self.connected:
            return TradeResult(
                success=False,
                pair=pair,
                order_type=order_type.value,
                lots=lots,
                message="Not connected to MT5"
            )
        
        try:
            # Get symbol info
            symbol_info = self.mt5.symbol_info(pair)
            if not symbol_info:
                return TradeResult(
                    success=False,
                    pair=pair,
                    order_type=order_type.value,
                    lots=lots,
                    message=f"Symbol {pair} not found"
                )
            
            # Enable symbol for trading
            if not symbol_info.visible:
                self.mt5.symbol_select(pair, True)
            
            # Get current price
            tick = self.mt5.symbol_info_tick(pair)
            point = symbol_info.point
            
            # Determine price based on order type
            if order_type in [OrderType.BUY, OrderType.BUY_LIMIT, OrderType.BUY_STOP]:
                price = tick.ask
                sl_price = price - (sl_pips * point * 10) if sl_pips > 0 else 0
                tp_price = price + (tp_pips * point * 10) if tp_pips > 0 else 0
            else:
                price = tick.bid
                sl_price = price + (sl_pips * point * 10) if sl_pips > 0 else 0
                tp_price = price - (tp_pips * point * 10) if tp_pips > 0 else 0
            
            # Map order type to MT5 constants
            mt5_order_type = {
                OrderType.BUY: self.mt5.ORDER_TYPE_BUY,
                OrderType.SELL: self.mt5.ORDER_TYPE_SELL,
                OrderType.BUY_LIMIT: self.mt5.ORDER_TYPE_BUY_LIMIT,
                OrderType.SELL_LIMIT: self.mt5.ORDER_TYPE_SELL_LIMIT,
                OrderType.BUY_STOP: self.mt5.ORDER_TYPE_BUY_STOP,
                OrderType.SELL_STOP: self.mt5.ORDER_TYPE_SELL_STOP,
            }[order_type]
            
            # Prepare request
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": pair,
                "volume": lots,
                "type": mt5_order_type,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": 20,
                "magic": 123456,
                "comment": comment,
                "type_time": self.mt5.ORDER_TIME_GTC,
                "type_filling": self.mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = self.mt5.order_send(request)
            
            if result.retcode != self.mt5.TRADE_RETCODE_DONE:
                return TradeResult(
                    success=False,
                    pair=pair,
                    order_type=order_type.value,
                    lots=lots,
                    message=f"Order failed: {result.comment}"
                )
            
            return TradeResult(
                success=True,
                order_id=result.order,
                pair=pair,
                order_type=order_type.value,
                lots=lots,
                entry_price=price,
                sl_price=sl_price,
                tp_price=tp_price,
                message="Order executed successfully"
            )
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return TradeResult(
                success=False,
                pair=pair,
                order_type=order_type.value,
                lots=lots,
                message=f"Error: {str(e)}"
            )
    
    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        if not self.connected:
            return []
        
        positions = self.mt5.positions_get()
        if not positions:
            return []
        
        result = []
        for pos in positions:
            result.append(Position(
                ticket=pos.ticket,
                pair=pos.symbol,
                order_type="buy" if pos.type == 0 else "sell",
                lots=pos.volume,
                entry_price=pos.price_open,
                current_price=pos.price_current,
                sl_price=pos.sl,
                tp_price=pos.tp,
                profit=pos.profit,
                opened_at=datetime.fromtimestamp(pos.time)
            ))
        
        return result
    
    def close_position(self, ticket: int) -> TradeResult:
        """Close a specific position by ticket"""
        if not self.connected:
            return TradeResult(
                success=False,
                pair="",
                order_type="close",
                lots=0,
                message="Not connected to MT5"
            )
        
        try:
            position = self.mt5.positions_get(ticket=ticket)
            if not position:
                return TradeResult(
                    success=False,
                    pair="",
                    order_type="close",
                    lots=0,
                    message=f"Position {ticket} not found"
                )
            
            pos = position[0]
            
            # Determine close order type
            close_type = self.mt5.ORDER_TYPE_SELL if pos.type == 0 else self.mt5.ORDER_TYPE_BUY
            price = self.mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else self.mt5.symbol_info_tick(pos.symbol).ask
            
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 123456,
                "comment": "AI Close",
                "type_time": self.mt5.ORDER_TIME_GTC,
                "type_filling": self.mt5.ORDER_FILLING_IOC,
            }
            
            result = self.mt5.order_send(request)
            
            if result.retcode != self.mt5.TRADE_RETCODE_DONE:
                return TradeResult(
                    success=False,
                    pair=pos.symbol,
                    order_type="close",
                    lots=pos.volume,
                    message=f"Close failed: {result.comment}"
                )
            
            return TradeResult(
                success=True,
                order_id=result.order,
                pair=pos.symbol,
                order_type="close",
                lots=pos.volume,
                entry_price=price,
                message="Position closed successfully"
            )
            
        except Exception as e:
            logger.error(f"Close position error: {e}")
            return TradeResult(
                success=False,
                pair="",
                order_type="close",
                lots=0,
                message=f"Error: {str(e)}"
            )
    
    def modify_position(
        self,
        ticket: int,
        sl_price: Optional[float] = None,
        tp_price: Optional[float] = None
    ) -> TradeResult:
        """Modify SL/TP of an open position"""
        if not self.connected:
            return TradeResult(
                success=False,
                pair="",
                order_type="modify",
                lots=0,
                message="Not connected to MT5"
            )
        
        try:
            position = self.mt5.positions_get(ticket=ticket)
            if not position:
                return TradeResult(
                    success=False,
                    pair="",
                    order_type="modify",
                    lots=0,
                    message=f"Position {ticket} not found"
                )
            
            pos = position[0]
            
            request = {
                "action": self.mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": ticket,
                "sl": sl_price if sl_price else pos.sl,
                "tp": tp_price if tp_price else pos.tp,
            }
            
            result = self.mt5.order_send(request)
            
            if result.retcode != self.mt5.TRADE_RETCODE_DONE:
                return TradeResult(
                    success=False,
                    pair=pos.symbol,
                    order_type="modify",
                    lots=pos.volume,
                    message=f"Modify failed: {result.comment}"
                )
            
            return TradeResult(
                success=True,
                order_id=result.order,
                pair=pos.symbol,
                order_type="modify",
                lots=pos.volume,
                sl_price=sl_price,
                tp_price=tp_price,
                message="Position modified successfully"
            )
            
        except Exception as e:
            logger.error(f"Modify position error: {e}")
            return TradeResult(
                success=False,
                pair="",
                order_type="modify",
                lots=0,
                message=f"Error: {str(e)}"
            )
