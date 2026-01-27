#!/usr/bin/env python3
"""
Generate test K-line data for daily review testing.

This creates synthetic but realistic K-line data for indices and stocks
based on the available IndustryDaily data.
"""

import random
from datetime import datetime
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import SessionLocal
from src.models.kline import Kline
from src.models.board import IndustryDaily, BoardMapping
from src.models.symbol import SymbolMetadata


def generate_test_data(trade_date: str = "20260109"):
    """Generate test K-line data for a given date."""

    db = SessionLocal()

    try:
        # Convert to YYYY-MM-DD format
        formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"

        print(f"Generating test K-line data for {formatted_date}")
        print("=" * 60)

        # 1. Generate index K-lines
        print("\n1. Generating index K-lines...")
        indices = [
            ("000001.SH", "上证指数", 3200.0),
            ("399001.SZ", "深证成指", 10500.0),
            ("399006.SZ", "创业板指", 2100.0),
            ("000688.SH", "科创50", 1000.0),
            ("899050.BJ", "北证50", 800.0),
        ]

        for code, name, base_price in indices:
            # Generate realistic price movement
            change_pct = random.uniform(-2, 2)
            close = base_price * (1 + change_pct / 100)
            open_price = base_price * (1 + random.uniform(-1, 1) / 100)
            high = max(open_price, close) * (1 + random.uniform(0, 0.5) / 100)
            low = min(open_price, close) * (1 - random.uniform(0, 0.5) / 100)
            volume = random.uniform(200e9, 400e9)  # 2000-4000亿
            amount = volume * (high + low) / 2

            kline = Kline(
                symbol_type='index',
                symbol_code=code,
                symbol_name=name,
                timeframe='DAY',
                trade_time=formatted_date,
                open=open_price,
                close=close,
                high=high,
                low=low,
                volume=volume,
                amount=amount
            )
            db.add(kline)
            print(f"  ✓ {name:12s} {code:12s} {change_pct:+6.2f}%")

        # 2. Get industries and generate stock K-lines
        print("\n2. Generating stock K-lines from industry data...")

        industries = db.query(IndustryDaily).filter(
            IndustryDaily.trade_date == trade_date
        ).all()

        if not industries:
            print(f"  ⚠️  No industry data found for {trade_date}")
            print("  Using fallback date...")
            industries = db.query(IndustryDaily).order_by(
                IndustryDaily.trade_date.desc()
            ).limit(90).all()
            if industries:
                trade_date = industries[0].trade_date
                formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
                print(f"  Using date: {trade_date}")

        stock_count = 0
        for industry in industries[:30]:  # Top 30 industries for testing
            # Get constituents from board mapping
            board = db.query(BoardMapping).filter(
                BoardMapping.board_name == industry.industry,
                BoardMapping.board_type == 'industry'
            ).first()

            if not board or not board.constituents:
                # Generate fake constituents
                num_stocks = random.randint(10, 40)
                constituents = [f"{600000 + i + hash(industry.industry) % 1000}.SH"
                              for i in range(num_stocks)]
            else:
                constituents = board.constituents[:20]  # Limit to 20 per industry

            # Generate K-lines for each constituent
            for ticker in constituents:
                # Use industry change as base, add individual variation
                base_change = industry.pct_change
                individual_change = base_change + random.uniform(-3, 3)

                base_price = random.uniform(10, 100)
                close = base_price * (1 + individual_change / 100)
                open_price = base_price * (1 + random.uniform(-2, 2) / 100)
                high = max(open_price, close) * (1 + random.uniform(0, 2) / 100)
                low = min(open_price, close) * (1 - random.uniform(0, 2) / 100)
                volume = random.uniform(1e7, 1e8)  # 1000万-1亿
                amount = volume * (high + low) / 2

                kline = Kline(
                    symbol_type='stock',
                    symbol_code=ticker,
                    symbol_name=f"股票{ticker[:6]}",
                    timeframe='DAY',
                    trade_time=formatted_date,
                    open=open_price,
                    close=close,
                    high=high,
                    low=low,
                    volume=volume,
                    amount=amount
                )
                db.add(kline)
                stock_count += 1

        print(f"  ✓ Generated {stock_count} stock K-lines")

        # 3. Generate previous day data for change calculation
        print("\n3. Generating previous day data...")
        from datetime import timedelta
        prev_date = datetime.strptime(trade_date, "%Y%m%d") - timedelta(days=1)
        prev_formatted = prev_date.strftime("%Y-%m-%d")

        # Copy and modify current day data
        current_klines = db.query(Kline).filter(
            Kline.trade_time == formatted_date
        ).all()

        for kline in current_klines:
            # Previous day was slightly different
            prev_close = kline.open * (1 + random.uniform(-1, 1) / 100)

            prev_kline = Kline(
                symbol_type=kline.symbol_type,
                symbol_code=kline.symbol_code,
                symbol_name=kline.symbol_name,
                timeframe='DAY',
                trade_time=prev_formatted,
                open=prev_close * (1 + random.uniform(-0.5, 0.5) / 100),
                close=prev_close,
                high=prev_close * (1 + random.uniform(0, 1) / 100),
                low=prev_close * (1 - random.uniform(0, 1) / 100),
                volume=kline.volume * random.uniform(0.8, 1.2),
                amount=kline.amount * random.uniform(0.8, 1.2)
            )
            db.add(prev_kline)

        print(f"  ✓ Generated previous day data for {prev_formatted}")

        # Commit all changes
        db.commit()

        print("\n" + "=" * 60)
        print("✅ Test data generation complete!")
        print("=" * 60)

        # Summary
        total_klines = db.query(Kline).filter(
            Kline.trade_time == formatted_date
        ).count()
        print(f"\nGenerated K-lines for {formatted_date}:")
        print(f"  Indices: {len(indices)}")
        print(f"  Stocks: {stock_count}")
        print(f"  Total: {total_klines}")
        print(f"\nYou can now run:")
        print(f"  python scripts/test_daily_review.py")
        print(f"  python scripts/generate_snapshot.py --date {trade_date}")

        return trade_date

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        db.close()


if __name__ == "__main__":
    trade_date = sys.argv[1] if len(sys.argv) > 1 else "20260109"
    generate_test_data(trade_date)
