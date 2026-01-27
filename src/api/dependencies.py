from functools import lru_cache
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from src.config import get_settings
from src.database import SessionLocal
from src.services.data_pipeline import MarketDataService
from src.repositories.symbol_repository import SymbolRepository


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库Session（依赖注入）

    用法:
        @router.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # 使用 db 进行数据库操作
            pass

    Yields:
        SQLAlchemy Session，自动管理生命周期（请求结束时关闭）
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
