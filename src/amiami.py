"""
AmiAmi 中古手办爬虫
专门抓取二手打折手办
URL: https://slist.amiami.jp/top/search/list3?s_st_condition_flg=1&s_condition_flg=1&s_sortkey=preowned&pagemax=60&inc_txt2=31
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict
from datetime import datetime
import time
import re

class AmiAmiScraper:
    
    # 中古手办专用 URL
    BASE_URL = "https://slist.amiami.jp/top/search/list3"
    
    # 成色等级说明
    CONDITION_MAP = {
        'A': '未使用に近い（接近新品）',
        'B': '目立った傷や汚れなし（无明显损伤）',
        'C': 'やや傷や汚れあり（有轻微损伤）',
        'D': '傷や汚れあり（有损伤）',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
            'Referer': 'https://slist.amiami.jp/',
        })
    
    def scrape_used_figures(self, max_pages: int = 5) -> List[Dict]:
        """
        抓取中古打折手办
        """
        all_items = []
        
        for page in range(1, max_pages + 1):
            print(f"📄 抓取第 {page} 页...")
            
            params = {
                's_st_condition_flg': '1',   # 打折
                's_condition_flg': '1',       # 中古
                's_sortkey': 'preowned',      # 按二手排序
                'pagemax': '60',              # 每页60个
                'inc_txt2': '31',             # 手办分类
                'page': str(page),
            }
            
            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=20)
                response.encoding = 'utf-8'
                
                if response.status_code != 200:
                    print(f"❌ 请求失败: {response.status_code}")
                    break
                
                items = self._parse_page(response.text)
                
                if not items:
                    print("✅ 没有更多商品了")
                    break
                
                all_items.extend(items)
                print(f"✅ 第 {page} 页: 找到 {len(items)} 个商品")
                
                time.sleep(2)  # 礼貌等待
                
            except Exception as e:
                print(f"❌ 错误: {e}")
                break
        
        return all_items
    
    def _parse_page(self, html: str) -> List[Dict]:
        """解析页面"""
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        # AmiAmi 商品列表容器
        for product in soup.select('.product_item, .item, li.item'):
            try:
                item = self._parse_item(product)
                if item:
                    items.append(item)
            except Exception as e:
                continue
        
        return items
    
    def _parse_item(self, elem) -> Dict:
        """解析单个商品"""
        
        # 商品名
        name_elem = elem.select_one('a.product_name, .name a, h2 a')
        if not name_elem:
            return None
        
        name = name_elem.text.strip()
        relative_url = name_elem.get('href', '')
        full_url = f"https://www.amiami.jp{relative_url}" if relative_url.startswith('/') else relative_url
        
        # 价格
        price_elem = elem.select_one('.price, .product_price')
        if not price_elem:
            return None
        
        price_text = price_elem.text.strip()
        
        # 解析价格（格式多样）
        prices = re.findall(r'[\d,]+', price_text.replace('¥', ''))
        if not prices:
            return None
        
        try:
            if len(prices) >= 2:
                original_price = int(prices[0].replace(',', ''))
                sale_price = int(prices[-1].replace(',', ''))
            else:
                sale_price = int(prices[0].replace(',', ''))
                original_price = sale_price
        except:
            return None
        
        # 折扣率
        discount = round(((original_price - sale_price) / original_price * 100), 1) if original_price > sale_price else 0
        
        # 成色（中古商品必有）
        condition = 'B'  # 默认 B（中古通常是B）
        condition_elem = elem.select_one('.condition, .rank, .grade')
        if condition_elem:
            text = condition_elem.text.strip().upper()
            for grade in ['A', 'B', 'C', 'D']:
                if grade in text:
                    condition = grade
                    break
        
        # 库存状态
        stock_status = 'in_stock'
        sold_elem = elem.select_one('.sold, .soldout, .out_of_stock')
        if sold_elem:
            stock_status = 'out_of_stock'
        
        # 图片
        img_elem = elem.select_one('img')
        image_url = ''
        if img_elem:
            image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
        
        # 商品 ID
        item_id = ''
        id_match = re.search(r'detail/detail_([A-Z0-9-]+)', full_url)
        if id_match:
            item_id = id_match.group(1)
        
        return {
            'id': item_id,
            'name': name,
            'url': full_url,
            'original_price': original_price,
            'sale_price': sale_price,
            'discount': discount,
            'condition': condition,
            'condition_desc': self.CONDITION_MAP.get(condition, ''),
            'stock_status': stock_status,
            'image_url': image_url,
            'type': 'used',
            'scraped_at': datetime.now().isoformat(),
        }
    
    def save_items(self, items: List[Dict], filename: str = "data/amiami_items.json"):
        """保存抓取的商品"""
        from pathlib import Path
        Path(filename).parent.mkdir(exist_ok=True)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'count': len(items),
            'source_url': 'https://slist.amiami.jp/top/search/list3?s_st_condition_flg=1&s_condition_flg=1&s_sortkey=preowned&pagemax=60&inc_txt2=31',
            'items': items
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 保存 {len(items)} 个商品到 {filename}")


if __name__ == "__main__":
    scraper = AmiAmiScraper()
    
    print("🔍 开始抓取 AmiAmi 中古打折手办...")
    print(f"URL: https://slist.amiami.jp/top/search/list3?s_st_condition_flg=1&s_condition_flg=1")
    
    items = scraper.scrape_used_figures(max_pages=3)
    
    print(f"\n📊 总共找到 {len(items)} 个商品")
    
    if items:
        print("\n前 5 个商品:")
        for item in items[:5]:
            print(f"\n  📦 {item['name']}")
            print(f"     成色: {item['condition']} ({item['condition_desc']})")
            print(f"     原价: ¥{item['original_price']:,} → 现价: ¥{item['sale_price']:,} ({item['discount']}% 折扣)")
            print(f"     链接: {item['url']}")
        
        scraper.save_items(items)
