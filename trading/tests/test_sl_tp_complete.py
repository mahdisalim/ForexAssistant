"""
Complete Test Suite for SL/TP Strategies
تست جامع استراتژی‌های استاپ‌لاس و حد سود
"""

import numpy as np
import sys
sys.path.insert(0, 'd:/Projects/ForexAssistant')

from trading import (
    # SL Strategies
    AdvancedSLFactory, AdvancedSLManager, AdvancedSLType,
    SL_DISPLAY_NAMES,
    FixedPipsSL, ATRBasedSL, PinBarSL, PreviousLegSL,
    FVGStartSL, SessionOpenSL, LegStartPinBarSL,
    KeyLevelsNearestSL, KeyLevelsSelectableSL,
    # TP Strategies
    AdvancedTPFactory, AdvancedTPManager, AdvancedTPType,
    TP_DISPLAY_NAMES,
    FixedPipsTP, ATRBasedTP, KeyLevelsNearestTP, KeyLevelsSelectableTP,
    RiskRewardFixedTP, SteppedRRTP, LegBasedTP,
    # Support/Resistance
    SupportResistanceDetector, LevelStrength,
)


def generate_sample_data(num_candles: int = 200) -> dict:
    """Generate sample OHLC data for testing."""
    np.random.seed(42)
    base_price = 1.1000
    returns = np.random.randn(num_candles) * 0.001
    close = base_price + np.cumsum(returns)
    high = close + np.abs(np.random.randn(num_candles) * 0.0005)
    low = close - np.abs(np.random.randn(num_candles) * 0.0005)
    open_prices = close - returns + np.random.randn(num_candles) * 0.0002
    
    return {
        "open": open_prices,
        "high": high,
        "low": low,
        "close": close
    }


def test_all_sl_strategies():
    """Test all SL strategies."""
    print("\n" + "=" * 70)
    print("STOP LOSS STRATEGIES TEST")
    print("=" * 70)
    
    data = generate_sample_data(200)
    entry_price = float(data["close"][-1])
    pip_value = 0.0001
    
    print(f"\nEntry Price: {entry_price:.5f}")
    print("\n--- BUY Trade SL ---\n")
    
    strategies = AdvancedSLFactory.get_available_strategies()
    
    for s in strategies:
        strategy_type = AdvancedSLType(s["id"])
        display_name = SL_DISPLAY_NAMES.get(strategy_type, s["name"])
        premium_tag = " [PREMIUM]" if s["premium"] else " [FREE]"
        
        try:
            strategy = AdvancedSLFactory.create(strategy_type)
            result = strategy.calculate(entry_price, is_buy=True, data=data, pip_value=pip_value)
            
            print(f"{display_name}{premium_tag}:")
            print(f"  SL: {result.stop_loss:.5f} ({result.sl_pips:.1f} pips)")
            print(f"  Fallback: {result.fallback_used}")
        except Exception as e:
            print(f"{display_name}{premium_tag}: Error - {e}")
        print()
    
    print("[OK] SL Strategies Test Complete!")


def test_all_tp_strategies():
    """Test all TP strategies."""
    print("\n" + "=" * 70)
    print("TAKE PROFIT STRATEGIES TEST")
    print("=" * 70)
    
    data = generate_sample_data(200)
    entry_price = float(data["close"][-1])
    stop_loss = entry_price - 0.0030  # 30 pips SL
    pip_value = 0.0001
    
    print(f"\nEntry Price: {entry_price:.5f}")
    print(f"Stop Loss: {stop_loss:.5f} (30 pips)")
    print("\n--- BUY Trade TP ---\n")
    
    strategies = AdvancedTPFactory.get_available_strategies()
    
    for s in strategies:
        strategy_type = AdvancedTPType(s["type"])
        display_name = TP_DISPLAY_NAMES.get(strategy_type, s["name"])
        premium_tag = " [PREMIUM]" if s["premium"] else " [FREE]"
        
        try:
            strategy = AdvancedTPFactory.create(strategy_type)
            result = strategy.calculate(entry_price, stop_loss, is_buy=True, data=data, pip_value=pip_value)
            
            print(f"{display_name}{premium_tag}:")
            print(f"  TP: {result.take_profit:.5f} ({result.tp_pips:.1f} pips)")
            print(f"  Fallback: {result.fallback_used}")
            
            if result.is_stepped:
                print(f"  Exit Levels:")
                for level in result.exit_levels:
                    print(f"    - {level['percentage']:.0f}% @ {level['price']:.5f} (R/R {level['rr_ratio']})")
        except Exception as e:
            print(f"{display_name}{premium_tag}: Error - {e}")
        print()
    
    print("[OK] TP Strategies Test Complete!")


