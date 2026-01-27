"""
K-line Pattern Analyzer

Provides labeling algorithms for K-line pattern recognition and technical analysis.
All methods return human-readable labels rather than raw numbers to facilitate AI narrative generation.
"""

from typing import Tuple, Dict, List, Optional
from src.models.kline import Kline


class KlinePatternAnalyzer:
    """
    Analyzer for K-line patterns and technical positions.

    Converts raw K-line data into labeled conclusions for reliable AI interpretation.
    """

    @staticmethod
    def analyze_pattern(kline: Kline) -> Tuple[str, Dict]:
        """
        Identify K-line pattern and return label with analysis details.

        Args:
            kline: K-line data object

        Returns:
            Tuple of (pattern_label, analysis_dict)
            - pattern_label: Human-readable pattern name
            - analysis_dict: Detailed analysis metrics

        Example:
            ("大阳线", {"body_ratio": 0.82, "is_yang": True})
        """
        body = abs(kline.close - kline.open)
        total_range = kline.high - kline.low

        # Handle edge case: no price movement
        if total_range == 0:
            is_yang = kline.close >= kline.open
            return "一字板", {
                "body_ratio": 0,
                "upper_shadow_ratio": 0,
                "lower_shadow_ratio": 0,
                "is_yang": is_yang
            }

        # Calculate ratios
        body_ratio = body / total_range
        upper_shadow = kline.high - max(kline.open, kline.close)
        lower_shadow = min(kline.open, kline.close) - kline.low
        upper_ratio = upper_shadow / total_range
        lower_ratio = lower_shadow / total_range
        is_yang = kline.close > kline.open

        # Pattern determination
        if body_ratio > 0.7:
            pattern = "大阳线" if is_yang else "大阴线"
        elif body_ratio < 0.1:
            pattern = "十字星"
        elif upper_ratio > 0.5:
            pattern = "上影阳线" if is_yang else "上影阴线"
        elif lower_ratio > 0.5:
            pattern = "下影阳线" if is_yang else "下影阴线"
        elif body_ratio < 0.3:
            pattern = "小阳线" if is_yang else "小阴线"
        else:
            pattern = "中阳线" if is_yang else "中阴线"

        return pattern, {
            "body_ratio": round(body_ratio, 3),
            "upper_shadow_ratio": round(upper_ratio, 3),
            "lower_shadow_ratio": round(lower_ratio, 3),
            "is_yang": is_yang
        }

    @staticmethod
    def get_volume_trend_label(current_volume: float,
                               avg_5d: float,
                               avg_10d: float) -> Tuple[str, Dict]:
        """
        Determine volume trend label.

        Args:
            current_volume: Current period volume
            avg_5d: 5-day average volume
            avg_10d: 10-day average volume

        Returns:
            Tuple of (trend_label, ratios_dict)

        Example:
            ("放量", {"vs_5d": 1.8, "vs_10d": 1.6})
        """
        ratio_5d = current_volume / avg_5d if avg_5d > 0 else 1
        ratio_10d = current_volume / avg_10d if avg_10d > 0 else 1

        # Label determination
        if ratio_5d > 1.5:
            label = "放量"
        elif ratio_5d < 0.7:
            label = "缩量"
        elif ratio_10d > 1.2:
            label = "温和放量"
        elif ratio_10d < 0.8:
            label = "温和缩量"
        else:
            label = "持平"

        return label, {
            "vs_5d": round(ratio_5d, 2),
            "vs_10d": round(ratio_10d, 2)
        }

    @staticmethod
    def analyze_ma_position(current_price: float, ma_values: Dict[str, float]) -> Tuple[str, Dict]:
        """
        Determine MA (Moving Average) position label and trend.

        Args:
            current_price: Current price
            ma_values: Dict with 'ma5', 'ma10', 'ma20' keys

        Returns:
            Tuple of (position_label, ma_dict)

        Example:
            ("MA10上方运行", {"ma5": 3425, "ma10": 3438, "trend": "偏强"})
        """
        ma5 = ma_values.get('ma5', 0)
        ma10 = ma_values.get('ma10', 0)
        ma20 = ma_values.get('ma20', 0)

        # Position determination
        if current_price > ma5 > ma10 > ma20:
            label = "多头排列,强势"
            trend = "上升"
        elif current_price > ma10:
            label = "MA10上方运行"
            trend = "偏强"
        elif current_price < ma5:
            if current_price < ma20:
                label = "跌破MA20,转弱"
                trend = "下降"
            else:
                label = "MA5下方运行,走弱"
                trend = "偏弱"
        elif ma5 < current_price < ma10:
            label = "MA5与MA10之间震荡"
            trend = "震荡"
        else:
            label = "均线附近"
            trend = "不明"

        return label, {
            "current": round(current_price, 2),
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "ma20": round(ma20, 2),
            "trend": trend
        }

    @staticmethod
    def detect_ma_breaks(kline: Kline,
                        prev_close: float,
                        ma_values: Dict[str, float]) -> List[str]:
        """
        Detect MA line breaks (golden/death crosses).

        Args:
            kline: Current K-line data
            prev_close: Previous closing price
            ma_values: Dict with MA values

        Returns:
            List of break event descriptions (e.g., ["上穿ma10", "下破ma5"])
        """
        breaks = []

        for ma_period in [5, 10, 20]:
            ma_key = f"ma{ma_period}"
            if ma_key not in ma_values:
                continue

            ma_value = ma_values[ma_key]

            # Check for upward break
            if prev_close < ma_value <= kline.close:
                breaks.append(f"上穿{ma_key}")

            # Check for downward break
            elif prev_close > ma_value >= kline.close:
                breaks.append(f"下破{ma_key}")

        return breaks

    @staticmethod
    def analyze_kline_strength(kline: Kline, volume_avg: float) -> Dict:
        """
        Analyze K-line strength characteristics.

        Args:
            kline: K-line data
            volume_avg: Average volume for comparison

        Returns:
            Dict with strength indicators
        """
        change_pct = ((kline.close - kline.open) / kline.open * 100
                     if kline.open > 0 else 0)
        volume_ratio = kline.volume / volume_avg if volume_avg > 0 else 1

        # Strength classification
        if abs(change_pct) > 5 and volume_ratio > 1.5:
            strength = "强势" if change_pct > 0 else "强势下跌"
        elif abs(change_pct) > 3:
            strength = "偏强" if change_pct > 0 else "偏弱"
        elif abs(change_pct) < 1:
            strength = "震荡"
        else:
            strength = "一般"

        return {
            "change_pct": round(change_pct, 2),
            "volume_ratio": round(volume_ratio, 2),
            "strength": strength
        }

    @staticmethod
    def assess_volume_significance(volume_ratio: float, price_change: float) -> str:
        """
        Assess the significance of volume change with price movement.

        Analyzes price-volume relationship to determine market behavior.

        Args:
            volume_ratio: Volume ratio vs average
            price_change: Price change percentage

        Returns:
            Significance label describing price-volume relationship
        """
        if price_change > 0:
            if volume_ratio > 1.5:
                return "放量上涨(健康)"
            elif volume_ratio < 0.7:
                return "缩量上涨(需观察)"
            else:
                return "温和上涨"
        elif price_change < 0:
            if volume_ratio > 1.5:
                return "放量下跌(杀跌)"
            elif volume_ratio < 0.7:
                return "缩量下跌(抵抗)"
            else:
                return "一般下跌"
        else:
            if volume_ratio > 1.5:
                return "放量横盘(变盘)"
            elif volume_ratio < 0.7:
                return "缩量横盘"
            else:
                return "横盘整理"

    @staticmethod
    def identify_support_resistance(kline_history: List[Kline],
                                   current_price: float) -> Dict:
        """
        Identify key support and resistance levels.

        Args:
            kline_history: Recent K-line history (20-60 days)
            current_price: Current price

        Returns:
            Dict with support/resistance levels and distances
        """
        if not kline_history:
            return {}

        # Find recent highs and lows
        highs = [k.high for k in kline_history]
        lows = [k.low for k in kline_history]

        resistance = max(highs)
        support = min(lows)

        # Find nearest significant levels
        recent_highs = sorted([h for h in highs if h > current_price])[:3]
        recent_lows = sorted([l for l in lows if l < current_price], reverse=True)[:3]

        nearest_resistance = recent_highs[0] if recent_highs else resistance
        nearest_support = recent_lows[0] if recent_lows else support

        return {
            "resistance": round(nearest_resistance, 2),
            "support": round(nearest_support, 2),
            "to_resistance_pct": round((nearest_resistance - current_price) / current_price * 100, 2),
            "to_support_pct": round((current_price - nearest_support) / current_price * 100, 2),
            "position": "高位" if current_price > (resistance + support) / 2 else "低位"
        }

    @staticmethod
    def get_position_label(days_5_change: float,
                          days_10_change: float,
                          current_change: float) -> str:
        """
        Determine stock position label based on recent performance.

        Args:
            days_5_change: 5-day cumulative change %
            days_10_change: 10-day cumulative change %
            current_change: Today's change %

        Returns:
            Position label (e.g., "高位回调", "低位反弹")
        """
        if days_10_change > 20:
            if current_change < -3:
                return "高位回调"
            else:
                return "高位强势"
        elif days_10_change < -20:
            if current_change > 3:
                return "低位反弹"
            else:
                return "低位弱势"
        elif days_5_change > 10:
            return "近期走强"
        elif days_5_change < -10:
            return "近期走弱"
        else:
            return "震荡整理"
