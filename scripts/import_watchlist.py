#!/usr/bin/env python3
"""
导入 watchlist 数据到数据库
数据源: https://github.com/zinan92/ashare/backups/watchlist_latest.json
"""

import json
import requests
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import SessionLocal
from src.models import Watchlist

WATCHLIST_URL = "https://raw.githubusercontent.com/zinan92/ashare/main/backups/watchlist_latest.json"


def fetch_watchlist():
    """从 GitHub 获取 watchlist 数据"""
    print(f"正在从 GitHub 获取 watchlist...")
    resp = requests.get(WATCHLIST_URL, timeout=30)
    resp.raise_for_status()
    return resp.json()


def import_watchlist(data: dict, replace: bool = True):
    """
    导入 watchlist 到数据库
    
    Args:
        data: watchlist JSON 数据
        replace: 是否清空现有数据
    """
    session = SessionLocal()
    
    try:
        if replace:
            # 清空现有数据
            deleted = session.query(Watchlist).delete()
            print(f"已清空现有 watchlist ({deleted} 条)")
        
        stocks = data.get("data", [])
        added = 0
        skipped = 0
        
        for item in stocks:
            ticker = item.get("ticker")
            if not ticker:
                continue
            
            # 检查是否已存在
            existing = session.query(Watchlist).filter(
                Watchlist.ticker == ticker
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # 创建新记录
            watchlist_item = Watchlist(
                ticker=ticker,
                category=item.get("category", "未分类"),
                is_focus=item.get("is_focus", False),
                added_at=datetime.now(),
            )
            session.add(watchlist_item)
            added += 1
        
        session.commit()
        print(f"导入完成: 新增 {added} 条, 跳过 {skipped} 条")
        print(f"当前 watchlist 总数: {session.query(Watchlist).count()}")
        
    except Exception as e:
        session.rollback()
        print(f"导入失败: {e}")
        raise
    finally:
        session.close()


def show_categories(data: dict):
    """显示分类统计"""
    stocks = data.get("data", [])
    categories = {}
    
    for item in stocks:
        cat = item.get("category", "未分类")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n分类统计:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} 只")
    
    focus_count = sum(1 for s in stocks if s.get("is_focus"))
    print(f"\n重点关注: {focus_count} 只")


def main():
    # 获取数据
    data = fetch_watchlist()
    
    print(f"\n备份时间: {data.get('backup_time')}")
    print(f"股票总数: {data.get('total_count')}")
    
    # 显示分类
    show_categories(data)
    
    # 导入数据
    print("\n开始导入...")
    import_watchlist(data, replace=True)


if __name__ == "__main__":
    main()
