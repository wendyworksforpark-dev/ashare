"""
BoardRepository - 板块数据访问层

封装板块（行业、概念）相关的数据库操作。
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from src.models import BoardMapping, ConceptDaily, IndustryDaily
from src.repositories.base_repository import BaseRepository
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BoardRepository(BaseRepository[BoardMapping]):
    """板块数据Repository"""

    def __init__(self, session: Session):
        """初始化BoardRepository"""
        super().__init__(session, BoardMapping)

    # ==================== BoardMapping 相关方法 ====================

    def find_board_by_name_and_type(
        self, board_name: str, board_type: str
    ) -> Optional[BoardMapping]:
        """
        根据板块名称和类型查询板块映射

        Args:
            board_name: 板块名称
            board_type: 板块类型（industry/concept）

        Returns:
            板块映射或None
        """
        stmt = select(BoardMapping).filter(
            and_(
                BoardMapping.board_name == board_name,
                BoardMapping.board_type == board_type,
            )
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def find_boards_by_type(self, board_type: str) -> List[BoardMapping]:
        """
        根据板块类型查询所有板块

        Args:
            board_type: 板块类型（industry/concept）

        Returns:
            板块映射列表
        """
        stmt = select(BoardMapping).filter(BoardMapping.board_type == board_type)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def upsert_board_mapping(self, board_mapping: BoardMapping) -> BoardMapping:
        """
        插入或更新板块映射

        Args:
            board_mapping: 板块映射

        Returns:
            保存后的板块映射
        """
        stmt = sqlite_insert(BoardMapping).values(
            board_name=board_mapping.board_name,
            board_type=board_mapping.board_type,
            board_code=board_mapping.board_code,
            constituents=board_mapping.constituents,
            last_updated=board_mapping.last_updated,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["board_name", "board_type"],
            set_={
                "board_code": stmt.excluded.board_code,
                "constituents": stmt.excluded.constituents,
                "last_updated": stmt.excluded.last_updated,
            },
        )

        self.session.execute(stmt)
        self.session.flush()

        return self.find_board_by_name_and_type(
            board_mapping.board_name, board_mapping.board_type
        )

    # ==================== IndustryDaily 相关方法 ====================

    def find_industry_daily(
        self, ts_code: str, trade_date: str
    ) -> Optional[IndustryDaily]:
        """
        查询行业日线数据

        Args:
            ts_code: 行业代码
            trade_date: 交易日期（YYYYMMDD）

        Returns:
            行业日线数据或None
        """
        stmt = select(IndustryDaily).filter(
            and_(
                IndustryDaily.ts_code == ts_code,
                IndustryDaily.trade_date == trade_date,
            )
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def find_industry_daily_by_code(
        self, ts_code: str, limit: int = 100
    ) -> List[IndustryDaily]:
        """
        查询行业的历史日线数据

        Args:
            ts_code: 行业代码
            limit: 返回数量限制

        Returns:
            行业日线数据列表（按日期倒序）
        """
        stmt = (
            select(IndustryDaily)
            .filter(IndustryDaily.ts_code == ts_code)
            .order_by(desc(IndustryDaily.trade_date))
            .limit(limit)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def find_industry_daily_by_date(
        self, trade_date: str
    ) -> List[IndustryDaily]:
        """
        查询指定日期的所有行业数据

        Args:
            trade_date: 交易日期（YYYYMMDD）

        Returns:
            行业日线数据列表
        """
        stmt = select(IndustryDaily).filter(
            IndustryDaily.trade_date == trade_date
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def upsert_industry_daily_batch(
        self, industry_dailies: List[IndustryDaily]
    ) -> int:
        """
        批量插入或更新行业日线数据

        Args:
            industry_dailies: 行业日线数据列表

        Returns:
            影响的行数
        """
        if not industry_dailies:
            return 0

        industry_dicts = [
            {
                "ts_code": ind.ts_code,
                "trade_date": ind.trade_date,
                "name": ind.name,
                "close": ind.close,
                "pct_change": ind.pct_change,
                "volume": ind.volume,
                "amount": ind.amount,
                "net_mf_amount": ind.net_mf_amount,
                "net_mf_volume": ind.net_mf_volume,
                "pe_ttm": ind.pe_ttm,
                "pb_mrq": ind.pb_mrq,
                "total_mv": ind.total_mv,
                "updated_at": ind.updated_at,
            }
            for ind in industry_dailies
        ]

        stmt = sqlite_insert(IndustryDaily).values(industry_dicts)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ts_code", "trade_date"],
            set_={
                "name": stmt.excluded.name,
                "close": stmt.excluded.close,
                "pct_change": stmt.excluded.pct_change,
                "volume": stmt.excluded.volume,
                "amount": stmt.excluded.amount,
                "net_mf_amount": stmt.excluded.net_mf_amount,
                "net_mf_volume": stmt.excluded.net_mf_volume,
                "pe_ttm": stmt.excluded.pe_ttm,
                "pb_mrq": stmt.excluded.pb_mrq,
                "total_mv": stmt.excluded.total_mv,
                "updated_at": stmt.excluded.updated_at,
            },
        )

        result = self.session.execute(stmt)
        self.session.flush()

        logger.info(f"Upserted {len(industry_dailies)} industry daily records")
        return result.rowcount

    # ==================== ConceptDaily 相关方法 ====================

    def find_concept_daily(
        self, code: str, trade_date: str
    ) -> Optional[ConceptDaily]:
        """
        查询概念日线数据

        Args:
            code: 概念代码
            trade_date: 交易日期（YYYYMMDD）

        Returns:
            概念日线数据或None
        """
        stmt = select(ConceptDaily).filter(
            and_(
                ConceptDaily.code == code,
                ConceptDaily.trade_date == trade_date,
            )
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def find_concept_daily_by_code(
        self, code: str, limit: int = 100
    ) -> List[ConceptDaily]:
        """
        查询概念的历史日线数据

        Args:
            code: 概念代码
            limit: 返回数量限制

        Returns:
            概念日线数据列表（按日期倒序）
        """
        stmt = (
            select(ConceptDaily)
            .filter(ConceptDaily.code == code)
            .order_by(desc(ConceptDaily.trade_date))
            .limit(limit)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def find_concept_daily_by_date(
        self, trade_date: str
    ) -> List[ConceptDaily]:
        """
        查询指定日期的所有概念数据

        Args:
            trade_date: 交易日期（YYYYMMDD）

        Returns:
            概念日线数据列表
        """
        stmt = select(ConceptDaily).filter(
            ConceptDaily.trade_date == trade_date
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def upsert_concept_daily_batch(
        self, concept_dailies: List[ConceptDaily]
    ) -> int:
        """
        批量插入或更新概念日线数据

        Args:
            concept_dailies: 概念日线数据列表

        Returns:
            影响的行数
        """
        if not concept_dailies:
            return 0

        concept_dicts = [
            {
                "code": con.code,
                "trade_date": con.trade_date,
                "name": con.name,
                "close": con.close,
                "pct_change": con.pct_change,
                "volume": con.volume,
                "amount": con.amount,
                "leader_symbol": con.leader_symbol,
                "leader_name": con.leader_name,
                "leader_pct_change": con.leader_pct_change,
                "up_count": con.up_count,
                "down_count": con.down_count,
                "updated_at": con.updated_at,
            }
            for con in concept_dailies
        ]

        stmt = sqlite_insert(ConceptDaily).values(concept_dicts)
        stmt = stmt.on_conflict_do_update(
            index_elements=["code", "trade_date"],
            set_={
                "name": stmt.excluded.name,
                "close": stmt.excluded.close,
                "pct_change": stmt.excluded.pct_change,
                "volume": stmt.excluded.volume,
                "amount": stmt.excluded.amount,
                "leader_symbol": stmt.excluded.leader_symbol,
                "leader_name": stmt.excluded.leader_name,
                "leader_pct_change": stmt.excluded.leader_pct_change,
                "up_count": stmt.excluded.up_count,
                "down_count": stmt.excluded.down_count,
                "updated_at": stmt.excluded.updated_at,
            },
        )

        result = self.session.execute(stmt)
        self.session.flush()

        logger.info(f"Upserted {len(concept_dailies)} concept daily records")
        return result.rowcount

    def get_all_industry_codes(self) -> List[str]:
        """
        获取所有行业代码

        Returns:
            行业代码列表
        """
        stmt = select(IndustryDaily.ts_code).distinct()
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_all_concept_codes(self) -> List[str]:
        """
        获取所有概念代码

        Returns:
            概念代码列表
        """
        stmt = select(ConceptDaily.code).distinct()
        result = self.session.execute(stmt)
        return list(result.scalars().all())
