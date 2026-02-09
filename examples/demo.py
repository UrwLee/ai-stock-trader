#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI选股示例
演示如何使用AI评分系统进行股票筛选
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.ai_stock_picker import AIStockPicker
from utils.risk_manager import RiskManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


def demo_ai_picker():
    """演示AI选股"""
    print("=" * 70)
    print("AI智能选股演示")
    print("=" * 70)
    
    # 创建AI选股器
    picker = AIStockPicker()
    
    # 候选股票池（可以替换为你自己的选股范围）
    stock_pool = [
        # 热门股
        "600519", "000001", "300750", "002594", "300015", "000651", 
        "600276", "002475", "601012", "600030", "300059",
        # 银行股
        "601398", "600036", "601988", "600000",
        # 券商股
        "600837", "600999", "601066",
        # 医药股
        "600436", "600276", "000513",
        # 科技股
        "002410", "300033", "300368",
    ]
    
    # AI综合评分选股
    print("\n🎯 AI综合评分选股...")
    results = picker.pick_by_ai_score(stock_pool, method="comprehensive")
    
    print(f"\n📊 选股结果 (共 {len(results)} 只满足条件)")
    print("-" * 70)
    
    # 显示TOP 10
    for i, stock in enumerate(results[:10], 1):
        print(f"{i:2d}. {stock['symbol']:8s} | "
              f"得分: {stock['score']:5.1f} | "
              f"价格: ¥{stock['price']:8.2f} | "
              f"涨跌: {stock['change_pct']:+6.2f}%")
    
    print("-" * 70)
    
    # 显示因子详情（TOP 5）
    if len(results) >= 1:
        print("\n📈 因子分析详情 (TOP 5):")
        for i, stock in enumerate(results[:5], 1):
            factors = stock['factors']
            print(f"\n{i}. {stock['symbol']} (得分: {stock['score']:.1f})")
            print(f"   动量: {factors['momentum']:.1f} | "
                  f"趋势: {factors['trend']:.1f} | "
                  f"量能: {factors['volume']:.1f} | "
                  f"波动: {factors['volatility']:.1f}")
    
    # 生成交易信号
    print("\n" + "=" * 70)
    print("🎯 交易信号")
    print("=" * 70)
    
    for stock in results[:5]:
        signal = picker.generate_trading_signal(stock['symbol'])
        print(f"\n{stock['symbol']}: {signal['signal'].upper():12s} "
              f"(得分: {signal['score']:5.1f})")
        print(f"   原因: {signal['reason']}")
        print(f"   当前价: ¥{signal['price']:.2f}")
        print(f"   MA5/MA20: {signal['ma5']:.2f} / {signal['ma20']:.2f}")
        print(f"   量比: {signal['volume_ratio']:.2f}")


def demo_portfolio_management():
    """演示组合管理"""
    print("\n" + "=" * 70)
    print("💼 组合管理演示")
    print("=" * 70)
    
    # 创建AI选股器
    picker = AIStockPicker()
    
    # 创建组合
    portfolio = picker.pick_by_ai_score([
        "600519", "000001", "300750", "002594", "300015"
    ], method="comprehensive")
    
    # 创建风险管理器
    risk_manager = RiskManager(
        initial_capital=10000,
        max_position_weight=0.3,
        stop_loss_ratio=0.1,
        take_profit_ratio=0.2
    )
    
    # 选择TOP 3建仓
    print("\n📈 建立组合:")
    for stock in portfolio[:3]:
        # 检查是否可以开仓
        can_open, reason = risk_manager.can_open_position(stock['symbol'], 0.2)
        if can_open:
            # 获取交易信号
            signal = picker.generate_trading_signal(stock['symbol'])
            if signal['signal'].startswith('buy'):
                # 计算仓位
                shares = risk_manager.calculate_position_size(
                    stock['symbol'],
                    signal['price'],
                    10000 * 0.3
                )
                
                # 添加持仓
                risk_manager.add_position(
                    stock['symbol'],
                    shares,
                    signal['price']
                )
    
    # 获取组合状态
    status = risk_manager.get_portfolio_status(current_value=10500)
    
    print(f"\n📊 组合状态:")
    print(f"  初始资金: ¥{status['initial_capital']:,.0f}")
    print(f"  当前价值: ¥{status['current_value']:,.0f}")
    print(f"  总收益: {status['total_return']:+.2f}%")
    print(f"  持仓数量: {status['position_count']}")
    print(f"  风险等级: {status['risk_level']}")
    
    if status['positions']:
        print(f"\n📋 持仓明细:")
        for pos in status['positions']:
            print(f"  {pos['symbol']:8s}: {pos['shares']:6d} 股 | "
                  f"成本 ¥{pos['cost']:.2f} | "
                  f"权重 {pos['weight']:.1f}%")


def demo_moving_average_strategy():
    """演示均线策略"""
    print("\n" + "=" * 70)
    print("📈 均线策略演示")
    print("=" * 70)
    
    from strategies.moving_average_strategy import MovingAverageStrategy
    from data.stock_api import StockDataAPI
    
    api = StockDataAPI(data_source="sina")
    strategy = MovingAverageStrategy(api, short_ma=5, long_ma=20)
    
    test_symbols = ["600519", "000001", "300750"]
    
    print("\n🎯 均线交叉信号:")
    for symbol in test_symbols:
        signal = strategy.generate_signal(symbol)
        print(f"\n{symbol}:")
        print(f"  信号: {signal['signal'].value}")
        print(f"  价格: ¥{signal.get('price', 'N/A'):.2f}" if isinstance(signal.get('price'), float) else f"  价格: {signal.get('price', 'N/A')}")
        print(f"  原因: {signal['reason']}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🤖 AI Stock Trader - 功能演示")
    print("=" * 70)
    
    try:
        # 1. AI选股演示
        demo_ai_picker()
        
        # 2. 组合管理演示
        demo_portfolio_management()
        
        # 3. 均线策略演示
        demo_moving_average_strategy()
        
        print("\n" + "=" * 70)
        print("✅ 演示完成!")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
