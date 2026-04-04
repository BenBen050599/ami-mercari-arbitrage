# AmiAmi × Mercari 套利系统 - 项目文档

> 📅 最后更新: 2026-04-04
> 🏷️ 状态: **活跃开发中**

---

## 🎯 项目目标

从 AmiAmi 低价买入中古手办，在 Mercari 高价卖出，赚取差价。

```
AmiAmi (批发价)  → 买入  →  Mercari (零售价)  →  卖出  →  利润 💰
```

---

## 📁 项目结构

```
ami-mercari-arbitrage/
├── src/                          # 核心代码
│   ├── amiami.py                 # AmiAmi 爬虫
│   ├── mercari_search.py         # Mercari 价格查询
│   ├── calculator.py             # 利润计算器
│   ├── database.py               # SQLite 数据库
│   ├── main.py                   # 主程序
│   ├── dashboard.py              # Dashboard（旧版）
│   └── notifier.py               # 通知模块
│
├── data/                         # 数据目录
│   ├── amiami_items.json         # AmiAmi 商品数据 (58个)
│   ├── arbitrage_analysis.json   # 套利分析结果 (17个机会)
│   ├── price_comparison.json     # 价格对比数据
│   ├── arbitrage.db              # SQLite 数据库
│   ├── report_matched.json       # 匹配报告
│   └── report_unmatched.json     # 未匹配报告
│
├── dashboard/                    # 可视化界面
│   ├── index.html                # AmiAmi 商品列表 (含嵌入数据)
│   ├── arbitrage.html            # 套利监控面板 (含嵌入数据)
│   └── data/
│       └── amiami_items.json     # 副本（供本地服务器用）
│
├── .github/workflows/
│   └── daily.yml                 # GitHub Actions 每日运行
│
├── requirements.txt              # Python 依赖
├── run.sh                        # 启动脚本
└── README.md                     # 项目说明
```

---

## 🔧 技术栈

| 组件 | 技术 | 说明 |
|-----|------|------|
| AmiAmi 爬虫 | `cloudscraper` + `BeautifulSoup` | 绕过 Cloudflare 保护 |
| Mercari 查询 | `mercari` Python 库 | 模拟 API 请求 |
| 数据库 | SQLite | 本地存储 |
| Dashboard | 纯 HTML + CSS | 无外部依赖，数据嵌入 |
| 自动化 | GitHub Actions | 每日自动运行 |

---

## 📊 当前数据 (2026-04-04)

### AmiAmi 商品

| 指标 | 数值 |
|-----|------|
| 总商品数 | 58 个 |
| 价格范围 | ¥1,040 ~ ¥54,880 |
| 平均价格 | ¥10,921 |
| 筛选条件 | ≥ ¥1,000（排除低价商品）|

### Mercari 匹配

| 指标 | 数值 |
|-----|------|
| 成功匹配 | ~40 个 |
| 无数据 | ~18 个 |
| 套利机会 | **17 个** |
| 总潜在利润 | **~¥200,000+** |

---

## 🏆 TOP 10 套利机会

| # | 利润 | 利润率 | AmiAmi | Mercari | 商品 |
|---|------|--------|--------|---------|------|
| 1 | ¥29,810 | 2866% | ¥1,040 | ¥41,699 | ウマ娘 ミホノブルボン |
| 2 | ¥28,070 | 1897% | ¥1,480 | ¥39,999 | 初音ミク×Rody AMP+ |
| 3 | ¥18,884 | 1600% | ¥1,180 | ¥27,599 | 初音ミク EVOLVE Clearluxe |
| 4 | ¥17,597 | 92% | ¥19,170 | ¥49,434 | ブルーアーカイブ プラナ |
| 5 | ¥15,441 | 490% | ¥3,150 | ¥25,675 | プロセカ 初音ミク |
| 6 | ¥12,873 | 370% | ¥3,480 | ¥22,749 | ウマ娘 タマモクロス |
| 7 | ¥12,303 | 387% | ¥3,180 | ¥21,611 | ToLOVEる ナナ |
| 8 | ¥11,865 | 254% | ¥4,680 | ¥23,000 | アルカナディア ルミティア |
| 9 | ¥11,345 | 271% | ¥4,180 | ¥21,666 | アイドルマスター 倉本千奈 |
| 10 | ¥10,367 | 237% | ¥4,380 | ¥20,650 | 俺の妹 高坂桐乃 |

---

## 🔄 工作流程

### 第1步: 抓取 AmiAmi

```python
from src.amiami import AmiAmiScraper

scraper = AmiAmiScraper()
items = scraper.scrape_used_figures(max_pages=1)
# 返回 60 个商品（每页60个）
```

**抓取的数据：**
- 商品 ID
- 商品名称
- 商品链接
- 销售价格
- 原价
- 图片 URL
- 成色
- 库存状态

