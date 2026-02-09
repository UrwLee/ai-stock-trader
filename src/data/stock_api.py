#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据获取模块
支持多种数据源：Tushare、免费新浪接口
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import requests
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger

logger = setup_logger(__name__)


class StockDataAPI:
    """股票数据统一接口"""

    def __init__(self, data_source: str = "sina"):
        """
        初始化股票数据接口

        Args:
            data_source: 数据源 ('sina', 'tushare')
        """
        self.data_source = data_source
        self.cache = {}

        if data_source == "tushare":
            self._init_tushare()
        else:
            logger.info(f"使用新浪免费接口获取股票数据")

    def _init_tushare(self):
        """初始化Tushare接口"""
        try:
            import tushare as ts
            token = os.getenv("TUSHARE_TOKEN")
            if token:
                self.pro = ts.pro_api(token)
                logger.info("Tushare 初始化成功")
            else:
                logger.warning("未配置 TUSHARE_TOKEN，将使用免费接口")
                self.data_source = "sina"
        except ImportError:
            logger.warning("Tushare 未安装，将使用免费接口")
            self.data_source = "sina"

    def get_stock_list(self, market: str = "all") -> pd.DataFrame:
        """
        获取股票列表

        Args:
            market: 市场类型 ('all', 'sh', 'sz')

        Returns:
            股票列表 DataFrame
        """
        if self.data_source == "tushare":
            return self._get_stock_list_tushare(market)
        else:
            return self._get_stock_list_sina(market)

    def _get_stock_list_sina(self, market: str = "all") -> pd.DataFrame:
        """从新浪获取股票列表"""
        try:
            # 获取常用股票池
            stocks = self._get_common_stocks()
            return stocks
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    def _get_stock_list_tushare(self, market: str = "all") -> pd.DataFrame:
        """从Tushare获取股票列表"""
        try:
            if market == "sh":
                df = self.pro.stock_basic(exchange='SSE', list_status='L')
            elif market == "sz":
                df = self.pro.stock_basic(exchange='SZSE', list_status='L')
            else:
                df = self.pro.stock_basic(list_status='L')
            return df
        except Exception as e:
            logger.error(f"Tushare获取股票列表失败: {e}")
            return pd.DataFrame()

    def _get_common_stocks(self) -> pd.DataFrame:
        """获取常用股票池（免费接口）"""
        # 常用指数成分股 + 热门股票
        common_codes = {
            "600519": "贵州茅台",
            "000001": "平安银行",
            "600036": "招商银行",
            "601398": "工商银行",
            "601988": "中国银行",
            "600000": "浦发银行",
            "300750": "宁德时代",
            "002594": "比亚迪",
            "300015": "爱尔眼科",
            "000651": "格力电器",
            "600276": "恒瑞医药",
            "002475": "立讯精密",
            "601012": "隆基绿能",
            "600030": "中信证券",
            "300059": "东方财富",
        }

        data = []
        for code, name in common_codes.items():
            prefix = "sh" if code.startswith("6") else "sz"
            data.append({
                "ts_code": f"{prefix}{code}",
                "symbol": code,
                "name": name,
                "market": "sh" if prefix == "sh" else "sz",
            })

        return pd.DataFrame(data)

    def get_daily_price(self, symbol: str, start_date: str = None,
                        end_date: str = None, adjust: str = "qfq") -> pd.DataFrame:
        """
        获取日线行情数据

        Args:
            symbol: 股票代码 (如 '600519')
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型 ('qfq' 前复权, 'hfq' 后复权, 'none' 不复权)

        Returns:
            日线数据 DataFrame
        """
        if self.data_source == "tushare":
            return self._get_daily_price_tushare(symbol, start_date, end_date, adjust)
        else:
            return self._get_daily_price_sina(symbol, start_date, end_date)

    def _get_daily_price_tushare(self, symbol: str, start_date: str = None,
                                  end_date: str = None, adjust: str = "qfq") -> pd.DataFrame:
        """从Tushare获取日线数据"""
        try:
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")

            ts_code = f"{'sh' if symbol.startswith('6') else 'sz'}{symbol}"

            adj_map = {"qfq": 1, "hfq": 2, "none": 3}
            adj_type = adj_map.get(adjust, 1)

            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                adj=adj_type
            )

            if df is not None and not df.empty:
                df = df.sort_values('trade_date')
            return df

        except Exception as e:
            logger.error(f"获取日线数据失败: {e}")
            return pd.DataFrame()

    def _get_daily_price_sina(self, symbol: str, start_date: str = None,
                              end_date: str = None) -> pd.DataFrame:
        """从新浪获取日线数据（简化版）"""
        try:
            prefix = "sh" if symbol.startswith("6") else "sz"
            url = f"https://hq.sinajs.cn/list={prefix}{symbol}"
            headers = {"Referer": "https://finance.sina.com.cn"}

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.text.split('"')[1].split(',')

                # 解析数据
                today_data = {
                    "trade_date": datetime.now().strftime("%Y%m%d"),
                    "open": float(data[1]),
                    "high": float(data[4]),
                    "low": float(data[5]),
                    "close": float(data[3]),
                    "pre_close": float(data[2]),
                    "vol": float(data[8]) / 100,
                    "amount": float(data[9]) / 10000,
                }

                df = pd.DataFrame([today_data])
                return df

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return pd.DataFrame()

    def get_realtime_quote(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            实时行情字典
        """
        quotes = {}

        for symbol in symbols:
            prefix = "sh" if symbol.startswith("6") else "sz"
            url = f"https://hq.sinajs.cn/list={prefix}{symbol}"
            headers = {"Referer": "https://finance.sina.com.cn"}

            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.text.split('"')[1].split(',')
                    name = data[0]

                    quotes[symbol] = {
                        "name": name,
                        "open": float(data[1]),
                        "pre_close": float(data[2]),
                        "close": float(data[3]),
                        "high": float(data[4]),
                        "low": float(data[5]),
                        "volume": float(data[8]),
                        "amount": float(data[9]),
                        "time": data[30] + " " + data[31] if len(data) > 31 else datetime.now().strftime("%H:%M:%S")
                    }

                    # 计算涨跌
                    pre_close = quotes[symbol]["pre_close"]
                    close = quotes[symbol]["close"]
                    change = close - pre_close
                    change_pct = (change / pre_close) * 100 if pre_close > 0 else 0

                    quotes[symbol]["change"] = change
                    quotes[symbol]["change_pct"] = change_pct

            except Exception as e:
                logger.error(f"获取 {symbol} 实时行情失败: {e}")
                continue

        return quotes


class StockScreener:
    """股票筛选器"""

    def __init__(self, api: StockDataAPI):
        self.api = api

    def screen_by_ma(self, symbols: List[str], ma_days: int = 5,
                     compare_ma: int = 20) -> List[Dict[str, Any]]:
        """
        均线筛选：筛选股价在MA均线上方的股票

        Args:
            symbols: 股票列表
            ma_days: 短期均线天数
            compare_ma: 长期均线天数

        Returns:
            符合条件的股票列表
        """
        results = []

        for symbol in symbols:
            try:
                df = self.api.get_daily_price(symbol, start_date=None)
                if df is None or df.empty or len(df) < compare_ma:
                    continue

                # 计算均线
                df['ma_short'] = df['close'].rolling(window=ma_days).mean()
                df['ma_long'] = df['close'].rolling(window=compare_ma).mean()

                latest = df.iloc[-1]

                # 筛选条件：股价在均线上方 + 均线金叉
                if latest['close'] > latest['ma_short'] > latest['ma_long']:
                    prev_short = df.iloc[-2]['ma_short']
                    prev_long = df.iloc[-2]['ma_long']

                    # 金叉检测
                    if prev_short <= prev_long and latest['ma_short'] > latest['ma_long']:
                        results.append({
                            "symbol": symbol,
                            "close": latest['close'],
                            "ma_short": latest['ma_short'],
                            "ma_long": latest['ma_long'],
                            "change_pct": ((latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100 if len(df) > 1 else 0
                        })

            except Exception as e:
                logger.error(f"筛选 {symbol} 时出错: {e}")
                continue

        return sorted(results, key=lambda x: x['change_pct'], reverse=True)

    def screen_by_volume(self, symbols: List[str], volume_multiplier: float = 2.0) -> List[Dict[str, Any]]:
        """
        量能筛选：筛选成交量放大的股票

        Args:
            symbols: 股票列表
            volume_multiplier: 成交量放大倍数

        Returns:
            符合条件的股票列表
        """
        results = []

        for symbol in symbols:
            try:
                df = self.api.get_daily_price(symbol, start_date=None)
                if df is None or df.empty or len(df) < 5:
                    continue

                latest = df.iloc[-1]
                avg_volume = df['vol'].iloc[-5:].mean()

                # 成交量放大
                if latest['vol'] > avg_volume * volume_multiplier:
                    results.append({
                        "symbol": symbol,
                        "close": latest['close'],
                        "volume": latest['vol'],
                        "avg_volume": avg_volume,
                        "volume_ratio": latest['vol'] / avg_volume,
                        "change_pct": ((latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100 if len(df) > 1 else 0
                    })

            except Exception as e:
                logger.error(f"筛选 {symbol} 时出错: {e}")
                continue

        return sorted(results, key=lambda x: x['volume_ratio'], reverse=True)


if __name__ == "__main__":
    # 测试代码
    api = StockDataAPI(data_source="sina")

    print("=" * 50)
    print("测试股票数据接口")
    print("=" * 50)

    # 获取股票列表
    stocks = api.get_stock_list()
    print(f"\n📊 股票列表 (共 {len(stocks)} 只):")
    print(stocks.head(10))

    # 获取实时行情
    test_symbols = ["600519", "000001", "300750"]
    quotes = api.get_realtime_quote(test_symbols)
    print(f"\n📈 实时行情:")
    for symbol, quote in quotes.items():
        print(f"{symbol}: {quote['close']:.2f} ({quote['change_pct']:+.2f}%)")

    # 测试筛选器
    screener = StockScreener(api)
    ma_stocks = screener.screen_by_ma(test_symbols, ma_days=5, compare_ma=20)
    print(f"\n🎯 均线金叉股票: {len(ma_stocks)}")
    for stock in ma_stocks:
        print(f"  {stock['symbol']}: {stock['close']:.2f} ({stock['change_pct']:+.2f}%)")
