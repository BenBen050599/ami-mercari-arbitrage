"""
AmiAmi 中古手办爬虫 - Playwright 版本
绕过 Cloudflare，用真实浏览器抓取
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict
from datetime import datetime
import time


class AmiAmiScraper:

    BASE_URL = "https://slist.amiami.jp/top/search/list3"
    SEARCH_PARAMS = "?s_st_condition_flg=1&s_condition_flg=1&s_sortkey=preowned&pagemax=60&inc_txt2=31"

    CONDITION_MAP = {
        'A': '未使用に近い',
        'B': '目立った傷や汚れなし',
        'C': 'やや傷や汚れあり',
        'D': '傷や汚れあり',
    }

    def scrape_used_figures(self, max_pages: int = 3) -> List[Dict]:
        all_items = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                locale='ja-JP',
                timezone_id='Asia/Tokyo',
            )
            page = context.new_page()

            for page_num in range(1, max_pages + 1):
                url = f"{self.BASE_URL}{self.SEARCH_PARAMS}&page={page_num}"
                print(f"📄 抓取第 {page_num} 页: {url}")

                try:
                    page.goto(url, timeout=30000, wait_until='domcontentloaded')
                    # 等待商品列表加载
                    page.wait_for_timeout(2000)

                    # 检查是否被 Cloudflare 封
                    title = page.title()
                    if 'Cloudflare' in title or 'Attention' in title:
                        print(f"❌ 被 Cloudflare 封锁")
                        break

                    html = page.content()
                    items = self._parse_page(html)

                    if not items:
                        print("✅ 没有更多商品了")
                        break

                    all_items.extend(items)
                    print(f"✅ 第 {page_num} 页: 找到 {len(items)} 个商品")
                    time.sleep(2)

                except Exception as e:
                    print(f"❌ 错误: {e}")
                    break

            browser.close()

        return all_items

    def _parse_page(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'html.parser')
        items = []

        # AmiAmi 商品列表
        for product in soup.select('li.product_item, div.product_item, .item'):
            try:
                item = self._parse_item(product)
                if item:
                    items.append(item)
            except Exception:
                continue

        return items

    def _parse_item(self, elem) -> Dict:
        # 商品名 + URL
        name_elem = elem.select_one('a.product_name, .name a, h2 a, a[href*="detail"]')
        if not name_elem:
            return None

        name = name_elem.text.strip()
        if not name:
            return None

        relative_url = name_elem.get('href', '')
        full_url = (
            f"https://www.amiami.jp{relative_url}"
            if relative_url.startswith('/')
            else relative_url
        )

        # 价格
        price_elem = elem.select_one('.price, .product_price, .price_box')
        if not price_elem:
            return None

        price_text = price_elem.text.strip()
        prices = re.findall(r'[\d,]+', price_text.replace('¥', '').replace('￥', ''))
        if not prices:
            return None

        try:
            if len(prices) >= 2:
                original_price = int(prices[0].replace(',', ''))
                sale_price = int(prices[-1].replace(',', ''))
            else:
                sale_price = int(prices[0].replace(',', ''))
                original_price = sale_price
        except Exception:
            return None

        discount = round(
            (original_price - sale_price) / original_price * 100, 1
        ) if original_price > sale_price else 0

        # 成色
        condition = 'B'
        for sel in ['.condition', '.rank', '.grade', '.item_condition']:
            cond_elem = elem.select_one(sel)
            if cond_elem:
                text = cond_elem.text.strip().upper()
                for grade in ['A', 'B', 'C', 'D']:
                    if grade in text:
                        condition = grade
                        break
                break

        # 库存
        stock_status = 'in_stock'
        if elem.select_one('.soldout, .sold_out, .out_of_stock'):
            stock_status = 'out_of_stock'

        # 画像
        img_elem = elem.select_one('img')
        image_url = ''
        if img_elem:
            image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
            if image_url.startswith('//'):
                image_url = 'https:' + image_url

        # ID
        item_id = ''
        id_match = re.search(r'detail_([A-Z0-9\-]+)', full_url)
        if id_match:
            item_id = id_match.group(1)

        return {
            'id': item_id or name[:20],
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
        from pathlib import Path
        Path(filename).parent.mkdir(exist_ok=True)
        data = {
            'timestamp': datetime.now().isoformat(),
            'count': len(items),
            'items': items,
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 保存 {len(items)} 个商品到 {filename}")


if __name__ == "__main__":
    scraper = AmiAmiScraper()
    print("🔍 开始抓取 AmiAmi 中古打折手办...")
    items = scraper.scrape_used_figures(max_pages=1)
    print(f"\n📊 总共找到 {len(items)} 个商品")
    if items:
        for item in items[:5]:
            print(f"\n  📦 {item['name']}")
            print(f"     成色: {item['condition']} | 折扣: {item['discount']}% | 价格: ¥{item['sale_price']:,}")
            print(f"     链接: {item['url']}")
        scraper.save_items(items)