**过滤规则：**
- 价格 ≥ ¥1,000
- 最多检查 50 个商品

### 第2步: 查询 Mercari

```python
from src.mercari_search import MercariSearcher

searcher = MercariSearcher()
stats = searcher.search_by_name(name, sample_size=10)
# 返回: 中位数, 最低, 最高, 样本数
```

**关键词提取策略（改良版）：**
1. 移除括号内容（プライズ、完成品等）
2. 移除比例（1/7、1/4）
3. 移除通用词（フィギュア、プラモデル等）
4. **不截断** — 完整关键词才能精准匹配

**搜索条件：**
- 只看已售商品（SOLD_OUT）
- 按价格降序排列
- 至少需要 3 个样本才可信

### 第3步: 计算利润

```python
from src.calculator import Calculator

calc = Calculator(min_profit=1000, min_profit_rate=20)
result = calc.calculate(
    amiami_price=1180,
    mercari_avg_price=27599,
    condition='B',
    size='small'
)
# 净利润: ¥18,884
# 利润率: 1600%
```

**利润计算包含：**
- Mercari 手续费 (10%)
- 运费 (¥500 ~ ¥1,200)
- 包装费 (¥100 ~ ¥300)

### 第4步: 生成报告

- `dashboard/arbitrage.html` — 可视化面板
- `data/arbitrage_analysis.json` — JSON 数据

---

## ⚠️ 已知问题

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| Mercari 偶尔 401 | API 限流 | 添加延迟，重试 |
| 利润数据不准确 | 关键词不匹配 | 改良关键词提取（已修复）|
| Dashboard 不显示 | 浏览器安全策略 | 数据嵌入 HTML（已修复）|
| 利润率虚高 | Mercari 样本不足 | 提高最低样本数要求 |

---

## 🔐 数据库结构

### amiami_items 表
```sql
CREATE TABLE amiami_items (
    id          TEXT PRIMARY KEY,   -- 商品ID
    name        TEXT NOT NULL,      -- 商品名称
    url         TEXT,               -- 商品链接
    sale_price  INTEGER,            -- 销售价格
    orig_price  INTEGER,            -- 原价
    discount    REAL,               -- 折扣率
    condition   TEXT,               -- 成色 (A/B/C)
    image_url   TEXT,               -- 图片URL
    stock       TEXT,               -- 库存状态
    scraped_at  TEXT                -- 抓取时间
);
```

### matched 表
```sql
CREATE TABLE matched (
    id                  TEXT PRIMARY KEY,
    amiami_name         TEXT,
    amiami_url          TEXT,
    amiami_price        INTEGER,
    mercari_median      INTEGER,
    mercari_count       INTEGER,
    net_profit          INTEGER,
    profit_rate         REAL,
    should_buy          INTEGER,
    found_at            TEXT
);
```

---

## 🚀 如何运行

### 1. 安装依赖

```bash
cd ami-mercari-arbitrage
pip3 install -r requirements.txt
```

**依赖列表：**
- `cloudscraper` — 绕过 Cloudflare
- `beautifulsoup4` — HTML 解析
- `mercari` — Mercari API wrapper
- `requests` — HTTP 请求

### 2. 抓取 AmiAmi

```bash
python3 src/amiami.py
# 输出: data/amiami_items.json (58个商品)
```

### 3. 运行完整分析

```bash
python3 src/main.py
# 输出: data/arbitrage_analysis.json + dashboard 更新
```

### 4. 查看 Dashboard

```bash
open dashboard/arbitrage.html
# 或
open dashboard/index.html
```

---

## 📋 更新日志

### 2026-04-04

- ✅ 修复 Mercari 搜索（改用 `mercari` Python 库）
- ✅ 改良关键词提取（不截断，更精准匹配）
- ✅ 分析全部 58 个商品
- ✅ 发现 17 个套利机会
- ✅ 修复 Dashboard（数据嵌入 HTML，无外部依赖）
- ✅ 创建项目文档

### 2026-04-03

- ✅ 抓取 AmiAmi 中古手办（60个）
- ✅ 保存到 SQLite 数据库
- ✅ 创建商品列表 Dashboard
- ✅ 价格筛选（≥ ¥1,000）

### 2026-03-30（初始）

- ✅ 项目创建
- ✅ AmiAmi 爬虫基础功能
- ✅ Mercari 搜索基础功能
- ✅ 利润计算器

---

## 🔮 下一步计划

- [ ] GitHub Actions 每日自动运行
- [ ] 邮件通知套利机会
- [ ] 自动下單功能
- [ ] 更多搜索关键词优化
- [ ] 支持 Playwright 浏览器抓取（备用方案）
- [ ] 添加更多商品分类

---

*由 AI 助手小老虎 🐯 开发*
