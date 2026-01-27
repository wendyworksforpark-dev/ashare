# A-Share Monitor 官方术语表 (Official Terminology)

**版本**: v1.0
**更新日期**: 2026-01-23

本文档定义系统中所有组件、功能、页面、数据类型的官方命名，用于开发沟通和问题定位。

---

## 1. 数据类型 (Data Types)

| 术语 | 英文 | 代码标识 | 说明 | 示例 |
|------|------|----------|------|------|
| 个股 | Individual Stock | `STOCK` / `stock` | 单个上市公司股票 | 000738（中航动控）, 002278（神州泰岳） |
| 指数 | Market Index | `INDEX` / `index` | 市场指数 | 000001.SH（上证指数）, 399006.SZ（创业板指） |
| 概念板块 | Concept Board | `CONCEPT` / `concept` | 主题概念分类 | 人工智能、新能源车、ChatGPT |
| 行业板块 | Industry Board | `industry` | 行业分类 | 房地产、银行、半导体 |

---

## 2. 数据周期 (Timeframes)

| 术语 | 英文 | 代码标识 | 数据库值 | 说明 |
|------|------|----------|----------|------|
| 日线 | Daily K-line | `DAY` / `day` | `day` | 每日K线数据 |
| 30分钟线 | 30-min K-line | `MINS_30` / `30m` | `30m` | 30分钟周期K线 |
| 5分钟线 | 5-min K-line | `MINS_5` / `5m` | `5m` | 5分钟周期K线（未启用） |
| 实时价格 | Realtime Price | - | - | 盘中实时推送价格 |

---

## 3. 价格类型 (Price Types)

| 术语 | 英文 | 说明 | 使用场景 |
|------|------|------|----------|
| 收盘价 | Close Price | K线的收盘价格 | 日线、30分钟线 |
| 实时价 | Realtime Price | 当前最新成交价 | 盘中实时监控 |
| 最新价 | Latest Price | 通用术语 | 根据上下文是收盘价或实时价 |
| 前收盘价 | Previous Close | 前一交易日收盘价 | 计算涨跌幅基准 |

---

## 4. 功能模块 (Feature Modules)

| 模块ID | 中文名称 | 英文名称 | 路由/组件 | 说明 |
|--------|----------|----------|-----------|------|
| M1 | 自选股列表 | Watchlist | `WatchlistView` | 用户关注的个股清单 |
| M2 | 板块监控 | Board Monitor | `ConceptMonitorTable` | 概念板块实时涨跌监控 |
| M3 | 模拟交易 | Simulated Trading | `SimulatedPortfolioView` | 虚拟账户交易功能 |
| M4 | 动量信号 | Momentum Signals | `MomentumSignalsView` | 板块动量信号监控 |
| M5 | 概念详情 | Concept Detail | `ConceptDetailView` | 单个概念板块详情 |
| M6 | 个股详情 | Stock Detail | `StockDetail` | 单个股票详情页 |

---

## 5. 页面结构 (Page Structure)

### 5.1 首页 (Home Page / Concepts View)

**路由**: `/` (默认)
**组件**: `App.tsx` (viewMode = "concepts")
**页面代号**: **P1**

| Section ID | 中文名称 | 英文名称 | 组件 | 说明 |
|------------|----------|----------|------|------|
| **P1.1** | 指数图表区 | Index Charts Section | `IndexChart` × 3 | 显示上证指数、创业板指、科创50 |
| **P1.2** | 当日热门概念监控区 | Hot Concepts Monitor Section | `ConceptMonitorTable` (type="top") | 显示当日涨幅前20概念板块 |
| **P1.3** | 自选概念监控区 | Watchlist Concepts Monitor Section | `ConceptMonitorTable` (type="watch") | 显示用户自选的概念板块 |
| **P1.4** | 自选概念K线区 | Watchlist Concepts K-line Section | `ConceptKlinePanel` | 显示90+个自选概念的K线图表 |

**数据来源**:
- P1.1: 新浪财经实时API (sh000001, sz399006, sh000688)
- P1.2: 同花顺概念板块数据 (通过 `/api/concept-monitor/top?top=20`)
- P1.3: 同花顺概念板块数据 (通过 `/api/concept-monitor/watch`)
- P1.4: 数据库 `klines` 表 (symbol_type='CONCEPT', timeframe='DAY')

#### P1.2/P1.3 概念监控区 - ConceptMonitorTable 组件结构

**表头列 (Table Columns)**:

