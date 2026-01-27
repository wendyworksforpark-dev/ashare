# 每日复盘系统使用指南

## 系统概述

每日复盘系统是一个**结构化数据驱动**的A股市场分析工具,遵循"结构化证据 → 归因分析 → 叙事生成"的原则,确保生成的复盘报告专业、可验证、基于事实。

### 核心特点

- ✅ **数据驱动**: 所有结论基于可验证的市场数据
- ✅ **标签化处理**: 将原始数据转换为人类可读的标签(如"缩量"而非"volume_ratio=0.92")
- ✅ **角色分类**: 自动识别龙头股、高位核心、补涨股等角色
- ✅ **AI辅助**: 使用Claude API生成专业叙事文本
- ✅ **可追溯**: 所有复盘都基于存储的数据快照,可重现

## 快速开始

### 方法1: 全自动生成(推荐)

```bash
# 1. 生成今日数据快照
python scripts/generate_snapshot.py

# 2. 生成AI复盘报告
export ANTHROPIC_API_KEY=your-api-key
python scripts/generate_review.py

# 输出位置:
# - 数据快照: docs/daily_review/snapshots/YYYYMMDD.json
# - 复盘报告: docs/daily_review/reviews/YYYYMMDD.md
```

### 方法2: 手动Claude Code CLI

```bash
# 1. 生成数据快照
python scripts/generate_snapshot.py --date 20250126

# 2. 在Claude Code CLI中:
read docs/daily_review/snapshots/20250126.json
read docs/daily_review/prompt_template.md
# 然后将JSON数据粘贴到prompt中,让AI生成复盘
```

## 详细使用说明

### 生成数据快照

**基本用法:**
```bash
# 今日数据
python scripts/generate_snapshot.py

# 指定日期
python scripts/generate_snapshot.py --date 20250126

# 自定义输出路径
python scripts/generate_snapshot.py --output /path/to/custom.json

# 强制重新生成(覆盖已有文件)
python scripts/generate_snapshot.py --force

# 带数据质量验证
python scripts/generate_snapshot.py --validate
```

**输出内容:**
- 主要指数(上证、深成、创业板等)的K线数据和形态分析
- 行业板块和概念板块的资金流向
- 市场情绪指标(涨跌家数、涨停板、成交额)
- 代表性样本股(龙头、高位核心、补涨股等)

**数据快照示例:**
```json
{
  "trade_date": "20250126",
  "indices": [
    {
      "name": "上证指数",
      "code": "000001.SH",
      "close": 3415.2,
      "change_pct": -0.15,
      "pattern": "小阴线带上影",
      "volume_trend": "缩量",
      "ma_position": "MA10下方运行"
    }
  ],
  "sectors": [...],
  "sentiment": {
    "up_down_ratio": 1.08,
    "limit_up": 45,
    "sentiment_label": "偏多"
  },
  "sample_stocks": {...}
}
```

### 生成AI复盘报告

**前置条件:**
```bash
# 设置API密钥
export ANTHROPIC_API_KEY=your-api-key-here
# 或者添加到 .env 文件
```

**基本用法:**
```bash
# 今日复盘
python scripts/generate_review.py

# 指定日期
python scripts/generate_review.py --date 20250126

# 指定数据快照文件
python scripts/generate_review.py --snapshot /path/to/snapshot.json

# 自定义输出路径
python scripts/generate_review.py --output /path/to/review.md

# 使用不同模型
python scripts/generate_review.py --model claude-opus-4-5-20251101

# 调整生成温度(0-1,默认0.3)
python scripts/generate_review.py --temperature 0.5
```

**生成的复盘报告包含:**
1. **大盘综述** (200字): 指数走势、K线形态、成交量、技术位置
2. **板块轮动分析** (400字): 资金流向、强弱板块、轮动特征
3. **重点个股解读** (250字): 龙头股、补涨股、回撤股表现
4. **市场情绪** (100字): 涨跌家数、涨停板、情绪判断
5. **明日交易策略** (50字): 操作建议、关注方向

### 定时自动化

创建自动化脚本 `scripts/daily_review_auto.sh`:

```bash
#!/bin/bash
# 每日复盘自动化脚本

DATE=$(date +%Y%m%d)
PROJECT_DIR="/Users/park/a-share-data"

cd $PROJECT_DIR

# 1. 生成数据快照
echo "生成数据快照: $DATE"
python scripts/generate_snapshot.py --date $DATE --validate

if [ $? -ne 0 ]; then
    echo "数据快照生成失败"
    exit 1
fi

# 2. 生成AI复盘
echo "生成AI复盘报告: $DATE"
python scripts/generate_review.py --date $DATE

if [ $? -ne 0 ]; then
    echo "复盘报告生成失败"
    exit 1
fi

echo "每日复盘完成: docs/daily_review/reviews/${DATE}.md"
```

**添加到crontab:**
```bash
# 每个交易日15:45自动运行
45 15 * * 1-5 /Users/park/a-share-data/scripts/daily_review_auto.sh >> /Users/park/a-share-data/logs/daily_review.log 2>&1
```

## 数据结构说明

### 标签化逻辑

系统将原始数值转换为人类可读标签:

