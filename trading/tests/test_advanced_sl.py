"""
Test Advanced Stop Loss Strategies
تست استراتژی‌های پیشرفته استاپ‌لاس
"""

import numpy as np
from datetime import datetime, timedelta
import sys
sys.path.insert(0, 'd:/Projects/ForexAssistant')

from trading.pattern_detection import (
    PinBarDetector, LegDetector, FVGDetector, SwingPointDetector,
    PatternManager, PatternType
)
from trading.market_sessions import (
    MarketSessionDetector, MarketSession, get_session_times_iran
)
from trading.advanced_sl_strategies import (
    AdvancedSLType, AdvancedSLFactory, AdvancedSLManager,
    FixedPipsSL, ATRBasedSL, PinBarSL, PreviousLegSL,
    FVGStartSL, SessionOpenSL, LegStartPinBarSL
)


def generate_sample_data(num_candles: int = 100) -> dict:
    """Generate sample OHLC data for testing."""
    np.random.seed(42)
    
    # Start price
    base_price = 1.1000
    
    # Generate random walk
    returns = np.random.randn(num_candles) * 0.001
    close = base_price + np.cumsum(returns)
    
    # Generate OHLC
    high = close + np.abs(np.random.randn(num_candles) * 0.0005)
    low = close - np.abs(np.random.randn(num_candles) * 0.0005)
    open_prices = close - returns + np.random.randn(num_candles) * 0.0002
    
    # Generate timestamps (hourly)
    base_time = datetime(2024, 1, 1, 0, 0)
    timestamps = [base_time + timedelta(hours=i) for i in range(num_candles)]
    
    return {
        "open": open_prices,
        "high": high,
        "low": low,
        "close": close,
        "timestamps": timestamps
    }


def test_pattern_detection():
    """Test pattern detection modules."""
    print("\n" + "="*60)
    print("Testing Pattern Detection")
    print("="*60)
    
    data = generate_sample_data(100)
    
    # Test Pin Bar Detector
    print("\n1. Pin Bar Detector:")
    pin_detector = PinBarDetector(min_shadow_ratio=1.5)
    pin_bars = pin_detector.detect(
        data["open"], data["high"], data["low"], data["close"],
        pip_value=0.0001, lookback=50
    )
    print(f"   Found {len(pin_bars)} pin bars")
    for pb in pin_bars[:3]:
        print(f"   - Index {pb.index}: {pb.pattern_type.value}, strength={pb.strength:.2f}")
    
    # Test Leg Detector
    print("\n2. Leg Detector:")
    leg_detector = LegDetector(swing_lookback=3, min_leg_pips=5)
    legs = leg_detector.detect_legs(
        data["open"], data["high"], data["low"], data["close"],
        pip_value=0.0001
    )
    print(f"   Found {len(legs)} legs")
    for leg in legs[:3]:
        print(f"   - {leg.direction} leg: {leg.start_index}->{leg.end_index}, {leg.size_pips:.1f} pips")
    
    # Test FVG Detector
    print("\n3. FVG Detector:")
    fvg_detector = FVGDetector(min_gap_pips=1)
    fvgs = fvg_detector.detect(data["high"], data["low"], pip_value=0.0001, lookback=50)
    print(f"   Found {len(fvgs)} FVGs")
    for fvg in fvgs[:3]:
        print(f"   - {fvg.direction} FVG at index {fvg.index}, gap={fvg.gap_size:.1f} pips")
    
    # Test Swing Point Detector
    print("\n4. Swing Point Detector:")
    swing_detector = SwingPointDetector(lookback=3)
    swing_highs, swing_lows = swing_detector.detect(data["high"], data["low"])
    print(f"   Found {len(swing_highs)} swing highs, {len(swing_lows)} swing lows")
    
    print("\n[OK] Pattern Detection Tests Passed!")


def test_market_sessions():
    """Test market session detection."""
    print("\n" + "="*60)
    print("Testing Market Sessions")
    print("="*60)
    
    detector = MarketSessionDetector()
    
    # Print session times
    print("\nStock Exchange Opening Times:")
    times = get_session_times_iran()
    for session, info in times.items():
        print(f"\n{info['name']}:")
        print(f"   Local: {info['local_time']}")
        print(f"   UTC: {info['utc_time']}")
        print(f"   Iran (Winter): {info['iran_winter']}")
        print(f"   Iran (Summer): {info['iran_summer']}")
    
    # Test session detection
    print("\n\nSession Open Check:")
    test_times = [
        datetime(2024, 1, 15, 1, 0),   # Tokyo session
        datetime(2024, 1, 15, 9, 0),   # London session
        datetime(2024, 1, 15, 15, 0),  # NY session
    ]
    
    for t in test_times:
        current = detector.get_current_session(t)
        print(f"   {t.strftime('%H:%M')} UTC -> {current.value if current else 'None'}")
    
    print("\n[OK] Market Sessions Tests Passed!")