| Column ID | 中文名称 | 英文 | 数据字段 | 说明 |
|----------|----------|------|----------|------|
| **P1.2.COL1** | 排名 | Rank | `rank` | 涨幅排名序号 |
| **P1.2.COL2** | 板块名称 | Board Name | `name` | 概念板块名称 |
| **P1.2.COL3** | 涨幅 | Change % | `changePct` | 板块涨跌幅百分比 |
| **P1.2.COL4** | 主力资金 | Money Inflow | `moneyInflow` | 主力资金净流入（亿元） |
| **P1.2.COL5** | 涨停数 | Limit Up Count | `limitUp` | 涨停股票数量 |
| **P1.2.COL6** | 涨/跌比 | Up/Down Ratio | `upCount`/`downCount` | 上涨股票数/下跌股票数 |
| **P1.2.COL7** | 5日涨幅 | 5-day % | `change5d` | 5日涨跌幅 |
| **P1.2.COL8** | 10日涨幅 | 10-day % | `change10d` | 10日涨跌幅 |
| **P1.2.COL9** | 20日涨幅 | 20-day % | `change20d` | 20日涨跌幅 |
| **P1.2.COL10** | 成交额 | Turnover | `turnover` | 成交额（亿元） |
| **P1.2.COL11** | 成交量 | Volume | `volume` | 成交量（手） |

**数据更新频率**: 2.5分钟 (150秒)

#### P1.4 自选概念K线区 - ConceptKlinePanel 组件结构

**每个概念卡片 (ConceptKlineCard) 包含**:

| Component ID | 中文名称 | 英文名称 | 说明 |
|-------------|----------|----------|------|
| **P1.4.C1** | 概念名称+分类 | Concept Name & Category | 概念板块名称和所属分类 |
| **P1.4.C2** | 涨跌幅指示器 | Change % Indicator | 当日涨跌幅百分比 |
| **P1.4.C3** | 成分股数量 | Stock Count | 包含股票数量 |
| **P1.4.C4** | 日线K线图 | Daily K-line Chart | 概念板块日线图表 |
| **P1.4.C5** | 点击查看详情 | Click to Detail | 点击卡片跳转到P3概念详情页 |

---

### 5.2 自选股页面 (Watchlist Page)

**路由**: N/A (内部状态)
**组件**: `WatchlistView.tsx`
**页面代号**: **P2**

| Section ID | 中文名称 | 英文名称 | 组件/功能 | 说明 |
|------------|----------|----------|-----------|------|
| **P2.1** | 大盘对比区 | Market Comparison Section | 内联计算 (lines 132-238) | 显示上证指数 vs 自选股平均涨跌幅对比 |
| **P2.2** | 热门赛道区 | Hot Sectors Section | `SectorSummaryPanel` | 显示自选股中各赛道分布和涨跌情况 |
| **P2.3** | 自选股汇总区 | Watchlist Summary Section | `WatchlistCard` 列表 | 显示所有自选个股的K线图表和实时数据 |

**数据来源**:
- P2.1: 新浪财经 (sh000001) + 自选股实时价格
- P2.2: `/api/sectors/` (股票赛道分类映射)
- P2.3: `/api/watchlist` + 新浪财经实时价格 + `klines` 表

#### P2.3 自选股汇总区 - WatchlistCard 组件结构

每个 WatchlistCard 包含以下子组件：

| Component ID | 中文名称 | 英文名称 | 位置/代码 | 说明 |
|-------------|----------|----------|-----------|------|
| **P2.3.C1** | 股票名称+代码 | Stock Name & Ticker | lines 328-333 | 显示股票名称、板块标签、股票代码 |
| **P2.3.C2** | 赛道选择下拉菜单 | Sector Dropdown | lines 334-366 | 点击赛道名称可切换分类 |
| **P2.3.C3** | 买入按钮 | Buy Button | lines 367-374 | 快捷买入按钮 |
| **P2.3.C4** | 卖出按钮 | Sell Button | lines 375-382 | 快捷卖出按钮 |
| **P2.3.C5** | 重点关注按钮 | Focus Button | lines 383-393 | 标记/取消标记重点关注股票 (★/☆) |
| **P2.3.C6** | 持仓信息 | Position Info | lines 394-401 | 显示持仓股数和盈亏百分比 |
| **P2.3.C7** | 业绩按钮 | Earnings Button | lines 404-409 | 展开/收起业绩数据 |
| **P2.3.C8** | 详情按钮 | Detail Button | lines 410-415 | 展开/收起公司详情 |
| **P2.3.C9** | 移除/添加自选按钮 | Add/Remove Watchlist Button | lines 416-436 | 添加或移除自选股 |
| **P2.3.C10** | 价格信息区 | Price Info Section | lines 440-464 | 实时价、今日涨跌、昨日涨跌、市值、PE、行业、更新时间 |
| **P2.3.C11** | 日线K线图 | Daily K-line Chart | lines 470-484 | 日线K线图表（含成交量、MACD） |
| **P2.3.C12** | 30分钟K线图 | 30-min K-line Chart | lines 485-499 | 30分钟K线图表（含成交量、MACD） |
| **P2.3.C13** | K线标注评估表单 | K-line Evaluation Form | lines 502-511 | K线图标注和评估功能 |
| **P2.3.C14** | 业绩数据区 (可展开) | Earnings Section | lines 513-620 | 业绩预告和业绩快报详情 |
| **P2.3.C15** | 公司详情区 (可展开) | Company Details Section | lines 622-642 | 概念板块、公司简介、主营业务 |
| **P2.3.C16** | 交易对话框 | Trade Dialog | lines 644-659 | 买入/卖出交易弹窗 |