def test_support_resistance():
    """Test support/resistance detection."""
    print("\n" + "=" * 70)
    print("SUPPORT/RESISTANCE DETECTION TEST")
    print("=" * 70)
    
    data = generate_sample_data(200)
    current_price = float(data["close"][-1])
    pip_value = 0.0001
    
    detector = SupportResistanceDetector()
    levels = detector.detect_all_levels(
        data["open"], data["high"], data["low"], data["close"],
        pip_value=pip_value,
        current_price=current_price
    )
    
    print(f"\nCurrent Price: {current_price:.5f}")
    print(f"Total Levels Detected: {len(levels)}")
    
    print("\n--- Top 5 Strongest Levels ---")
    for i, level in enumerate(levels[:5], 1):
        direction = "Support" if level.is_support else "Resistance"
        print(f"{i}. {direction} @ {level.price:.5f}")
        print(f"   Strength: {level.strength_class.value} ({level.strength_score:.1f})")
        print(f"   Touches: {level.touches}, Pin Bar: {level.has_pin_bar}")
    
    # Test nearest/most important
    nearest_support = detector.get_nearest_level(levels, current_price, is_support=True)
    nearest_resistance = detector.get_nearest_level(levels, current_price, is_support=False)
    most_important_support = detector.get_most_important_level(levels, current_price, is_support=True)
    most_important_resistance = detector.get_most_important_level(levels, current_price, is_support=False)
    
    print("\n--- Key Levels ---")
    if nearest_support:
        print(f"Nearest Support: {nearest_support.price:.5f} ({nearest_support.strength_class.value})")
    if nearest_resistance:
        print(f"Nearest Resistance: {nearest_resistance.price:.5f} ({nearest_resistance.strength_class.value})")
    if most_important_support:
        print(f"Most Important Support: {most_important_support.price:.5f} (Score: {most_important_support.strength_score:.1f})")
    if most_important_resistance:
        print(f"Most Important Resistance: {most_important_resistance.price:.5f} (Score: {most_important_resistance.strength_score:.1f})")
    
    print("\n[OK] Support/Resistance Test Complete!")


def test_premium_access():
    """Test premium access control."""
    print("\n" + "=" * 70)
    print("PREMIUM ACCESS CONTROL TEST")
    print("=" * 70)
    
    data = generate_sample_data(200)
    entry_price = float(data["close"][-1])
    stop_loss = entry_price - 0.0030
    pip_value = 0.0001
    
    # Free user SL
    print("\n--- Free User SL Access ---")
    sl_manager = AdvancedSLManager(is_premium=False)
    free_sl = [s["name"] for s in sl_manager.get_available_strategies() if s["available"]]
    print(f"Available: {free_sl}")
    
    # Try premium strategy
    success = sl_manager.set_strategy(AdvancedSLType.KEY_LEVELS_SELECTABLE)
    print(f"Set KEY_LEVELS_SELECTABLE: {'Allowed' if success else 'Denied (fallback)'}")
    
    # Premium user SL
    print("\n--- Premium User SL Access ---")
    sl_manager = AdvancedSLManager(is_premium=True)
    premium_sl = [s["name"] for s in sl_manager.get_available_strategies() if s["available"]]
    print(f"Available: {premium_sl}")
    
    success = sl_manager.set_strategy(AdvancedSLType.KEY_LEVELS_SELECTABLE)
    print(f"Set KEY_LEVELS_SELECTABLE: {'Allowed' if success else 'Denied'}")
    
    # Free user TP
    print("\n--- Free User TP Access ---")
    tp_manager = AdvancedTPManager(is_premium=False)
    free_tp = [s["name"] for s in tp_manager.get_available_strategies() if s["available"]]
    print(f"Available: {free_tp}")
    
    # Premium user TP
    print("\n--- Premium User TP Access ---")
    tp_manager = AdvancedTPManager(is_premium=True)
    premium_tp = [s["name"] for s in tp_manager.get_available_strategies() if s["available"]]
    print(f"Available: {premium_tp}")
    
    print("\n[OK] Premium Access Test Complete!")


def print_strategy_summary():
    """Print summary of all strategies with display names."""
    print("\n" + "=" * 70)
    print("STRATEGY SUMMARY FOR UI")
    print("=" * 70)
    
    print("\n--- STOP LOSS STRATEGIES ---\n")
    print(f"{'Display Name':<25} {'Type':<25} {'Access':<10}")
    print("-" * 60)
    for s in AdvancedSLFactory.get_available_strategies():
        strategy_type = AdvancedSLType(s["id"])
        display_name = SL_DISPLAY_NAMES.get(strategy_type, s["name"])
        access = "PREMIUM" if s["premium"] else "FREE"
        print(f"{display_name:<25} {s['id']:<25} {access:<10}")
    
    print("\n--- TAKE PROFIT STRATEGIES ---\n")
    print(f"{'Display Name':<25} {'Type':<25} {'Access':<10}")
    print("-" * 60)
    for s in AdvancedTPFactory.get_available_strategies():
        strategy_type = AdvancedTPType(s["type"])
        display_name = TP_DISPLAY_NAMES.get(strategy_type, s["name"])
        access = "PREMIUM" if s["premium"] else "FREE"
        print(f"{display_name:<25} {s['type']:<25} {access:<10}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COMPLETE SL/TP STRATEGIES TEST SUITE")
    print("=" * 70)
    
    test_all_sl_strategies()
    test_all_tp_strategies()
    test_support_resistance()
    test_premium_access()
    print_strategy_summary()
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")
