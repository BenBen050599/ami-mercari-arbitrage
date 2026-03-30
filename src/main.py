"""
主程序 - AmiAmi → Mercari 套利分析
输出:
  data/arbitrage.db          SQLite 数据库
  data/report_matched.json   匹配成功 + 利润计算
  data/report_unmatched.json 未匹配，待人工处理
"""

import time
import uuid
from datetime import datetime

from src.amiami import AmiAmiScraper
from src.mercari_search import MercariSearcher
from src.calculator import Calculator
from src.database import init_db, save_matched, save_unmatched, export_reports

# ── 配置 ──────────────────────────────────────────
CONFIG = {
    'MIN_DISCOUNT':       30,  # AmiAmi 最低折扣 %
    'MIN_PRICE':        1000,  # 最低价格 yen
    'MAX_PRICE':       30000,  # 最高价格 yen
    'MIN_PROFIT':       1000,  # 最低净利润 yen
    'MIN_PROFIT_RATE':    20,  # 最低利润率 %
    'MIN_MERCARI_COUNT':   3,  # Mercari 最少成交记录数
    'AMIAMI_MAX_PAGES':    3,  # 每页60个，最多180个原始商品
    'MAX_ITEMS_TO_CHECK': 50,  # 过滤后最多查50个（约4分钟）
    'MERCARI_SAMPLE_SIZE': 20, # 每个商品查20条成交记录
}
# ──────────────────────────────────────────────────


def run():
    print("=" * 60)
    print("🚀 AmiAmi → Mercari 套利分析")
    print("=" * 60)

    init_db()
    scraper  = AmiAmiScraper()
    searcher = MercariSearcher()
    calc     = Calculator(
        min_profit=CONFIG['MIN_PROFIT'],
        min_profit_rate=CONFIG['MIN_PROFIT_RATE']
    )

    # ── Step 1: 抓取 AmiAmi ──────────────────────
    print("\n📥 Step 1: 抓取 AmiAmi 中古手办...")
    raw_items = scraper.scrape_used_figures(max_pages=CONFIG['AMIAMI_MAX_PAGES'])

    # 基础过滤
    # 注意：AmiAmi 列表页无折扣字段（discount=0），不用折扣过滤
    # 只按价格区间过滤
    items = [
        i for i in raw_items
        if CONFIG['MIN_PRICE'] <= i['sale_price'] <= CONFIG['MAX_PRICE']
    ]
    # 限制最多查 MAX_ITEMS_TO_CHECK 个
    items = items[:CONFIG['MAX_ITEMS_TO_CHECK']]
    print(f"  原始: {len(raw_items)} 个 → 过滤后: {len(items)} 个（上限 {CONFIG['MAX_ITEMS_TO_CHECK']}）")

    # ── Step 2: Mercari 匹配 ─────────────────────
    print("\n🔍 Step 2: Mercari 价格匹配...")
    matched_rows   = []
    unmatched_rows = []

    for i, item in enumerate(items, 1):
        name = item['name']
        print(f"  [{i}/{len(items)}] {name[:45]}")

        stats = searcher.get_price_stats(name, sample_size=CONFIG['MERCARI_SAMPLE_SIZE'])

        if stats['status'] == 'OK' and stats['count'] >= CONFIG['MIN_MERCARI_COUNT']:
            # ✅ 匹配成功
            result = calc.calculate(
                amiami_price=item['sale_price'],
                mercari_avg_price=stats['median'],   # 用中位数更保守
                condition=item['condition'],
                size='small'
            )
            row = {
                'id':                 item.get('id') or str(uuid.uuid4())[:8],
                'amiami_name':        name,
                'amiami_url':         item['url'],
                'amiami_price':       item['sale_price'],
                'amiami_orig_price':  item['original_price'],
                'discount':           item['discount'],
                'condition':          item['condition'],
                'mercari_keyword':    name,
                'mercari_avg_price':  stats['average'],
                'mercari_median':     stats['median'],
                'mercari_min':        stats['min'],
                'mercari_max':        stats['max'],
                'mercari_count':      stats['count'],
                'mercari_search_url': stats['search_url'],
                'adjusted_price':     result.sell_price,
                'mercari_fee':        result.mercari_fee,
                'shipping':           result.shipping,
                'net_profit':         result.net_profit,
                'profit_rate':        round(result.profit_rate, 1),
                'should_buy':         1 if result.should_buy else 0,
                'found_at':           datetime.now().isoformat(),
            }
            matched_rows.append(row)
            flag = "✅" if result.should_buy else "➖"
            print(f"    {flag} 匹配 | 中位数 ¥{stats['median']:,} | 净利润 ¥{result.net_profit:,}")
        else:
            # ❓ 未匹配
            row = {
                'id':               item.get('id') or str(uuid.uuid4())[:8],
                'amiami_name':      name,
                'amiami_url':       item['url'],
                'amiami_price':     item['sale_price'],
                'amiami_orig_price':item['original_price'],
                'discount':         item['discount'],
                'condition':        item['condition'],
                'image_url':        item.get('image_url', ''),
                'tried_keywords':   [name],
                'found_at':         datetime.now().isoformat(),
            }
            unmatched_rows.append(row)
            print(f"    ❓ 未匹配 (Mercari 结果: {stats['count']} 个)")

        time.sleep(1)  # 礼貌等待

    # ── Step 3: 保存到 SQLite ────────────────────
    print("\n💾 Step 3: 保存到数据库...")
    save_matched(matched_rows)
    save_unmatched(unmatched_rows)

    # ── Step 4: 导出报告 ─────────────────────────
    print("\n📊 Step 4: 导出报告...")
    matched, unmatched = export_reports()

    # ── 汇总 ─────────────────────────────────────
    buy_list = [m for m in matched_rows if m['should_buy']]
    print("\n" + "=" * 60)
    print(f"✅ 匹配成功:  {len(matched_rows)} 个")
    print(f"❓ 未匹配:    {len(unmatched_rows)} 个")
    print(f"🎯 建议买入:  {len(buy_list)} 个")
    print("=" * 60)

    if buy_list:
        print("\n🎯 TOP 套利机会:")
        for item in sorted(buy_list, key=lambda x: x['net_profit'], reverse=True)[:5]:
            print(f"  ¥{item['net_profit']:,} 利润 ({item['profit_rate']}%) | {item['amiami_name'][:40]}")
            print(f"  买入 ¥{item['amiami_price']:,} → 卖出 ¥{item['adjusted_price']:,}")
            print(f"  {item['amiami_url']}")
            print()


if __name__ == "__main__":
    run()