---

### 5.3 概念详情页 (Concept Detail Page)

**路由**: N/A (内部状态)
**组件**: `ConceptDetailView.tsx`
**页面代号**: **P3**

| Section ID | 中文名称 | 英文名称 | 说明 |
|------------|----------|----------|------|
| **P3.1** | 概念K线图区 | Concept K-line Chart Section | 显示概念板块的日线/30分钟K线 |
| **P3.2** | 成分股列表区 | Constituent Stocks Section | 显示该概念板块包含的所有股票 |

#### P3.1 概念K线图区 - 组件结构

| Component ID | 中文名称 | 英文名称 | 说明 |
|-------------|----------|----------|------|
| **P3.1.C1** | 概念名称标题 | Concept Title | 概念板块名称和代码 |
| **P3.1.C2** | 周期切换器 | Timeframe Switcher | 日线/30分钟切换按钮 |
| **P3.1.C3** | K线图表 | K-line Chart | 概念板块K线图（含MA线、成交量、MACD） |
| **P3.1.C4** | 统计信息 | Stats Info | 成分股数量、涨跌家数等统计 |

#### P3.2 成分股列表区 - 组件结构

| Component ID | 中文名称 | 英文名称 | 说明 |
|-------------|----------|----------|------|
| **P3.2.C1** | 股票列表表头 | Stock List Header | 代码、名称、价格、涨跌幅等列标题 |
| **P3.2.C2** | 股票行 | Stock Row | 每只股票的基本信息行（可点击跳转P4） |
| **P3.2.C3** | 排序控件 | Sort Controls | 按涨跌幅、市值等排序 |

---

### 5.4 个股详情页 (Stock Detail Page)

**路由**: N/A (内部状态)
**组件**: `StockDetail.tsx`
**页面代号**: **P4**

| Section ID | 中文名称 | 英文名称 | 说明 |
|------------|----------|----------|------|
| **P4.1** | 个股K线图区 | Stock K-line Chart Section | 显示个股的日线/30分钟K线 |
| **P4.2** | 个股基本信息区 | Stock Info Section | PE、市值、所属赛道等基本信息 |
| **P4.3** | 交易操作区 | Trading Actions Section | 买入/卖出/加入自选等操作按钮 |

**注意**: P4页面结构类似于 P2.3 的 WatchlistCard 展开状态，但占据全屏显示，包含更详细的信息。

---

### 5.5 模拟交易页面 (Simulated Portfolio Page)

**路由**: N/A (内部状态)
**组件**: `SimulatedPortfolioView.tsx`
**页面代号**: **P5**

| Section ID | 中文名称 | 英文名称 | 说明 |
|------------|----------|----------|------|
| **P5.1** | 账户总览区 | Account Summary Section | 总资产、持仓市值、可用资金 |
| **P5.2** | 持仓明细区 | Positions Section | 当前持有的股票列表 |
| **P5.3** | 交易记录区 | Trade History Section | 历史买卖记录 |

#### P5.1 账户总览区 - 组件结构

| Component ID | 中文名称 | 英文名称 | 说明 |
|-------------|----------|----------|------|
| **P5.1.C1** | 总资产 | Total Assets | 现金 + 持仓市值 |
| **P5.1.C2** | 可用资金 | Available Cash | 可用于买入的现金 |
| **P5.1.C3** | 持仓市值 | Market Value | 所有持仓的当前市值 |
| **P5.1.C4** | 总盈亏 | Total P&L | 总盈亏金额和百分比 |

#### P5.2 持仓明细区 - 组件结构

