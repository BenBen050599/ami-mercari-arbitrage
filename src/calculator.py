"""
费用计算器
"""

from dataclasses import dataclass

@dataclass
class ArbitrageResult:
    condition: str
    buy_price: int
    sell_price: int
    mercari_fee: int
    shipping: int
    packaging: int
    transfer_fee: int
    net_profit: int
    profit_rate: float
    should_buy: bool

class Calculator:
    SHIPPING_COSTS = {
        "small": 700,
        "medium": 1000,
        "large": 1500,
        "extra_large": 2000,
    }
    
    CONDITION_MULTIPLIERS = {
        "A": 1.0,
        "B": 0.9,
        "C": 0.8,
        "D": 0.6,
    }
    
    def __init__(self, min_profit: int = 1000, min_profit_rate: float = 20):
        self.min_profit = min_profit
        self.min_profit_rate = min_profit_rate
    
    def calculate(self, amiami_price: int, mercari_avg_price: int, condition: str = "A", size: str = "small") -> ArbitrageResult:
        # 根据成色调整售价
        adjusted_price = int(mercari_avg_price * self.CONDITION_MULTIPLIERS.get(condition, 1.0))
        
        # 计算成本
        mercari_fee = int(adjusted_price * 0.10)
        shipping = self.SHIPPING_COSTS.get(size, 700)
        packaging = 150
        transfer_fee = 200
        
        # 净利润
        total_cost = amiami_price + packaging + transfer_fee
        total_revenue = adjusted_price - mercari_fee - shipping
        net_profit = total_revenue - total_cost
        profit_rate = (net_profit / amiami_price) * 100 if amiami_price > 0 else 0
        
        should_buy = (
            net_profit >= self.min_profit
            and profit_rate >= self.min_profit_rate
            and condition in ["A", "B", "C"]
        )
        
        return ArbitrageResult(
            condition=condition,
            buy_price=amiami_price,
            sell_price=adjusted_price,
            mercari_fee=mercari_fee,
            shipping=shipping,
            packaging=packaging,
            transfer_fee=transfer_fee,
            net_profit=net_profit,
            profit_rate=profit_rate,
            should_buy=should_buy
        )
