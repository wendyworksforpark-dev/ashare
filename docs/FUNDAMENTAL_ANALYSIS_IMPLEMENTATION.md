# 基本面分析功能实现文档

## 📊 功能概述

在每日复盘系统中新增**基本面质量分析**模块,帮助识别:
1. 价格与基本面背离的股票 (股价新高但业绩未跟上)
2. 行业内基本面Top 20%的优质标的
3. 业绩差但股价上涨的高风险股票

## 🎯 核心理念

**"第一批情绪驱动的上涨已基本结束,后续板块将出现分化,板块内部基本面强的股票会更加强"**

基本面分析主要关注:
- **ROE (净资产收益率)**: 衡量公司盈利能力
- **净利润同比增长率**: 衡量公司成长性
- **毛利率**: 衡量公司竞争力
- **行业内排名**: 横向对比识别优质标的

## 📁 文件结构

```
src/
├── utils/
│   └── fundamental_analyzer.py   # 基本面分析核心工具类
├── services/
│   └── tushare_client.py         # 新增财务数据API
└── schemas/
    └── daily_review.py           # 数据模型 (待扩展)
```

## 🔧 API 接口

### TushareClient 新增方法

| 方法 | 说明 | 关键字段 |
|-----|------|---------|
| `fetch_fina_indicator` | 财务指标 | ROE, 净利润增长, 毛利率 |
| `fetch_income` | 利润表 | 营收, 净利润 |
| `fetch_forecast` | 业绩预告 | 预计净利润范围 |
| `fetch_express` | 业绩快报 | 营收增速, 净利润增速 |

### FundamentalAnalyzer 核心方法

```python
class FundamentalAnalyzer:
    def get_52w_high_low(ticker, trade_date) -> (high, low)
    def get_financial_indicators(ticker, periods=8) -> List[Dict]
    def analyze_price_fundamental_divergence(ticker, price, change_pct, date) -> Dict
    def get_industry_ranking(ticker, industry, metric='roe') -> Dict
    def batch_analyze_fundamentals(stocks, trade_date) -> Dict
```

## 📊 背离检测算法

```python
# 价格与基本面背离判断
is_near_high = (current_price / high_52w >= 0.95)  # 距52周高点5%以内

if is_near_high and (profit_trend == "亏损" or "下降"):
    divergence_level = "严重"
elif is_near_high and profit_yoy < 10%:
    divergence_level = "中等"
elif price_change > 30% and profit_yoy < price_change / 2:
    divergence_level = "轻微"
```

## 📊 行业排名算法

```python
# 同行业所有股票按ROE排序
percentile = (1 - (rank - 1) / total_count) * 100
is_top20 = (percentile >= 80)  # Top 20%
```

## 使用示例

```python
from src.database import SessionLocal
from src.utils.fundamental_analyzer import FundamentalAnalyzer

session = SessionLocal()
analyzer = FundamentalAnalyzer(session)

# 分析单只股票
result = analyzer.analyze_price_fundamental_divergence(
    ticker="300077",
    current_price=24.69,
    price_change_pct=12.38,
    trade_date="20260127"
)

# 批量分析
stocks = [
    {"ticker": "300077", "name": "国民技术", "current_price": 24.69, "change_pct": 12.38, "industry": "半导体"},
    {"ticker": "600183", "name": "生益科技", "current_price": 28.50, "change_pct": 3.2, "industry": "元件"},
]
results = analyzer.batch_analyze_fundamentals(stocks, "20260127")

print(f"背离警报: {len(results['divergence_alerts'])}个")
print(f"优质股票: {len(results['quality_stocks'])}个")
print(f"风险股票: {len(results['risk_stocks'])}个")
```

## 输出示例

### 背离警报
```json
{
  "ticker": "000028",
  "name": "国药一致",
  "warning": "⚠️ 股价接近新高(96.9%)，但公司下降",
  "divergence_level": "严重",
  "details": {
    "price_vs_52w_high": 96.9,
    "latest_profit_yoy": -10.18,
    "roe": 5.3
  }
}
```

### 优质股票
```json
{
  "ticker": "600183",
  "name": "生益科技",
  "industry": "元件",
  "roe": 16.05,
  "rank": 6,
  "percentile": 91.0,
  "profit_yoy": 78.04
}
```

---

**生成日期**: 2026-01-28
**版本**: v1.0
