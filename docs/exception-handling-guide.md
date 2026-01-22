# 异常处理使用指南

本指南说明如何在项目中使用自定义异常体系进行错误处理。

## 目录

- [异常层次结构](#异常层次结构)
- [使用场景](#使用场景)
- [在Repository中使用](#在repository中使用)
- [在Service中使用](#在service中使用)
- [在API路由中使用](#在api路由中使用)
- [HTTP状态码映射](#http状态码映射)
- [最佳实践](#最佳实践)

## 异常层次结构

```
Exception
└── AShareBaseException (基础业务异常)
    ├── DataNotFoundError (数据未找到)
    ├── DatabaseError (数据库错误)
    ├── DataIntegrityError (数据完整性错误)
    ├── ExternalAPIError (外部API错误)
    │   ├── TushareAPIError (Tushare API错误)
    │   └── RateLimitExceededError (速率限制)
    ├── ValidationError (数据验证错误)
    │   ├── InvalidSymbolError (无效股票代码)
    │   ├── InvalidTimeframeError (无效时间周期)
    │   └── InvalidDateRangeError (无效日期范围)
    ├── BusinessLogicError (业务逻辑错误)
    │   ├── InsufficientDataError (数据不足)
    │   └── DataStaleError (数据过期)
    ├── ConfigurationError (配置错误)
    │   └── MissingConfigError (缺少配置)
    ├── AuthenticationError (认证失败)
    ├── AuthorizationError (授权失败)
    ├── ServiceUnavailableError (服务不可用)
    └── TimeoutError (操作超时)
```

## 使用场景

### 1. 数据未找到

当查询的数据不存在时使用：

```python
from src.exceptions import DataNotFoundError

def get_stock_by_ticker(ticker: str):
    stock = repository.find_by_ticker(ticker)
    if not stock:
        raise DataNotFoundError(resource="Stock", identifier=ticker)
    return stock
```

### 2. 数据验证失败

当输入参数不符合要求时使用：

```python
from src.exceptions import InvalidSymbolError, InvalidTimeframeError

def validate_symbol(symbol: str):
    if not symbol or len(symbol) != 6:
        raise InvalidSymbolError(symbol=symbol, reason="Symbol must be 6 digits")

def validate_timeframe(timeframe: str):
    valid_timeframes = ["day", "30m", "5m", "1m"]
    if timeframe not in valid_timeframes:
        raise InvalidTimeframeError(timeframe=timeframe)
```

### 3. 外部API错误

当调用Tushare等外部API失败时使用：

```python
from src.exceptions import TushareAPIError, RateLimitExceededError

try:
    response = tushare_client.query(api_name="daily", params={...})
except requests.HTTPError as e:
    if e.response.status_code == 429:
        raise RateLimitExceededError(provider="Tushare", retry_after=60)
    else:
        raise TushareAPIError(details=str(e), status_code=e.response.status_code)
```

### 4. 数据库错误

当数据库操作失败时使用：

```python
from src.exceptions import DatabaseError, DataIntegrityError
from sqlalchemy.exc import IntegrityError

try:
    session.add(new_record)
    session.commit()
except IntegrityError as e:
    session.rollback()
    raise DataIntegrityError(table="klines", constraint=str(e.orig))
except Exception as e:
    session.rollback()
    raise DatabaseError(operation="INSERT", reason=str(e))
```

### 5. 业务逻辑错误

当数据不满足业务规则时使用：

```python
from src.exceptions import InsufficientDataError, DataStaleError
from datetime import datetime, timedelta

def calculate_macd(klines: list):
    if len(klines) < 26:
        raise InsufficientDataError(
            operation="MACD calculation",
            required=26,
            actual=len(klines)
        )
    # 计算MACD...

def check_data_freshness(last_update: datetime):
    if datetime.now() - last_update > timedelta(days=1):
        raise DataStaleError(
            resource="Stock data",
            last_update=last_update.isoformat()
        )
```

## 在Repository中使用

Repository层应该抛出数据访问相关的异常：

```python
from src.exceptions import DataNotFoundError, DatabaseError

class StockRepository:
    def find_by_ticker(self, ticker: str) -> Optional[Stock]:
        """查找股票，不存在时返回None（不抛异常）"""
        try:
            return self.session.query(Stock).filter_by(ticker=ticker).first()
        except Exception as e:
            raise DatabaseError(operation="SELECT", reason=str(e))

    def get_by_ticker(self, ticker: str) -> Stock:
        """获取股票，不存在时抛出异常"""
        stock = self.find_by_ticker(ticker)
        if not stock:
            raise DataNotFoundError(resource="Stock", identifier=ticker)
        return stock
```

## 在Service中使用

Service层应该抛出业务逻辑相关的异常：

```python
from src.exceptions import (
    DataNotFoundError,
    InvalidSymbolError,
    InsufficientDataError,
)

class KlineService:
    def get_klines_with_macd(self, symbol: str, limit: int = 120):
        # 验证输入
        if not symbol or len(symbol) != 6:
            raise InvalidSymbolError(symbol=symbol)

        # 获取数据
        klines = self.kline_repo.find_by_symbol(symbol, limit=limit)
        if not klines:
            raise DataNotFoundError(resource="Klines", identifier=symbol)

        # 业务逻辑验证
        if len(klines) < 26:
            raise InsufficientDataError(
                operation="MACD calculation",
                required=26,
                actual=len(klines)
            )

        # 计算指标
        return self._calculate_macd(klines)
```

## 在API路由中使用

API路由应该直接抛出异常，FastAPI会自动调用注册的异常处理器：

```python
from fastapi import APIRouter, Depends
from src.exceptions import DataNotFoundError, InvalidSymbolError

router = APIRouter()

@router.get("/stocks/{ticker}")
def get_stock(ticker: str, service: StockService = Depends()):
    """
    获取股票信息

    - 如果股票不存在，会返回404错误
    - 如果股票代码格式无效，会返回400错误
    """
    # 不需要try-except，直接调用service
    # 异常会被FastAPI的异常处理器自动捕获
    return service.get_stock_by_ticker(ticker)
```

**旧的错误处理方式（不推荐）：**

```python
@router.get("/stocks/{ticker}")
def get_stock_old(ticker: str):
    try:
        stock = service.get_stock_by_ticker(ticker)
        return stock
    except Exception as e:
        logger.exception("获取股票失败")
        raise HTTPException(status_code=500, detail=str(e))
```

**新的处理方式（推荐）：**

```python
@router.get("/stocks/{ticker}")
def get_stock_new(ticker: str):
    # 直接调用，异常会被自动处理
    return service.get_stock_by_ticker(ticker)
```

## HTTP状态码映射

FastAPI异常处理器会自动将自定义异常映射到合适的HTTP状态码：

| 异常类型 | HTTP状态码 | 说明 |
|---------|-----------|------|
| `DataNotFoundError` | 404 | 资源未找到 |
| `ValidationError` | 400 | 请求参数验证失败 |
| `InvalidSymbolError` | 400 | 股票代码格式错误 |
| `AuthenticationError` | 401 | 认证失败 |
| `AuthorizationError` | 403 | 权限不足 |
| `BusinessLogicError` | 422 | 业务逻辑错误 |
| `ExternalAPIError` | 502 | 外部API错误 |
| `ServiceUnavailableError` | 503 | 服务不可用 |
| `DatabaseError` | 500 | 数据库错误 |
| `ConfigurationError` | 500 | 配置错误 |
| `AShareBaseException` | 500 | 其他业务异常 |

## 最佳实践

### 1. 选择合适的异常类型

- **数据不存在** → `DataNotFoundError`
- **参数格式错误** → `ValidationError` 或其子类
- **数据不满足业务规则** → `BusinessLogicError` 或其子类
- **外部服务调用失败** → `ExternalAPIError` 或其子类
- **数据库操作失败** → `DatabaseError`

### 2. 提供详细的错误信息

```python
# 好的做法
raise DataNotFoundError(resource="Stock", identifier="000001.SZ")

# 不好的做法
raise Exception("Not found")
```

### 3. 在合适的层次抛出异常

- **Repository层**：数据访问异常（`DatabaseError`, `DataNotFoundError`）
- **Service层**：业务逻辑异常（`BusinessLogicError`, `ValidationError`）
- **API层**：直接抛出异常，不要捕获

### 4. 不要过度捕获异常

```python
# 好的做法 - 让异常向上传播
def get_stock(ticker: str):
    return service.get_stock_by_ticker(ticker)

# 不好的做法 - 不必要的try-except
def get_stock_bad(ticker: str):
    try:
        return service.get_stock_by_ticker(ticker)
    except DataNotFoundError as e:
        # 重新抛出同样的异常没有意义
        raise DataNotFoundError(resource=e.resource, identifier=e.identifier)
```

### 5. 记录日志

异常处理器会自动记录日志，但在某些情况下可以手动添加上下文信息：

```python
from src.utils.logging import get_logger

logger = get_logger(__name__)

def fetch_external_data(symbol: str):
    try:
        response = requests.get(f"https://api.example.com/{symbol}")
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        logger.error(f"Failed to fetch data for {symbol}", extra={"status": e.response.status_code})
        raise ExternalAPIError(provider="ExampleAPI", details=str(e), status_code=e.response.status_code)
```

## 测试异常处理

编写测试时，使用`pytest.raises`来验证异常：

```python
import pytest
from src.exceptions import DataNotFoundError, InvalidSymbolError

def test_get_stock_not_found():
    """测试股票不存在的情况"""
    with pytest.raises(DataNotFoundError) as exc_info:
        service.get_stock_by_ticker("999999")

    assert exc_info.value.resource == "Stock"
    assert exc_info.value.identifier == "999999"

def test_invalid_symbol():
    """测试无效股票代码"""
    with pytest.raises(InvalidSymbolError):
        service.validate_symbol("INVALID")
```

## 迁移现有代码

逐步将现有的通用异常替换为自定义异常：

### 迁移前

```python
def get_klines(symbol: str):
    klines = repo.find_by_symbol(symbol)
    if not klines:
        raise HTTPException(status_code=404, detail=f"未找到K线数据: {symbol}")
    return klines
```

### 迁移后

```python
def get_klines(symbol: str):
    klines = repo.find_by_symbol(symbol)
    if not klines:
        raise DataNotFoundError(resource="Klines", identifier=symbol)
    return klines
```

## 总结

- ✅ 使用具体的异常类型，不要使用通用`Exception`
- ✅ 在Repository层抛出数据访问异常
- ✅ 在Service层抛出业务逻辑异常
- ✅ 在API层直接抛出异常，让FastAPI处理
- ✅ 提供详细的错误信息和上下文
- ✅ 编写测试验证异常行为
- ❌ 不要过度捕获和重新抛出异常
- ❌ 不要在API层手动转换为HTTPException