| Component ID | 中文名称 | 英文名称 | 说明 |
|-------------|----------|----------|------|
| **P5.2.C1** | 持仓列表表头 | Position List Header | 股票名称、持仓股数、成本价、当前价、盈亏等列 |
| **P5.2.C2** | 持仓行 | Position Row | 每个持仓股票的详细信息 |
| **P5.2.C3** | 卖出按钮 | Sell Button | 每行的快捷卖出按钮 |

#### P5.3 交易记录区 - 组件结构

| Component ID | 中文名称 | 英文名称 | 说明 |
|-------------|----------|----------|------|
| **P5.3.C1** | 记录列表表头 | Trade List Header | 日期、股票、类型、价格、数量等列 |
| **P5.3.C2** | 交易记录行 | Trade Row | 每笔交易的详细记录 |
| **P5.3.C3** | 筛选控件 | Filter Controls | 按日期、类型筛选交易记录 |

---

### 5.6 动量信号页面 (Momentum Signals Page)

**路由**: N/A (内部状态)
**组件**: `MomentumSignalsView.tsx`
**页面代号**: **P6**

| Section ID | 中文名称 | 英文名称 | 说明 |
|------------|----------|----------|------|
| **P6.1** | 动量信号列表区 | Momentum Signals Section | 显示板块动量信号 |

---

## 6. 数据源 (Data Sources)

| 数据源ID | 名称 | 英文 | API/库 | 用途 | 权限/限制 |
|----------|------|------|--------|------|-----------|
| DS1 | 新浪财经 | Sina Finance | 新浪实时行情API | 指数实时价格、个股实时价格 | 免费，无需认证 |
| DS2 | 同花顺 | Tonghuashun (10jqka) | AkShare库 | 概念板块数据、板块成分股 | 需爬取，有反爬风险 |
| DS3 | 东方财富 | Dongfang Wealth | AkShare库 | 个股历史数据 | 需爬取 |
| DS4 | 本地数据库 | Local DB | SQLite (data/market.db) | 历史K线、自选股列表 | 本地存储 |

---

## 7. 数据一致性问题 (Data Consistency Issue)

**问题代号**: **DC-001**
**问题描述**: 收盘后（16:00后）三个价格数据不一致

### 涉及的三种价格:
1. **实时价格** (Realtime Price) - 来自新浪财经实时API推送
2. **日线收盘价** (Daily Close Price) - 来自日线K线数据 (timeframe='DAY')
3. **30分钟线收盘价** (30-min Close Price) - 来自30分钟K线数据 (timeframe='30m')

### 预期行为:
收盘后（15:00收盘，数据更新时间15:30），三个价格应该完全一致（容忍度0.01%）

### 当前状态:
- 已修复3个Issue #11遗留bug（session未定义问题）
- 等待2-3个交易日观察数据一致性
- 待决定：以哪个价格为基准进行自动修正

---

## 8. 使用示例 (Usage Examples)

### 8.1 讨论页面级别问题

❌ **不规范**: "首页的板块那里显示不对"
✅ **规范**: "P1.2 (当日热门概念监控区) 显示数据不正确"

❌ **不规范**: "自选股页面上面那个对比"
✅ **规范**: "P2.1 (大盘对比区) 的涨跌幅计算有问题"

❌ **不规范**: "概念板块的K线"
✅ **规范**: "P1.4 (自选概念K线区) 的日线数据缺失"

### 8.2 讨论组件级别问题

❌ **不规范**: "自选股卡片的买入按钮点不了"
✅ **规范**: "P2.3.C3 (买入按钮) 无法点击，可能是 accountData 未加载"

❌ **不规范**: "股票的赛道选择下拉菜单选不中"
✅ **规范**: "P2.3.C2 (赛道选择下拉菜单) 点击后 updateSectorMutation 失败"

❌ **不规范**: "概念监控表格的资金流入数据不对"
✅ **规范**: "P1.2.COL4 (主力资金) 显示数值与同花顺网站不一致"

❌ **不规范**: "那个五星标记按钮没反应"
✅ **规范**: "P2.3.C5 (重点关注按钮) 点击后 toggleFocusMutation 报错"

❌ **不规范**: "30分钟K线图表画不出来"
✅ **规范**: "P2.3.C12 (30分钟K线图) 数据为空，fetchCandles返回空数组"

### 8.3 Bug报告模板

**模板1: 页面级别问题**
```
【问题页面】: P2 (自选股页面)
【问题Section】: P2.3 (自选股汇总区)
【问题描述】: 个股002278的实时价格显示为0
【数据源】: DS1 (新浪财经)
【影响范围】: 单个股票
【复现步骤】:
1. 打开自选股页面
2. 滚动到002278神州泰岳
3. 观察P2.3.C10 (价格信息区)
```

