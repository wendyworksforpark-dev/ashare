"""
K线形态匹配服务
使用简化的DTW/欧氏距离算法找相似形态
"""
from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
from src.database import SessionLocal
import tushare as ts
from src.config import get_settings


class PatternMatcher:
    """K线形态匹配"""
    
    def __init__(self):
        self.session = SessionLocal()
        settings = get_settings()
        self.pro = ts.pro_api(settings.tushare_token)
    
    def close(self):
        self.session.close()
    
    def get_stock_klines(self, ticker: str, days: int = 120) -> Optional[np.ndarray]:
        """获取股票K线数据"""
        try:
            if ticker.startswith('6'):
                ts_code = f"{ticker}.SH"
            elif ticker.startswith('0') or ticker.startswith('3'):
                ts_code = f"{ticker}.SZ"
            else:
                ts_code = f"{ticker}.BJ"
            
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
            
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df is None or len(df) < 30:
                return None
            
            # 按日期排序
            df = df.sort_values('trade_date').reset_index(drop=True)
            
            # 返回收盘价数组
            return df['close'].values[-days:]
            
        except Exception as e:
            return None
    
    def normalize_pattern(self, prices: np.ndarray) -> np.ndarray:
        """归一化价格序列到0-1区间"""
        if len(prices) < 2:
            return prices
        
        min_p = np.min(prices)
        max_p = np.max(prices)
        
        if max_p == min_p:
            return np.zeros_like(prices)
        
        return (prices - min_p) / (max_p - min_p)
    
    def calculate_similarity(self, pattern1: np.ndarray, pattern2: np.ndarray) -> float:
        """计算两个形态的相似度 (0-100)"""
        if len(pattern1) != len(pattern2):
            # 简单插值对齐
            min_len = min(len(pattern1), len(pattern2))
            pattern1 = np.interp(np.linspace(0, 1, min_len), 
                                np.linspace(0, 1, len(pattern1)), pattern1)
            pattern2 = np.interp(np.linspace(0, 1, min_len),
                                np.linspace(0, 1, len(pattern2)), pattern2)
        
        # 归一化
        norm1 = self.normalize_pattern(pattern1)
        norm2 = self.normalize_pattern(pattern2)
        
        # 计算欧氏距离
        distance = np.sqrt(np.sum((norm1 - norm2) ** 2))
        
        # 转换为相似度 (0-100)
        max_distance = np.sqrt(len(norm1))  # 最大可能距离
        similarity = max(0, 100 * (1 - distance / max_distance))
        
        return similarity
    
    def find_similar_patterns(self, ticker: str, pattern_days: int = 20, 
                             lookback_days: int = 100, top_n: int = 5) -> List[Dict]:
        """
        在历史数据中找相似形态
        
        Args:
            ticker: 股票代码
            pattern_days: 当前形态天数
            lookback_days: 回溯天数
            top_n: 返回前N个相似形态
        """
        # 获取历史K线
        prices = self.get_stock_klines(ticker, lookback_days + pattern_days + 50)
        
        if prices is None or len(prices) < pattern_days + 30:
            return []
        
        # 当前形态 (最近N天)
        current_pattern = prices[-pattern_days:]
        
        # 在历史中滑动窗口匹配
        matches = []
        
        for i in range(len(prices) - pattern_days - 10 - pattern_days):  # 留出后续空间
            historical_pattern = prices[i:i + pattern_days]
            similarity = self.calculate_similarity(current_pattern, historical_pattern)
            
            if similarity > 50:  # 只保留相似度>50%的
                # 计算该形态后的涨跌
                future_prices = prices[i + pattern_days:i + pattern_days + 10]
                if len(future_prices) > 0:
                    future_return = (future_prices[-1] - historical_pattern[-1]) / historical_pattern[-1] * 100
                else:
                    future_return = 0
                
                matches.append({
                    'start_idx': i,
                    'end_idx': i + pattern_days,
                    'similarity': similarity,
                    'future_return': future_return,
                    'pattern_start_price': float(historical_pattern[0]),
                    'pattern_end_price': float(historical_pattern[-1]),
                })
        
        # 按相似度排序
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches[:top_n]
    
    def analyze_pattern_outcome(self, ticker: str, pattern_days: int = 20) -> Dict:
        """
        分析当前形态的历史胜率
        """
        matches = self.find_similar_patterns(ticker, pattern_days, lookback_days=200, top_n=20)
        
        if not matches:
            return {
                'ticker': ticker,
                'pattern_days': pattern_days,
                'similar_count': 0,
                'win_rate': None,
                'avg_return': None,
                'message': '未找到足够的相似形态'
            }
        
        # 统计
        win_count = sum(1 for m in matches if m['future_return'] > 0)
        avg_return = np.mean([m['future_return'] for m in matches])
        avg_similarity = np.mean([m['similarity'] for m in matches])
        
        return {
            'ticker': ticker,
            'pattern_days': pattern_days,
            'similar_count': len(matches),
            'win_rate': win_count / len(matches) * 100,
            'avg_return': avg_return,
            'avg_similarity': avg_similarity,
            'best_match': matches[0] if matches else None,
            'matches': matches[:5]
        }


def analyze_stock_pattern(ticker: str, pattern_days: int = 20) -> Dict:
    """分析股票形态（供API调用）"""
    matcher = PatternMatcher()
    try:
        return matcher.analyze_pattern_outcome(ticker, pattern_days)
    finally:
        matcher.close()
