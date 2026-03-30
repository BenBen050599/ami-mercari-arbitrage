"""
数据库模块 - SQLite 存储
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path


DB_PATH = Path("data/arbitrage.db")


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """初始化数据库表"""
    conn = get_conn()
    c = conn.cursor()

    # AmiAmi 抓取的商品（原始数据）
    c.execute("""
        CREATE TABLE IF NOT EXISTS amiami_items (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            url         TEXT,
            sale_price  INTEGER,
            orig_price  INTEGER,
            discount    REAL,
            condition   TEXT,
            image_url   TEXT,
            stock       TEXT,
            scraped_at  TEXT
        )
    """)

    # Mercari 匹配成功的商品
    c.execute("""
        CREATE TABLE IF NOT EXISTS matched (
            id                  TEXT PRIMARY KEY,
            amiami_name         TEXT,
            amiami_url          TEXT,
            amiami_price        INTEGER,
            amiami_orig_price   INTEGER,
            discount            REAL,
            condition           TEXT,
            mercari_keyword     TEXT,
            mercari_avg_price   INTEGER,
            mercari_median      INTEGER,
            mercari_min         INTEGER,
            mercari_max         INTEGER,
            mercari_count       INTEGER,
            mercari_search_url  TEXT,
            adjusted_price      INTEGER,
            mercari_fee         INTEGER,
            shipping            INTEGER,
            net_profit          INTEGER,
            profit_rate         REAL,
            should_buy          INTEGER,
            found_at            TEXT
        )
    """)

    # Mercari 未匹配的商品（待人工处理）
    c.execute("""
        CREATE TABLE IF NOT EXISTS unmatched (
            id              TEXT PRIMARY KEY,
            amiami_name     TEXT,
            amiami_url      TEXT,
            amiami_price    INTEGER,
            amiami_orig_price INTEGER,
            discount        REAL,
            condition       TEXT,
            image_url       TEXT,
            tried_keywords  TEXT,   -- JSON array of keywords tried
            found_at        TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")


def save_matched(items: list):
    conn = get_conn()
    c = conn.cursor()
    for item in items:
        c.execute("""
            INSERT OR REPLACE INTO matched VALUES (
                :id, :amiami_name, :amiami_url, :amiami_price, :amiami_orig_price,
                :discount, :condition, :mercari_keyword, :mercari_avg_price,
                :mercari_median, :mercari_min, :mercari_max, :mercari_count,
                :mercari_search_url, :adjusted_price, :mercari_fee, :shipping,
                :net_profit, :profit_rate, :should_buy, :found_at
            )
        """, item)
    conn.commit()
    conn.close()


def save_unmatched(items: list):
    conn = get_conn()
    c = conn.cursor()
    for item in items:
        item['tried_keywords'] = json.dumps(item.get('tried_keywords', []), ensure_ascii=False)
        c.execute("""
            INSERT OR REPLACE INTO unmatched VALUES (
                :id, :amiami_name, :amiami_url, :amiami_price, :amiami_orig_price,
                :discount, :condition, :image_url, :tried_keywords, :found_at
            )
        """, item)
    conn.commit()
    conn.close()


def export_reports():
    """导出两份 JSON 报告"""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 报告A：匹配成功，按净利润排序
    c.execute("SELECT * FROM matched ORDER BY net_profit DESC")
    matched = [dict(r) for r in c.fetchall()]

    # 报告B：未匹配，等待人工处理
    c.execute("SELECT * FROM unmatched ORDER BY discount DESC")
    unmatched = [dict(r) for r in c.fetchall()]

    conn.close()

    ts = datetime.now().isoformat()

    with open("data/report_matched.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": ts, "count": len(matched), "items": matched},
                  f, ensure_ascii=False, indent=2)

    with open("data/report_unmatched.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": ts, "count": len(unmatched), "items": unmatched},
                  f, ensure_ascii=False, indent=2)

    print(f"✅ 报告A（匹配）: {len(matched)} 个")
    print(f"✅ 报告B（未匹配）: {len(unmatched)} 个")
    return matched, unmatched


if __name__ == "__main__":
    init_db()