| 原始数据 | 标签 | 说明 |
|---------|------|------|
| volume_ratio=1.8 | "放量" | 成交量是5日均量的1.8倍 |
| up_down_ratio=1.08 | "偏多" | 涨跌家数比,市场偏多 |
| net_inflow=5.8 | "主力流入" | 净流入5.8亿,主力资金 |
| body_ratio=0.82 | "大阳线" | 实体占比82%,大阳线 |

### 样本股角色分类

| 角色 | 条件 | 说明 |
|------|------|------|
| 龙头 | ticker == leader_symbol | 板块领涨股 |
| 高位核心 | 5日涨>10% AND 市值前3 | 大市值强势股 |
| 补涨 | 今日涨>板块均值 AND 市值靠后 | 小市值跟涨股 |
| 回撤 | 跌幅最大(弱势板块) | 回调风险股 |

### 市场情绪评分

情绪评分 (-5 到 +5):
- 涨跌家数比: >1.3 (+2), >1.1 (+1), <0.8 (-2), <0.9 (-1)
- 涨停板数量: >80 (+2), >50 (+1), <20 (-1)
- 成交量变化: >1.2倍 (+1), <0.8倍 (-1)

| 总分 | 标签 |
|------|------|
| ≥3 | 强势 |
| 1~2 | 偏多 |
| -1~0 | 震荡 |
| -3~-2 | 偏空 |
| ≤-4 | 弱势 |

## 故障排查

### 问题1: 没有找到数据

**错误信息:**
```
No kline data found for date 20250126
```

**解决方案:**
1. 检查市场是否开盘(不是周末或节假日)
2. 确认K线数据已更新:
   ```bash
   python scripts/update_klines.py --date 20250126
   ```
3. 检查数据库连接是否正常

### 问题2: 板块数据不完整

**错误信息:**
```
板块数据不足(5个),建议至少10个
```

**解决方案:**
1. 更新行业板块数据:
   ```bash
   python scripts/update_industry_daily.py --date 20250126
   ```
2. 更新概念板块数据:
   ```bash
   python scripts/update_concept_daily.py --date 20250126
   ```

### 问题3: API密钥未设置

**错误信息:**
```
ANTHROPIC_API_KEY environment variable not set
```

**解决方案:**
```bash
# 临时设置
export ANTHROPIC_API_KEY=your-key

# 永久设置(添加到 ~/.bashrc 或 ~/.zshrc)
echo 'export ANTHROPIC_API_KEY=your-key' >> ~/.bashrc
source ~/.bashrc
```

### 问题4: 样本股为空

**错误信息:**
```
样本股不足(0只),建议至少20只
```

**解决方案:**
1. 检查板块成分股数据:
   ```sql
   SELECT board_code, constituents FROM board_mapping WHERE board_code = '886001.TI';
   ```
2. 确保Symbol表有市值数据
3. 确认K线数据覆盖成分股

## 高级配置

### 自定义追踪指数

编辑 `src/services/daily_review_data_service.py`:

```python
TRACKED_INDICES = [
    "000001.SH",  # 上证指数
    "399001.SZ",  # 深证成指
    "399006.SZ",  # 创业板指
    "000688.SH",  # 科创50
    "899050.BJ",  # 北证50
    "000852.SH",  # 中证1000
    "000300.SH",  # 沪深300 (新增)
]
```

### 调整标签阈值

编辑 `src/utils/market_sentiment_analyzer.py`:

```python
# 修改放量阈值(默认1.5倍)
if ratio_5d > 2.0:  # 改为2.0倍
    label = "放量"
```

### 自定义复盘格式

编辑 `docs/daily_review/prompt_template.md` 修改生成格式:
- 调整各部分字数
- 增加技术指标分析
- 添加估值分析
- 改为英文输出

## 性能优化

### 数据采集优化

1. **并行查询**: 使用asyncio并行查询多个板块数据
2. **缓存策略**: 缓存Symbol表和BoardMapping数据
3. **批量查询**: 使用`in_`查询批量获取K线数据

### API成本控制

1. **控制温度**: 使用低温度(0.3)减少随机性
2. **使用Haiku**: 对于简单场景使用`claude-haiku`降低成本
3. **本地缓存**: 缓存已生成的复盘,避免重复生成

## 最佳实践

1. **市场收盘后运行**: 建议15:30后运行,确保数据完整
2. **数据验证**: 使用`--validate`标志检查数据质量
3. **版本控制**: 将生成的复盘纳入git,追踪历史
4. **人工审核**: AI生成的复盘建议人工审核后再发布
5. **成本监控**: 定期检查API使用量和成本

## 文件组织

```
docs/daily_review/
├── README.md                    # 本文档
├── prompt_template.md           # AI生成模板
├── snapshots/                   # 数据快照目录
│   ├── 20250126.json
│   ├── 20250127.json
│   └── ...
└── reviews/                     # 复盘报告目录
    ├── 20250126.md
    ├── 20250127.md
    └── ...
```

## 相关文档

- **实施计划**: 查看项目根目录的实施计划文档了解系统设计
- **API文档**: `src/api/routes_review.py` (如果实现了API接口)
- **数据模型**: `src/schemas/daily_review.py` 查看完整数据结构
- **算法详解**: `.claude/skills/daily-review/references/` 查看算法实现细节

## 技术支持

如遇问题,检查顺序:
1. 查看日志: `logs/daily_review.log`
2. 运行验证: `python scripts/generate_snapshot.py --validate`
3. 检查数据: 查询数据库确认数据完整性
4. 参考文档: 阅读skill文档了解详细实现
