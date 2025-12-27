"""
Market Sessions Module
Provides detection of market session times and session-based candle identification.

IMPORTANT: Iran does NOT observe DST (since 1401/2022). Iran is always UTC+3:30.

Stock Exchange Opening Times:
=============================

Tokyo Stock Exchange (TSE):
- Local: 09:00 - 15:30 JST (with lunch break 11:30-12:30)
- UTC: 00:00 - 06:30 UTC (Japan has NO DST)
- Iran: 03:30 (always, since both Iran and Japan have no DST)

London Stock Exchange (LSE):
- Local: 08:00 - 16:30 UK time
- UTC (Winter GMT): 08:00 - 16:30 UTC
- UTC (Summer BST): 07:00 - 15:30 UTC
- Iran (Winter - when London is GMT): 11:30
- Iran (Summer - when London is BST): 10:30

New York Stock Exchange (NYSE):
- Local: 09:30 - 16:00 ET
- UTC (Winter EST): 14:30 - 21:00 UTC
- UTC (Summer EDT): 13:30 - 20:00 UTC
- Iran (Winter - when NY is EST): 18:00
- Iran (Summer - when NY is EDT): 17:00

Note: "Winter/Summer" refers to DST status in London/New York, NOT Iran.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, time, timedelta
import numpy as np


class MarketSession(str, Enum):
    """Major market sessions"""
    TOKYO = "tokyo"
    LONDON = "london"
    NEW_YORK = "new_york"
    SYDNEY = "sydney"


@dataclass
class SessionInfo:
    """Information about a market session"""
    session: MarketSession
    name: str
    stock_exchange_open_utc: time  # Stock exchange opening time in UTC
    forex_session_start_utc: time  # Forex session start in UTC
    forex_session_end_utc: time    # Forex session end in UTC
    timezone: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session": self.session.value,
            "name": self.name,
            "stock_exchange_open_utc": self.stock_exchange_open_utc.isoformat(),
            "forex_session_start_utc": self.forex_session_start_utc.isoformat(),
            "forex_session_end_utc": self.forex_session_end_utc.isoformat(),
            "timezone": self.timezone
        }


@dataclass
class SessionCandle:
    """Information about a session opening candle"""
    session: MarketSession
    candle_index: int
    candle_time: datetime
    high: float
    low: float
    open_price: float
    close_price: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session": self.session.value,
            "candle_index": self.candle_index,
            "candle_time": self.candle_time.isoformat() if self.candle_time else None,
            "high": self.high,
            "low": self.low,
            "open": self.open_price,
            "close": self.close_price
        }


class MarketSessionDetector:
    """
    Detects market session times and identifies session opening candles.
    
    Stock Exchange Opening Times (Verified):
    =========================================
    
    Tokyo Stock Exchange (TSE):
    - Local: 09:00 - 15:30 JST (lunch break 11:30-12:30)
    - Opens: 09:00 JST = 00:00 UTC
    - Japan does NOT observe DST
    - Iran Time: 03:30 (winter) / 04:30 (summer)
    
    London Stock Exchange (LSE):
    - Local: 08:00 - 16:30 UK time
    - Opens: 08:00 GMT = 08:00 UTC (winter) / 07:00 UTC (summer BST)
    - Iran Time: 11:30 (winter) / 11:30 (summer, both offset)
    
    New York Stock Exchange (NYSE):
    - Local: 09:30 - 16:00 ET
    - Opens: 09:30 EST = 14:30 UTC (winter) / 13:30 UTC (summer EDT)
    - Iran Time: 18:00 (winter) / 18:00 (summer, both offset)
    
    Note: Default times are winter (standard) times.
    """
    
    # Session definitions with stock exchange opening times
    SESSIONS = {
        MarketSession.TOKYO: SessionInfo(
            session=MarketSession.TOKYO,
            name="Tokyo Stock Exchange",
            stock_exchange_open_utc=time(0, 0),   # 09:00 JST = 00:00 UTC (Japan no DST)
            forex_session_start_utc=time(0, 0),
            forex_session_end_utc=time(6, 30),    # TSE closes 15:30 JST = 06:30 UTC
            timezone="Asia/Tokyo"
        ),
        MarketSession.LONDON: SessionInfo(
            session=MarketSession.LONDON,
            name="London Stock Exchange",
            stock_exchange_open_utc=time(8, 0),   # 08:00 GMT = 08:00 UTC (winter)
            forex_session_start_utc=time(8, 0),
            forex_session_end_utc=time(16, 30),   # LSE closes 16:30 GMT
            timezone="Europe/London"
        ),
        MarketSession.NEW_YORK: SessionInfo(
            session=MarketSession.NEW_YORK,
            name="New York Stock Exchange",
            stock_exchange_open_utc=time(14, 30), # 09:30 EST = 14:30 UTC (winter)
            forex_session_start_utc=time(14, 30),
            forex_session_end_utc=time(21, 0),    # NYSE closes 16:00 EST = 21:00 UTC
            timezone="America/New_York"
        ),
        MarketSession.SYDNEY: SessionInfo(
            session=MarketSession.SYDNEY,
            name="Australian Securities Exchange",
            stock_exchange_open_utc=time(23, 0),  # 10:00 AEDT = 23:00 UTC (summer) / 00:00 UTC (winter)
            forex_session_start_utc=time(22, 0),
            forex_session_end_utc=time(6, 0),
            timezone="Australia/Sydney"
        )
    }
    
    def __init__(self, use_dst: bool = False):
        """
        Initialize session detector.
        
        Args:
            use_dst: Whether to adjust for daylight saving time
        """
        self.use_dst = use_dst
    
    def get_session_info(self, session: MarketSession) -> SessionInfo:
        """Get information about a specific session."""
        return self.SESSIONS[session]
    
    def get_stock_exchange_open_utc(self, session: MarketSession) -> time:
        """
        Get the stock exchange opening time in UTC.
        
        Returns:
            Opening time in UTC
        """
        return self.SESSIONS[session].stock_exchange_open_utc
    
    def get_iran_time(self, session: MarketSession, is_summer_dst: bool = False) -> str:
        """
        Get the stock exchange opening time in Iran time.
        
        Args:
            session: Market session
            is_summer_dst: Whether DST is active in that market's country (NOT Iran)
                          Iran does NOT observe DST (since 1401/2022)
                          Iran is always UTC+3:30
            
        Returns:
            Time string in Iran timezone
        """
        # Iran is always UTC+3:30 (no DST since 2022)
        iran_offset = timedelta(hours=3, minutes=30)
        
        # Get UTC time - adjust for DST in the source market
        utc_time = self.SESSIONS[session].stock_exchange_open_utc
        
        # For markets with DST (London, New York), summer time means 1 hour earlier in UTC
        # Tokyo/Japan does NOT have DST
        if is_summer_dst and session in [MarketSession.LONDON, MarketSession.NEW_YORK]:
            # In summer, these markets open 1 hour earlier in UTC
            utc_dt = datetime.combine(datetime.today(), utc_time)
            utc_dt = utc_dt - timedelta(hours=1)
        else:
            utc_dt = datetime.combine(datetime.today(), utc_time)
        
        iran_dt = utc_dt + iran_offset
        
        return iran_dt.strftime("%H:%M")
    
    def is_session_open(
        self,
        timestamp: datetime,
        session: MarketSession,
        use_forex_hours: bool = True
    ) -> bool:
        """
        Check if a session is currently open.
        
        Args:
            timestamp: UTC timestamp to check
            session: Session to check
            use_forex_hours: Use forex session hours (True) or stock exchange hours (False)
        """
        session_info = self.SESSIONS[session]
        current_time = timestamp.time()
        
        if use_forex_hours:
            start = session_info.forex_session_start_utc
            end = session_info.forex_session_end_utc
        else:
            # Stock exchange is typically open for ~6-8 hours
            start = session_info.stock_exchange_open_utc
            # Approximate close time (6.5 hours for NYSE, 8 hours for others)
            if session == MarketSession.NEW_YORK:
                end = time(21, 0)  # NYSE closes 16:00 EST = 21:00 UTC
            elif session == MarketSession.LONDON:
                end = time(16, 30)  # LSE closes 16:30 GMT
            elif session == MarketSession.TOKYO:
                end = time(6, 0)   # TSE closes 15:00 JST = 06:00 UTC
            else:
                end = session_info.forex_session_end_utc
        
        # Handle sessions that cross midnight
        if start <= end:
            return start <= current_time <= end
        else:
            return current_time >= start or current_time <= end
    
    def find_session_opening_candle(
        self,
        timestamps: List[datetime],
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        open_prices: np.ndarray,
        close_prices: np.ndarray,
        session: MarketSession,
        lookback: int = 100
    ) -> Optional[SessionCandle]:
        """
        Find the most recent candle at session opening.
        
        Args:
            timestamps: List of candle timestamps (UTC)
            high_prices: High prices array
            low_prices: Low prices array
            open_prices: Open prices array
            close_prices: Close prices array
            session: Target session
            lookback: Number of candles to look back
            
        Returns:
            SessionCandle if found, None otherwise
        """
        if len(timestamps) == 0:
            return None
        
        session_open_time = self.SESSIONS[session].stock_exchange_open_utc
        
        # Search from most recent backwards
        start_idx = max(0, len(timestamps) - lookback)
        
        for i in range(len(timestamps) - 1, start_idx - 1, -1):
            candle_time = timestamps[i]
            
            # Check if this candle is at session opening
            # Allow some tolerance (within same hour)
            if self._is_session_opening_candle(candle_time, session_open_time):
                return SessionCandle(
                    session=session,
                    candle_index=i,
                    candle_time=candle_time,
                    high=high_prices[i],
                    low=low_prices[i],
                    open_price=open_prices[i],
                    close_price=close_prices[i]
                )
        
        return None
    
    def _is_session_opening_candle(
        self,
        candle_time: datetime,
        session_open: time,
        tolerance_minutes: int = 30
    ) -> bool:
        """
        Check if a candle is at session opening time.
        
        Args:
            candle_time: Candle timestamp
            session_open: Session opening time
            tolerance_minutes: Tolerance in minutes
        """
        candle_minutes = candle_time.hour * 60 + candle_time.minute
        session_minutes = session_open.hour * 60 + session_open.minute
        
        diff = abs(candle_minutes - session_minutes)
        
        # Handle midnight crossing
        if diff > 720:  # More than 12 hours
            diff = 1440 - diff
        
        return diff <= tolerance_minutes
    
    def find_all_session_candles(
        self,
        timestamps: List[datetime],
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        open_prices: np.ndarray,
        close_prices: np.ndarray,
        session: MarketSession,
        lookback: int = 100,
        max_results: int = 5
    ) -> List[SessionCandle]:
        """
        Find all session opening candles within lookback period.
        
        Returns list of SessionCandle objects, most recent first.
        """
        results = []
        session_open_time = self.SESSIONS[session].stock_exchange_open_utc
        
        start_idx = max(0, len(timestamps) - lookback)
        
        for i in range(len(timestamps) - 1, start_idx - 1, -1):
            if len(results) >= max_results:
                break
                
            candle_time = timestamps[i]
            
            if self._is_session_opening_candle(candle_time, session_open_time):
                results.append(SessionCandle(
                    session=session,
                    candle_index=i,
                    candle_time=candle_time,
                    high=high_prices[i],
                    low=low_prices[i],
                    open_price=open_prices[i],
                    close_price=close_prices[i]
                ))
        
        return results
    
    def get_current_session(self, timestamp: datetime) -> Optional[MarketSession]:
        """
        Get the currently active session based on timestamp.
        
        Returns the most relevant active session, or None if no major session is active.
        """
        # Priority: NY > London > Tokyo > Sydney
        priority_order = [
            MarketSession.NEW_YORK,
            MarketSession.LONDON,
            MarketSession.TOKYO,
            MarketSession.SYDNEY
        ]
        
        for session in priority_order:
            if self.is_session_open(timestamp, session, use_forex_hours=True):
                return session
        
        return None
    
    @staticmethod
    def print_session_times():
        """Print all session times for reference."""
        print("=" * 60)
        print("STOCK EXCHANGE OPENING TIMES")
        print("=" * 60)
        print()
        
        detector = MarketSessionDetector()
        
        sessions_info = [
            (MarketSession.TOKYO, "Tokyo Stock Exchange (TSE)", "09:00 JST"),
            (MarketSession.LONDON, "London Stock Exchange (LSE)", "08:00 GMT"),
            (MarketSession.NEW_YORK, "New York Stock Exchange (NYSE)", "09:30 EST"),
        ]
        
        for session, name, local_time in sessions_info:
            utc_time = detector.get_stock_exchange_open_utc(session)
            iran_winter = detector.get_iran_time(session, is_summer_dst=False)
            iran_summer = detector.get_iran_time(session, is_summer_dst=True)
            
            print(f"{name}:")
            print(f"  Local Time: {local_time}")
            print(f"  UTC Time: {utc_time.strftime('%H:%M')}")
            print(f"  Iran Time (Winter): {iran_winter}")
            print(f"  Iran Time (Summer): {iran_summer}")
            print()


# Convenience function to get session times
def get_session_times_iran() -> Dict[str, Dict[str, str]]:
    """
    Get all session opening times in Iran timezone.
    
    Note: Iran does NOT have DST (since 1401/2022). Iran is always UTC+3:30.
    "Winter/Summer" refers to DST status in London/New York, NOT Iran.
    
    Returns:
        Dictionary with session times in Iran timezone
    """
    detector = MarketSessionDetector()
    
    return {
        "tokyo": {
            "name": "Tokyo Stock Exchange",
            "local_time": "09:00 JST",
            "utc_time": "00:00 UTC",
            "iran_time": "03:30",  # Always same (Japan has no DST, Iran has no DST)
            "note": "Japan and Iran both have no DST"
        },
        "london": {
            "name": "London Stock Exchange",
            "local_time": "08:00 UK time",
            "utc_winter": "08:00 UTC (GMT)",
            "utc_summer": "07:00 UTC (BST)",
            "iran_when_london_winter": detector.get_iran_time(MarketSession.LONDON, False),  # 11:30
            "iran_when_london_summer": detector.get_iran_time(MarketSession.LONDON, True),   # 10:30
            "note": "London has DST, Iran does not"
        },
        "new_york": {
            "name": "New York Stock Exchange",
            "local_time": "09:30 ET",
            "utc_winter": "14:30 UTC (EST)",
            "utc_summer": "13:30 UTC (EDT)",
            "iran_when_ny_winter": detector.get_iran_time(MarketSession.NEW_YORK, False),  # 18:00
            "iran_when_ny_summer": detector.get_iran_time(MarketSession.NEW_YORK, True),   # 17:00
            "note": "New York has DST, Iran does not"
        }
    }


if __name__ == "__main__":
    # Print session times for verification
    MarketSessionDetector.print_session_times()
    
    print("\nSession times in Iran timezone:")
    times = get_session_times_iran()
    
    print(f"\n{times['tokyo']['name']}:")
    print(f"  Iran: {times['tokyo']['iran_time']} ({times['tokyo']['note']})")
    
    print(f"\n{times['london']['name']}:")
    print(f"  Iran (when London winter/GMT): {times['london']['iran_when_london_winter']}")
    print(f"  Iran (when London summer/BST): {times['london']['iran_when_london_summer']}")
    
    print(f"\n{times['new_york']['name']}:")
    print(f"  Iran (when NY winter/EST): {times['new_york']['iran_when_ny_winter']}")
    print(f"  Iran (when NY summer/EDT): {times['new_york']['iran_when_ny_summer']}")
