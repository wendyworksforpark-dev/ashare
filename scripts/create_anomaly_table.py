#!/usr/bin/env python3
"""创建异动监控表"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import engine
from sqlalchemy import text

def create_table():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS stock_anomaly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker VARCHAR(10) NOT NULL,
            name VARCHAR(32),
            trade_date VARCHAR(8) NOT NULL,
            trade_time VARCHAR(8),
            
            -- 异动类型
            anomaly_type VARCHAR(32) NOT NULL,  -- 'limit_up', 'limit_down', 'large_buy', 'large_sell', 'volume_spike', 'price_spike'
            
            -- 异动数据
            price FLOAT,
            pct_change FLOAT,
            volume FLOAT,
            amount FLOAT,
            
            -- 额外信息
            details TEXT,  -- JSON
            
            -- 是否已推送
            notified BOOLEAN DEFAULT FALSE,
            
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(ticker, trade_date, trade_time, anomaly_type)
        )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_anom_date ON stock_anomaly(trade_date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_anom_type ON stock_anomaly(anomaly_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_anom_ticker ON stock_anomaly(ticker)"))
        conn.commit()
        
    print("✅ stock_anomaly 表创建成功")

if __name__ == '__main__':
    create_table()
