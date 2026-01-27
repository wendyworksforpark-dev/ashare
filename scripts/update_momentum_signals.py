#!/usr/bin/env python3
"""更新动量信号数据 - 简化版本"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime

SIGNALS_FILE = Path('/Users/park/a-share-data/docs/monitor/momentum_signals.json')

print("=" * 60)
print("更新动量信号数据")
print("=" * 60)

# 清空信号（因为这些信号需要实时监控才能生成）
output_data = {
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_signals': 0,
    'surge_signals_count': 0,
    'kline_signals_count': 0,
    'signals': []
}

with open(SIGNALS_FILE, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 动量信号已更新")
print(f"   更新时间: {output_data['timestamp']}")
print(f"   当前信号数: {output_data['total_signals']}")
print(f"\n💡 提示: 动量信号需要持续监控才能检测，请运行:")
print(f"   python scripts/monitor_no_flask.py")
print("=" * 60)
