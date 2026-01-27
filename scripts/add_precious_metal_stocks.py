#!/usr/bin/env python3
"""添加贵金属赛道股票到自选列表"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.batch_add_to_watchlist import add_stocks_to_watchlist, print_results
from scripts.update_watchlist_category import update_category


# 贵金属概念股列表（从截图整理）
PRECIOUS_METAL_STOCKS = [
    ("300139", "晓程科技", "黄金"),
    ("002155", "湖南黄金", "黄金"),
    ("002237", "恒邦股份", "黄金"),
    ("001337", "四川黄金", "黄金"),
    ("002716", "湖南白银", "白银"),
    ("000506", "招金黄金", "黄金"),
    ("600489", "中金黄金", "黄金"),
    ("601069", "西部黄金", "黄金"),
    ("600547", "山东黄金", "黄金"),
    ("000975", "山金国际", "黄金"),
    ("600988", "赤峰黄金", "黄金"),
]


def main():
    """主函数：检查并添加贵金属概念股"""
    print("\n" + "=" * 60)
    print("贵金属赛道股票管理")
    print("=" * 60)

    # 步骤1: 添加股票到自选（跳过已存在的）
    print("\n📝 步骤 1: 添加股票到自选列表...")
    added, skipped, failed = add_stocks_to_watchlist(
        PRECIOUS_METAL_STOCKS,
        simulate_purchase=True,  # 模拟买入（记录价格）
        category="贵金属"
    )

    # 步骤2: 更新已存在但分类不是"贵金属"的股票
    print("\n📝 步骤 2: 更新分类为'贵金属'...")
    all_tickers = [ticker for ticker, _, _ in PRECIOUS_METAL_STOCKS]
    updated, not_found = update_category(all_tickers, "贵金属")

    # 打印结果
    print_results("添加贵金属概念股 - 结果", added, skipped, failed)

    if updated:
        print(f"\n✅ 更新分类 {len(updated)} 只股票 → 贵金属")
        for ticker in updated:
            print(f"   {ticker}")

    print("\n" + "=" * 60)
    print(f"📊 最终统计:")
    print(f"   新添加: {len(added)}")
    print(f"   已存在（跳过）: {len(skipped)}")
    print(f"   更新分类: {len(updated)}")
    print(f"   失败: {len(failed)}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
