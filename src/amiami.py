"""
AmiAmi 中古手办爬虫 - cloudscraper 版本
使用 cloudscraper 绕过 Cloudflare
"""

import cloudscraper
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict
from datetime import datetime
import time


class AmiAmiScraper:

    BASE_URL = "https://slist.amiami.jp/top/search/list3"
    ITEM_BASE = "https://www.amiami.jp"

    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'darwin', 'mobile': False}
        )

    def scrape_used_figures(self, max_pages: int = 3) -> List[Dict]:
        all_items = []

        for page_num in range(1, max_pages + 1):
            # AmiAmi 翻页用 pagecnt 参数
            if page_num == 1:
                url = (
                    f"{self.BASE_URL}"
                    f"?s_st_condition_flg=1&s_condition_flg=1"
                    f"&s_sortkey=preowned&pagemax=60&inc_txt2=31"
                )
            else:
                url = (
                    f"{self.BASE_URL}"
                    f"?inc_txt2=31&s_condition_flg=1&s_sortkey=preowned"
                    f"&s_st_condition_flg=1&pagemax=60&getcnt=0&pagecnt={page_num}"
                )

            print(f"📄 抓取第 {page_num} 页...")

            try:
                r = self.scraper.get(url, timeout=20)

                if r.status_code != 200:
                    print(f"❌ 请求失败: {r.status_code}")
                    break

                items = self._parse_page(r.text)

                if not items:
                    print("✅ 没有更多商品了")
                    break

                all_items.extend(items)
                print(f"✅ 第 {page_num} 页: 找到 {len(items)} 个商品")
                time.sleep(2)

            except Exception as e:
                print(f"❌ 错误: {e}")
                break

        return all_items

    def _parse_page(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'html.parser')
        items = []

        for box in soup.select('div.product_box'):
            try:
                item = self._parse_item(box)
                if item:
                    items.append(item)
            except Exception:
                continue

        return items

    def _parse_item(self, box) -> Dict:
        # リンク + gcode
        a_tag = box.select_one('a[href]')
        if not a_tag:
            return None

        href = a_tag.get('href', '')
        gcode_match = re.search(r'gcode=([A-Z0-9\-]+)', href)
        if not gcode_match:
            return None

        gcode = gcode_match.group(1)
        full_url = f"{self.ITEM_BASE}/top/detail/detail?gcode={gcode}"

        # 商品名
        name_elem = box.select_one('div.product_name_inner')
        if not name_elem:
            return None
        name = name_elem.text.strip()
        if not name:
            return None

        # 価格
        # product_price = 固定価格
        # product_price_fromto = 価格帯（複数成色）
        price_elem = box.select_one('div.product_price')
        price_range_elem = box.select_one('div.product_price_fromto')

        sale_price = 0
        original_price = 0
        has_multiple_conditions = False

        if price_elem:
            # 固定価格（単一成色）
            price_text = price_elem.text.strip().replace(',', '')
            nums = re.findall(r'\d+', price_text)
            if nums:
                sale_price = int(nums[0])
                original_price = sale_price
        elif price_range_elem:
            # 価格帯（複数成色あり）→ 最低価格を使用
            price_text = price_range_elem.text.strip().replace(',', '')
            nums = re.findall(r'\d+', price_text)
            if nums:
                sale_price = int(nums[0])
                original_price = sale_price
                has_multiple_conditions = True

        if sale_price == 0:
            return None

        # 割引率（product_off があれば）
        discount = 0
        off_elem = box.select_one('div.product_off')
        if off_elem:
            # 例: "24% - 31%"
            off_text = off_elem.text.strip()
            nums = re.findall(r'\d+', off_text)
            if nums:
                discount = int(nums[0])  # 最低割引率
                # 割引前価格を逆算
                original_price = int(sale_price / (1 - discount / 100))

        # 画像
        img_elem = box.select_one('img[data-src]')
        image_url = ''
        if img_elem:
            image_url = img_elem.get('data-src', '')

        return {
            'id': gcode,
            'name': name,
            'url': full_url,
            'original_price': original_price,
            'sale_price': sale_price,
            'discount': discount,
            'condition': 'B',  # 列表页无成色，默认B（中古）
            'has_multiple_conditions': has_multiple_conditions,
            'stock_status': 'in_stock',
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
    print("🔍 开始抓取 AmiAmi 中古手办...")
    items = scraper.scrape_used_figures(max_pages=1)
    print(f"\n📊 总共找到 {len(items)} 个商品")
    if items:
        for item in items[:5]:
            print(f"\n  📦 {item['name'][:50]}")
            print(f"     价格: ¥{item['sale_price']:,} | 折扣: {item['discount']}%")
            print(f"     链接: {item['url']}")
        scraper.save_items(items)
