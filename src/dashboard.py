"""
生成 GitHub Pages Dashboard
读取 SQLite 数据，生成 docs/index.html
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/arbitrage.db")
DOCS_PATH = Path("docs")


def get_data():
    if not DB_PATH.exists():
        return [], []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM matched ORDER BY net_profit DESC")
    matched = [dict(r) for r in c.fetchall()]

    c.execute("SELECT * FROM unmatched ORDER BY discount DESC")
    unmatched = [dict(r) for r in c.fetchall()]

    conn.close()
    return matched, unmatched


def build_html(matched, unmatched):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    buy_list = [m for m in matched if m['should_buy']]
    total_profit = sum(m['net_profit'] for m in buy_list)

    # ── 套利机会卡片 ──────────────────────────────
    def opportunity_card(item):
        condition_color = {'A': '#22c55e', 'B': '#3b82f6', 'C': '#f59e0b', 'D': '#ef4444'}
        color = condition_color.get(item['condition'], '#6b7280')
        profit_color = '#22c55e' if item['net_profit'] > 3000 else '#3b82f6' if item['net_profit'] > 1000 else '#f59e0b'
        return f"""
        <div class="card {'card-buy' if item['should_buy'] else 'card-skip'}">
          <div class="card-header">
            <span class="condition-badge" style="background:{color}">{item['condition']}品</span>
            <span class="profit-badge" style="background:{profit_color}">¥{item['net_profit']:,} 利润</span>
          </div>
          <div class="item-name">{item['amiami_name'][:50]}</div>
          <div class="price-row">
            <div class="price-box buy-box">
              <div class="price-label">AmiAmi 买入</div>
              <div class="price-value">¥{item['amiami_price']:,}</div>
              <div class="price-sub">原价 ¥{item['amiami_orig_price']:,} · {item['discount']:.0f}%折扣</div>
            </div>
            <div class="arrow">→</div>
            <div class="price-box sell-box">
              <div class="price-label">Mercari 卖出</div>
              <div class="price-value">¥{item['adjusted_price']:,}</div>
              <div class="price-sub">中位数 ¥{item['mercari_median']:,} · {item['mercari_count']}笔成交</div>
            </div>
          </div>
          <div class="fee-row">
            <span>手续费 ¥{item['mercari_fee']:,}</span>
            <span>运费 ¥{item['shipping']:,}</span>
            <span>利润率 {item['profit_rate']:.1f}%</span>
          </div>
          <div class="link-row">
            <a href="{item['amiami_url']}" target="_blank" class="btn btn-buy">🛒 AmiAmi 购买</a>
            <a href="{item['mercari_search_url']}" target="_blank" class="btn btn-mercari">🔍 Mercari 参考</a>
          </div>
        </div>"""

    # ── 未匹配卡片 ────────────────────────────────
    def unmatched_card(item):
        mercari_search = f"https://jp.mercari.com/search?keyword={item['amiami_name']}&status=sold_out"
        return f"""
        <div class="card card-unmatched">
          <div class="card-header">
            <span class="condition-badge" style="background:#6b7280">{item['condition']}品</span>
            <span class="discount-badge">-{item['discount']:.0f}%</span>
          </div>
          <div class="item-name">{item['amiami_name'][:55]}</div>
          <div class="price-row-simple">
            <span>AmiAmi: ¥{item['amiami_price']:,}</span>
            <span>原价: ¥{item['amiami_orig_price']:,}</span>
          </div>
          <div class="link-row">
            <a href="{item['amiami_url']}" target="_blank" class="btn btn-buy">🛒 AmiAmi</a>
            <a href="{mercari_search}" target="_blank" class="btn btn-search">🔍 手动搜 Mercari</a>
          </div>
        </div>"""

    cards_buy    = "\n".join(opportunity_card(i) for i in buy_list)
    cards_all    = "\n".join(opportunity_card(i) for i in matched if not i['should_buy'])
    cards_unmatched = "\n".join(unmatched_card(i) for i in unmatched)

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AmiAmi → Mercari 套利 Dashboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f172a; color: #e2e8f0; min-height: 100vh; }}

  /* Header */
  .header {{ background: linear-gradient(135deg, #1e293b, #0f172a);
             border-bottom: 1px solid #334155; padding: 24px 32px; }}
  .header h1 {{ font-size: 1.6rem; font-weight: 700; color: #f8fafc; }}
  .header h1 span {{ color: #f59e0b; }}
  .updated {{ color: #64748b; font-size: 0.8rem; margin-top: 4px; }}

  /* Stats bar */
  .stats {{ display: flex; gap: 16px; padding: 20px 32px;
            background: #1e293b; border-bottom: 1px solid #334155; flex-wrap: wrap; }}
  .stat {{ background: #0f172a; border: 1px solid #334155; border-radius: 10px;
           padding: 14px 20px; min-width: 140px; }}
  .stat-value {{ font-size: 1.5rem; font-weight: 700; color: #f8fafc; }}
  .stat-label {{ font-size: 0.75rem; color: #64748b; margin-top: 2px; }}
  .stat.green .stat-value {{ color: #22c55e; }}
  .stat.blue  .stat-value {{ color: #3b82f6; }}
  .stat.amber .stat-value {{ color: #f59e0b; }}

  /* Tabs */
  .tabs {{ display: flex; gap: 0; padding: 0 32px; background: #1e293b;
           border-bottom: 1px solid #334155; }}
  .tab {{ padding: 14px 24px; cursor: pointer; font-size: 0.9rem; color: #64748b;
          border-bottom: 2px solid transparent; transition: all 0.2s; }}
  .tab.active {{ color: #f8fafc; border-bottom-color: #f59e0b; }}
  .tab:hover {{ color: #cbd5e1; }}

  /* Content */
  .content {{ padding: 24px 32px; }}
  .section {{ display: none; }}
  .section.active {{ display: block; }}

  .section-title {{ font-size: 1rem; font-weight: 600; color: #94a3b8;
                    margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em; }}

  /* Cards grid */
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }}

  /* Card */
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px;
           padding: 16px; transition: border-color 0.2s; }}
  .card:hover {{ border-color: #475569; }}
  .card-buy  {{ border-left: 3px solid #22c55e; }}
  .card-skip {{ border-left: 3px solid #475569; opacity: 0.7; }}
  .card-unmatched {{ border-left: 3px solid #f59e0b; }}

  .card-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
  .condition-badge {{ font-size: 0.72rem; font-weight: 600; color: #fff;
                      padding: 2px 8px; border-radius: 4px; }}
  .profit-badge {{ font-size: 0.8rem; font-weight: 700; color: #fff;
                   padding: 2px 10px; border-radius: 4px; }}
  .discount-badge {{ font-size: 0.8rem; font-weight: 700; color: #f59e0b;
                     background: #451a03; padding: 2px 10px; border-radius: 4px; }}

  .item-name {{ font-size: 0.88rem; color: #cbd5e1; margin-bottom: 12px;
                line-height: 1.4; min-height: 2.4em; }}

  .price-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
  .price-box {{ flex: 1; background: #0f172a; border-radius: 8px; padding: 10px; }}
  .buy-box  {{ border: 1px solid #1d4ed8; }}
  .sell-box {{ border: 1px solid #15803d; }}
  .price-label {{ font-size: 0.7rem; color: #64748b; margin-bottom: 2px; }}
  .price-value {{ font-size: 1.1rem; font-weight: 700; color: #f8fafc; }}
  .price-sub   {{ font-size: 0.68rem; color: #64748b; margin-top: 2px; }}
  .arrow {{ color: #475569; font-size: 1.2rem; flex-shrink: 0; }}

  .price-row-simple {{ font-size: 0.82rem; color: #94a3b8; margin-bottom: 10px;
                       display: flex; gap: 16px; }}

  .fee-row {{ display: flex; gap: 12px; font-size: 0.72rem; color: #64748b;
              margin-bottom: 12px; flex-wrap: wrap; }}

  .link-row {{ display: flex; gap: 8px; }}
  .btn {{ font-size: 0.75rem; font-weight: 600; padding: 6px 12px; border-radius: 6px;
          text-decoration: none; transition: opacity 0.2s; }}
  .btn:hover {{ opacity: 0.8; }}
  .btn-buy     {{ background: #1d4ed8; color: #fff; }}
  .btn-mercari {{ background: #15803d; color: #fff; }}
  .btn-search  {{ background: #92400e; color: #fff; }}

  /* Empty state */
  .empty {{ text-align: center; padding: 60px; color: #475569; }}
  .empty-icon {{ font-size: 3rem; margin-bottom: 12px; }}

  @media (max-width: 600px) {{
    .header, .stats, .content {{ padding-left: 16px; padding-right: 16px; }}
    .tabs {{ padding: 0 16px; }}
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>🐯 AmiAmi → <span>Mercari</span> 套利 Dashboard</h1>
  <div class="updated">最后更新: {now}</div>
</div>

<div class="stats">
  <div class="stat green">
    <div class="stat-value">{len(buy_list)}</div>
    <div class="stat-label">✅ 建议买入</div>
  </div>
  <div class="stat blue">
    <div class="stat-value">{len(matched)}</div>
    <div class="stat-label">🔍 匹配成功</div>
  </div>
  <div class="stat amber">
    <div class="stat-value">{len(unmatched)}</div>
    <div class="stat-label">❓ 待人工处理</div>
  </div>
  <div class="stat green">
    <div class="stat-value">¥{total_profit:,}</div>
    <div class="stat-label">💰 潜在总利润</div>
  </div>
</div>

<div class="tabs">
  <div class="tab active" onclick="showTab('buy')">✅ 建议买入 ({len(buy_list)})</div>
  <div class="tab" onclick="showTab('all')">📋 全部匹配 ({len(matched)})</div>
  <div class="tab" onclick="showTab('unmatched')">❓ 未匹配 ({len(unmatched)})</div>
</div>

<div class="content">

  <div id="tab-buy" class="section active">
    <div class="section-title">净利润 ≥ ¥1,000 且 利润率 ≥ 20%</div>
    {'<div class="grid">' + cards_buy + '</div>' if buy_list else
     '<div class="empty"><div class="empty-icon">🔍</div><div>暂无套利机会，等待下次扫描</div></div>'}
  </div>

  <div id="tab-all" class="section">
    <div class="section-title">所有 Mercari 匹配成功的商品（含利润不足的）</div>
    {'<div class="grid">' + cards_all + '</div>' if [m for m in matched if not m['should_buy']] else
     '<div class="empty"><div class="empty-icon">✨</div><div>所有匹配商品都值得买入！</div></div>'}
  </div>

  <div id="tab-unmatched" class="section">
    <div class="section-title">Mercari 搜索结果不足 3 个，需要你手动确认关键词</div>
    {'<div class="grid">' + cards_unmatched + '</div>' if unmatched else
     '<div class="empty"><div class="empty-icon">🎉</div><div>所有商品都匹配成功！</div></div>'}
  </div>

</div>

<script>
function showTab(name) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}}
</script>
</body>
</html>"""
    return html


def generate():
    DOCS_PATH.mkdir(exist_ok=True)
    matched, unmatched = get_data()
    html = build_html(matched, unmatched)
    out = DOCS_PATH / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ Dashboard 生成: {out}")
    print(f"   匹配: {len(matched)} | 未匹配: {len(unmatched)}")


if __name__ == "__main__":
    generate()
