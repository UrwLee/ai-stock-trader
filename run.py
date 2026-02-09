#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Stock Trader - 运行脚本
快速启动量化交易系统
"""

import os
import sys

# 添加项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.strategies.ai_stock_picker import AIStockPicker
from src.utils.risk_manager import RiskManager
from src.data.stock_api import StockDataAPI
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🤖 AI Stock Trader - 智能量化交易系统")
    print("=" * 70)
    print("\n📁 项目路径:", PROJECT_ROOT)
    print("🐍 Python 版本:", sys.version.split()[0])
    
    try:
        # 创建API实例
        api = StockDataAPI(data_source="sina")
        print("\n✅ 股票数据接口初始化成功")
        
        # 测试获取股票列表
        stocks = api.get_stock_list()
        print(f"✅ 股票列表获取成功 ({len(stocks)} 只)")
        
        # 测试获取实时行情
        test_symbols = ["600519", "000001", "300750"]
        quotes = api.get_realtime_quote(test_symbols)
        print(f"✅ 实时行情获取成功 ({len(quotes)} 只)")
        
        print("\n📊 测试结果:")
        for symbol, quote in quotes.items():
            print(f"  {symbol}: ¥{quote['close']:.2f} ({quote['change_pct']:+.2f}%)")
        
        print("\n" + "=" * 70)
        print("🎉 环境配置成功！")
        print("=" * 70)
        
        # 显示下一步
        print("\n📝 下一步操作:")
        print("  1. 运行完整示例: python3 examples/demo.py")
        print("  2. 查看项目文档: README.md")
        print("  3. 配置API密钥: cp .env.example .env")
        print("\n💡 提示: 当前使用免费新浪接口，无需配置即可获取基础数据")
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
