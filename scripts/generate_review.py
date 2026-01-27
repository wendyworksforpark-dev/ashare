#!/usr/bin/env python3
"""
AI Daily Review Generator

Generates professional daily market review narrative using Claude API
based on structured data snapshot.

Usage:
    python generate_review.py                     # Today's review
    python generate_review.py --date 20250126    # Specific date
    python generate_review.py --snapshot custom.json  # Custom snapshot
"""

import asyncio
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate AI daily market review'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Trade date in YYYYMMDD format (default: today)'
    )
    parser.add_argument(
        '--snapshot',
        type=str,
        help='Snapshot file path (default: auto-locate from date)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: docs/daily_review/reviews/{date}.md)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='claude-sonnet-4-5-20250929',
        help='Claude model to use'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.3,
        help='Temperature for generation (0-1, default: 0.3 for stability)'
    )
    return parser.parse_args()


def load_prompt_template() -> str:
    """Load the prompt template."""
    template_path = project_root / "docs" / "daily_review" / "prompt_template.md"
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        # Return default template if file doesn't exist
        return """# 股市每日复盘任务

你是一位资深A股交易员,需要基于以下结构化数据生成今日的复盘报告。

## 要求:
1. **详细版复盘(1000+字)**,深度分析市场动态
2. 基于数据事实,不要臆测
3. 提及具体指数、板块、个股代码(带$符号)
4. 结合K线形态、资金流向、成交量做判断
5. 包含历史对比和持续性判断
6. 给出明日交易策略建议

## 数据快照

{SNAPSHOT_DATA}

## 生成复盘报告

格式要求:
1. **大盘综述** (200字): 主要指数走势、成交量、K线形态
2. **板块轮动分析** (400字): 资金流向、强势/弱势板块、轮动特征
3. **重点个股解读** (250字): 龙头股、补涨股、高位核心的表现
4. **市场情绪** (100字): 涨跌家数、涨停板、市场情绪判断
5. **明日交易策略** (50字): 明确的操作建议

总计1000字左右,专业、深度、精炼。"""


async def generate_review_with_claude(snapshot_data: dict,
                                     prompt_template: str,
                                     model: str,
                                     temperature: float) -> str:
    """
    Generate review using Claude API.

    Args:
        snapshot_data: Structured snapshot data
        prompt_template: Prompt template with {SNAPSHOT_DATA} placeholder
        model: Claude model name
        temperature: Generation temperature

    Returns:
        Generated review text
    """
    if not HAS_ANTHROPIC:
        raise ImportError(
            "anthropic package not installed. "
            "Install with: pip install anthropic"
        )

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Set it with: export ANTHROPIC_API_KEY=your-key"
        )

    # Format snapshot data as JSON string
    snapshot_json = json.dumps(snapshot_data, ensure_ascii=False, indent=2)

    # Build prompt
    prompt = prompt_template.replace("{SNAPSHOT_DATA}", snapshot_json)

    # Initialize client
    client = Anthropic(api_key=api_key)

    # Call API
    print("Calling Claude API...")
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=temperature,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Extract text
    review_text = message.content[0].text

    return review_text


async def main():
    """Main execution function."""
    args = parse_args()

    # Determine trade date
    trade_date = args.date or datetime.now().strftime("%Y%m%d")

    # Locate snapshot file
    if args.snapshot:
        snapshot_path = Path(args.snapshot)
    else:
        snapshot_path = project_root / "docs" / "daily_review" / "snapshots" / f"{trade_date}.json"

    if not snapshot_path.exists():
        print(f"✗ Snapshot not found: {snapshot_path}")
        print(f"\nGenerate snapshot first:")
        print(f"  python scripts/generate_snapshot.py --date {trade_date}")
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        review_dir = project_root / "docs" / "daily_review" / "reviews"
        review_dir.mkdir(parents=True, exist_ok=True)
        output_path = review_dir / f"{trade_date}.md"

    print(f"Generating daily review for {trade_date}...")
    print(f"Snapshot: {snapshot_path}")
    print(f"Output:   {output_path}")
    print(f"Model:    {args.model}")
    print(f"Temp:     {args.temperature}")
    print("-" * 60)

    try:
        # Load snapshot
        print("Loading snapshot...")
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)
        print("✓ Snapshot loaded")

        # Load prompt template
        print("Loading prompt template...")
        prompt_template = load_prompt_template()
        print("✓ Template loaded")

        # Generate review
        review_text = await generate_review_with_claude(
            snapshot_data,
            prompt_template,
            args.model,
            args.temperature
        )
        print("✓ Review generated")

        # Add metadata header
        header = f"""---
trade_date: {trade_date}
generated_at: {datetime.now().isoformat()}
model: {args.model}
---

"""
        full_content = header + review_text

        # Save review
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        print(f"✓ Review saved: {output_path}")

        # Print preview
        print("\n" + "=" * 60)
        print("REVIEW PREVIEW")
        print("=" * 60)
        preview_lines = review_text.split('\n')[:20]
        print('\n'.join(preview_lines))
        if len(review_text.split('\n')) > 20:
            print("\n... (truncated)")
        print("=" * 60)

        print(f"\nWord count: ~{len(review_text)} characters")
        print(f"\nFull review: {output_path}")

        return 0

    except Exception as e:
        print(f"\n✗ Error generating review: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
