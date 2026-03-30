"""
费用计算器（中古手办专用）
"""

from dataclasses import dataclass

@dataclass
class ArbitrageResult:
    condition: str
    buy_price: int
    sell_price: int          # 调整后的 Mercari 预期售价
    mercari_fee: int
    shipping: int
    packaging: int
    transfer_fee: int
    net_profit: int
    profit_rate: float
    should_buy: bool
    reason: str              # 不买的原因

class Calculator:
    SHIPPING_COSTS = {
        "small": 700,        # 小件手办
        "medium": 1000,      # 中件
        "large": 1500,       # 大件
        "extra_large": 2000,
    }
    
    # 中古成色价格调整（保守估计）
    CONDITION_MULTIPLIERS = {
        "A": 1.0,    # 未使用に近い → 100%（接近新品）
        "B": 0.85,   # 目立った傷なし → -15%（中古主力，最常见）
        "C": 0.70,   # やや傷あり → -30%（有轻微损伤）
        "D": 0.50,   # 傷あり → -50%（不推荐）
    }
    
    def __init__(self, min_profit: int = 1000, min_profit_rate: float = 20):
        self.min_profit = min_profit
        self.min_profit_rate = min_profit_rate
    
    def calculate(
        self,
        amiami_price: int,
        mercari_avg_price: int,
        condition: str = "B",
        size: str = "small"
    ) -> ArbitrageResult:
        
        # 根据成色调整 Mercari 预期售价
        multiplier = self.CONDITION_MULTIPLIERS.get(condition, 0.85)
        adjusted_price = int(mercari_avg_price * multiplier)
        
        # Mercari 卖出成本
        mercari_fee = int(adjusted_price * 0.10)   # 手续费 10%
        shipping = self.SHIPPING_COSTS.get(size, 700)
        packaging = 150                             # 包装材料
        transfer_fee = 200                          # 提现手续费
        
        # 净利润计算
        total_cost = amiami_price + packaging + transfer_fee
        total_revenue = adjusted_price - mercari_fee - shipping
        net_profit = total_revenue - total_cost
        profit_rate = (net_profit / amiami_price) * 100 if amiami_price > 0 else 0
        
        # 判断是否值得买
        reason = ""
        if condition == "D":
            should_buy = False
            reason = "成色 D，风险太高"
        elif net_profit < self.min_profit:
            should_buy = False
            reason = f"净利润 ¥{net_profit:,} 低于最低要求 ¥{self.min_profit:,}"
        elif profit_rate < self.min_profit_rate:
            should_buy = False
            reason = f"利润率 {profit_rate:.1f}% 低于最低要求 {self.min_profit_rate}%"
        else:
            should_buy = True
            reason = "✅ 值得买入"
        
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
            should_buy=should_buy,
            reason=reason
        )
    
    def print_breakdown(self, result: ArbitrageResult, item_name: str = ""):
        """打印详细费用分解"""
        print(f"\n{'='*50}")
        if item_name:
            print(f"📦 {item_name}")
        print(f"{'='*50}")
        print(f"成色: {result.condition}")
        print(f"\n💰 收入:")
        print(f"  Mercari 售价:     ¥{result.sell_price:>8,}")
        print(f"  - 手续费(10%):    ¥{result.mercari_fee:>8,}")
        print(f"  - 运费:           ¥{result.shipping:>8,}")
        print(f"  净收入:           ¥{result.sell_price - result.mercari_fee - result.shipping:>8,}")
        print(f"\n💸 成本:")
        print(f"  AmiAmi 买入价:    ¥{result.buy_price:>8,}")
        print(f"  + 包装费:         ¥{result.packaging:>8,}")
        print(f"  + 提现手续费:     ¥{result.transfer_fee:>8,}")
        print(f"  总成本:           ¥{result.buy_price + result.packaging + result.transfer_fee:>8,}")
        print(f"\n📊 结果:")
        print(f"  净利润:           ¥{result.net_profit:>8,}")
        print(f"  利润率:           {result.profit_rate:>8.1f}%")
        print(f"\n  {result.reason}")
        print(f"{'='*50}")


if __name__ == "__main__":
    # 测试
    calc = Calculator(min_profit=1000, min_profit_rate=20)
    
    test_cases = [
        {"name": "ねんどろいど 初音ミク", "buy": 3500, "mercari": 6500, "condition": "B"},
        {"name": "figma 鬼滅の刃", "buy": 2000, "mercari": 4000, "condition": "A"},
        {"name": "スケールフィギュア", "buy": 8000, "mercari": 12000, "condition": "C"},
    ]
    
    for case in test_cases:
        result = calc.calculate(
            amiami_price=case["buy"],
            mercari_avg_price=case["mercari"],
            condition=case["condition"]
        )
        calc.print_breakdown(result, case["name"])
