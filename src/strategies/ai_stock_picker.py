#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI选股策略模块
基于多因子模型的智能选股系统
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.stock_api import StockDataAPI, StockScreener
from utils.logger import setup_logger
from utils.technical_analysis import TechnicalAnalyzer

logger = setup_logger(__name__)


class AIStockPicker:
    """AI智能选股器"""

    def __init__(self, data_api: StockDataAPI = None):
        """
        初始化AI选股器

        Args:
            data_api: 股票数据API实例
        """
        self.api = data_api or StockDataAPI()
        self.screener = StockScreener(self.api)
        self.tech_analyzer = TechnicalAnalyzer()

    def pick_by_ai_score(self, symbols: List[str], method: str = "comprehensive") -> List[Dict[str, Any]]:
        """
        AI综合评分选股

        Args:
            symbols: 候选股票列表
            method: 评分方法 ('comprehensive', 'momentum', 'value', 'growth')

        Returns:
            评分后的股票列表
        """
        results = []

        for symbol in symbols:
            try:
                # 获取历史数据
                df = self.api.get_daily_price(symbol, start_date=None)
                if df is None or df.empty or len(df) < 30:
                    continue

                # 计算各项因子得分
                score = 0.0
                factors = {}

                # 1. 动量因子
                momentum_score = self._calc_momentum_score(df)
                factors['momentum'] = momentum_score

                # 2. 趋势因子
                trend_score = self._calc_trend_score(df)
                factors['trend'] = trend_score

                # 3. 量能因子
                volume_score = self._calc_volume_score(df)
                factors['volume'] = volume_score

                # 4. 波动因子
                volatility_score = self._calc_volatility_score(df)
                factors['volatility'] = volatility_score

                # 综合评分
                if method == "comprehensive":
                    score = (momentum_score * 0.3 + trend_score * 0.3 +
                            volume_score * 0.2 + volatility_score * 0.2)
                elif method == "momentum":
                    score = momentum_score
                elif method == "trend":
                    score = trend_score
                else:
                    score = (momentum_score + trend_score) / 2

                latest = df.iloc[-1]
                quote = self.api.get_realtime_quote([symbol])
                current_price = latest['close']
                change_pct = ((current_price - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100 if len(df) > 1 else 0

                results.append({
                    "symbol": symbol,
                    "score": score,
                    "factors": factors,
                    "price": current_price,
                    "change_pct": change_pct,
                    "ma5": latest['close'] if len(df) < 5 else df['close'].iloc[-5:].mean(),
                    "ma20": df['close'].iloc[-20:].mean() if len(df) >= 20 else current_price,
                    "volume_ratio": latest['vol'] / df['vol'].iloc[-20:].mean() if len(df) >= 20 else 1.0,
                })

            except Exception as e:
                logger.error(f"分析 {symbol} 时出错: {e}")
                continue

        # 按分数排序
        results = sorted(results, key=lambda x: x['score'], reverse=True)

        return results

    def _calc_momentum_score(self, df: pd.DataFrame) -> float:
        """计算动量得分 (0-100)"""
        try:
            if len(df) < 10:
                return 50.0

            returns = df['close'].pct_change(periods=5).dropna()

            # 最近5日收益
            recent_return = returns.iloc[-5:].mean() * 100 if len(returns) >= 5 else 0

            # 动量强度
            momentum = min(max(recent_return * 10 + 50, 0), 100)

            return momentum
        except:
            return 50.0

    def _calc_trend_score(self, df: pd.DataFrame) -> float:
        """计算趋势得分 (0-100)"""
        try:
            if len(df) < 20:
                return 50.0

            current = df['close'].iloc[-1]
            ma5 = df['close'].iloc[-5:].mean()
            ma20 = df['close'].iloc[-20:].mean()
            ma60 = df['close'].iloc[-60:].mean() if len(df) >= 60 else ma20

            # 价格在均线上方
            price_above_ma5 = current > ma5
            price_above_ma20 = current > ma20
            price_above_ma60 = current > ma60

            # 均线多头排列
            ma_bullish = ma5 > ma20 > ma60

            score = 50.0
            if price_above_ma5:
                score += 10
            if price_above_ma20:
                score += 15
            if price_above_ma60:
                score += 15
            if ma_bullish:
                score += 10

            return min(score, 100)
        except:
            return 50.0

    def _calc_volume_score(self, df: pd.DataFrame) -> float:
        """计算量能得分 (0-100)"""
        try:
            if len(df) < 10:
                return 50.0

            recent_vol = df['vol'].iloc[-5:].mean()
            avg_vol = df['vol'].iloc[-20:].mean()

            vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1.0

            # 量能适中或偏大为好
            if 0.8 <= vol_ratio <= 2.0:
                score = 70 + (vol_ratio - 1) * 20
            elif vol_ratio < 0.8:
                score = 50 + vol_ratio * 25
            else:
                score = min(90 - (vol_ratio - 2) * 10, 90)

            return max(min(score, 100), 0)
        except:
            return 50.0

    def _calc_volatility_score(self, df: pd.DataFrame) -> float:
        """计算波动得分 (0-100)"""
        try:
            if len(df) < 20:
                return 50.0

            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * 100

            # 适度波动较好
            if 2.0 <= volatility <= 4.0:
                return 80
            elif volatility < 2.0:
                return 60 + volatility * 10
            else:
                return max(80 - (volatility - 4) * 10, 40)
        except:
            return 50.0

    def generate_trading_signal(self, symbol: str) -> Dict[str, Any]:
        """
        生成交易信号

        Args:
            symbol: 股票代码

        Returns:
            交易信号字典
        """
        try:
            df = self.api.get_daily_price(symbol, start_date=None)
            if df is None or df.empty or len(df) < 30:
                return {"signal": "hold", "reason": "数据不足"}

            # 计算综合得分
            scores = self.pick_by_ai_score([symbol], method="comprehensive")
            if not scores:
                return {"signal": "hold", "reason": "无法分析"}

            stock = scores[0]
            score = stock['score']

            # 生成信号
            if score >= 80:
                signal = "strong_buy"
                reason = "AI综合得分极高，多项指标向好"
            elif score >= 65:
                signal = "buy"
                reason = "AI综合得分较高，可以关注"
            elif score >= 50:
                signal = "hold"
                reason = "AI综合得分一般，建议观望"
            elif score >= 35:
                signal = "sell"
                reason = "AI综合得分偏低，谨慎持有"
            else:
                signal = "strong_sell"
                reason = "AI综合得分很低，建议卖出"

            return {
                "signal": signal,
                "score": score,
                "price": stock['price'],
                "factors": stock['factors'],
                "reason": reason,
                "ma5": stock['ma5'],
                "ma20": stock['ma20'],
                "volume_ratio": stock['volume_ratio'],
            }

        except Exception as e:
            logger.error(f"生成交易信号失败: {e}")
            return {"signal": "hold", "reason": f"分析出错: {str(e)}"}


class StrategyPortfolio:
    """策略组合管理"""

    def __init__(self, initial_capital: float = 10000):
        """
        初始化组合

        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}  # 持仓
        self.trade_history = []  # 交易记录
        self.picker = AIStockPicker()

    def add_position(self, symbol: str, weight: float = 0.2):
        """
        添加持仓

        Args:
            symbol: 股票代码
            weight: 仓位权重 (0-1)
        """
        if symbol in self.positions:
            logger.info(f"{symbol} 已在持仓中")
            return

        # 生成交易信号
        signal = self.picker.generate_trading_signal(symbol)

        if signal['signal'].startswith('buy'):
            # 计算买入金额
            available_capital = self.current_capital * weight
            price = signal['price']

            if price > 0 and available_capital > 0:
                shares = int(available_capital / price / 100) * 100  # 按手买入

                if shares > 0:
                    self.positions[symbol] = {
                        'shares': shares,
                        'price': price,
                        'weight': weight,
                        'signal': signal['signal'],
                        'add_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    self.trade_history.append({
                        'symbol': symbol,
                        'action': 'buy',
                        'shares': shares,
                        'price': price,
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'signal': signal['signal']
                    })

                    logger.info(f"买入 {symbol}: {shares} 股 @ {price:.2f}")

        return signal

    def remove_position(self, symbol: str):
        """
        清仓持仓

        Args:
            symbol: 股票代码
        """
        if symbol not in self.positions:
            logger.info(f"{symbol} 不在持仓中")
            return

        position = self.positions[symbol]
        quote = self.picker.api.get_realtime_quote([symbol])

        if symbol in quote:
            current_price = quote[symbol]['close']

            self.trade_history.append({
                'symbol': symbol,
                'action': 'sell',
                'shares': position['shares'],
                'price': current_price,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'profit': (current_price - position['price']) / position['price'] * 100
            })

            del self.positions[symbol]
            logger.info(f"卖出 {symbol} @ {current_price:.2f}")

    def get_portfolio_status(self) -> Dict[str, Any]:
        """获取组合状态"""
        total_value = 0
        positions_info = []

        for symbol, position in self.positions.items():
            quote = self.picker.api.get_realtime_quote([symbol])
            if symbol in quote:
                current_price = quote[symbol]['close']
                market_value = current_price * position['shares']
                profit_pct = (current_price - position['price']) / position['price'] * 100

                total_value += market_value

                positions_info.append({
                    'symbol': symbol,
                    'shares': position['shares'],
                    'cost': position['price'],
                    'current': current_price,
                    'market_value': market_value,
                    'profit_pct': profit_pct,
                    'weight': position['weight']
                })

        return {
            'initial_capital': self.initial_capital,
            'total_value': total_value,
            'positions': positions_info,
            'position_count': len(self.positions),
            'total_profit_pct': (total_value - self.initial_capital) / self.initial_capital * 100 if total_value > 0 else 0
        }

    def rebalance(self, target_weights: Dict[str, float]):
        """
        组合再平衡

        Args:
            target_weights: 目标权重字典
        """
        # 卖出不在目标中的持仓
        for symbol in list(self.positions.keys()):
            if symbol not in target_weights:
                self.remove_position(symbol)

        # 调整现有持仓权重
        for symbol, target_weight in target_weights.items():
            if symbol in self.positions:
                self.positions[symbol]['weight'] = target_weight


if __name__ == "__main__":
    # 测试AI选股
    picker = AIStockPicker()

    print("=" * 60)
    print("AI智能选股测试")
    print("=" * 60)

    # 测试股票池
    test_stocks = [
        "600519", "000001", "300750", "002594",  # 热门股
        "601398", "600036", "601988",  # 银行股
        "300015", "000651", "600276",  # 消费医疗
        "002475", "601012", "300059",  # 科技成长
    ]

    # AI综合评分选股
    results = picker.pick_by_ai_score(test_stocks, method="comprehensive")

    print(f"\n📊 AI评分选股结果 (共 {len(results)} 只):")
    print("-" * 60)

    for i, stock in enumerate(results[:10], 1):
        print(f"{i}. {stock['symbol']:8s} | "
              f"得分: {stock['score']:5.1f} | "
              f"价格: {stock['price']:8.2f} | "
              f"涨跌: {stock['change_pct']:+6.2f}% | "
              f"量比: {stock['volume_ratio']:.2f}")

    print("\n" + "=" * 60)

    # 测试交易信号
    print("\n🎯 交易信号:")
    for stock in results[:5]:
        signal = picker.generate_trading_signal(stock['symbol'])
        print(f"{stock['symbol']}: {signal['signal'].upper():12s} | "
              f"得分: {signal['score']:5.1f} | "
              f"{signal['reason']}")

    print("\n" + "=" * 60)

    # 测试组合管理
    print("\n💼 组合管理测试:")
    portfolio = StrategyPortfolio(initial_capital=10000)

    # 选择前3只股票建仓
    for stock in results[:3]:
        portfolio.add_position(stock['symbol'], weight=0.3)

    status = portfolio.get_portfolio_status()
    print(f"\n📈 组合状态:")
    print(f"  初始资金: ¥{status['initial_capital']:,.0f}")
    print(f"  当前总市值: ¥{status['total_value']:,.0f}")
    print(f"  持仓数量: {status['position_count']} 只")
    print(f"  总体盈亏: {status['total_profit_pct']:+.2f}%")

    if status['positions']:
        print("\n  持仓明细:")
        for pos in status['positions']:
            print(f"    {pos['symbol']:8s}: {pos['shares']:6d} 股 | "
                  f"成本 ¥{pos['cost']:.2f} | "
                  f"现价 ¥{pos['current']:.2f} | "
                  f"盈亏 {pos['profit_pct']:+.2f}%")
