"""
Mercari 价格查询（使用 marvinody/mercari 库）
https://github.com/marvinody/mercari
"""

from mercari import search, MercariSearchStatus, MercariSort, MercariOrder
from statistics import mean, median
from typing import Dict
import time

class MercariSearcher:
    
    def get_price_stats(self, keyword: str, sample_size: int = 30) -> Dict:
        """
        搜索已售商品，返回价格统计
        """
        prices = []
        urls = []
        
        try:
            for item in search(
                keyword,
                sort=MercariSort.SORT_CREATED_TIME,
                order=MercariOrder.ORDER_DESC,
                status=MercariSearchStatus.SOLD_OUT  # 只看已售
            ):
                price = int(item.price)  # price 是字符串，需转 int
                prices.append(price)
                urls.append(item.productURL)
                
                if len(prices) >= sample_size:
                    break
            
        except Exception as e:
            print(f"❌ Mercari 搜索错误: {e}")
        
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


if __name__ == "__main__":
    searcher = MercariSearcher()
    
    test_keywords = [
        "ねんどろいど",
        "figma",
        "スケールフィギュア",
    ]
    
    for keyword in test_keywords:
        print(f"\n🔍 搜索: {keyword}")
        stats = searcher.get_price_stats(keyword, sample_size=20)
        
        if stats['status'] == 'OK':
            print(f"  平均价: ¥{stats['average']:,}")
            print(f"  中位数: ¥{stats['median']:,}")
            print(f"  范围:   ¥{stats['min']:,} - ¥{stats['max']:,}")
            print(f"  样本数: {stats['count']}")
            print(f"  参考:   {stats['search_url']}")
        else:
            print(f"  没有数据")
        
        time.sleep(1)
