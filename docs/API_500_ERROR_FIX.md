# API 500错误修复记录

## 问题描述

在搜索栏搜索股票后，加载股票信息页面时出现多个API请求失败：

### 错误类型

1. **500 Internal Server Error**
   - `/api/simulated/account` - 模拟账户API
   - `/api/simulated/positions` - 持仓列表API
   - `/api/symbols` - 股票列表API
   - `/api/concepts/realtime/*` - 概念板块实时数据API

2. **ERR_NETWORK_CHANGED**
   - `/api/concepts/kline/*` - 概念板块K线数据API

## 根本原因

服务类在代码重构后引入了依赖注入模式（Repository Pattern），但是依赖注入配置没有同步更新：

### 1. MarketDataService 初始化失败

**文件**: `src/api/dependencies.py`

**问题代码**:
```python
@lru_cache
def data_service() -> MarketDataService:
    return MarketDataService()  # ❌ 缺少必需的 symbol_repo 参数
```

**错误信息**:
```
TypeError: MarketDataService.__init__() missing 1 required positional argument: 'symbol_repo'
```

**原因**:
- `MarketDataService` 重构后需要传入 `SymbolRepository` 参数
- 但 `dependencies.py` 中的工厂函数没有提供参数

### 2. SimulatedService 方法调用错误

**文件**: `src/services/simulated_service.py`

**问题代码**:
```python
def _get_current_price(self, ticker: str) -> Optional[float]:
    klines = self.kline_repo.find_by_symbol_and_timeframe(  # ❌ 方法不存在
        symbol_code=ticker,
        symbol_type=SymbolType.STOCK,
        timeframe=KlineTimeframe.DAY,
        limit=1,
        order_desc=True  # ❌ 参数不存在
    )
```

**错误信息**:
```
AttributeError: 'KlineRepository' object has no attribute 'find_by_symbol_and_timeframe'
```

**原因**:
- `KlineRepository` 中的方法名是 `find_by_symbol`，不是 `find_by_symbol_and_timeframe`
- `find_by_symbol` 方法也没有 `order_desc` 参数

## 解决方案

### 修复1: 更新 MarketDataService 依赖注入 ✅

**文件**: `src/api/dependencies.py`

**修复后的代码**:
```python
# 全局服务实例（单例模式）
_market_data_service: MarketDataService | None = None


def get_data_service() -> MarketDataService:
    """
    获取 MarketDataService 单例

    注意：使用全局单例和专用Session，因为服务需要长期存在
    """
    global _market_data_service
    if _market_data_service is None:
        # 为服务创建专用session（不会自动关闭）
        session = SessionLocal()
        symbol_repo = SymbolRepository(session)
        _market_data_service = MarketDataService(symbol_repo=symbol_repo)
    return _market_data_service
```

**说明**:
- 移除了 `@lru_cache` 装饰器（不支持带参数的依赖）
- 使用全局单例模式管理服务实例
- 创建专用 Session 和 Repository 实例
- 服务生命周期与应用相同（不会自动关闭session）

### 修复2: 修正 KlineRepository 方法调用 ✅

**文件**: `src/services/simulated_service.py`

**修复后的代码**:
```python
def _get_current_price(self, ticker: str) -> Optional[float]:
    """获取股票当前价格（最近收盘价）"""
    # 使用 KlineRepository 查询最新日线
    klines = self.kline_repo.find_by_symbol(
        symbol_code=ticker,
        symbol_type=SymbolType.STOCK,
        timeframe=KlineTimeframe.DAY,
        limit=1
    )
    return klines[0].close if klines else None
```

**说明**:
- 使用正确的方法名 `find_by_symbol`
- 移除不存在的 `order_desc` 参数
- `find_by_symbol` 默认按时间倒序排列，limit=1 即获取最新数据

## 测试验证

### 1. 测试 /api/symbols ✅
```bash
curl -s http://localhost:8000/api/symbols | head -100
```

**结果**: 返回股票列表数据（工商银行、农业银行等）

### 2. 测试 /api/simulated/account ✅
```bash
curl -s http://localhost:8000/api/simulated/account
```

**结果**:
```json
{
  "initial_capital": 10000000.0,
  "cash": 220645.0,
  "position_value": 10020968.0,
  "total_value": 10241613.0,
  "total_pnl": 241613.0,
  "total_pnl_pct": 2.42,
  "position_count": 11
}
```

### 3. 测试 /api/concepts/realtime/{code} ✅
```bash
curl -s http://localhost:8000/api/concepts/realtime/886076
```

**结果**:
```json
{
  "code": "886076",
  "name": "军工信息化",
  "price": 2153.082,
  "pre_close": 2258.907,
  "change_pct": -4.68,
  "last_update": ""
}
```

## 相关文件

### 修改的文件
- `src/api/dependencies.py` - 修复 MarketDataService 依赖注入
- `src/services/simulated_service.py` - 修复 KlineRepository 方法调用

### 相关文件
- `src/services/data_pipeline.py` - MarketDataService 定义
- `src/repositories/kline_repository.py` - KlineRepository 定义
- `src/repositories/symbol_repository.py` - SymbolRepository 定义
- `src/api/routes_meta.py` - 使用 MarketDataService 的路由
- `src/api/routes_simulated.py` - 使用 SimulatedService 的路由

## 教训总结

1. **重构时同步更新依赖配置**
   - 修改服务类的构造函数签名时，必须同时更新所有调用点
   - 特别是依赖注入配置文件 (`dependencies.py`)

2. **注意方法重命名**
   - Repository 重构时方法名可能改变
   - 使用IDE的"查找引用"功能确保所有调用都已更新

3. **FastAPI自动重载的局限性**
   - `--reload` 模式会重新加载代码文件
   - 但全局单例变量可能需要手动重启服务才能完全重置
   - 对于依赖注入配置的更改，建议完全重启服务

4. **测试覆盖的重要性**
   - 应该为所有API端点编写集成测试
   - 重构后运行完整的测试套件
   - 避免依赖手动测试发现问题

## 后续建议

1. **添加启动时健康检查**
   ```python
   @app.on_event("startup")
   async def startup_check():
       try:
           # 测试所有服务能否正常初始化
           get_data_service()
           get_simulated_service()
       except Exception as e:
           logger.error(f"Service initialization failed: {e}")
           raise
   ```

2. **添加API集成测试**
   ```python
   def test_api_symbols():
       response = client.get("/api/symbols")
       assert response.status_code == 200
       assert len(response.json()) > 0
   ```

3. **使用依赖注入框架**
   考虑使用更成熟的DI框架（如 `dependency-injector`）来管理复杂的依赖关系

4. **改进错误处理**
   在依赖注入函数中添加更详细的错误日志，便于快速定位问题

## 状态

- [x] 问题诊断完成
- [x] MarketDataService 依赖注入修复
- [x] SimulatedService 方法调用修复
- [x] API测试验证通过
- [x] 文档记录完成
- [ ] 添加集成测试（后续）
- [ ] 添加启动健康检查（后续）
