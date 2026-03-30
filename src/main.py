"""
套利分析主程序
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from src.amiami import AmiAmiScraper
from src.mercari import MercariSearcher
from src.calculator import Calculator

class ArbitrageAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.scraper = AmiAmiScraper()
        self.searcher = MercariSearcher()
        self.calculator = Calculator(
            min_profit=config.get('MIN_PROFIT', 1000),
            min_profit_rate=config.get('MIN_PROFIT_RATE', 20)
        )
    
    def run(self):
        """运行完整分析"""
        print("=" * 60)
        print("🚀 AmiAmi → Mercari 套利分析")
        print("=" * 60)
        
        # 1. 抓取 AmiAmi 打折手办
        print("\n📥 第一步: 抓取 AmiAmi 打折手办...")
        amiami_items = self.scraper.scrape_sale_figures(
            category_id="22",
            max_pages=self.config.get('AMIAMI_MAX_PAGES', 3)
        )
        
        if not amiami_items:
            print("❌ 没有找到商品")
            return
        
        print(f"✅ 找到 {len(amiami_items)} 个商品")
        
        # 2. 对每个商品查询 Mercari 价格
        print("\n📊 第二步: 查询 Mercari 价格...")
        opportunities = []
        
        for i, item in enumerate(amiami_items, 1):
            print(f"\n[{i}/{len(amiami_items)}] {item['name']}")
            
            # 搜索 Mercari
            mercari_stats = self.searcher.get_price_stats(item['name'])
            
            if mercari_stats['status'] != 'OK':
                print(f"  ⚠️  Mercari 没有数据")
                continue
            
            # 计算套利
            result = self.calculator.calculate(
                amiami_price=item['sale_price'],
                mercari_avg_price=mercari_stats['average'],
                condition=item['condition'],
                size='small'
            )
            
            # 检查是否值得买
            if result.should_buy:
                print(f"  ✅ 套利机会!")
                print(f"     AmiAmi: ¥{item['sale_price']:,}")
                print(f"     Mercari: ¥{mercari_stats['average']:,}")
                print(f"     净利润: ¥{result.net_profit:,} ({result.profit_rate:.1f}%)")
                
                opportunity = {
                    'name': item['name'],
                    'amiami_url': item['url'],
                    'amiami_price': item['sale_price'],
                    'amiami_original_price': item['original_price'],
                    'discount': item['discount'],
                    'condition': item['condition'],
                    'mercari_keyword': item['name'],
                    'mercari_avg_price': mercari_stats['average'],
                    'mercari_adjusted_price': result.sell_price,
                    'mercari_sold_count': mercari_stats['count'],
                    'net_profit': result.net_profit,
                    'profit_rate': result.profit_rate,
                    'image_url': item['image_url'],
                    'found_at': datetime.now().isoformat(),
                }
                opportunities.append(opportunity)
            else:
                print(f"  ❌ 利润不足 (¥{result.net_profit:,})")
        
        # 3. 保存结果
        print("\n" + "=" * 60)
        print(f"📈 分析完成: 找到 {len(opportunities)} 个套利机会")
        print("=" * 60)
        
        if opportunities:
            self._save_opportunities(opportunities)
            self._print_report(opportunities)
    
    def _save_opportunities(self, opportunities: list):
        """保存套利机会"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'count': len(opportunities),
            'opportunities': opportunities
        }
        
        output_file = Path('data/opportunities.json')
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 保存到 {output_file}")
    
    def _print_report(self, opportunities: list):
        """打印报告"""
        print("\n🎯 套利机会列表:\n")
        
        for i, opp in enumerate(opportunities, 1):
            print(f"{i}. {opp['name']}")
            print(f"   AmiAmi: ¥{opp['amiami_price']:,} (原价 ¥{opp['amiami_original_price']:,}, {opp['discount']}% 折扣)")
            print(f"   Mercari: ¥{opp['mercari_avg_price']:,} → 调整后 ¥{opp['mercari_adjusted_price']:,}")
            print(f"   净利润: ¥{opp['net_profit']:,} ({opp['profit_rate']:.1f}%)")
            print(f"   链接: {opp['amiami_url']}")
            print()


if __name__ == "__main__":
    # 配置
    config = {
        'MIN_DISCOUNT': 30,
        'MIN_PROFIT': 1000,
        'MIN_PROFIT_RATE': 20,
        'AMIAMI_MAX_PAGES': 3,
        'ACCEPTABLE_CONDITIONS': ['A', 'B', 'C'],
    }
    
    analyzer = ArbitrageAnalyzer(config)
    analyzer.run()
