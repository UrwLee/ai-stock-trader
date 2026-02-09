#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理模块
提供止损止盈、仓位控制、风险评估等功能
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger

logger = setup_logger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class RiskMetrics:
    """风险指标"""
    # 收益指标
    total_return: float = 0.0  # 总收益率
    annual_return: float = 0.0  # 年化收益率
    
    # 风险指标
    volatility: float = 0.0  # 波动率
    max_drawdown: float = 0.0  # 最大回撤
    var_95: float = 0.0  # 95% VaR
    
    # 风险收益比
    sharpe_ratio: float = 0.0  # 夏普比率
    sortino_ratio: float = 0.0  # 索提诺比率
    calmar_ratio: float = 0.0  # 卡玛比率
    
    # 风险等级
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    # 详细信息
    position_count: int = 0  # 持仓数量
    cash_ratio: float = 0.0  # 现金比例
    concentration: float = 0.0  # 集中度


class RiskManager:
    """风险管理器"""
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 max_position_weight: float = 0.3,
                 stop_loss_ratio: float = 0.1,
                 take_profit_ratio: float = 0.2,
                 max_drawdown_limit: float = 0.15,
                 max_position_count: int = 5):
        """
        初始化风险管理器
        
        Args:
            initial_capital: 初始资金
            max_position_weight: 单只股票最大仓位比例
            stop_loss_ratio: 止损比例
            take_profit_ratio: 止盈比例
            max_drawdown_limit: 最大回撤限制
            max_position_count: 最大持仓数量
        """
        self.initial_capital = initial_capital
        self.max_position_weight = max_position_weight
        self.stop_loss_ratio = stop_loss_ratio
        self.take_profit_ratio = take_profit_ratio
        self.max_drawdown_limit = max_drawdown_limit
        self.max_position_count = max_position_count
        
        # 风险统计
        self.positions = {}  # 当前持仓
        self.trade_history = []  # 交易历史
        self.equity_curve = []  # 权益曲线
        
    def calculate_position_size(self, 
                               symbol: str,
                               price: float,
                               available_capital: float,
                               risk_per_trade: float = 0.02) -> int:
        """
        计算仓位大小
        
        Args:
            symbol: 股票代码
            price: 当前价格
            available_capital: 可用资金
            risk_per_trade: 每笔交易风险比例
            
        Returns:
            买入股数
        """
        try:
            # 计算可承受风险金额
            risk_amount = available_capital * risk_per_trade
            
            # 计算止损价位
            stop_loss_price = price * (1 - self.stop_loss_ratio)
            risk_per_share = price - stop_loss_price
            
            if risk_per_share <= 0:
                logger.warning(f"{symbol}: 止损价计算异常")
                return 0
            
            # 计算股数
            shares = int(risk_amount / risk_per_share / 100) * 100
            
            # 检查是否超过最大仓位
            max_shares = int(available_capital * self.max_position_weight / price / 100) * 100
            shares = min(shares, max_shares)
            
            logger.info(f"{symbol}: 建议买入 {shares} 股 (@ ¥{price:.2f})")
            return shares
            
        except Exception as e:
            logger.error(f"计算仓位失败: {e}")
            return 0
    
    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        检查是否触发止损
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            
        Returns:
            是否触发止损
        """
        if symbol not in self.positions:
            return False
            
        position = self.positions[symbol]
        cost_price = position['cost_price']
        stop_loss_price = cost_price * (1 - self.stop_loss_ratio)
        
        if current_price <= stop_loss_price:
            logger.warning(f"🚨 {symbol} 触发止损: 当前 ¥{current_price:.2f} < 止损 ¥{stop_loss_price:.2f}")
            return True
            
        return False
    
    def check_take_profit(self, symbol: str, current_price: float) -> bool:
        """
        检查是否触发止盈
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            
        Returns:
            是否触发止盈
        """
        if symbol not in self.positions:
            return False
            
        position = self.positions[symbol]
        cost_price = position['cost_price']
        take_profit_price = cost_price * (1 + self.take_profit_ratio)
        
        if current_price >= take_profit_price:
            logger.info(f"🎯 {symbol} 触发止盈: 当前 ¥{current_price:.2f} >= 止盈 ¥{take_profit_price:.2f}")
            return True
            
        return False
    
    def can_open_position(self, symbol: str, proposed_weight: float) -> tuple:
        """
        检查是否可以开仓
        
        Args:
            symbol: 股票代码
            proposed_weight: 拟买入金额/总资产比例
            
        Returns:
            (是否可以, 原因)
        """
        # 检查是否已有持仓
        if symbol in self.positions:
            return False, f"已在持仓中"
        
        # 检查持仓数量
        if len(self.positions) >= self.max_position_count:
            return False, f"持仓数量已达上限 ({self.max_position_count})"
        
        # 检查仓位比例
        total_weight = self._get_total_weight()
        if total_weight + proposed_weight > self.max_position_weight * self.max_position_count:
            return False, f"仓位比例过高"
        
        return True, "可以开仓"
    
    def _get_total_weight(self) -> float:
        """计算当前总仓位比例"""
        return sum(pos['weight'] for pos in self.positions.values())
    
    def add_position(self, 
                    symbol: str, 
                    shares: int, 
                    price: float, 
                    target_weight: float = 0.2):
        """
        添加持仓
        
        Args:
            symbol: 股票代码
            shares: 股数
            price: 买入价格
            target_weight: 目标仓位比例
        """
        if shares <= 0 or price <= 0:
            logger.warning(f"无效的持仓参数: {symbol}")
            return
        
        self.positions[symbol] = {
            'shares': shares,
            'cost_price': price,
            'target_weight': target_weight,
            'add_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"➕ 添加持仓: {symbol} - {shares} 股 @ ¥{price:.2f}")
    
    def remove_position(self, symbol: str, sell_price: float):
        """
        清仓
        
        Args:
            symbol: 股票代码
            sell_price: 卖出价格
        """
        if symbol not in self.positions:
            logger.warning(f"不在持仓中: {symbol}")
            return
        
        position = self.positions[symbol]
        cost_price = position['cost_price']
        shares = position['shares']
        
        profit_pct = (sell_price - cost_price) / cost_price * 100
        
        # 记录交易
        self.trade_history.append({
            'symbol': symbol,
            'shares': shares,
            'buy_price': cost_price,
            'sell_price': sell_price,
            'profit_pct': profit_pct,
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # 删除持仓
        del self.positions[symbol]
        
        logger.info(f"➖ 清仓: {symbol} - 卖出 @ ¥{sell_price:.2f} (盈亏: {profit_pct:+.2f}%)")
    
    def calculate_risk_metrics(self, current_value: float) -> RiskMetrics:
        """
        计算风险指标
        
        Args:
            current_value: 当前总资产
            
        Returns:
            RiskMetrics 对象
        """
        metrics = RiskMetrics()
        
        # 计算收益率
        metrics.total_return = (current_value - self.initial_capital) / self.initial_capital * 100
        
        # 计算持仓统计
        metrics.position_count = len(self.positions)
        
        if self.positions:
            # 计算现金比例
            if current_value > 0:
                metrics.cash_ratio = (current_value - sum(
                    p['shares'] * p['cost_price'] for p in self.positions.values()
                )) / current_value
            
            # 计算集中度（最大仓位）
            if current_value > 0:
                weights = [p['target_weight'] for p in self.positions.values()]
                metrics.concentration = max(weights) if weights else 0
        else:
            metrics.cash_ratio = 1.0
            metrics.concentration = 0
        
        # 计算最大回撤（简化版）
        if len(self.equity_curve) > 1:
            equity = [e['value'] for e in self.equity_curve]
            peak = max(equity)
            drawdown = (peak - equity[-1]) / peak * 100 if peak > 0 else 0
            metrics.max_drawdown = drawdown
        
        # 评估风险等级
        metrics.risk_level = self._assess_risk_level(metrics)
        
        return metrics
    
    def _assess_risk_level(self, metrics: RiskMetrics) -> RiskLevel:
        """评估风险等级"""
        if metrics.max_drawdown > 20:
            return RiskLevel.EXTREME
        elif metrics.max_drawdown > 10 or metrics.concentration > 0.4:
            return RiskLevel.HIGH
        elif metrics.max_drawdown > 5 or metrics.concentration > 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_portfolio_status(self, current_value: float) -> Dict[str, Any]:
        """
        获取组合状态
        
        Args:
            current_value: 当前总资产
            
        Returns:
            组合状态字典
        """
        metrics = self.calculate_risk_metrics(current_value)
        
        positions_info = []
        for symbol, position in self.positions.items():
            market_value = position['shares'] * position['cost_price']
            positions_info.append({
                'symbol': symbol,
                'shares': position['shares'],
                'cost': position['cost_price'],
                'market_value': market_value,
                'weight': market_value / current_value * 100 if current_value > 0 else 0,
                'target_weight': position['target_weight']
            })
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': current_value,
            'total_return': metrics.total_return,
            'positions': positions_info,
            'position_count': metrics.position_count,
            'cash_ratio': metrics.cash_ratio,
            'max_drawdown': metrics.max_drawdown,
            'risk_level': metrics.risk_level.value,
            'trade_count': len(self.trade_history),
            'win_rate': self._calculate_win_rate()
        }
    
    def _calculate_win_rate(self) -> float:
        """计算胜率"""
        if not self.trade_history:
            return 0.0
        
        wins = sum(1 for t in self.trade_history if t['profit_pct'] > 0)
        return wins / len(self.trade_history) * 100
    
    def should_stop_trading(self, current_value: float) -> tuple:
        """
        检查是否应该停止交易
        
        Args:
            current_value: 当前资产
            
        Returns:
            (是否停止, 原因)
        """
        # 检查是否触发最大回撤
        if self.initial_capital > 0:
            drawdown = (self.initial_capital - current_value) / self.initial_capital
            if drawdown >= self.max_drawdown_limit:
                return True, f"触发最大回撤限制 ({drawdown*100:.1f}%)"
        
        # 检查连续亏损
        if len(self.trade_history) >= 3:
            recent_trades = self.trade_history[-3:]
            if all(t['profit_pct'] < 0 for t in recent_trades):
                return True, "连续3笔亏损"
        
        return False, ""


class PositionSizer:
    """仓位管理器"""
    
    def __init__(self, total_capital: float, risk_manager: RiskManager):
        self.total_capital = total_capital
        self.risk_manager = risk_manager
    
    def calculate_allocation(self, 
                           symbols: List[str],
                           scores: Dict[str, float],
                           prices: Dict[str, float]) -> Dict[str, int]:
        """
        计算资金分配
        
        Args:
            symbols: 候选股票列表
            scores: 股票得分
            prices: 股票价格
            
        Returns:
            建议买入股数字典
        """
        # 按得分排序
        sorted_symbols = sorted(symbols, key=lambda x: scores.get(x, 0), reverse=True)
        
        # 选择前N只
        top_n = min(len(sorted_symbols), self.risk_manager.max_position_count)
        selected = sorted_symbols[:top_n]
        
        # 计算权重（按得分加权）
        total_score = sum(scores.get(s, 0) for s in selected)
        allocations = {}
        
        for symbol in selected:
            score = scores.get(symbol, 0)
            weight = score / total_score if total_score > 0 else 1 / len(selected)
            
            # 计算买入股数
            allocation_capital = self.total_capital * weight
            shares = self.risk_manager.calculate_position_size(
                symbol, 
                prices.get(symbol, 0), 
                allocation_capital
            )
            
            if shares > 0:
                allocations[symbol] = shares
        
        return allocations


if __name__ == "__main__":
    print("=" * 60)
    print("风险管理模块测试")
    print("=" * 60)
    
    # 创建风险管理器
    risk_manager = RiskManager(
        initial_capital=10000,
        max_position_weight=0.3,
        stop_loss_ratio=0.1,
        take_profit_ratio=0.2
    )
    
    # 测试开仓检查
    can_open, reason = risk_manager.can_open_position("600519", 0.2)
    print(f"\n开仓检查 600519 (20%): {can_open} - {reason}")
    
    # 测试仓位计算
    shares = risk_manager.calculate_position_size(
        "600519", 
        price=1800.0, 
        available_capital=10000
    )
    print(f"\n仓位计算 600519 (¥1800): 建议买入 {shares} 股")
    
    # 添加测试持仓
    risk_manager.add_position("600519", shares=100, price=1800.0)
    risk_manager.add_position("000001", shares=500, price=12.0)
    
    # 模拟价格更新
    risk_manager.equity_curve.append({
        'date': datetime.now().strftime("%Y-%m-%d"),
        'value': 10000 + 500 + 500  # 简化计算
    })
    
    # 获取组合状态
    status = risk_manager.get_portfolio_status(current_value=11500)
    
    print(f"\n📊 组合状态:")
    print(f"  初始资金: ¥{status['initial_capital']:,.0f}")
    print(f"  当前价值: ¥{status['current_value']:,.0f}")
    print(f"  总收益: {status['total_return']:+.2f}%")
    print(f"  持仓数量: {status['position_count']}")
    print(f"  风险等级: {status['risk_level']}")
    print(f"  胜率: {status['win_rate']:.1f}%")
    
    # 检查止损
    print(f"\n🚨 止损检查:")
    if risk_manager.check_stop_loss("600519", 1600.0):
        print("  600519 触发止损!")
    else:
        print("  600519 未触发止损")
    
    # 组合状态
    if status['positions']:
        print(f"\n📈 持仓明细:")
        for pos in status['positions']:
            print(f"  {pos['symbol']:8s}: {pos['shares']:6d} 股 | "
                  f"成本 ¥{pos['cost']:.2f} | "
                  f"市值 ¥{pos['market_value']:,.0f} | "
                  f"权重 {pos['weight']:.1f}%")
    
    print("\n" + "=" * 60)
