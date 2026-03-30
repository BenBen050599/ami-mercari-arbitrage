"""
Mercari 价格查询
搜索已售商品，获取成交价格
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict
from statistics import mean, median
import time

class MercariSearcher:
    BASE_URL = "https://www.mercari.com/jp/search/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja-JP,ja;q=0.9',
        })
    
    def search_sold_items(self, keyword: str, max_results: int = 50) -> List[int]:
        """
        搜索已售商品，获取成交价格列表
        返回: 价格列表 [¥1000, ¥1200, ...]
        """
        prices = []
        
        try:
            # Mercari 搜索 URL
            params = {
                'keyword': keyword,
                'status': 'sold',  # 只看已售
                'sort': 'created_time',
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"❌ Mercari 搜索失败: {response.status_code}")
                return prices
            
            # 解析页面
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找商品列表
            items = soup.find_all('div', class_='item')
            
            for item in items[:max_results]:
                try:
                    # 提取价格
                    price_elem = item.find('span', class_='price')
                    if price_elem:
                        price_text = price_elem.text.strip()
                        # 格式: "¥1,200"
                        price = int(price_text.replace('¥', '').replace(',', ''))
                        prices.append(price)
                except:
                    continue
            
            print(f"✅ Mercari 搜索 '{keyword}': 找到 {len(prices)} 个成交价格")
            
        except Exception as e:
            print(f"❌ Mercari 搜索错误: {e}")
        
        return prices
    
    def get_price_stats(self, keyword: str) -> Dict:
        """获取价格统计"""
        prices = self.search_sold_items(keyword)
        
        if not prices:
            return {
                'keyword': keyword,
                'count': 0,
                'average': 0,
                'median': 0,
                'min': 0,
                'max': 0,
                'status': 'NO_DATA'
            }
        
        return {
            'keyword': keyword,
            'count': len(prices),
            'average': int(mean(prices)),
            'median': int(median(prices)),
            'min': min(prices),
            'max': max(prices),
            'prices': prices,
            'status': 'OK'
        }


if __name__ == "__main__":
    searcher = MercariSearcher()
    
    # 测试搜索
    test_keywords = [
        "ねんどろいど",
        "figma",
        "グッドスマイルカンパニー",
    ]
    
    for keyword in test_keywords:
        print(f"\n🔍 搜索: {keyword}")
        stats = searcher.get_price_stats(keyword)
        
        if stats['status'] == 'OK':
            print(f"  平均价格: ¥{stats['average']:,}")
            print(f"  中位数: ¥{stats['median']:,}")
            print(f"  范围: ¥{stats['min']:,} - ¥{stats['max']:,}")
            print(f"  样本数: {stats['count']}")
        else:
            print(f"  没有数据")
        
        time.sleep(2)  # 礼貌地等待
