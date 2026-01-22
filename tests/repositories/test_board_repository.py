"""BoardRepository单元测试

测试覆盖:
1. BoardMapping CRUD操作
2. IndustryDaily CRUD操作
3. ConceptDaily CRUD操作
4. 边界情况和错误处理
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.models import Base, BoardMapping, IndustryDaily, ConceptDaily
from src.repositories.board_repository import BoardRepository


@pytest.fixture(scope="function")
def test_db():
    """创建内存数据库用于测试"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def board_repo(test_db: Session):
    """创建BoardRepository实例"""
    return BoardRepository(test_db)


# ==================== BoardMapping 测试 ====================


class TestBoardMappingOperations:
    """BoardMapping CRUD操作测试"""

    def test_upsert_board_mapping(self, board_repo: BoardRepository, test_db: Session):
        """测试插入板块映射"""
        mapping = BoardMapping(
            board_name="人工智能",
            board_type="concept",
            board_code="885728",
            constituents=["000001.SZ", "600000.SH"],
            last_updated=datetime.utcnow(),
        )

        result = board_repo.upsert_board_mapping(mapping)
        test_db.commit()

        assert result.id is not None
        assert result.board_name == "人工智能"
        assert result.board_code == "885728"
        assert len(result.constituents) == 2

    def test_find_board_by_name_and_type(self, board_repo: BoardRepository, test_db: Session):
        """测试按名称和类型查询板块"""
        # 插入测试数据
        mapping = BoardMapping(
            board_name="人工智能",
            board_type="concept",
            board_code="885728",
            constituents=["000001.SZ", "600000.SH"],
            last_updated=datetime.utcnow(),
        )
        test_db.add(mapping)
        test_db.commit()

        # 查询
        result = board_repo.find_board_by_name_and_type("人工智能", "concept")

        assert result is not None
        assert result.board_name == "人工智能"
        assert result.board_type == "concept"
        assert result.board_code == "885728"

    def test_find_boards_by_type(self, board_repo: BoardRepository, test_db: Session):
        """测试按类型查询板块"""
        # 插入不同类型的板块
        concept = BoardMapping(
            board_name="人工智能",
            board_type="concept",
            board_code="885728",
            constituents=["000001.SZ"],
            last_updated=datetime.utcnow(),
        )
        industry = BoardMapping(
            board_name="银行",
            board_type="industry",
            board_code="801010",
            constituents=["000001.SZ"],
            last_updated=datetime.utcnow(),
        )
        test_db.add_all([concept, industry])
        test_db.commit()

        # 只查询concept类型
        results = board_repo.find_boards_by_type("concept")

        assert len(results) == 1
        assert results[0].board_type == "concept"
        assert results[0].board_name == "人工智能"

    def test_upsert_board_mapping_update_existing(self, board_repo: BoardRepository, test_db: Session):
        """测试更新已存在的板块映射"""
        # 首次插入
        mapping1 = BoardMapping(
            board_name="人工智能",
            board_type="concept",
            board_code="885728",
            constituents=["000001.SZ"],
            last_updated=datetime.utcnow(),
        )
        test_db.add(mapping1)
        test_db.commit()

        # 更新（增加成分股）
        mapping2 = BoardMapping(
            board_name="人工智能",
            board_type="concept",
            board_code="885728",
            constituents=["000001.SZ", "600000.SH"],
            last_updated=datetime.utcnow(),
        )
        result = board_repo.upsert_board_mapping(mapping2)
        test_db.commit()

        # 验证更新
        assert len(result.constituents) == 2
        assert "600000.SH" in result.constituents


# ==================== IndustryDaily 测试 ====================


