"""
Mercari 价格查询（使用 marvinody/mercari 库）
https://github.com/marvinody/mercari
"""

from mercari import search, MercariSearchStatus, MercariSort, MercariOrder
from statistics import mean, median
from typing import Dict
import time
import re

class MercariSearcher:
    
    def get_price_stats(self, keyword: str, sample_size: int = 30) -> Dict:
        """
        搜索已售商品，返回价格统计
        """
        prices = []
        urls = []
        
        try:
            # 清理关键词
            keyword = keyword.strip()
            
            for item in search(
                keyword,
                sort=MercariSort.SORT_PRICE,
                order=MercariOrder.ORDER_DESC,
                status=MercariSearchStatus.SOLD_OUT  # 只看已售
            ):
                # 价格可能是字符串或数字
                price = item.price
                if isinstance(price, str):
                    price = int(price.replace(',', ''))
                else:
                    price = int(price)
                
                prices.append(price)
                urls.append(item.productURL)
                
                if len(prices) >= sample_size:
                    break
            
        except Exception as e:
            print(f"    ❌ Mercari 搜索错误: {e}")
        
        if not prices:
            return {
                'keyword': keyword,
                'count': 0,
                'average': 0,
                'median': 0,
                'min': 0,
                'max': 0,
                'search_url': f'https://jp.mercari.com/search?keyword={keyword}&status=sold_out',
                'status': 'NO_DATA'
            }
        
        return {
            'keyword': keyword,
            'count': len(prices),
            'average': int(mean(prices)),
            'median': int(median(prices)),
            'min': min(prices),
            'max': max(prices),
            'sample_urls': urls[:3],  # 保存前3个参考链接
            'search_url': f'https://jp.mercari.com/search?keyword={keyword}&status=sold_out',
            'status': 'OK'
        }
    
    def search_by_name(self, name: str, sample_size: int = 20) -> Dict:
        """
        根据商品名称搜索 Mercari 已售价格
        自动提取关键词
        """
        # 提取关键词（移除常见后缀）
        keywords = self._extract_keywords(name)
        
        print(f"    🔍 搜索关键词: {keywords}")
        
        return self.get_price_stats(keywords, sample_size)
    
    def _extract_keywords(self, name: str) -> str:
        """
        从商品名提取搜索关键词
        策略：保留系列名+角色名，移除通用词，不截断
        """
        # 1. 移除括号内容（プライズ、完成品フィギュア等）
        name = re.sub(r'[（(][^)）]*[)）]', '', name)
        
        # 2. 移除比例（如：1/7、1/4）
        name = re.sub(r'\s*1/\d+\s*', ' ', name)
        
        # 3. 移除通用词（保留特定词）
        remove_words = [
            '完成品フィギュア', '完成品', 'フィギュア', 'プラモデル',
            'ABS&PVC 塗装済み完成品', '塗装済み完成品',
            'スーパープレミアムフィギュア', 'スーパープレミアム',
            'プレミアムフィギュア',
        ]
        for word in remove_words:
            name = name.replace(word, '')
        
        # 4. 清理多余空格
        name = ' '.join(name.split()).strip()
        
        # 5. 不截断！完整关键词才能精准匹配
        return name


if __name__ == "__main__":
    searcher = MercariSearcher()
    
    test_names = [
        "初音ミク BANPRESTO EVOLVE Clearluxe-クリオネ-フィギュア (プライズ)",
        "一番くじ 学園アイドルマスター Part4 B賞 倉本千奈 フィギュア 1/7",
        "ウマ娘 プリティーダービー ミホノブルボン フィギュア (プライズ)",
    ]
    
    for name in test_names:
        print(f"\n{'='*60}")
        print(f"📦 商品: {name[:40]}")
        
        stats = searcher.search_by_name(name, sample_size=10)
        
        if stats['status'] == 'OK':
            print(f"   ✅ 找到 {stats['count']} 个已售商品")
            print(f"   💰 中位数: ¥{stats['median']:,}")
            print(f"   📊 范围: ¥{stats['min']:,} - ¥{stats['max']:,}")
            print(f"   🔗 {stats['search_url']}")
        else:
            print(f"   ❌ 没有数据")
        
        time.sleep(2)
