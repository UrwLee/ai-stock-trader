#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI选股示例 - 简化版
可以直接运行的演示
"""

import os
import sys

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 导入模块
from src.strategies.ai_stock_picker import AIStockPicker
from src.utils.risk_manager import RiskManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def demo_ai_picker():
    """演示AI选股"""
    print("\n" + "=" * 70)
    print("🤖 AI智能选股演示")
    print("=" * 70)
    
    # 创建AI选股器
    picker = AIStockPicker()
    
    # 候选股票池
    stock_pool = [
        "600519",  # 贵州茅台
        "000001",  # 平安银行
        "300750",  # 宁德时代
        "002594",  # 比亚迪
        "300015",  # 爱尔眼科
        "000651",  # 格力电器
        "600276",  # 恒瑞医药
        "002475",  # 立讯精密
        "601012",  # 隆基绿能
        "300059",  # 东方财富
    ]
    
    print(f"\n📊 候选股票: {len(stock_pool)} 只")
    print("🎯 AI综合评分选股中...")
    
    # AI综合评分选股
    results = picker.pick_by_ai_score(stock_pool, method="comprehensive")
    
    print(f"\n✅ 选股完成 (符合条件: {len(results)} 只)")
    print("-" * 70)
    
    # 显示TOP 5
    if results:
        print("\n📈 TOP 5 评分股票:")
        for i, stock in enumerate(results[:5], 1):
            print(f"{i}. {stock['symbol']:8s} | "
                  f"得分: {stock['score']:5.1f} | "
                  f"价格: ¥{stock['price']:8.2f} | "
                  f"涨跌: {stock['change_pct']:+6.2f}%")
        
        # 显示因子详情
        print("\n📊 因子分析:")
        for i, stock in enumerate(results[:3], 1):
            f = stock['factors']
            print(f"\n{i}. {stock['symbol']} (综合: {stock['score']:.1f})")
            print(f"   动量 {f['momentum']:.1f} | 趋势 {f['trend']:.1f} | "
                  f"量能 {f['volume']:.1f} | 波动 {f['volatility']:.1f}")
        
        # 生成交易信号
        print("\n" + "=" * 70)
        print("🎯 交易信号")
        print("=" * 70)
        
        for stock in results[:3]:
            signal = picker.generate_trading_signal(stock['symbol'])
            emoji = "🟢" if signal['signal'].startswith('buy') else ("🔴" if signal['signal'].startswith('sell') else "🟡")
            print(f"\n{emoji} {stock['symbol']}: {signal['signal'].upper():12s} "
                  f"(得分: {signal['score']:5.1f})")
            print(f"   原因: {signal['reason']}")
            print(f"   当前价: ¥{signal['price']:.2f}")


def demo_portfolio():
    """演示组合管理"""
    print("\n" + "=" * 70)
    print("💼 组合管理演示")
    print("=" * 70)
    
    # 创建风险管理器
    risk_manager = RiskManager(
        initial_capital=10000,
        max_position_weight=0.3,
        stop_loss_ratio=0.1,
        take_profit_ratio=0.2
    )
    
    print(f"\n📊 初始资金: ¥10,000")
    print(f"🛡️ 止损线: -10%")
    print(f"🎯 止盈线: +20%")
    print(f"📦 最大持仓: 5 只")
    
    # 模拟添加持仓
    test_positions = [
        ("600519", 100, 1500.0),
        ("000001", 500, 11.0),
    ]
    
    print(f"\n📋 模拟持仓:")
    for symbol, shares, price in test_positions:
        risk_manager.add_position(symbol, shares, price)
        print(f"   ✓ {symbol}: {shares} 股 @ ¥{price:.2f}")
    
    # 获取状态
    status = risk_manager.get_portfolio_status(current_value=10500)
    
    print(f"\n📈 当前状态:")
    print(f"   总市值: ¥{status['current_value']:,.0f}")
    print(f"   收益率: {status['total_return']:+.2f}%")
    print(f"   持仓数: {status['position_count']} 只")
    print(f"   风险等级: {status['risk_level']}")


def demo_technical():
    """演示技术指标"""
    print("\n" + "=" * 70)
    print("📊 技术指标演示")
    print("=" * 70)
    
    from src.utils.technical_analysis import TechnicalAnalyzer
    from src.data.stock_api import StockDataAPI
    
    api = StockDataAPI(data_source="sina")
    analyzer = TechnicalAnalyzer()
    
    test_symbols = ["600519", "000001", "300750"]
    
    print(f"\n📈 技术指标分析:")
    for symbol in test_symbols:
        df = api.get_daily_price(symbol, start_date=None)
        if df is not None and not df.empty and len(df) >= 30:
            indicators = analyzer.calculate_indicators(df)
            trend_emoji = "📈" if indicators.trend.value == "uptrend" else ("📉" if indicators.trend.value == "downtrend" else "➡️")
            print(f"\n{symbol}:")
            print(f"   趋势: {trend_emoji} {indicators.trend.value}")
            print(f"   MA5/MA20: ¥{indicators.ma5:.2f} / ¥{indicators.ma20:.2f}")
            print(f"   RSI12: {indicators.rsi12:.1f}")
            print(f"   综合评分: {indicators.score}/100")
        else:
            print(f"\n{symbol}: 数据不足，无法分析")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🤖 AI Stock Trader - 功能演示")
    print("=" * 70)
    print(f"\n📁 项目路径: {PROJECT_ROOT}")
    
    try:
        # 1. AI选股演示
        demo_ai_picker()
        
        # 2. 组合管理演示
        demo_portfolio()
        
        # 3. 技术指标演示
        demo_technical()
        
        print("\n" + "=" * 70)
        print("✅ 演示完成!")
        print("=" * 70)
        
        print("\n📝 下一步:")
        print("   1. 运行主程序: python3 run.py")
        print("   2. 查看文档: README.md")
        print("   3. 扩展功能: 添加工商银行、证券股等")
        
    except Exception as e:
        logger.error(f"演示失败: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
