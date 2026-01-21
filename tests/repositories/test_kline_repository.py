"""
Unit tests for KlineRepository

Tests all data access methods using an in-memory SQLite database.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base
from src.models import Kline, KlineTimeframe, SymbolType
from src.repositories.kline_repository import KlineRepository


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory database for each test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def sample_klines():
    """Generate sample K-line data for testing"""
    now = datetime.now()
    return [
        Kline(
            symbol_type=SymbolType.INDEX,
            symbol_code="000001.SH",
            symbol_name="上证指数",
            timeframe=KlineTimeframe.DAY,
            trade_time="2024-01-01",
            open=3000.0,
            high=3100.0,
            low=2950.0,
            close=3050.0,
            volume=1000000.0,
            amount=5000000.0,
            created_at=now,
            updated_at=now,
        ),
        Kline(
            symbol_type=SymbolType.INDEX,
            symbol_code="000001.SH",
            symbol_name="上证指数",
            timeframe=KlineTimeframe.DAY,
            trade_time="2024-01-02",
            open=3050.0,
            high=3150.0,
            low=3000.0,
            close=3100.0,
            volume=1200000.0,
            amount=6000000.0,
            created_at=now,
            updated_at=now,
        ),
        Kline(
            symbol_type=SymbolType.INDEX,
            symbol_code="000001.SH",
            symbol_name="上证指数",
            timeframe=KlineTimeframe.DAY,
            trade_time="2024-01-03",
            open=3100.0,
            high=3200.0,
            low=3050.0,
            close=3150.0,
            volume=1500000.0,
            amount=7500000.0,
            created_at=now,
            updated_at=now,
        ),
    ]


class TestKlineRepositoryBasicOperations:
    """Test basic CRUD operations"""

    def test_save_single_kline(self, db_session):
        """Test saving a single K-line"""
        repo = KlineRepository(db_session)

        kline = Kline(
            symbol_type=SymbolType.STOCK,
            symbol_code="000001",
            symbol_name="平安银行",
            timeframe=KlineTimeframe.DAY,
            trade_time="2024-01-01",
            open=10.0,
            high=10.5,
            low=9.8,
            close=10.3,
            volume=100000.0,
            amount=1000000.0,
        )

        saved = repo.save(kline)
        repo.commit()

        assert saved.id is not None
        assert saved.symbol_code == "000001"
        assert saved.close == 10.3

    def test_find_by_id(self, db_session, sample_klines):
        """Test finding K-line by ID"""
        repo = KlineRepository(db_session)

        # Save a kline
        saved = repo.save(sample_klines[0])
        repo.commit()

        # Find by ID
        found = repo.find_by_id(saved.id)

        assert found is not None
        assert found.symbol_code == "000001.SH"
        assert found.close == 3050.0

    def test_count(self, db_session, sample_klines):
        """Test counting all K-lines"""
        repo = KlineRepository(db_session)

        for kline in sample_klines:
            repo.save(kline)
        repo.commit()

        count = repo.count()
        assert count == 3


class TestKlineRepositoryQueries:
    """Test query methods"""

    def test_find_by_symbol(self, db_session, sample_klines):
        """Test finding K-lines by symbol"""
        repo = KlineRepository(db_session)

        for kline in sample_klines:
            repo.save(kline)
        repo.commit()

        klines = repo.find_by_symbol(
            symbol_code="000001.SH",
            symbol_type=SymbolType.INDEX,
            timeframe=KlineTimeframe.DAY,
            limit=10,
        )

        assert len(klines) == 3
        # Should be in descending order (latest first)
        assert klines[0].trade_time == "2024-01-03"
        assert klines[1].trade_time == "2024-01-02"
        assert klines[2].trade_time == "2024-01-01"

    def test_find_by_symbol_with_limit(self, db_session, sample_klines):
        """Test finding K-lines with limit"""
        repo = KlineRepository(db_session)

        for kline in sample_klines:
            repo.save(kline)
        repo.commit()

        klines = repo.find_by_symbol(
            symbol_code="000001.SH",
            symbol_type=SymbolType.INDEX,
            timeframe=KlineTimeframe.DAY,
            limit=2,
        )

        assert len(klines) == 2
        assert klines[0].trade_time == "2024-01-03"
        assert klines[1].trade_time == "2024-01-02"

    def test_find_by_symbol_and_date_range(self, db_session, sample_klines):
        """Test finding K-lines by date range"""
        repo = KlineRepository(db_session)

        for kline in sample_klines:
            repo.save(kline)
        repo.commit()

        klines = repo.find_by_symbol_and_date_range(
            symbol_code="000001.SH",
            symbol_type=SymbolType.INDEX,
            timeframe=KlineTimeframe.DAY,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
        )

        assert len(klines) == 2
        # Should be in ascending order
        assert klines[0].trade_time == "2024-01-01"
        assert klines[1].trade_time == "2024-01-02"

    def test_find_latest_by_symbol(self, db_session, sample_klines):
        """Test finding latest K-line"""
        repo = KlineRepository(db_session)

        for kline in sample_klines:
            repo.save(kline)
        repo.commit()

        latest = repo.find_latest_by_symbol(
            symbol_code="000001.SH",
            symbol_type=SymbolType.INDEX,
            timeframe=KlineTimeframe.DAY,
        )

        assert latest is not None
        assert latest.trade_time == "2024-01-03"
        assert latest.close == 3150.0

    def test_find_by_symbols(self, db_session):
        """Test finding K-lines for multiple symbols"""
        repo = KlineRepository(db_session)

        # Create data for two different symbols
        symbols_data = [
            ("000001.SH", "上证指数", 3000.0),
            ("000001.SH", "上证指数", 3050.0),
            ("000300.SH", "沪深300", 4000.0),
            ("000300.SH", "沪深300", 4100.0),
        ]

        for i, (code, name, close) in enumerate(symbols_data):
            kline = Kline(
                symbol_type=SymbolType.INDEX,
                symbol_code=code,
                symbol_name=name,
                timeframe=KlineTimeframe.DAY,
                trade_time=f"2024-01-0{i+1}",
                open=close - 50,
                high=close + 50,
                low=close - 100,
                close=close,
                volume=100000.0,
                amount=1000000.0,
            )
            repo.save(kline)
        repo.commit()

        klines = repo.find_by_symbols(
            symbol_codes=["000001.SH", "000300.SH"],
            symbol_type=SymbolType.INDEX,
            timeframe=KlineTimeframe.DAY,
            limit_per_symbol=10,
        )

        assert len(klines) == 4

        # Check we have both symbols
        codes = set(k.symbol_code for k in klines)
        assert codes == {"000001.SH", "000300.SH"}

    def test_count_by_symbol(self, db_session, sample_klines):
        """Test counting K-lines for a symbol"""
        repo = KlineRepository(db_session)

        for kline in sample_klines:
            repo.save(kline)
        repo.commit()

        count = repo.count_by_symbol(
            symbol_code="000001.SH",
            symbol_type=SymbolType.INDEX,
            timeframe=KlineTimeframe.DAY,
        )

        assert count == 3

    def test_find_symbols_with_data(self, db_session):
        """Test finding symbols that have data"""
        repo = KlineRepository(db_session)

        # Create data for multiple symbols
        for code in ["000001.SH", "000300.SH", "399001.SZ"]:
            kline = Kline(
                symbol_type=SymbolType.INDEX,
                symbol_code=code,
                symbol_name=f"Index {code}",
                timeframe=KlineTimeframe.DAY,
                trade_time="2024-01-01",
                open=3000.0,
                high=3100.0,
                low=2950.0,
                close=3050.0,
                volume=100000.0,
                amount=1000000.0,
            )
            repo.save(kline)
        repo.commit()

        symbols = repo.find_symbols_with_data(
            symbol_type=SymbolType.INDEX,
            timeframe=KlineTimeframe.DAY,
        )

        assert len(symbols) == 3
        assert set(symbols) == {"000001.SH", "000300.SH", "399001.SZ"}


class TestKlineRepositoryBatchOperations:
    """Test batch operations"""

    def test_upsert_batch_insert(self, db_session, sample_klines):
        """Test batch insert"""
        repo = KlineRepository(db_session)

        count = repo.upsert_batch(sample_klines)
        repo.commit()

        assert count == 3

        # Verify data was inserted
        all_klines = repo.find_all()
        assert len(all_klines) == 3

    def test_upsert_batch_update(self, db_session, sample_klines):
        """Test batch update (upsert existing data)"""
        repo = KlineRepository(db_session)

        # Insert initial data
        repo.upsert_batch(sample_klines)
        repo.commit()

        # Modify close prices
        for kline in sample_klines:
            kline.close = kline.close + 100.0

        # Upsert again
        count = repo.upsert_batch(sample_klines)
        repo.commit()

        # Should still have 3 records (updated, not duplicated)
        all_klines = repo.find_all()
        assert len(all_klines) == 3

        # Verify prices were updated
        latest = repo.find_latest_by_symbol(
            symbol_code="000001.SH",
            symbol_type=SymbolType.INDEX,
            timeframe=KlineTimeframe.DAY,
        )
        assert latest.close == 3250.0  # 3150 + 100


class TestKlineRepositoryDelete:
    """Test delete operations"""

    def test_delete_by_symbol(self, db_session, sample_klines):
        """Test deleting all K-lines for a symbol"""
        repo = KlineRepository(db_session)

        for kline in sample_klines:
            repo.save(kline)
        repo.commit()

        # Delete all
        deleted = repo.delete_by_symbol(
            symbol_code="000001.SH",
            symbol_type=SymbolType.INDEX,
            timeframe=KlineTimeframe.DAY,
        )
        repo.commit()

        assert deleted == 3

        # Verify deletion
        count = repo.count()
        assert count == 0

    def test_delete_by_date_range(self, db_session, sample_klines):
        """Test deleting K-lines by date range"""
        repo = KlineRepository(db_session)

        for kline in sample_klines:
            repo.save(kline)
        repo.commit()

        # Delete first two days
        deleted = repo.delete_by_date_range(
            symbol_code="000001.SH",
            symbol_type=SymbolType.INDEX,
            timeframe=KlineTimeframe.DAY,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
        )
        repo.commit()

        assert deleted == 2

        # Should have 1 remaining (2024-01-03)
        remaining = repo.find_all()
        assert len(remaining) == 1
        assert remaining[0].trade_time == "2024-01-03"


class TestKlineRepositoryEdgeCases:
    """Test edge cases and error handling"""

    def test_find_by_symbol_empty_result(self, db_session):
        """Test querying non-existent symbol"""
        repo = KlineRepository(db_session)

        klines = repo.find_by_symbol(
            symbol_code="NONEXISTENT",
            symbol_type=SymbolType.STOCK,
            timeframe=KlineTimeframe.DAY,
        )

        assert klines == []

    def test_find_latest_by_symbol_no_data(self, db_session):
        """Test finding latest when no data exists"""
        repo = KlineRepository(db_session)

        latest = repo.find_latest_by_symbol(
            symbol_code="NONEXISTENT",
            symbol_type=SymbolType.STOCK,
            timeframe=KlineTimeframe.DAY,
        )

        assert latest is None

    def test_upsert_batch_empty_list(self, db_session):
        """Test upserting empty list"""
        repo = KlineRepository(db_session)

        count = repo.upsert_batch([])

        assert count == 0

    def test_count_by_symbol_no_data(self, db_session):
        """Test counting when no data exists"""
        repo = KlineRepository(db_session)

        count = repo.count_by_symbol(
            symbol_code="NONEXISTENT",
            symbol_type=SymbolType.STOCK,
            timeframe=KlineTimeframe.DAY,
        )

        assert count == 0
