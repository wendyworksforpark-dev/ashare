#!/usr/bin/env python3
"""
更新股票的概念板块数据
从TuShare获取同花顺概念板块成分股，然后反向构建映射
"""
import sys
from pathlib import Path
import time
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import tushare as ts
from src.config import get_settings
from src.database import SessionLocal
from src.models import SymbolMetadata, Watchlist


def build_stock_concept_map(pro, watchlist_tickers: set[str]) -> dict[str, list[str]]:
    """
    构建股票 -> 概念列表的映射
    
    Args:
        pro: TuShare pro API
        watchlist_tickers: 需要关注的股票代码集合 (如 {'000001', '600519'})
    
    Returns:
        {ticker: [concept1, concept2, ...]}
    """
    stock_concepts = defaultdict(list)
    
    # 1. 获取所有概念板块 (type='N' 表示概念指数)
    print("获取同花顺概念列表...", flush=True)
    concepts = pro.ths_index(exchange='A', type='N')
    print(f"共 {len(concepts)} 个概念板块", flush=True)
    
    # 2. 遍历每个概念，获取成分股
    print("\n遍历概念板块获取成分股...", flush=True)
    total = len(concepts)
    
    for idx, row in concepts.iterrows():
        concept_code = row['ts_code']
        concept_name = row['name']
        
        try:
            # 获取概念成分股
            members = pro.ths_member(ts_code=concept_code)
            
            if members is not None and not members.empty:
                for _, member in members.iterrows():
                    # con_code 格式如 000001.SZ，需要提取纯代码
                    ticker = member['con_code'].split('.')[0]
                    if ticker in watchlist_tickers:
                        stock_concepts[ticker].append(concept_name)
            
            if (idx + 1) % 50 == 0:
                print(f"  [{idx + 1}/{total}] 已处理 {idx + 1} 个概念", flush=True)
            
            # TuShare API 限流
            time.sleep(0.15)
            
        except Exception as e:
            if (idx + 1) % 100 == 0:
                print(f"  [{idx + 1}] {concept_name}: 跳过 ({e})", flush=True)
            continue
    
    return dict(stock_concepts)


def update_all_concepts():
    """更新所有自选股的概念数据"""
    settings = get_settings()
    pro = ts.pro_api(settings.tushare_token)
    session = SessionLocal()
    
    try:
        # 获取所有自选股
        watchlist = session.query(Watchlist.ticker).all()
        watchlist_tickers = set(w[0] for w in watchlist)
        
        print(f"自选股数量: {len(watchlist_tickers)}", flush=True)
        print("=" * 60, flush=True)
        
        # 构建映射
        stock_concepts = build_stock_concept_map(pro, watchlist_tickers)
        
        print(f"\n找到 {len(stock_concepts)} 只股票有概念数据", flush=True)
        
        # 更新数据库
        print("\n更新数据库...", flush=True)
        updated = 0
        total_concepts = 0
        
        for ticker, concepts in stock_concepts.items():
            symbol = session.query(SymbolMetadata).filter(
                SymbolMetadata.ticker == ticker
            ).first()
            
            if symbol:
                symbol.concepts = concepts
                updated += 1
                total_concepts += len(concepts)
        
        session.commit()
        
        print("=" * 60, flush=True)
        print(f"完成！", flush=True)
        print(f"  - 有概念数据的股票: {updated}", flush=True)
        print(f"  - 总概念标签数: {total_concepts}", flush=True)
        print(f"  - 平均每只股票的概念数: {total_concepts / max(updated, 1):.1f}", flush=True)
        
        # 显示一些示例
        print("\n示例:", flush=True)
        for ticker, concepts in list(stock_concepts.items())[:5]:
            print(f"  {ticker}: {', '.join(concepts[:5])}{'...' if len(concepts) > 5 else ''}", flush=True)
        
    except Exception as e:
        print(f"更新失败: {e}", flush=True)
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == '__main__':
    update_all_concepts()
