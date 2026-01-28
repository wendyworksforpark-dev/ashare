#!/usr/bin/env python3
"""
Test script for fundamental analysis.

Usage:
    python scripts/test_fundamental_analysis.py
    python scripts/test_fundamental_analysis.py --ticker 300077
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import SessionLocal
from src.utils.fundamental_analyzer import FundamentalAnalyzer


def test_single_stock(ticker: str, trade_date: str = "20260127"):
    """Test analysis for a single stock."""
    print(f"\n{'='*60}")
    print(f"Testing fundamental analysis for {ticker}")
    print(f"Trade date: {trade_date}")
    print(f"{'='*60}\n")

    session = SessionLocal()
    try:
        analyzer = FundamentalAnalyzer(session)

        # 1. Test 52-week high/low
        print("1. 52-week High/Low:")
        high, low = analyzer.get_52w_high_low(ticker, trade_date)
        print(f"   52W High: {high:.2f}")
        print(f"   52W Low:  {low:.2f}")

        # 2. Test financial indicators
        print("\n2. Financial Indicators (latest 4 quarters):")
        indicators = analyzer.get_financial_indicators(ticker, periods=4)
        if indicators:
            for i, ind in enumerate(indicators[:4]):
                print(f"   [{ind['end_date']}] ROE: {ind.get('roe', 'N/A')}%, "
                      f"净利润YoY: {ind.get('netprofit_yoy', 'N/A')}%, "
                      f"毛利率: {ind.get('gross_margin', 'N/A')}%")
        else:
            print("   No financial data available")

        # 3. Test divergence analysis
        print("\n3. Price-Fundamental Divergence Analysis:")
        # Get current price from DB or use dummy
        from src.models import Kline
        formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
        kline = session.query(Kline).filter(
            Kline.symbol_code == ticker,
            Kline.trade_time == formatted_date,
            Kline.timeframe == 'DAY'
        ).first()

        if kline:
            current_price = kline.close
            divergence = analyzer.analyze_price_fundamental_divergence(
                ticker=ticker,
                current_price=current_price,
                price_change_pct=10.0,  # Assume 10% recent gain
                trade_date=trade_date
            )
            print(f"   Current Price: {current_price:.2f}")
            print(f"   vs 52W High: {divergence.get('price_vs_52w_high', 'N/A')}%")
            print(f"   Profit Trend: {divergence.get('profit_trend', 'N/A')}")
            print(f"   Divergence: {divergence.get('divergence_level', 'N/A')}")
            if divergence.get('warning'):
                print(f"   ⚠️ Warning: {divergence['warning']}")
        else:
            print(f"   No price data found for {ticker} on {trade_date}")

        print("\n" + "="*60)
        print("Test completed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def test_batch_analysis(trade_date: str = "20260127"):
    """Test batch analysis with sample stocks."""
    print(f"\n{'='*60}")
    print(f"Testing batch fundamental analysis")
    print(f"Trade date: {trade_date}")
    print(f"{'='*60}\n")

    # Sample stocks to analyze
    sample_stocks = [
        {"ticker": "300077", "name": "国民技术", "current_price": 24.69, "change_pct": 12.38, "industry": "半导体", "sector": "半导体"},
        {"ticker": "600183", "name": "生益科技", "current_price": 28.50, "change_pct": 3.2, "industry": "元件", "sector": "PCB"},
        {"ticker": "000028", "name": "国药一致", "current_price": 38.20, "change_pct": 2.1, "industry": "医药商业", "sector": "医药"},
        {"ticker": "002916", "name": "深南电路", "current_price": 115.80, "change_pct": 4.5, "industry": "元件", "sector": "PCB"},
    ]

    session = SessionLocal()
    try:
        analyzer = FundamentalAnalyzer(session)
        results = analyzer.batch_analyze_fundamentals(sample_stocks, trade_date)

        print(f"Analyzed {len(sample_stocks)} stocks\n")

        # Divergence alerts
        print("📊 Divergence Alerts:")
        if results['divergence_alerts']:
            for alert in results['divergence_alerts']:
                print(f"   ⚠️ {alert['ticker']} ({alert['name']}): {alert['warning']}")
                print(f"      Level: {alert['divergence_level']}")
        else:
            print("   No divergence alerts")

        # Quality stocks
        print("\n✅ Quality Stocks (Top 20%):")
        if results['quality_stocks']:
            for stock in results['quality_stocks']:
                print(f"   {stock['ticker']} ({stock['name']}): "
                      f"ROE={stock['roe']:.1f}%, Rank #{stock['rank']}, "
                      f"Percentile={stock['percentile']:.0f}%")
        else:
            print("   No top 20% stocks found")

        # Risk stocks
        print("\n⚠️ Risk Stocks:")
        if results['risk_stocks']:
            for stock in results['risk_stocks']:
                print(f"   {stock['ticker']} ({stock['name']}): {stock['warning']}")
        else:
            print("   No high-risk stocks found")

        print("\n" + "="*60)
        print("Batch test completed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description='Test fundamental analysis')
    parser.add_argument('--ticker', type=str, help='Single ticker to analyze')
    parser.add_argument('--date', type=str, default='20260127', help='Trade date YYYYMMDD')
    parser.add_argument('--batch', action='store_true', help='Run batch analysis')
    args = parser.parse_args()

    if args.ticker:
        test_single_stock(args.ticker, args.date)
    elif args.batch:
        test_batch_analysis(args.date)
    else:
        # Default: run both tests
        test_batch_analysis(args.date)


if __name__ == "__main__":
    main()
