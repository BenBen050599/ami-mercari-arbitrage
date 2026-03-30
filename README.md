# AmiAmi → Mercari 套利系统

日本动漫手办套利工具：从 AmiAmi 低价买入，在 Mercari 高价卖出。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行

```bash
cd /Users/marinespheredeveloppers/.qclaw/workspace/ami-mercari-arbitrage
python src/main.py
```

### 3. 查看结果

结果保存在 `data/opportunities.json`

---

## 工作原理

```
AmiAmi 打折手办 → 查询 Mercari 价格 → 计算利润 → 发现套利机会
```

---

## 配置

编辑 `src/main.py`:

```python
config = {
    'MIN_DISCOUNT': 30,      # 最低折扣 30%
    'MIN_PROFIT': 1000,      # 最低净利润 ¥1000
    'MIN_PROFIT_RATE': 20,   # 最低利润率 20%
    'ACCEPTABLE_CONDITIONS': ['A', 'B', 'C'],  # 可接受成色
}
```

---

## 输出示例

```
🎯 套利机会发现！

1. ねんどろいど 初音ミク
   AmiAmi: ¥3,500 (原价 ¥7,000, 50% 折扣)
   Mercari: ¥6,500 → 调整后 ¥5,850
   净利润: ¥1,715 (49%)
   链接: https://www.amiami.jp/...
```

---

## 注意事项

⚠️ **爬虫使用注意事项:**
- AmiAmi 有 Cloudflare 保护，可能需要从日本本地运行
- Mercari 搜索有频率限制，请勿过于频繁
- 建议添加延迟，礼貌爬取

⚠️ **商业风险:**
- 价格波动风险
- 库存风险
- 手续费变化

---

## 文件结构

```
ami-mercari-arbitrage/
├── src/
│   ├── amiami.py       # AmiAmi 爬虫
│   ├── mercari.py      # Mercari 价格查询
│   ├── calculator.py   # 费用计算
│   └── main.py         # 主程序
├── data/
│   └── opportunities.json  # 套利机会
└── README.md
```

---

**Powered by QClaw 🐯**
