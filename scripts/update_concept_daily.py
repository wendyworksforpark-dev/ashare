#!/usr/bin/env python3
"""
获取同花顺概念板块每日数据并保存到数据库
包括涨跌幅、成交量、领涨股等
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import tushare as ts
from src.config import get_settings
from src.database import SessionLocal
from src.models import ConceptDaily
from sqlalchemy import select


def main():
    settings = get_settings()
    pro = ts.pro_api(settings.tushare_token)
    session = SessionLocal()
    
    today = datetime.now().strftime('%Y%m%d')
    
    print("=" * 60, flush=True)
    print(f"  同花顺概念板块每日数据更新", flush=True)
    print(f"  日期: {today}", flush=True)
    print("=" * 60, flush=True)
    
    try:
        # 1. 获取所有概念板块列表
        print("\n1. 获取概念板块列表...", flush=True)
        concepts = pro.ths_index(exchange='A', type='N')
        print(f"   共 {len(concepts)} 个概念板块", flush=True)
        
        # 2. 获取每个概念的今日行情
        print("\n2. 获取概念行情数据...", flush=True)
        
        new_count = 0
        update_count = 0
        error_count = 0
        
        for idx, row in concepts.iterrows():
            concept_code = row['ts_code']
            concept_name = row['name']
            
            try:
                # 获取概念指数行情
                quote = pro.ths_daily(
                    ts_code=concept_code,
                    start_date=today,
                    end_date=today
                )
                
                if quote is not None and not quote.empty:
                    q = quote.iloc[0]
                    
                    # 检查是否已存在
                    existing = session.execute(
                        select(ConceptDaily).where(
                            ConceptDaily.trade_date == today,
                            ConceptDaily.code == concept_code
                        )
                    ).scalar_one_or_none()
                    
                    if existing:
                        # 更新
                        existing.close = q.get('close', 0)
                        existing.pct_change = q.get('pct_change', 0)
                        existing.volume = q.get('vol', 0)
                        existing.amount = q.get('amount', 0)
                        existing.updated_at = datetime.now(timezone.utc)
                        update_count += 1
                    else:
                        # 新增
                        record = ConceptDaily(
                            trade_date=today,
                            code=concept_code,
                            name=concept_name,
                            close=q.get('close', 0),
                            pct_change=q.get('pct_change', 0),
                            volume=q.get('vol', 0),
                            amount=q.get('amount', 0),
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        session.add(record)
                        new_count += 1
                
                if (idx + 1) % 50 == 0:
                    print(f"   [{idx + 1}/{len(concepts)}] 已处理", flush=True)
                    session.commit()
                
                # TuShare 限流
                time.sleep(0.12)
                
            except Exception as e:
                error_count += 1
                if (idx + 1) % 100 == 0:
                    print(f"   [{idx + 1}] {concept_name}: 跳过 ({e})", flush=True)
                continue
        
        session.commit()
        
        print("\n" + "=" * 60, flush=True)
        print("  ✅ 完成！", flush=True)
        print("=" * 60, flush=True)
        print(f"  新增: {new_count}", flush=True)
        print(f"  更新: {update_count}", flush=True)
        print(f"  失败: {error_count}", flush=True)
        
        # 显示涨幅前10
        print("\n📈 今日涨幅前10概念:", flush=True)
        top10 = session.execute(
            select(ConceptDaily)
            .where(ConceptDaily.trade_date == today)
            .order_by(ConceptDaily.pct_change.desc())
            .limit(10)
        ).scalars().all()
        
        for i, c in enumerate(top10, 1):
            print(f"   {i}. {c.name}: {c.pct_change:+.2f}%", flush=True)
        
        return 0
        
    except Exception as e:
        print(f"更新失败: {e}", flush=True)
        session.rollback()
        return 1
    finally:
        session.close()


if __name__ == '__main__':
    sys.exit(main())