class TestIndustryDailyOperations:
    """IndustryDaily CRUD操作测试"""

    def test_upsert_industry_daily_batch(self, board_repo: BoardRepository, test_db: Session):
        """测试批量插入行业日线数据"""
        industries = [
            IndustryDaily(
                ts_code="801010",
                industry="农林牧渔",
                trade_date="20260122",
                close=1234.56,
                pct_change=1.23,
                company_num=50,
            ),
            IndustryDaily(
                ts_code="801020",
                industry="采掘",
                trade_date="20260122",
                close=2345.67,
                pct_change=-0.45,
                company_num=30,
            ),
        ]

        count = board_repo.upsert_industry_daily_batch(industries)
        test_db.commit()

        assert count == 2

    def test_find_industry_daily(self, board_repo: BoardRepository, test_db: Session):
        """测试查询行业日线数据"""
        # 插入测试数据
        industry = IndustryDaily(
            ts_code="801010",
            industry="农林牧渔",
            trade_date="20260122",
            close=1234.56,
            pct_change=1.23,
            company_num=50,
        )
        test_db.add(industry)
        test_db.commit()

        # 查询
        result = board_repo.find_industry_daily("801010", "20260122")

        assert result is not None
        assert result.ts_code == "801010"
        assert result.industry == "农林牧渔"
        assert result.close == 1234.56

    def test_find_industry_daily_by_code(self, board_repo: BoardRepository, test_db: Session):
        """测试按代码查询行业日线"""
        # 插入多天数据
        for i in range(3):
            industry = IndustryDaily(
                ts_code="801010",
                industry="农林牧渔",
                trade_date=f"2026012{i}",
                close=1234.56 + i,
                pct_change=1.23,
                company_num=50,
            )
            test_db.add(industry)
        test_db.commit()

        # 查询最近2天
        results = board_repo.find_industry_daily_by_code("801010", limit=2)

        assert len(results) == 2
        # 应该按日期倒序
        assert results[0].trade_date > results[1].trade_date

    def test_find_industry_daily_by_date(self, board_repo: BoardRepository, test_db: Session):
        """测试按日期查询行业日线"""
        # 插入多个行业的同一天数据
        industries = [
            IndustryDaily(
                ts_code="801010",
                industry="农林牧渔",
                trade_date="20260122",
                close=1234.56,
                pct_change=1.23,
                company_num=50,
            ),
            IndustryDaily(
                ts_code="801020",
                industry="采掘",
                trade_date="20260122",
                close=2345.67,
                pct_change=-0.45,
                company_num=30,
            ),
        ]
        test_db.add_all(industries)
        test_db.commit()

        # 查询
        results = board_repo.find_industry_daily_by_date("20260122")

        assert len(results) == 2

    def test_get_all_industry_codes(self, board_repo: BoardRepository, test_db: Session):
        """测试获取所有行业代码"""
        # 插入数据
        industries = [
            IndustryDaily(
                ts_code="801010",
                industry="农林牧渔",
                trade_date="20260122",
                close=1234.56,
                pct_change=1.23,
                company_num=50,
            ),
            IndustryDaily(
                ts_code="801020",
                industry="采掘",
                trade_date="20260122",
                close=2345.67,
                pct_change=-0.45,
                company_num=30,
            ),
        ]
        test_db.add_all(industries)
        test_db.commit()

        # 查询
        codes = board_repo.get_all_industry_codes()

        assert len(codes) == 2
        assert "801010" in codes
        assert "801020" in codes


# ==================== ConceptDaily 测试 ====================


