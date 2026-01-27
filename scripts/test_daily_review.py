#!/usr/bin/env python3
"""
Test script for daily review system.

Simple test to verify all components work correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import SessionLocal
from src.services.daily_review_data_service import DailyReviewDataService
from src.models.kline import Kline
from sqlalchemy import desc


async def main():
    """Test daily review data collection."""
    print("Testing Daily Review System")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Find most recent trading date with data
        print("\n1. Finding most recent trading date...")
        recent_kline = db.query(Kline).filter(
            Kline.symbol_type == 'index',
            Kline.timeframe == 'DAY'
        ).order_by(desc(Kline.trade_time)).first()

        if not recent_kline:
            print("✗ No K-line data found in database")
            return 1

        # Extract date from trade_time (YYYY-MM-DD)
        trade_date = recent_kline.trade_time.replace('-', '')[:8]
        print(f"✓ Most recent trading date: {trade_date}")

        # Initialize service
        print("\n2. Initializing DailyReviewDataService...")
        service = DailyReviewDataService(db)
        print("✓ Service initialized")

        # Collect review data
        print(f"\n3. Collecting review data for {trade_date}...")
        snapshot = await service.collect_review_data(trade_date)
        print("✓ Data collection complete")

        # Display summary
        print("\n" + "=" * 60)
        print("SNAPSHOT SUMMARY")
        print("=" * 60)
        print(f"Trade Date:      {snapshot.trade_date}")
        print(f"Indices:         {len(snapshot.indices)}")
        print(f"Sectors:         {len(snapshot.sectors)}")
        print(f"Concepts:        {len(snapshot.concepts)}")
        total_samples = sum(len(stocks) for stocks in snapshot.sample_stocks.values())
        print(f"Sample Stocks:   {total_samples}")
        print(f"Market Sentiment: {snapshot.sentiment.sentiment_label} (score: {snapshot.sentiment.sentiment_score})")
        print(f"  Up/Down Ratio: {snapshot.sentiment.up_down_ratio:.2f}")
        print(f"  Limit Up:      {snapshot.sentiment.limit_up}")
        print(f"  Total Amount:  {snapshot.sentiment.total_amount / 1e12:.2f}万亿")

        # Show top indices
        print("\nMajor Indices:")
        for idx in snapshot.indices[:3]:
            print(f"  {idx.name:10s} {idx.change_pct:+6.2f}% {idx.pattern:12s} [{idx.volume_trend}]")

        # Show top sectors
        if snapshot.sectors:
            print("\nTop 3 Strong Sectors:")
            for i, sector in enumerate(snapshot.sectors[:3], 1):
                print(f"  {i}. {sector.sector_name:10s} {sector.change_pct:+6.2f}% "
                      f"流入{sector.net_inflow:6.2f}亿 [{sector.strength}]")

        # Show sample stocks
        if snapshot.sample_stocks:
            print("\nSample Stocks:")
            for sector_name, stocks in list(snapshot.sample_stocks.items())[:2]:
                print(f"  {sector_name}:")
                for stock in stocks[:3]:
                    print(f"    - {stock.name:10s} ({stock.role}) {stock.change_pct:+6.2f}%")

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

        print("\n✨ You can now generate full reviews with:")
        print(f"   python scripts/generate_snapshot.py --date {trade_date}")
        print(f"   python scripts/generate_review.py --date {trade_date}")

        return 0

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
