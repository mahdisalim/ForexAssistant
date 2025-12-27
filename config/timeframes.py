"""
Timeframe Configuration for Multi-Timeframe Analysis
"""
from enum import Enum
from typing import Dict, List


class Timeframe(str, Enum):
    """Available timeframes"""
    M1 = "M1"      # 1 minute
    M5 = "M5"      # 5 minutes
    M15 = "M15"    # 15 minutes
    M30 = "M30"    # 30 minutes
    H1 = "H1"      # 1 hour
    H4 = "H4"      # 4 hours
    D1 = "D1"      # Daily
    W1 = "W1"      # Weekly
    MN1 = "MN1"    # Monthly


# Timeframe display names (Persian)
TIMEFRAME_NAMES = {
    "M1": "۱ دقیقه",
    "M5": "۵ دقیقه",
    "M15": "۱۵ دقیقه",
    "M30": "۳۰ دقیقه",
    "H1": "۱ ساعت",
    "H4": "۴ ساعت",
    "D1": "روزانه",
    "W1": "هفتگی",
    "MN1": "ماهانه"
}

# Timeframe weights for multi-timeframe analysis
TIMEFRAME_WEIGHTS = {
    "M1": 0.05,
    "M5": 0.10,
    "M15": 0.15,
    "M30": 0.15,
    "H1": 0.20,
    "H4": 0.25,
    "D1": 0.30,
    "W1": 0.25,
    "MN1": 0.20
}

# Default timeframes for different trading styles
TRADING_STYLES = {
    "scalping": {
        "name": "اسکالپ",
        "timeframes": ["M1", "M5", "M15"],
        "primary": "M5",
        "description": "معاملات کوتاه‌مدت (چند دقیقه تا چند ساعت)"
    },
    "day_trading": {
        "name": "معاملات روزانه",
        "timeframes": ["M15", "M30", "H1", "H4"],
        "primary": "H1",
        "description": "معاملات در طول روز (چند ساعت)"
    },
    "swing_trading": {
        "name": "سوئینگ",
        "timeframes": ["H1", "H4", "D1"],
        "primary": "H4",
        "description": "معاملات میان‌مدت (چند روز)"
    },
    "position_trading": {
        "name": "پوزیشن",
        "timeframes": ["D1", "W1", "MN1"],
        "primary": "D1",
        "description": "معاملات بلندمدت (چند هفته تا چند ماه)"
    }
}

# Multi-timeframe analysis configuration
MTF_CONFIG = {
    "M5": ["M15", "H1"],
    "M15": ["H1", "H4"],
    "M30": ["H1", "H4"],
    "H1": ["H4", "D1"],
    "H4": ["D1", "W1"],
    "D1": ["W1", "MN1"]
}


def get_mtf_timeframes(primary_tf: str) -> List[str]:
    """Get timeframes for multi-timeframe analysis"""
    higher_tfs = MTF_CONFIG.get(primary_tf, [])
    return [primary_tf] + higher_tfs


def calculate_mtf_score(signals: Dict[str, str]) -> Dict:
    """Calculate multi-timeframe confluence score"""
    bullish_score = 0
    bearish_score = 0
    total_weight = 0
    
    for tf, signal in signals.items():
        weight = TIMEFRAME_WEIGHTS.get(tf, 0.1)
        total_weight += weight
        
        if signal.lower() == "bullish":
            bullish_score += weight
        elif signal.lower() == "bearish":
            bearish_score += weight
    
    if total_weight == 0:
        return {"direction": "neutral", "confidence": 0, "confluence": 0}
    
    bullish_pct = (bullish_score / total_weight) * 100
    bearish_pct = (bearish_score / total_weight) * 100
    
    if bullish_pct > bearish_pct:
        direction = "bullish"
        confidence = bullish_pct
    elif bearish_pct > bullish_pct:
        direction = "bearish"
        confidence = bearish_pct
    else:
        direction = "neutral"
        confidence = 50
    
    agreeing = sum(1 for s in signals.values() if s.lower() == direction)
    confluence = (agreeing / len(signals)) * 100 if signals else 0
    
    return {
        "direction": direction,
        "confidence": round(confidence, 1),
        "confluence": round(confluence, 1),
        "bullish_score": round(bullish_pct, 1),
        "bearish_score": round(bearish_pct, 1)
    }