**模板2: 组件级别问题**
```
【问题组件】: P2.3.C5 (重点关注按钮)
【问题描述】: 点击后按钮变为"⌛"但一直不恢复，控制台报错 500
【错误信息】: TypeError: Cannot read property 'isFocus' of undefined
【影响范围】: 所有自选股的重点关注功能
【数据依赖】: toggleFocusMutation -> /api/watchlist/{ticker}/focus
```

**模板3: 数据一致性问题**
```
【问题代号】: DC-001
【问题Section】: P2.3.C10 (价格信息区) + P2.3.C11/C12 (K线图)
【问题描述】: 收盘后三个价格不一致
【对比数据】:
  - 实时价 (DS1): ¥15.32
  - 日线收盘价 (DS4): ¥15.30
  - 30分钟收盘价 (DS4): ¥15.31
【容忍度】: 0.01% (当前差异 0.13% 超标)
【影响标的】: 所有个股、指数、概念板块
```

### 8.4 功能请求模板

```
【功能位置】: P2.3 (自选股汇总区)
【请求组件】: 新增组件 P2.3.C17
【功能描述】: 在每个 WatchlistCard 顶部添加"分时图"按钮，点击后显示当日分时走势
【参考实现】: 类似 P2.3.C7 (业绩按钮) 的展开/收起机制
【数据需求】: 新增 API `/api/timeshare/{ticker}` 返回分时数据
```

---

## 9. 附录: 数据库表映射 (Database Tables)

| 表名 | 用途 | 对应Section |
|------|------|-------------|
| `klines` | 统一K线数据表 | P1.4, P2.3, P3.1, P4.1 |
| `watchlist` | 自选股列表 | P2.3 |
| `board_mapping` | 概念板块映射 | P1.2, P1.3, P3.2 |
| `stock_sectors` | 股票赛道分类 | P2.2 |
| `simulated_account` | 模拟账户 | P5.1 |
| `simulated_positions` | 模拟持仓 | P5.2 |
| `simulated_trades` | 模拟交易记录 | P5.3 |
| `trade_calendar` | 交易日历 | 全局使用 |
| `symbol_metadata` | 标的元数据 | 全局使用 |

---

## 10. 快速参考索引 (Quick Reference Index)

### 页面编号速查

- **P1** = 首页 (Concepts View)
  - P1.1 = 指数图表区
  - P1.2 = 当日热门概念监控区 (涨幅TOP20)
  - P1.3 = 自选概念监控区 (自选热门)
  - P1.4 = 自选概念K线区 (90+概念卡片)

- **P2** = 自选股页面 (Watchlist Page)
  - P2.1 = 大盘对比区
  - P2.2 = 热门赛道区
  - P2.3 = 自选股汇总区 (WatchlistCard列表)

- **P3** = 概念详情页
- **P4** = 个股详情页
- **P5** = 模拟交易页面
- **P6** = 动量信号页面

### 常用组件编号速查 (P2.3 WatchlistCard)

- **P2.3.C1** = 股票名称+代码
- **P2.3.C2** = 赛道选择下拉菜单
- **P2.3.C3** = 买入按钮
- **P2.3.C4** = 卖出按钮
- **P2.3.C5** = 重点关注按钮 (★/☆)
- **P2.3.C6** = 持仓信息
- **P2.3.C7** = 业绩按钮
- **P2.3.C8** = 详情按钮
- **P2.3.C9** = 移除/添加自选按钮
- **P2.3.C10** = 价格信息区
- **P2.3.C11** = 日线K线图
- **P2.3.C12** = 30分钟K线图
- **P2.3.C13** = K线标注评估表单
- **P2.3.C14** = 业绩数据区 (可展开)
- **P2.3.C15** = 公司详情区 (可展开)
- **P2.3.C16** = 交易对话框

### 数据类型速查

- **STOCK** = 个股
- **INDEX** = 指数
- **CONCEPT** = 概念板块
- **industry** = 行业板块

### 数据源速查

- **DS1** = 新浪财经 (实时价格)
- **DS2** = 同花顺 (概念板块)
- **DS3** = 东方财富 (个股历史)
- **DS4** = 本地数据库 (klines表)

### 问题代号速查

- **DC-001** = 数据一致性问题 (收盘后三价格不一致)

---

## 11. 版本历史 (Version History)

- **v1.0** (2026-01-23): 初始版本，定义全部页面Section编号和组件编号
