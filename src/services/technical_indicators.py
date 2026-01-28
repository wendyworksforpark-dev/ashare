"""
技术指标计算模块

基于 K 线数据计算各类技术指标，并生成交易信号评分
参考: Ashare-AI-Strategy-Analyst 项目
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""

    def __init__(self):
        logger.info("技术指标计算器已初始化")

    def calculate_all(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        计算所有技术指标

        Args:
            df: 包含 OHLCV 数据的 DataFrame
                必须包含: open, high, low, close, volume

        Returns:
            包含所有技术指标的 DataFrame
        """
        if df is None or df.empty:
            logger.error("输入数据为空")
            return None

        if len(df) < 30:
            logger.warning(f"数据量不足 ({len(df)} 条)，部分指标可能不准确")

        try:
            result = df.copy()

            # 提取基础数据
            close = result['close'].values
            high = result['high'].values
            low = result['low'].values
            volume = result['volume'].values

            # 均线
            result['MA5'] = self._ma(close, 5)
            result['MA10'] = self._ma(close, 10)
            result['MA20'] = self._ma(close, 20)
            result['MA60'] = self._ma(close, 60)

            # MACD
            dif, dea, macd = self._macd(close)
            result['DIF'] = dif
            result['DEA'] = dea
            result['MACD'] = macd

            # KDJ
            k, d, j = self._kdj(close, high, low)
            result['K'] = k
            result['D'] = d
            result['J'] = j

            # RSI
            result['RSI'] = self._rsi(close, 14)

            # 布林带
            upper, mid, lower = self._boll(close)
            result['BOLL_UP'] = upper
            result['BOLL_MID'] = mid
            result['BOLL_LOW'] = lower

            # 成交量均线
            result['VOL_MA5'] = self._ma(volume, 5)
            result['VOL_MA10'] = self._ma(volume, 10)

            logger.debug("技术指标计算完成")
            return result

        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return None

    # ==================== 基础指标计算 ====================

    def _ma(self, data: np.ndarray, period: int) -> np.ndarray:
        """移动平均线"""
        result = np.full(len(data), np.nan)
        if len(data) >= period:
            for i in range(period - 1, len(data)):
                result[i] = np.mean(data[i - period + 1:i + 1])
        return result

    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """指数移动平均线"""
        result = np.full(len(data), np.nan)
        if len(data) < period:
            return result

        # 初始值用简单平均
        result[period - 1] = np.mean(data[:period])
        multiplier = 2.0 / (period + 1)

        for i in range(period, len(data)):
            result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]

        return result

    def _macd(
        self, close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD 指标"""
        ema_fast = self._ema(close, fast)
        ema_slow = self._ema(close, slow)
        dif = ema_fast - ema_slow
        dea = self._ema(dif, signal)
        macd = (dif - dea) * 2
        return dif, dea, macd

    def _kdj(
        self, close: np.ndarray, high: np.ndarray, low: np.ndarray, n: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """KDJ 指标"""
        length = len(close)
        k = np.full(length, 50.0)
        d = np.full(length, 50.0)

        for i in range(n - 1, length):
            high_n = np.max(high[i - n + 1:i + 1])
            low_n = np.min(low[i - n + 1:i + 1])

            if high_n != low_n:
                rsv = (close[i] - low_n) / (high_n - low_n) * 100
            else:
                rsv = 50

            k[i] = 2 / 3 * k[i - 1] + 1 / 3 * rsv
            d[i] = 2 / 3 * d[i - 1] + 1 / 3 * k[i]

        j = 3 * k - 2 * d
        return k, d, j

    def _rsi(self, close: np.ndarray, period: int = 14) -> np.ndarray:
        """RSI 指标"""
        result = np.full(len(close), np.nan)
        if len(close) < period + 1:
            return result

        # 计算价格变化
        delta = np.diff(close)
        gains = np.where(delta > 0, delta, 0)
        losses = np.where(delta < 0, -delta, 0)

        # 初始平均
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        if avg_loss == 0:
            result[period] = 100
        else:
            rs = avg_gain / avg_loss
            result[period] = 100 - (100 / (1 + rs))

        # 后续值使用平滑
        for i in range(period + 1, len(close)):
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period

            if avg_loss == 0:
                result[i] = 100
            else:
                rs = avg_gain / avg_loss
                result[i] = 100 - (100 / (1 + rs))

        return result

    def _boll(
        self, close: np.ndarray, period: int = 20, std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """布林带"""
        mid = self._ma(close, period)
        std = np.full(len(close), np.nan)

        for i in range(period - 1, len(close)):
            std[i] = np.std(close[i - period + 1:i + 1])

        upper = mid + std_dev * std
        lower = mid - std_dev * std

        return upper, mid, lower


class SignalAnalyzer:
    """交易信号分析器"""

    def __init__(self):
        self.indicators = TechnicalIndicators()

    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        分析交易信号

        Args:
            df: K 线数据 DataFrame

        Returns:
            {
                'score': 1-5 评分,
                'signal': '看涨'/'看跌'/'中性',
                'signals': [信号列表],
                'buy_count': 买入信号数,
                'sell_count': 卖出信号数
            }
        """
        # 计算技术指标
        df_with_indicators = self.indicators.calculate_all(df)
        if df_with_indicators is None or len(df_with_indicators) < 2:
            return {
                'score': 2,
                'signal': '中性',
                'signals': ['数据不足'],
                'buy_count': 0,
                'sell_count': 0
            }

        signals = []

        # MACD 信号
        macd_signal = self._analyze_macd(df_with_indicators)
        if macd_signal:
            signals.append(macd_signal)

        # KDJ 信号
        kdj_signal = self._analyze_kdj(df_with_indicators)
        if kdj_signal:
            signals.append(kdj_signal)

        # RSI 信号
        rsi_signal = self._analyze_rsi(df_with_indicators)
        if rsi_signal:
            signals.append(rsi_signal)

        # 布林带信号
        boll_signal = self._analyze_boll(df_with_indicators)
        if boll_signal:
            signals.append(boll_signal)

        # 均线信号
        ma_signal = self._analyze_ma(df_with_indicators)
        if ma_signal:
            signals.append(ma_signal)

        # 统计买卖信号
        buy_keywords = ['上涨', '反弹', '金叉', '超卖', '突破']
        sell_keywords = ['下跌', '回调', '死叉', '超买', '跌破']

        buy_count = sum(1 for s in signals if any(k in s for k in buy_keywords))
        sell_count = sum(1 for s in signals if any(k in s for k in sell_keywords))

        # 计算评分 (1-5)
        total = buy_count + sell_count
        if total == 0:
            score = 2
            signal = '中性'
        elif buy_count > sell_count:
            ratio = buy_count / total
            score = min(5, int(3 + ratio * 2))
            signal = '看涨' if score >= 4 else '偏多'
        elif sell_count > buy_count:
            ratio = sell_count / total
            score = max(1, int(3 - ratio * 2))
            signal = '看跌' if score <= 1 else '偏空'
        else:
            score = 2
            signal = '中性'

        return {
            'score': score,
            'signal': signal,
            'signals': signals if signals else ['无明显信号'],
            'buy_count': buy_count,
            'sell_count': sell_count
        }

    def _analyze_macd(self, df: pd.DataFrame) -> str:
        """分析 MACD"""
        if 'MACD' not in df.columns:
            return ""

        current = df['MACD'].iloc[-1]
        prev = df['MACD'].iloc[-2]

        if pd.isna(current) or pd.isna(prev):
            return ""

        if current > 0 >= prev:
            return "MACD金叉，可能上涨"
        elif current < 0 <= prev:
            return "MACD死叉，可能下跌"

        return ""

    def _analyze_kdj(self, df: pd.DataFrame) -> str:
        """分析 KDJ"""
        if 'K' not in df.columns or 'D' not in df.columns:
            return ""

        k = df['K'].iloc[-1]
        d = df['D'].iloc[-1]

        if pd.isna(k) or pd.isna(d):
            return ""

        if k < 20 and d < 20:
            return "KDJ超卖，可能反弹"
        elif k > 80 and d > 80:
            return "KDJ超买，注意回调"

        return ""

    def _analyze_rsi(self, df: pd.DataFrame) -> str:
        """分析 RSI"""
        if 'RSI' not in df.columns:
            return ""

        rsi = df['RSI'].iloc[-1]
        if pd.isna(rsi):
            return ""

        if rsi < 20:
            return "RSI超卖，可能反弹"
        elif rsi > 80:
            return "RSI超买，注意回调"

        return ""

    def _analyze_boll(self, df: pd.DataFrame) -> str:
        """分析布林带"""
        required = ['close', 'BOLL_UP', 'BOLL_LOW']
        if not all(col in df.columns for col in required):
            return ""

        close = df['close'].iloc[-1]
        upper = df['BOLL_UP'].iloc[-1]
        lower = df['BOLL_LOW'].iloc[-1]

        if pd.isna(upper) or pd.isna(lower):
            return ""

        if close > upper:
            return "突破布林上轨，超买"
        elif close < lower:
            return "跌破布林下轨，超卖"

        return ""

    def _analyze_ma(self, df: pd.DataFrame) -> str:
        """分析均线"""
        if 'MA5' not in df.columns or 'MA20' not in df.columns:
            return ""

        ma5 = df['MA5'].iloc[-1]
        ma20 = df['MA20'].iloc[-1]
        ma5_prev = df['MA5'].iloc[-2]
        ma20_prev = df['MA20'].iloc[-2]

        if pd.isna(ma5) or pd.isna(ma20) or pd.isna(ma5_prev) or pd.isna(ma20_prev):
            return ""

        if ma5 > ma20 and ma5_prev <= ma20_prev:
            return "MA5上穿MA20，金叉"
        elif ma5 < ma20 and ma5_prev >= ma20_prev:
            return "MA5下穿MA20，死叉"

        return ""


def analyze_stock(klines: List[Dict]) -> Dict:
    """
    便捷函数：分析股票 K 线数据

    Args:
        klines: K 线数据列表 [{"datetime": ..., "open": ..., ...}, ...]

    Returns:
        分析结果
    """
    df = pd.DataFrame(klines)
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')

    analyzer = SignalAnalyzer()
    return analyzer.analyze(df)
