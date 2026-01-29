#!/usr/bin/env python3
"""
获取同花顺概念板块每日数据并保存到数据库
包括涨跌幅、成交量、资金流向、涨跌家数等

用法：
  python scripts/update_concept_daily.py          # 正常运行
  python scripts/update_concept_daily.py --bg     # 后台运行(nohup)
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import time

# 后台模式检测
if '--bg' in sys.argv:
    # 重新以 nohup 方式启动自己
    import subprocess
    script_path = Path(__file__).resolve()
    log_path = script_path.parent.parent / 'logs' / 'concept_daily.log'
    log_path.parent.mkdir(exist_ok=True)
    
    cmd = f'nohup python {script_path} > {log_path} 2>&1 &'
    subprocess.Popen(cmd, shell=True)
    print(f"后台任务已启动，日志: {log_path}")
    sys.exit(0)

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import akshare as ak
import tushare as ts
from src.config import get_settings
from src.database import SessionLocal
from src.models import ConceptDaily
from sqlalchemy import select


def parse_pct(s: str) -> float:
    """解析百分比字符串"""
    try:
        return float(str(s).replace('%', '').strip())
    except:
        return 0.0


def parse_rank(s: str) -> tuple[int, int]:
    """解析排名字符串 '3/390' -> (3, 390)"""
    try:
        parts = str(s).split('/')
        return int(parts[0].strip()), int(parts[1].strip())
    except:
        return 0, 0


def parse_up_down(s: str) -> tuple[int, int]:
    """解析涨跌家数 '120/22' -> (120, 22)"""
    try:
        parts = str(s).split('/')
        return int(parts[0].strip()), int(parts[1].strip())
    except:
        return 0, 0


def main():
    settings = get_settings()
    pro = ts.pro_api(settings.tushare_token)
    session = SessionLocal()
    
    today = datetime.now().strftime('%Y%m%d')
    
    print("=" * 60, flush=True)
    print(f"  同花顺概念板块每日数据更新 (含资金流向)", flush=True)
    print(f"  日期: {today}", flush=True)
    print(f"  开始时间: {datetime.now().strftime('%H:%M:%S')}", flush=True)
    print("=" * 60, flush=True)
    
    try:
        # 1. 获取所有概念板块列表 (TuShare)
        print("\n1. 获取概念板块列表 (TuShare)...", flush=True)
        concepts = pro.ths_index(exchange='A', type='N')
        code_to_name = {row['ts_code']: row['name'] for _, row in concepts.iterrows()}
        print(f"   共 {len(concepts)} 个概念板块", flush=True)
        
        # 2. 获取同花顺概念列表 (AKShare)
        print("\n2. 获取同花顺概念列表 (AKShare)...", flush=True)
        ths_concepts = ak.stock_board_concept_name_ths()
        print(f"   共 {len(ths_concepts)} 个概念板块", flush=True)
        
        # 3. 遍历获取详情
        print("\n3. 获取概念详细数据...", flush=True)
        
        new_count = 0
        update_count = 0
        error_count = 0
        
        total = len(ths_concepts)
        start_time = time.time()
        
        for idx, row in ths_concepts.iterrows():
            concept_name = row['name']
            concept_code = row.get('code', '')
            
            try:
                # 获取概念详情
                info = ak.stock_board_concept_info_ths(symbol=concept_name)
                
                if info is not None and not info.empty:
                    # 解析数据
                    data = {r['项目']: r['值'] for _, r in info.iterrows()}
                    
                    pct_change = parse_pct(data.get('板块涨幅', '0%'))
                    rank, total_boards = parse_rank(data.get('涨幅排名', '0/0'))
                    up_count, down_count = parse_up_down(data.get('涨跌家数', '0/0'))
                    
                    try:
                        net_inflow = float(data.get('资金净流入(亿)', 0))
                    except:
                        net_inflow = 0.0
                    
                    try:
                        amount = float(data.get('成交额(亿)', 0))
                    except:
                        amount = 0.0
                    
                    try:
                        volume = float(data.get('成交量(万手)', 0))
                    except:
                        volume = 0.0
                    
                    try:
                        open_price = float(data.get('今开', 0))
                        high_price = float(data.get('最高', 0))
                        low_price = float(data.get('最低', 0))
                        prev_close = float(data.get('昨收', 0))
                        close_price = prev_close * (1 + pct_change / 100) if prev_close else 0
                    except:
                        open_price = high_price = low_price = close_price = 0.0
                    
                    # 查找 TuShare 对应的 ts_code
                    ts_code = None
                    for code, name in code_to_name.items():
                        if name == concept_name:
                            ts_code = code
                            break
                    
                    if not ts_code:
                        ts_code = f"THS_{concept_code}"
                    
                    # 检查是否已存在
                    existing = session.execute(
                        select(ConceptDaily).where(
                            ConceptDaily.trade_date == today,
                            ConceptDaily.name == concept_name
                        )
                    ).scalar_one_or_none()
                    
                    if existing:
                        existing.close = close_price
                        existing.pct_change = pct_change
                        existing.volume = volume
                        existing.amount = amount
                        existing.up_count = up_count
                        existing.down_count = down_count
                        existing.net_inflow = net_inflow
                        existing.rank = rank
                        existing.total_boards = total_boards
                        existing.open = open_price
                        existing.high = high_price
                        existing.low = low_price
                        existing.updated_at = datetime.now(timezone.utc)
                        update_count += 1
                    else:
                        record = ConceptDaily(
                            trade_date=today,
                            code=ts_code,
                            name=concept_name,
                            close=close_price,
                            pct_change=pct_change,
                            volume=volume,
                            amount=amount,
                            up_count=up_count,
                            down_count=down_count,
                            net_inflow=net_inflow,
                            rank=rank,
                            total_boards=total_boards,
                            open=open_price,
                            high=high_price,
                            low=low_price,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        session.add(record)
                        new_count += 1
                
                if (idx + 1) % 50 == 0:
                    elapsed = time.time() - start_time
                    eta = elapsed / (idx + 1) * (total - idx - 1)
                    print(f"   [{idx + 1}/{total}] 已处理, 耗时 {elapsed:.0f}s, 预计剩余 {eta:.0f}s", flush=True)
                    session.commit()
                
                # 限流
                time.sleep(0.3)
                
            except Exception as e:
                error_count += 1
                continue
        
        session.commit()
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 60, flush=True)
        print("  ✅ 完成！", flush=True)
        print("=" * 60, flush=True)
        print(f"  新增: {new_count}", flush=True)
        print(f"  更新: {update_count}", flush=True)
        print(f"  失败: {error_count}", flush=True)
        print(f"  耗时: {elapsed:.0f}秒", flush=True)
        
        # 显示涨幅前10
        print("\n📈 今日涨幅前10概念:", flush=True)
        top10 = session.execute(
            select(ConceptDaily)
            .where(ConceptDaily.trade_date == today)
            .order_by(ConceptDaily.pct_change.desc())
            .limit(10)
        ).scalars().all()
        
        for i, c in enumerate(top10, 1):
            inflow_str = f", 净流入{c.net_inflow:.1f}亿" if c.net_inflow else ""
            print(f"   {i}. {c.name}: {c.pct_change:+.2f}% (↑{c.up_count}/↓{c.down_count}{inflow_str})", flush=True)
        
        # 显示资金流入前10
        print("\n💰 今日资金净流入前10:", flush=True)
        top_inflow = session.execute(
            select(ConceptDaily)
            .where(ConceptDaily.trade_date == today, ConceptDaily.net_inflow != None)
            .order_by(ConceptDaily.net_inflow.desc())
            .limit(10)
        ).scalars().all()
        
        for i, c in enumerate(top_inflow, 1):
            print(f"   {i}. {c.name}: {c.net_inflow:+.2f}亿 ({c.pct_change:+.2f}%)", flush=True)
        
        return 0
        
    except Exception as e:
        print(f"更新失败: {e}", flush=True)
        import traceback
        traceback.print_exc()
        session.rollback()
        return 1
    finally:
        session.close()


if __name__ == '__main__':
    sys.exit(main())