class TestConceptDailyOperations:
    """ConceptDaily CRUD操作测试"""

    def test_upsert_concept_daily_batch(self, board_repo: BoardRepository, test_db: Session):
        """测试批量插入概念日线数据"""
        concepts = [
            ConceptDaily(
                code="885728",
                name="人工智能",
                trade_date="20260122",
                close=1530.33,
                pct_change=2.45,
                amount=987654321.0,
                leader_symbol="300750.SZ",
                leader_name="宁德时代",
            ),
            ConceptDaily(
                code="886100",
                name="华为概念",
                trade_date="20260122",
                close=1245.67,
                pct_change=1.23,
                amount=876543210.0,
                leader_symbol="000063.SZ",
                leader_name="中兴通讯",
            ),
        ]

        count = board_repo.upsert_concept_daily_batch(concepts)
        test_db.commit()

        assert count == 2

    def test_find_concept_daily(self, board_repo: BoardRepository, test_db: Session):
        """测试查询概念日线数据"""
        # 插入测试数据
        concept = ConceptDaily(
            code="885728",
            name="人工智能",
            trade_date="20260122",
            close=1530.33,
            pct_change=2.45,
            amount=987654321.0,
        )
        test_db.add(concept)
        test_db.commit()

        # 查询
        result = board_repo.find_concept_daily("885728", "20260122")

        assert result is not None
        assert result.code == "885728"
        assert result.name == "人工智能"
        assert result.close == 1530.33

    def test_find_concept_daily_by_code(self, board_repo: BoardRepository, test_db: Session):
        """测试按代码查询概念日线"""
        # 插入多天数据
        for i in range(3):
            concept = ConceptDaily(
                code="885728",
                name="人工智能",
                trade_date=f"2026012{i}",
                close=1530.33 + i,
                pct_change=2.45,
                amount=987654321.0,
            )
            test_db.add(concept)
        test_db.commit()

        # 查询最近2天
        results = board_repo.find_concept_daily_by_code("885728", limit=2)

        assert len(results) == 2
        # 应该按日期倒序
        assert results[0].trade_date > results[1].trade_date

    def test_find_concept_daily_by_date(self, board_repo: BoardRepository, test_db: Session):
        """测试按日期查询概念日线"""
        # 插入多个概念的同一天数据
        concepts = [
            ConceptDaily(
                code="885728",
                name="人工智能",
                trade_date="20260122",
                close=1530.33,
                pct_change=2.45,
            ),
            ConceptDaily(
                code="886100",
                name="华为概念",
                trade_date="20260122",
                close=1245.67,
                pct_change=1.23,
            ),
        ]
        test_db.add_all(concepts)
        test_db.commit()

        # 查询
        results = board_repo.find_concept_daily_by_date("20260122")

        assert len(results) == 2

    def test_get_all_concept_codes(self, board_repo: BoardRepository, test_db: Session):
        """测试获取所有概念代码"""
        # 插入数据
        concepts = [
            ConceptDaily(
                code="885728",
                name="人工智能",
                trade_date="20260122",
                close=1530.33,
                pct_change=2.45,
            ),
            ConceptDaily(
                code="886100",
                name="华为概念",
                trade_date="20260122",
                close=1245.67,
                pct_change=1.23,
            ),
        ]
        test_db.add_all(concepts)
        test_db.commit()

        # 查询
        codes = board_repo.get_all_concept_codes()

        assert len(codes) == 2
        assert "885728" in codes
        assert "886100" in codes


# ==================== 边界情况测试 ====================


class TestBoardRepositoryEdgeCases:
    """边界情况和错误处理测试"""

    def test_find_board_by_name_and_type_not_found(self, board_repo: BoardRepository):
        """测试查询不存在的板块"""
        result = board_repo.find_board_by_name_and_type("不存在的板块", "concept")
        assert result is None

    def test_find_boards_by_type_empty(self, board_repo: BoardRepository):
        """测试查询空的板块类型"""
        results = board_repo.find_boards_by_type("concept")
        assert len(results) == 0

    def test_find_industry_daily_not_found(self, board_repo: BoardRepository):
        """测试查询不存在的行业日线"""
        result = board_repo.find_industry_daily("999999", "20260122")
        assert result is None

    def test_find_concept_daily_not_found(self, board_repo: BoardRepository):
        """测试查询不存在的概念日线"""
        result = board_repo.find_concept_daily("999999", "20260122")
        assert result is None

    def test_upsert_industry_daily_batch_empty(self, board_repo: BoardRepository):
        """测试批量插入空列表"""
        count = board_repo.upsert_industry_daily_batch([])
        assert count == 0

    def test_upsert_concept_daily_batch_empty(self, board_repo: BoardRepository):
        """测试批量插入空列表"""
        count = board_repo.upsert_concept_daily_batch([])
        assert count == 0

    def test_get_all_industry_codes_empty(self, board_repo: BoardRepository):
        """测试获取空的行业代码列表"""
        codes = board_repo.get_all_industry_codes()
        assert len(codes) == 0

    def test_get_all_concept_codes_empty(self, board_repo: BoardRepository):
        """测试获取空的概念代码列表"""
        codes = board_repo.get_all_concept_codes()
        assert len(codes) == 0

    def test_find_industry_daily_by_code_empty(self, board_repo: BoardRepository):
        """测试查询不存在代码的行业日线"""
        results = board_repo.find_industry_daily_by_code("999999")
        assert len(results) == 0

    def test_find_concept_daily_by_code_empty(self, board_repo: BoardRepository):
        """测试查询不存在代码的概念日线"""
        results = board_repo.find_concept_daily_by_code("999999")
        assert len(results) == 0

    def test_find_industry_daily_by_date_empty(self, board_repo: BoardRepository):
        """测试查询不存在日期的行业数据"""
        results = board_repo.find_industry_daily_by_date("20990101")
        assert len(results) == 0

    def test_find_concept_daily_by_date_empty(self, board_repo: BoardRepository):
        """测试查询不存在日期的概念数据"""
        results = board_repo.find_concept_daily_by_date("20990101")
        assert len(results) == 0
