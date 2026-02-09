#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术分析工具模块
提供各种技术指标计算和K线形态识别
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger

logger = setup_logger(__name__)


class TrendType(Enum):
    """趋势类型"""
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


@dataclass
class TechnicalIndicators:
    """技术指标数据结构"""
    # 移动平均线
    ma5: float = None
    ma10: float = None
    ma20: float = None
    ma60: float = None
    ma120: float = None

    # 指数移动平均线
    ema5: float = None
    ema10: float = None
    ema20: float = None

    # MACD
    macd: float = None
    signal: float = None
    histogram: float = None

    # RSI
    rsi6: float = None
    rsi12: float = None
    rsi24: float = None

    # 布林带
    bollinger_upper: float = None
    bollinger_middle: float = None
    bollinger_lower: float = None
    bollinger_width: float = None

    # ATR
    atr14: float = None
    atr10: float = None

    # 成交量指标
    volume_ma5: float = None
    volume_ma10: float = None
    volume_ma20: float = None
    volume_ratio: float = None

    # 趋势
    trend: TrendType = TrendType.UNKNOWN

    # 综合评分
    score: int = 50


class TechnicalAnalyzer:
    """技术分析器"""

    def __init__(self):
        pass

    def calculate_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """
        计算所有技术指标

        Args:
            df: 包含 'open', 'high', 'low', 'close', 'vol' 列的DataFrame

        Returns:
            TechnicalIndicators 对象
        """
        if df is None or df.empty or len(df) < 60:
            logger.warning("数据不足，无法计算技术指标")
            return TechnicalIndicators()

        try:
            close = df['close'].astype(float)
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            volume = df['vol'].astype(float) if 'vol' in df.columns else df['volume'].astype(float)

            indicators = TechnicalIndicators()

            # 移动平均线
            indicators.ma5 = self._sma(close, 5)
            indicators.ma10 = self._sma(close, 10)
            indicators.ma20 = self._sma(close, 20)
            indicators.ma60 = self._sma(close, 60)
            indicators.ma120 = self._sma(close, 120) if len(df) >= 120 else None

            # MACD
            macd_line, signal_line, hist = self._macd(close)
            indicators.macd = macd_line.iloc[-1] if len(macd_line) > 0 else None
            indicators.signal = signal_line.iloc[-1] if len(signal_line) > 0 else None
            indicators.histogram = hist.iloc[-1] if len(hist) > 0 else None

            # RSI
            indicators.rsi6 = self._rsi(close, 6)
            indicators.rsi12 = self._rsi(close, 12)
            indicators.rsi24 = self._rsi(close, 24)

            # 布林带
            upper, middle, lower = self._bollinger_bands(close)
            indicators.bollinger_upper = upper.iloc[-1]
            indicators.bollinger_middle = middle.iloc[-1]
            indicators.bollinger_lower = lower.iloc[-1]
            indicators.bollinger_width = (upper.iloc[-1] - lower.iloc[-1]) / middle.iloc[-1] * 100

            # ATR
            indicators.atr14 = self._atr(high, low, close, 14)
            indicators.atr10 = self._atr(high, low, close, 10)

            # 成交量指标
            indicators.volume_ma5 = self._sma(volume, 5)
            indicators.volume_ma10 = self._sma(volume, 10)
            indicators.volume_ma20 = self._sma(volume, 20)
            indicators.volume_ratio = volume.iloc[-1] / indicators.volume_ma20 if indicators.volume_ma20 > 0 else 1.0

            # 判断趋势
            indicators.trend = self._judge_trend(indicators)

            # 综合评分
            indicators.score = self._calc_comprehensive_score(indicators)

            return indicators

        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return TechnicalIndicators()

    def generate_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成交易信号

        Args:
            df: K线数据

        Returns:
            信号字典
        """
        indicators = self.calculate_indicators(df)

        if indicators.ma5 is None:
            return {"signal": SignalType.HOLD, "reason": "数据不足"}

        score = indicators.score
        signals = []

        # 1. 均线信号
        if indicators.ma5 > indicators.ma20 > indicators.ma60:
            signals.append("MA多头排列")
            if df['close'].iloc[-1] > indicators.ma5:
                signals.append("价格在MA5上方")
        elif indicators.ma5 < indicators.ma20 < indicators.ma60:
            signals.append("MA空头排列")

        # 2. MACD信号
        if indicators.histogram is not None:
            if indicators.macd > indicators.signal and indicators.histogram > 0:
                signals.append("MACD金叉/多头")
            elif indicators.macd < indicators.signal and indicators.histogram < 0:
                signals.append("MACD死叉/空头")

        # 3. RSI信号
        rsi = indicators.rsi12
        if rsi < 30:
            signals.append("RSI超卖")
        elif rsi > 70:
            signals.append("RSI超买")

        # 综合判断
        if score >= 80:
            signal = SignalType.STRONG_BUY
            reason = "技术面全面向好"
        elif score >= 65:
            signal = SignalType.BUY
            reason = "技术面偏强"
        elif score >= 45:
            signal = SignalType.HOLD
            reason = "技术面中性"
        elif score >= 30:
            signal = SignalType.SELL
            reason = "技术面偏弱"
        else:
            signal = SignalType.STRONG_SELL
            reason = "技术面全面走弱"

        return {
            "signal": signal,
            "score": score,
            "indicators": indicators,
            "reason": reason,
            "details": signals
        }

    def _sma(self, series: pd.Series, period: int) -> float:
        """简单移动平均"""
        if len(series) < period:
            return None
        return series.iloc[-period:].mean()

    def _ema(self, series: pd.Series, period: int) -> float:
        """指数移动平均"""
        if len(series) < period:
            return None
        return series.ewm(span=period, adjust=False).mean().iloc[-1]

    def _macd(self, close: pd.Series, fast: int = 12, slow: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD计算"""
        ema_fast = close.ewm(span=fast, adjust=False)
        ema_slow = close.ewm(span=slow, adjust=False)

        macd_line = ema_fast.mean() - ema_slow.mean()
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def _rsi(self, series: pd.Series, period: int) -> float:
        """RSI计算"""
        if len(series) < period + 1:
            return 50.0

        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0

    def _bollinger_bands(self, series: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """布林带计算"""
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()

        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        return upper, middle, lower

    def _atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """ATR计算"""
        if len(high) < period + 1:
            return None

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr.iloc[-1]

    def _judge_trend(self, indicators: TechnicalIndicators) -> TrendType:
        """判断趋势"""
        if indicators.ma5 is None or indicators.ma20 is None:
            return TrendType.UNKNOWN

        # 多头排列
        if indicators.ma5 > indicators.ma20 > indicators.ma60:
            if indicators.ma5 > indicators.ma20 * 1.02:
                return TrendType.UPTREND

        # 空头排列
        if indicators.ma5 < indicators.ma20 < indicators.ma60:
            if indicators.ma5 < indicators.ma20 * 0.98:
                return TrendType.DOWNTREND

        return TrendType.SIDEWAYS

    def _calc_comprehensive_score(self, indicators: TechnicalIndicators) -> int:
        """计算综合评分 (0-100)"""
        score = 50  # 基础分

        # 均线趋势
        if indicators.trend == TrendType.UPTREND:
            score += 20
        elif indicators.trend == TrendType.DOWNTREND:
            score -= 20

        # MACD
        if indicators.histogram is not None:
            if indicators.histogram > 0:
                score += 10
            elif indicators.histogram < 0:
                score -= 10

        # RSI
        if indicators.rsi12 is not None:
            if 40 <= indicators.rsi12 <= 60:
                score += 5
            elif indicators.rsi12 > 70:
                score -= 5
            elif indicators.rsi12 < 30:
                score += 5

        return max(min(score, 100), 0)


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("技术分析工具测试")
    print("=" * 60)

    # 模拟一些数据
    import numpy as np

    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=120, freq='D')

    # 生成模拟价格数据
    close_prices = 100 + np.cumsum(np.random.randn(120) + 0.1)
    open_prices = close_prices - np.random.uniform(-2, 2, 120)
    high_prices = np.maximum(close_prices, open_prices) + np.random.uniform(0, 3, 120)
    low_prices = np.minimum(close_prices, open_prices) - np.random.uniform(0, 3, 120)

    df = pd.DataFrame({
        'trade_date': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'vol': np.random.randint(1000000, 10000000, 120)
    })

    # 计算技术指标
    analyzer = TechnicalAnalyzer()
    indicators = analyzer.calculate_indicators(df)

    print("\n📊 技术指标:")
    print(f"  MA5:   {indicators.ma5:.2f}")
    print(f"  MA20:  {indicators.ma20:.2f}")
    print(f"  MA60:  {indicators.ma60:.2f}")
    print(f"  RSI12: {indicators.rsi12:.2f}")
    print(f"  趋势:  {indicators.trend.value}")
    print(f"  综合评分: {indicators.score}")

    # 生成信号
    signal = analyzer.generate_signal(df)
    print(f"\n🎯 交易信号:")
    print(f"  信号: {signal['signal'].value}")
    print(f"  得分: {signal['score']}")
    print(f"  原因: {signal['reason']}")

    print("\n" + "=" * 60)
