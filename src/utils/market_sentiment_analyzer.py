"""
Market Sentiment Analyzer

Provides labeling algorithms for market sentiment analysis based on breadth indicators.
Converts aggregated market statistics into human-readable sentiment labels.
"""

from typing import Tuple, Dict, List
from src.schemas.daily_review import SectorSnapshot


class MarketSentimentAnalyzer:
    """
    Analyzer for overall market sentiment from breadth indicators.

    Aggregates advance/decline ratio, limit boards, and turnover into sentiment labels.
    """

    @staticmethod
    def calculate_sentiment(up_count: int,
                           down_count: int,
                           limit_up: int,
                           volume_ratio: float) -> Tuple[str, int]:
        """
        Calculate market sentiment score and label.

        Uses a scoring system based on:
        - Advance/decline ratio
        - Limit-up board count
        - Volume ratio

        Args:
            up_count: Number of stocks up
            down_count: Number of stocks down
            limit_up: Number of limit-up stocks
            volume_ratio: Volume vs historical average

        Returns:
            Tuple of (sentiment_label, sentiment_score)
            - sentiment_label: "强势", "偏多", "震荡", "偏空", or "弱势"
            - sentiment_score: Integer from -5 to +5

        Example:
            ("偏多", 2)
        """
        score = 0
        total = up_count + down_count
        up_down_ratio = up_count / down_count if down_count > 0 else 5.0

        # Advance/decline ratio scoring
        if up_down_ratio > 1.3:
            score += 2
        elif up_down_ratio > 1.1:
            score += 1
        elif up_down_ratio < 0.8:
            score -= 2
        elif up_down_ratio < 0.9:
            score -= 1

        # Limit-up board scoring
        if limit_up > 80:
            score += 2
        elif limit_up > 50:
            score += 1
        elif limit_up < 20:
            score -= 1

        # Volume scoring
        if volume_ratio > 1.2:
            score += 1
        elif volume_ratio < 0.8:
            score -= 1

        # Determine label from score
        if score >= 3:
            label = "强势"
        elif score >= 1:
            label = "偏多"
        elif score <= -3:
            label = "弱势"
        elif score <= -1:
            label = "偏空"
        else:
            label = "震荡"

        return label, score

    @staticmethod
    def analyze_limit_boards(limit_up: int,
                            limit_down: int,
                            first_board_sealed: int,
                            first_board_total: int) -> Dict:
        """
        Analyze limit board market heat.

        Args:
            limit_up: Total limit-up stocks
            limit_down: Total limit-down stocks
            first_board_sealed: Number of first-board stocks that stayed sealed
            first_board_total: Total number of first-board attempts

        Returns:
            Dict with heat analysis
        """
        seal_rate = (first_board_sealed / first_board_total
                    if first_board_total > 0 else 0)

        # Market heat classification
        if limit_up > 100 and seal_rate > 0.8:
            heat = "火爆"
        elif limit_up > 60 and seal_rate > 0.6:
            heat = "活跃"
        elif limit_up > 30:
            heat = "一般"
        else:
            heat = "低迷"

        # Sentiment from limit boards
        if limit_up > limit_down * 3:
            sentiment = "做多情绪高涨"
        elif limit_down > limit_up * 2:
            sentiment = "恐慌情绪蔓延"
        else:
            sentiment = "情绪中性"

        return {
            "heat": heat,
            "seal_rate": round(seal_rate, 2),
            "sentiment": sentiment,
            "limit_up": limit_up,
            "limit_down": limit_down
        }

    @staticmethod
    def get_money_flow_label(net_inflow: float) -> str:
        """
        Label money flow based on net inflow amount.

        Args:
            net_inflow: Net inflow in 亿元 (100 million yuan)

        Returns:
            Money flow label
        """
        if net_inflow > 10:
            return "大幅流入"
        elif net_inflow > 3:
            return "主力流入"
        elif net_inflow > 0:
            return "小幅流入"
        elif net_inflow > -3:
            return "小幅流出"
        elif net_inflow > -10:
            return "主力流出"
        else:
            return "大幅流出"

    @staticmethod
    def calculate_flow_strength_score(net_inflow: float,
                                      net_buy_amount: float,
                                      total_amount: float) -> int:
        """
        Calculate flow strength score from -5 to +5.

        Args:
            net_inflow: Net inflow (亿元)
            net_buy_amount: Total buy amount (亿元)
            total_amount: Total turnover (亿元)

        Returns:
            Score from -5 (strong outflow) to +5 (strong inflow)
        """
        score = 0

        # Base score from net inflow
        if net_inflow > 10:
            score += 3
        elif net_inflow > 3:
            score += 2
        elif net_inflow > 0:
            score += 1
        elif net_inflow > -3:
            score -= 1
        elif net_inflow > -10:
            score -= 2
        else:
            score -= 3

        # Adjust by buy/sell ratio
        if total_amount > 0:
            buy_ratio = net_buy_amount / total_amount
            if buy_ratio > 0.6:
                score += 1
            elif buy_ratio < 0.4:
                score -= 1

        # Adjust by flow intensity
        if total_amount > 0:
            flow_intensity = abs(net_inflow) / total_amount
            if flow_intensity > 0.15:
                score += 1 if net_inflow > 0 else -1

        return max(-5, min(5, score))

    @staticmethod
    def get_sector_strength_label(up_count: int,
                                  down_count: int,
                                  change_pct: float) -> Tuple[str, Dict]:
        """
        Determine sector strength label.

        Args:
            up_count: Number of stocks up in sector
            down_count: Number of stocks down in sector
            change_pct: Sector average change percentage

        Returns:
            Tuple of (strength_label, stats_dict)

        Example:
            ("强势", {"up_ratio": 0.85, "total_count": 40})
        """
        total = up_count + down_count
        up_ratio = up_count / total if total > 0 else 0.5

        if up_ratio > 0.8 and change_pct > 2:
            label = "强势"
        elif up_ratio > 0.6 and change_pct > 0:
            label = "偏强"
        elif up_ratio < 0.3 and change_pct < -2:
            label = "弱势"
        elif up_ratio < 0.4 and change_pct < 0:
            label = "偏弱"
        else:
            label = "震荡"

        return label, {
            "up_ratio": round(up_ratio, 2),
            "total_count": total
        }

    @staticmethod
    def analyze_sector_rotation(sectors: List[SectorSnapshot],
                               prev_sectors: List[SectorSnapshot]) -> Dict:
        """
        Analyze sector rotation patterns between two periods.

        Args:
            sectors: Current period sector snapshots
            prev_sectors: Previous period sector snapshots

        Returns:
            Dict with rotation analysis including hot/cold rotations
        """
        # Build previous sector lookup
        prev_lookup = {s.sector_code: s for s in prev_sectors}

        gainers = []
        losers = []
        stable = []

        for sector in sectors:
            prev = prev_lookup.get(sector.sector_code)
            if not prev:
                continue

            strength_change = sector.change_pct - prev.change_pct
            flow_change = sector.net_inflow - prev.net_inflow

            sector_change = {
                "name": sector.sector_name,
                "strength_change": round(strength_change, 2),
                "flow_change": round(flow_change, 2)
            }

            # Classify rotation
            if strength_change > 2 and flow_change > 3:
                gainers.append(sector_change)
            elif strength_change < -2 and flow_change < -3:
                losers.append(sector_change)
            else:
                stable.append(sector_change)

        return {
            "hot_rotation": sorted(gainers, key=lambda x: x["strength_change"], reverse=True)[:5],
            "cold_rotation": sorted(losers, key=lambda x: x["strength_change"])[:5],
            "rotation_intensity": "强" if len(gainers) + len(losers) > 10 else "弱"
        }

    @staticmethod
    def classify_stock_role(ticker: str,
                           change_pct: float,
                           days_5_change: float,
                           market_cap_rank: int,
                           leader_symbol: str,
                           sector_avg_change: float) -> str:
        """
        Classify stock's role in the sector.

        Args:
            ticker: Stock ticker
            change_pct: Today's change percentage
            days_5_change: 5-day cumulative change
            market_cap_rank: Market cap rank within sector
            leader_symbol: Sector's leader stock ticker
            sector_avg_change: Sector average change percentage

        Returns:
            Role label: "龙头", "高位核心", "补涨", or "成分股"
        """
        # Leader
        if ticker == leader_symbol:
            return "龙头"

        # High-position core
        if days_5_change > 10 and market_cap_rank <= 3:
            return "高位核心"

        # Catch-up
        if change_pct > sector_avg_change and market_cap_rank > 3:
            return "补涨"

        return "成分股"


def validate_snapshot_quality(snapshot: 'DailyReviewSnapshot') -> List[str]:
    """
    Validate data snapshot quality and completeness.

    Args:
        snapshot: Daily review snapshot to validate

    Returns:
        List of validation warnings (empty if all good)
    """
    warnings = []

    # Check indices
    if len(snapshot.indices) < 3:
        warnings.append("指数数据不足,至少需要3个主要指数")

    # Check sectors
    if len(snapshot.sectors) < 10:
        warnings.append(f"板块数据不足({len(snapshot.sectors)}个),建议至少10个")

    # Check sample stocks
    total_samples = sum(len(stocks) for stocks in snapshot.sample_stocks.values())
    if total_samples < 20:
        warnings.append(f"样本股不足({total_samples}只),建议至少20只")

    # Check sentiment completeness
    if snapshot.sentiment.up_count + snapshot.sentiment.down_count < 3000:
        warnings.append("市场广度数据可能不完整")

    # Check for zero values that shouldn't be zero
    if snapshot.sentiment.total_amount == 0:
        warnings.append("市场成交额为0,数据异常")

    return warnings
