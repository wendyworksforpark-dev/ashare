#!/usr/bin/env python3
"""
Daily Review Data Snapshot Generator

Collects and structures all data needed for daily market review.
This script should be run after market close (15:30+).

Usage:
    python generate_snapshot.py                    # Today's data
    python generate_snapshot.py --date 20250126   # Specific date
    python generate_snapshot.py --output custom.json  # Custom output
"""

import asyncio
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.services.daily_review_data_service import DailyReviewDataService


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate daily review data snapshot'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Trade date in YYYYMMDD format (default: today)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: docs/daily_review/snapshots/{date}.json)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing snapshot'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run validation checks on generated snapshot'
    )
    return parser.parse_args()


async def main():
    """Main execution function."""
    args = parse_args()

    # Determine trade date
    trade_date = args.date or datetime.now().strftime("%Y%m%d")

    # Determine output path
    if args.output:
        snapshot_path = Path(args.output)
    else:
        snapshot_dir = project_root / "docs" / "daily_review" / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / f"{trade_date}.json"

    # Check if already exists
    if snapshot_path.exists() and not args.force:
        print(f"✓ Snapshot already exists: {snapshot_path}")
        print("Use --force to regenerate")
        return 0

    print(f"Generating daily review snapshot for {trade_date}...")
    print(f"Output: {snapshot_path}")
    print("-" * 60)

    db = SessionLocal()
    try:
        # Initialize service
        data_service = DailyReviewDataService(db)

        # Collect data
        print("Collecting data...")
        snapshot = await data_service.collect_review_data(trade_date)
        print("✓ Data collection complete")

        # Validate if requested
        if args.validate:
            print("\nValidating snapshot quality...")
            from src.utils.market_sentiment_analyzer import validate_snapshot_quality
            warnings = validate_snapshot_quality(snapshot)
            if warnings:
                print("⚠️  Validation warnings:")
                for warning in warnings:
                    print(f"  - {warning}")
            else:
                print("✓ Validation passed")

        # Save to JSON
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(
                snapshot.model_dump(),
                f,
                ensure_ascii=False,
                indent=2
            )
        print(f"✓ Snapshot saved: {snapshot_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("SNAPSHOT SUMMARY")
        print("=" * 60)
        print(f"Trade Date:      {snapshot.trade_date}")
        print(f"Indices:         {len(snapshot.indices)}")
        print(f"Sectors:         {len(snapshot.sectors)}")
        print(f"Concepts:        {len(snapshot.concepts)}")
        total_samples = sum(len(stocks) for stocks in snapshot.sample_stocks.values())
        print(f"Sample Stocks:   {total_samples}")
        print(f"Market Sentiment: {snapshot.sentiment.sentiment_label}")
        print(f"  Up/Down Ratio: {snapshot.sentiment.up_down_ratio:.2f}")
        print(f"  Limit Up:      {snapshot.sentiment.limit_up}")
        print(f"  Total Amount:  {snapshot.sentiment.total_amount / 1e12:.2f}万亿")
        print("=" * 60)

        # Show top sectors
        print("\nTop 5 Strong Sectors:")
        top_sectors = sorted(snapshot.sectors, key=lambda x: x.net_inflow, reverse=True)[:5]
        for i, sector in enumerate(top_sectors, 1):
            print(f"  {i}. {sector.sector_name:10s} +{sector.change_pct:5.2f}% "
                  f"流入{sector.net_inflow:6.2f}亿 [{sector.strength}]")

        print("\nTop 5 Weak Sectors:")
        weak_sectors = sorted(snapshot.sectors, key=lambda x: x.change_pct)[:5]
        for i, sector in enumerate(weak_sectors, 1):
            print(f"  {i}. {sector.sector_name:10s} {sector.change_pct:6.2f}% "
                  f"流出{abs(sector.net_inflow):6.2f}亿 [{sector.strength}]")

        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print("1. Generate AI review:")
        print(f"   python scripts/generate_review.py --date {trade_date}")
        print("\n2. Or use Claude Code CLI manually:")
        print(f"   read {snapshot_path}")
        print("   read docs/daily_review/prompt_template.md")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n✗ Error generating snapshot: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
