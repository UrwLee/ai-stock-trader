#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
均线交叉策略示例
演示如何在系统中实现简单的技术分析策略
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.stock_api import StockDataAPI
from utils.technical_analysis import TechnicalAnalyzer, SignalType
from utils.risk_manager import RiskManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MovingAverageStrategy:
    """
    均线交叉策略
    
    策略逻辑：
    - 金叉（MA5上穿MA20） -> 买入信号
    - 死叉（MA5下穿MA20） -> 卖出信号
    """
    
    def __init__(self, 
                 stock_api: StockDataAPI,
                 short_ma: int = 5,
                 long_ma: int = 20):
        """
        初始化均线策略
        
        Args:
            stock_api: 股票数据API
            short_ma: 短期均线天数
            long_ma: 长期均线天数
        """
        self.api = stock_api
        self.short_ma = short_ma
        self.long_ma = long_ma
        self.analyzer = TechnicalAnalyzer()
        
        # 持仓状态
        self.position = None  # None, 'long'
        
    def generate_signal(self, symbol: str) -> Dict[str, Any]:
        """
        生成交易信号
        
        Args:
            symbol: 股票代码
            
        Returns:
            信号字典
        """
        try:
            # 获取历史数据
            df = self.api.get_daily_price(symbol, start_date=None)
            if df is None or df.empty or len(df) < self.long_ma + 5:
                return {"signal": SignalType.HOLD, "reason": "数据不足"}
            
            # 计算均线
            df['ma_short'] = df['close'].rolling(window=self.short_ma).mean()
            df['ma_long'] = df['close'].rolling(window=self.long_ma).mean()
            
            # 最新数据
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # 判断均线状态
            ma_short_above = latest['ma_short'] > latest['ma_long']
            prev_short_above = prev['ma_short'] > prev['ma_long']
            
            # 生成信号
            if ma_short_above and not prev_short_above:
                # 金叉
                if self.position is None or self.position != 'long':
                    self.position = 'long'
                    return {
                        "signal": SignalType.BUY,
                        "reason": f"MA{self.short_ma}金叉MA{self.long_ma}",
                        "price": latest['close'],
                        "ma_short": latest['ma_short'],
                        "ma_long": latest['ma_long']
                    }
                    
            elif not ma_short_above and prev_short_above:
                # 死叉
                if self.position == 'long':
                    self.position = None
                    return {
                        "signal": SignalType.SELL,
                        "reason": f"MA{self.short_ma}死叉MA{self.long_ma}",
                        "price": latest['close'],
                        "ma_short": latest['ma_short'],
                        "ma_long": latest['ma_long']
                    }
            
            return {
                "signal": SignalType.HOLD,
                "reason": "无交叉信号",
                "price": latest['close'],
                "ma_short": latest['ma_short'],
                "ma_long": latest['ma_long']
            }
            
        except Exception as e:
            logger.error(f"生成信号失败: {e}")
            return {"signal": SignalType.HOLD, "reason": str(e)}


class DualMAStrategy(MovingAverageStrategy):
    """
    双均线策略增强版
    增加过滤条件和仓位管理
    """
    
    def __init__(self, 
                 stock_api: StockDataAPI,
                 short_ma: int = 5,
                 long_ma: int = 20,
                 risk_manager: RiskManager = None):
        """
        初始化增强版均线策略
        
        Args:
            stock_api: 股票数据API
            short_ma: 短期均线天数
            long_ma: 长期均线天数
            risk_manager: 风险管理器
        """
        super().__init__(stock_api, short_ma, long_ma)
        self.risk_manager = risk_manager
        
    def filter_by_trend(self, df: pd.DataFrame) -> bool:
        """
        趋势过滤：只在多头市场中做多
        
        Args:
            df: 价格数据
            
        Returns:
            是否符合趋势条件
        """
        if len(df) < 60:
            return True
            
        # 计算长期均线
        ma60 = df['close'].rolling(window=60).mean()
        current_price = df['close'].iloc[-1]
        ma60_value = ma60.iloc[-1]
        
        # 只在价格高于MA60时做多
        return current_price > ma60_value
    
    def filter_by_volatility(self, df: pd.DataFrame) -> bool:
        """
        波动过滤：避开波动过大的股票
        
        Args:
            df: 价格数据
            
        Returns:
            是否符合波动条件
        """
        if len(df) < 20:
            return True
            
        # 计算波动率
        returns = df['close'].pct_change()
        volatility = returns.std() * 100
        
        # 波动率过高时不交易
        return volatility < 5.0
    
    def generate_signal(self, symbol: str) -> Dict[str, Any]:
        """
        生成交易信号（增强版）
        
        Args:
            symbol: 股票代码
            
        Returns:
            信号字典
        """
        try:
            # 获取数据
            df = self.api.get_daily_price(symbol, start_date=None)
            if df is None or df.empty or len(df) < self.long_ma + 5:
                return {"signal": SignalType.HOLD, "reason": "数据不足"}
            
            # 应用过滤器
            if not self.filter_by_trend(df):
                return {"signal": SignalType.HOLD, "reason": "不符合趋势条件"}
            
            if not self.filter_by_volatility(df):
                return {"signal": SignalType.HOLD, "reason": "波动过大"}
            
            # 调用父类方法生成信号
            return super().generate_signal(symbol)
            
        except Exception as e:
            logger.error(f"生成信号失败: {e}")
            return {"signal": SignalType.HOLD, "reason": str(e)}