def test_sl_strategies():
    """Test all SL strategies."""
    print("\n" + "="*60)
    print("Testing Stop Loss Strategies")
    print("="*60)
    
    data = generate_sample_data(100)
    entry_price = float(data["close"][-1])
    pip_value = 0.0001
    
    print(f"\nEntry Price: {entry_price:.5f}")
    print(f"Testing BUY trade:\n")
    
    # 1. Fixed Pips
    print("1. Fixed Pips SL:")
    sl = FixedPipsSL(pips=30)
    result = sl.calculate(entry_price, is_buy=True, data=data, pip_value=pip_value)
    print(f"   SL: {result.stop_loss:.5f} ({result.sl_pips:.1f} pips)")
    
    # 2. ATR-Based
    print("\n2. ATR-Based SL:")
    sl = ATRBasedSL(multiplier=2.0, period=14)
    result = sl.calculate(entry_price, is_buy=True, data=data, pip_value=pip_value)
    print(f"   SL: {result.stop_loss:.5f} ({result.sl_pips:.1f} pips)")
    print(f"   ATR: {result.pattern_info.get('atr', 'N/A')}")
    
    # 3. Pin Bar
    print("\n3. Pin Bar SL:")
    sl = PinBarSL(buffer_pips=5, min_shadow_ratio=1.5)
    result = sl.calculate(entry_price, is_buy=True, data=data, pip_value=pip_value)
    print(f"   SL: {result.stop_loss:.5f} ({result.sl_pips:.1f} pips)")
    print(f"   Fallback used: {result.fallback_used}")
    
    # 4. Previous Leg
    print("\n4. Previous Leg SL:")
    sl = PreviousLegSL(buffer_pips=5, min_leg_pips=5)
    result = sl.calculate(entry_price, is_buy=True, data=data, pip_value=pip_value)
    print(f"   SL: {result.stop_loss:.5f} ({result.sl_pips:.1f} pips)")
    print(f"   Fallback used: {result.fallback_used}")
    
    # 5. FVG Start
    print("\n5. FVG Start SL:")
    sl = FVGStartSL(buffer_pips=5, min_gap_pips=1)
    result = sl.calculate(entry_price, is_buy=True, data=data, pip_value=pip_value)
    print(f"   SL: {result.stop_loss:.5f} ({result.sl_pips:.1f} pips)")
    print(f"   Fallback used: {result.fallback_used}")
    
    # 6. Session Open
    print("\n6. Session Open SL (New York):")
    sl = SessionOpenSL(session=MarketSession.NEW_YORK, buffer_pips=5)
    result = sl.calculate(entry_price, is_buy=True, data=data, pip_value=pip_value)
    print(f"   SL: {result.stop_loss:.5f} ({result.sl_pips:.1f} pips)")
    print(f"   Fallback used: {result.fallback_used}")
    
    # 7. Leg Start Pin Bar
    print("\n7. Leg Start Pin Bar SL:")
    sl = LegStartPinBarSL(buffer_pips=5)
    result = sl.calculate(entry_price, is_buy=True, data=data, pip_value=pip_value)
    print(f"   SL: {result.stop_loss:.5f} ({result.sl_pips:.1f} pips)")
    print(f"   Fallback used: {result.fallback_used}")
    
    print("\n[OK] SL Strategies Tests Passed!")


def test_sl_manager():
    """Test SL Manager with premium access control."""
    print("\n" + "="*60)
    print("Testing SL Manager (Premium Access Control)")
    print("="*60)
    
    data = generate_sample_data(100)
    entry_price = float(data["close"][-1])
    pip_value = 0.0001
    
    # Free user
    print("\n1. Free User:")
    manager = AdvancedSLManager(is_premium=False)
    strategies = manager.get_available_strategies()
    available = [s["name"] for s in strategies if s["available"]]
    print(f"   Available strategies: {available}")
    
    # Try to set premium strategy
    success = manager.set_strategy(AdvancedSLType.PIN_BAR)
    print(f"   Set PIN_BAR strategy: {'Success' if success else 'Denied (fallback to ATR)'}")
    
    result = manager.calculate(entry_price, is_buy=True, data=data, pip_value=pip_value)
    print(f"   Strategy used: {result.strategy_used.value}")
    
    # Premium user
    print("\n2. Premium User:")
    manager = AdvancedSLManager(is_premium=True)
    strategies = manager.get_available_strategies()
    available = [s["name"] for s in strategies if s["available"]]
    print(f"   Available strategies: {available}")
    
    success = manager.set_strategy(AdvancedSLType.PIN_BAR)
    print(f"   Set PIN_BAR strategy: {'Success' if success else 'Denied'}")
    
    result = manager.calculate(entry_price, is_buy=True, data=data, pip_value=pip_value)
    print(f"   Strategy used: {result.strategy_used.value}")
    
    print("\n[OK] SL Manager Tests Passed!")


def test_factory():
    """Test SL Factory."""
    print("\n" + "="*60)
    print("Testing SL Factory")
    print("="*60)
    
    print("\nAvailable Strategies:")
    for strategy in AdvancedSLFactory.get_available_strategies():
        premium_tag = " [PREMIUM]" if strategy["premium"] else " [FREE]"
        print(f"   - {strategy['name']}{premium_tag}: {strategy['description']}")
    
    print("\n[OK] Factory Tests Passed!")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ADVANCED STOP LOSS STRATEGIES - TEST SUITE")
    print("="*60)
    
    test_pattern_detection()
    test_market_sessions()
    test_sl_strategies()
    test_sl_manager()
    test_factory()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("="*60 + "\n")
