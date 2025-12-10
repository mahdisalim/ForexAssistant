"""
Risk/Reward Take Profit Strategy
استراتژی حد سود بر اساس نسبت ریسک به ریوارد
"""

from typing import Optional
from .base import BaseTPStrategy, TPResult, TradeDirection


class RiskRewardTP(BaseTPStrategy):
    """
    استراتژی Take Profit بر اساس نسبت ریسک به ریوارد
    
    TP در فاصله‌ای از قیمت ورود قرار می‌گیرد که
    نسبت مشخصی از فاصله SL باشد.
    
    مثال:
    - Entry: 1.1000
    - SL: 1.0950 (50 پیپ ریسک)
    - R:R = 2.0
    - TP: 1.1100 (100 پیپ ریوارد)
    
    Attributes:
        ratio: نسبت ریسک به ریوارد (پیش‌فرض 2.0 یعنی 1:2)
    """
    
    # نسبت‌های رایج
    CONSERVATIVE = 1.0    # 1:1
    STANDARD = 1.5        # 1:1.5
    AGGRESSIVE = 2.0      # 1:2
    VERY_AGGRESSIVE = 3.0 # 1:3
    
    def __init__(self, ratio: float = 2.0, pip_value: float = 0.0001):
        """
        Args:
            ratio: نسبت ریسک به ریوارد (مثلاً 2.0 برای 1:2)
            pip_value: ارزش هر پیپ
        """
        super().__init__(pip_value)
        self.ratio = ratio
    
    @property
    def name(self) -> str:
        return f"R:R {self.ratio}"
    
    def calculate(self, entry_price: float, sl_price: float,
                  direction: TradeDirection, **kwargs) -> Optional[TPResult]:
        """
        محاسبه Take Profit بر اساس R:R
        
        Args:
            entry_price: قیمت ورود
            sl_price: قیمت SL
            direction: جهت معامله
            
        Returns:
            TPResult
        """
        # محاسبه ریسک
        risk = abs(entry_price - sl_price)
        
        if risk == 0:
            return None
        
        # محاسبه ریوارد
        reward = risk * self.ratio
        
        # محاسبه TP
        if direction == TradeDirection.BUY:
            tp_price = entry_price + reward
        else:
            tp_price = entry_price - reward
        
        # محاسبه پیپ
        pips = self.calculate_pips(entry_price, tp_price)
        
        return TPResult(
            tp_price=tp_price,
            method=self.name,
            reason=f"ریسک: {self.calculate_pips(entry_price, sl_price):.1f} پیپ × {self.ratio} = {pips:.1f} پیپ ریوارد",
            risk_reward_ratio=self.ratio,
            pips=pips,
            confidence=85.0
        )


class MultiTargetTP(BaseTPStrategy):
    """
    استراتژی چند هدفه (Partial TP)
    
    چند سطح TP با نسبت‌های مختلف تعریف می‌کند.
    مناسب برای بستن بخشی از معامله در هر سطح.
    
    مثال:
    - TP1: 1:1 (بستن 50% پوزیشن)
    - TP2: 1:2 (بستن 30% پوزیشن)
    - TP3: 1:3 (بستن 20% پوزیشن)
    """
    
    def __init__(self, 
                 targets: list = None,
                 pip_value: float = 0.0001):
        """
        Args:
            targets: لیست تاپل‌ها [(ratio, percent), ...]
                     مثال: [(1.0, 50), (2.0, 30), (3.0, 20)]
            pip_value: ارزش هر پیپ
        """
        super().__init__(pip_value)
        self.targets = targets or [
            (1.0, 50),   # TP1: R:R 1:1, بستن 50%
            (2.0, 30),   # TP2: R:R 1:2, بستن 30%
            (3.0, 20),   # TP3: R:R 1:3, بستن 20%
        ]
    
    @property
    def name(self) -> str:
        return "Multi-Target TP"
    
    def calculate(self, entry_price: float, sl_price: float,
                  direction: TradeDirection, **kwargs) -> Optional[TPResult]:
        """
        محاسبه اولین TP (برای سازگاری با interface)
        برای همه TPها از calculate_all استفاده کنید.
        """
        all_tps = self.calculate_all(entry_price, sl_price, direction)
        return all_tps[0] if all_tps else None
    
    def calculate_all(self, entry_price: float, sl_price: float,
                      direction: TradeDirection) -> list:
        """
        محاسبه همه سطوح TP
        
        Returns:
            لیست TPResult برای هر سطح
        """
        results = []
        risk = abs(entry_price - sl_price)
        
        if risk == 0:
            return results
        
        for i, (ratio, percent) in enumerate(self.targets, 1):
            reward = risk * ratio
            
            if direction == TradeDirection.BUY:
                tp_price = entry_price + reward
            else:
                tp_price = entry_price - reward
            
            pips = self.calculate_pips(entry_price, tp_price)
            
            results.append(TPResult(
                tp_price=tp_price,
                method=f"TP{i} (R:R {ratio})",
                reason=f"سطح {i}: بستن {percent}% در R:R {ratio}",
                risk_reward_ratio=ratio,
                pips=pips,
                confidence=80.0
            ))
        
        return results