class MultiTimeframeStrategy:
    """
    多周期均线策略
    
    结合日线和周线信号
    """
    
    def __init__(self, stock_api: StockDataAPI):
        self.api = stock_api
        self.analyzer = TechnicalAnalyzer()
        
    def generate_signal(self, symbol: str) -> Dict[str, Any]:
        """
        生成交易信号
        
        Args:
            symbol: 股票代码
            
        Returns:
            信号字典
        """
        # 获取日线信号
        daily_signal = self.analyzer.generate_signal(
            self.api.get_daily_price(symbol, start_date=None)
        )
        
        # 综合判断
        if daily_signal['signal'] == SignalType.STRONG_BUY:
            return {
                "signal": SignalType.BUY,
                "reason": "日线技术面强势",
                "details": daily_signal['details']
            }
        elif daily_signal['signal'] == SignalType.BUY:
            return {
                "signal": SignalType.HOLD,
                "reason": "日线偏多，但需等待确认",
                "details": daily_signal['details']
            }
        else:
            return {
                "signal": SignalType.HOLD,
                "reason": "技术面不支持",
                "details": daily_signal['details']
            }


# 回测框架
class BacktestEngine:
    """
    简单的回测引擎
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 commission: float = 0.001):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission: 手续费率
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.cash = initial_capital
        self.position = 0  # 持仓股数
        self.trades = []  # 交易记录
        
    def run(self, 
            strategy, 
            symbol: str,
            prices: pd.DataFrame) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            strategy: 策略对象
            symbol: 股票代码
            prices: 价格数据（DataFrame，需要包含trade_date, close列）
            
        Returns:
            回测结果
        """
        # 简化回测（实际应该逐日模拟）
        for i, row in prices.iterrows():
            signal = strategy.generate_signal(symbol)
            
            if signal['signal'] == SignalType.BUY and self.position == 0:
                # 买入
                shares = int(self.cash / row['close'] / 100) * 100
                cost = shares * row['close'] * (1 + self.commission)
                
                if shares > 0 and cost <= self.cash:
                    self.position = shares
                    self.cash -= cost
                    
                    self.trades.append({
                        'date': row['trade_date'],
                        'action': 'BUY',
                        'shares': shares,
                        'price': row['close'],
                        'cost': cost
                    })
                    
            elif signal['signal'] == SignalType.SELL and self.position > 0:
                # 卖出
                revenue = self.position * row['close'] * (1 - self.commission)
                
                self.trades.append({
                    'date': row['trade_date'],
                    'action': 'SELL',
                    'shares': self.position,
                    'price': row['close'],
                    'revenue': revenue
                })
                
                self.cash += revenue
                self.position = 0
        
        # 计算最终收益
        final_value = self.cash + self.position * prices.iloc[-1]['close']
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'trades': self.trades,
            'trade_count': len(self.trades)
        }


if __name__ == "__main__":
    print("=" * 60)
    print("均线策略示例")
    print("=" * 60)
    
    # 创建API
    api = StockDataAPI(data_source="sina")
    
    # 测试均线策略
    strategy = MovingAverageStrategy(api, short_ma=5, long_ma=20)
    
    test_symbols = ["600519", "000001", "300750"]
    
    print("\n📊 均线交叉信号:")
    for symbol in test_symbols:
        signal = strategy.generate_signal(symbol)
        print(f"\n{symbol}:")
        print(f"  信号: {signal['signal'].value}")
        print(f"  价格: ¥{signal.get('price', 'N/A'):.2f}" if isinstance(signal.get('price'), float) else f"  价格: {signal.get('price', 'N/A')}")
        print(f"  MA5:  ¥{signal.get('ma_short', 'N/A'):.2f}" if isinstance(signal.get('ma_short'), float) else f"  MA5:  {signal.get('ma_short', 'N/A')}")
        print(f"  MA20: ¥{signal.get('ma_long', 'N/A'):.2f}" if isinstance(signal.get('ma_long'), float) else f"  MA20: {signal.get('ma_long', 'N/A')}")
        print(f"  原因: {signal['reason']}")
    
    print("\n" + "=" * 60)
    print("策略说明:")
    print("  • 金叉(MA5上穿MA20) -> 买入")
    print("  • 死叉(MA5下穿MA20) -> 卖出")
    print("  • 需要至少20天历史数据")
    print("=" * 60)
