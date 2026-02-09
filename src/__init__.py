# src/__init__.py
"""
量化交易系统 - 核心代码
"""

__version__ = "1.0.0"
__author__ = "丁明旭"

from .data.stock_api import StockDataAPI, StockScreener
from .strategies.ai_stock_picker import AIStockPicker, StrategyPortfolio
from .utils.technical_analysis import TechnicalAnalyzer, TechnicalIndicators, TrendType, SignalType

__all__ = [
    'StockDataAPI',
    'StockScreener',
    'AIStockPicker',
    'StrategyPortfolio',
    'TechnicalAnalyzer',
    'TechnicalIndicators',
    'TrendType',
    'SignalType',
]
