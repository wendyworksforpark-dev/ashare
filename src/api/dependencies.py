from functools import lru_cache
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from src.config import get_settings
from src.database import SessionLocal
from src.services.data_pipeline import MarketDataService


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


@lru_cache
def data_service() -> MarketDataService:
    return MarketDataService()


def get_data_service(service: MarketDataService = Depends(data_service)) -> MarketDataService:
    return service
