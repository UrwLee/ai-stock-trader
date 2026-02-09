#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Stock Trader - Web可视化界面
使用 Streamlit 快速创建交互界面

运行方式:
    streamlit run app.py

访问: http://localhost:8501
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# 导入项目模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.stock_api import StockDataAPI
from src.strategies.ai_stock_picker import AIStockPicker
from src.utils.risk_manager import RiskManager
from src.utils.technical_analysis import TechnicalAnalyzer

# 页面配置
st.set_page_config(
    page_title="AI Stock Trader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS样式
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .main {
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.title("🤖 AI Stock Trader")
st.markdown("### 智能量化交易系统")
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("📊 功能导航")
    
    page = st.selectbox(
        "选择功能",
        ["📈 实时行情", "🎯 AI选股", "💼 组合管理", "⚙️ 设置"]
    )
    
    st.markdown("---")
    
    st.info("💡 **提示:**")
    st.markdown("""
    - 免费使用，无需配置
    - 完整功能需Tushare Token
    - 实盘交易需券商账户
    """)


# ========== 页面1: 实时行情 ==========
if page == "📈 实时行情":
    st.header("📈 实时行情")
    
    # 输入区域
    col1, col2 = st.columns([4, 1])
    with col1:
        symbols_input = st.text_input(
            "输入股票代码 (逗号分隔)",
            value="600519,000001,300750,002594,600036"
        )
    with col2:
        st.write("")
        st.write("")
        query_btn = st.button("🔍 查询", use_container_width=True)
    
    # 解析并查询
    if symbols_input:
        symbols = [s.strip() for s in symbols_input.split(",") if s.strip()]
        
        if symbols:
            api = StockDataAPI(data_source="sina")
            quotes = api.get_realtime_quote(symbols)
            
            if quotes:
                # 转换数据
                data = []
                for symbol, quote in quotes.items():
                    data.append({
                        "代码": symbol,
                        "名称": quote.get('name', '-'),
                        "当前价": quote['close'],
                        "涨跌": quote['change'],
                        "涨跌幅": f"{quote['change_pct']:+.2f}%",
                        "最高": quote['high'],
                        "最低": quote['low'],
                        "成交量": f"{quote['volume']/10000:.0f}万",
                    })
                
                df = pd.DataFrame(data)
                
                # 设置索引
                df = df.set_index("代码")
                
                # 显示数据
                st.dataframe(
                    df.style.format({
                        "当前价": "{:.2f}",
                        "涨跌": "{:+.2f}",
                        "最高": "{:.2f}",
                        "最低": "{:.2f}",
                    }).applymap(
                        lambda x: 'color: green' if isinstance(x, str) and '+' in x else ('color: red' if isinstance(x, str) and '-' in x else ''),
                        subset=["涨跌幅"]
                    ),
                    use_container_width=True
                )
                
                # 涨跌统计
                up_count = sum(1 for q in quotes.values() if q['change_pct'] > 0)
                down_count = sum(1 for q in quotes.values() if q['change_pct'] < 0)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("上涨", f"{up_count}只", delta=f"{up_count}", delta_color="normal")
                col2.metric("下跌", f"{down_count}只", delta=f"-{down_count}", delta_color="inverse")
                col3.metric("总股票", f"{len(quotes)}只")
                
            else:
                st.warning("⚠️ 未获取到数据，请检查股票代码是否正确")
        else:
            st.warning("⚠️ 请输入股票代码")


# ========== 页面2: AI选股 ==========
elif page == "🎯 AI选股":
    st.header("🎯 AI智能选股")
    
    # 快速选择
    st.subheader("📋 选择候选股票")
    
    # 常用板块
    tabs = st.tabs(["🔥 热门", "🏦 银行", "💊 医药", "💻 科技", "📝 自定义"])
    
    with tabs[0]:
        hot_stocks = st.multiselect(
            "选择热门股",
            ["600519", "300750", "002594", "000651", "600276", "300059"],
            default=["600519", "300750", "002594"],
            key="hot"
        )
    
    with tabs[1]:
        bank_stocks = st.multiselect(
            "选择银行股",
            ["601398", "600036", "601988", "600000"],
            key="bank"
        )
    
    with tabs[2]:
        med_stocks = st.multiselect(
            "选择医药股",
            ["600436", "000513", "600276"],
            key="med"
        )
    
    with tabs[3]:
        tech_stocks = st.multiselect(
            "选择科技股",
            ["002410", "300033", "300368"],
            key="tech"
        )
    
    with tabs[4]:
        custom_stocks = st.text_input(
            "自定义 (逗号分隔)",
            value="",
            key="custom"
        )
        if custom_stocks:
            custom_list = [s.strip() for s in custom_stocks.split(",")]
        else:
            custom_list = []
    
    # 合并选择
    all_stocks = hot_stocks + bank_stocks + med_stocks + tech_stocks + custom_list
    all_stocks = list(set(all_stocks))  # 去重
    
    # 评分方法
    st.subheader("🎯 AI评分")
    method = st.radio(
        "评分方法",
        ["comprehensive"", "momentum", "trend"],
        horizontal=True,
        index=0
    )
    method_names = {
        "comprehensive": "综合评分",
        "momentum": "动量优先",
        "trend": "趋势优先"
    }
    st.caption(f"选择: {method_names.get(method, method)}")
    
    # 开始选股
    if st.button("🎯 开始AI选股", type="primary", use_container_width=True):
        if all_stocks:
            with st.spinner("🤖 AI正在分析股票..."):
                picker = AIStockPicker()
                results = picker.pick_by_ai_score(all_stocks, method=method)
            
            if results:
                st.success(f"✅ AI分析完成! 找到 {len(results)} 只优质股票")
                
                # TOP 5
                st.subheader("🏆 TOP 5 评分股票")
                
                for i, stock in enumerate(results[:5], 1):
                    with st.expander(f"{i}. {stock['symbol']} (得分: {stock['score']:.1f})", expanded=i==1):
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("当前价", f"¥{stock['price']:.2f}")
                        col2.metric("涨跌", f"{stock['change_pct']:+.2f}%")
                        col3.metric("MA5", f"¥{stock['ma5']:.2f}")
                        col4.metric("MA20", f"¥{stock['ma20']:.2f}")
                        
                        # 因子
                        f = stock['factors']
                        st.progress(f['momentum']/100, text=f"动量 {f['momentum']:.0f}/100")
                        st.progress(f['trend']/100, text=f"趋势 {f['trend']:.0f}/100")
                        
                        # 交易信号
                        signal = picker.generate_trading_signal(stock['symbol'])
                        emoji = "🟢" if signal['signal'].startswith('buy') else ("🔴" if signal['signal'].startswith('sell') else "🟡")
                        st.markdown(f"{emoji} **{signal['signal'].upper()}** - {signal['reason']}")
                        
                        # 操作按钮
                        c1, c2 = st.columns(2)
                        if c1.button(f"➕ 买入 {stock['symbol']}", key=f"buy_{stock['symbol']}"):
                            st.session_state[f"portfolio_{stock['symbol']}"] = {
                                'shares': 100,
                                'price': stock['price']
                            }
                            st.success(f"已添加到组合!")
                        
                        if c2.button(f"📊 分析 {stock['symbol']}", key=f"ana_{stock['symbol']}"):
                            st.info(f"技术指标分析需要历史数据，请配置Tushare")
            else:
                st.warning("⚠️ 没有找到符合条件的股票")
        else:
            st.error("请先选择股票!")


# ========== 页面3: 组合管理 ==========
elif page == "💼 组合管理":
    st.header("💼 组合管理")
    
    # 初始化组合
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = RiskManager(initial_capital=10000)
    
    portfolio = st.session_state.portfolio
    
    # 状态卡片
    status = portfolio.get_portfolio_status(current_value=10000)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("初始资金", f"¥{status['initial_capital']:,.0f}")
    col2.metric("当前价值", f"¥{status['current_value']:,.0f}", delta=f"{status['total_return']:+.2f}%")
    col3.metric("持仓数", f"{status['position_count']}只")
    col4.metric("风险等级", status['risk_level'].upper(), 
               delta="低" if status['risk_level'] == "low" else ("中" if status['risk_level'] == "medium" else "高"))
    
    st.markdown("---")
    
    # 添加持仓
    st.subheader("➕ 添加持仓")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    with c1:
        new_symbol = st.text_input("股票代码", key="psym")
    with c2:
        new_shares = st.number_input("股数", min_value=1, value=100, key="pshares")
    with c3:
        new_price = st.number_input("买入价", min_value=0.01, value=10.0, key="pprice")
    with c4:
        st.write("")
        st.write("")
        if st.button("➕ 添加", key="padd"):
            if new_symbol and new_shares > 0 and new_price > 0:
                portfolio.add_position(new_symbol, new_shares, new_price)
                st.success(f"✅ 已添加 {new_symbol}: {new_shares}股 @ ¥{new_price:.2f}")
                st.rerun()
    
    # 持仓列表
    st.subheader("📋 当前持仓")
    
    if status['positions']:
        positions_df = pd.DataFrame(status['positions'])
        positions_df['市值'] = positions_df['market_value'].apply(lambda x: f"¥{x:,.0f}")
        positions_df['盈亏'] = positions_df['profit_pct'].apply(lambda x: f"{x:+.2f}%")
        
        st.dataframe(
            positions_df[['symbol', 'shares', 'cost', 'current', '市值', '盈亏']].style.format({
                'cost': '¥{:.2f}',
                'current': '¥{:.2f}',
            }),
            use_container_width=True
        )
        
        # 清仓按钮
        if st.button("🗑️ 清空所有持仓"):
            for symbol in list(portfolio.positions.keys()):
                portfolio.remove_position(symbol)
            st.rerun()
    else:
        st.info("💡 暂无持仓，点击上方添加")


# ========== 页面4: 设置 ==========
elif page == "⚙️ 设置":
    st.header("⚙️ 系统设置")
    
    st.subheader("📊 数据源配置")
    st.markdown("""
    **当前数据源:** 新浪免费行情
    
    **可配置的数据源:**
    - Tushare Pro (推荐)
    - 东方财富证券
    - 华鑫证券
    """)
    
    with st.expander("📝 Tushare 配置说明"):
        st.markdown("""
        1. 注册账号: https://tushare.pro
        2. 获取API Token
        3. 配置到 `.env` 文件:
           ```
           TUSHARE_TOKEN = your_token_here
           ```
        """)
    
    st.subheader("📈 交易设置")
    
    # 风险设置
    col1, col2 = st.columns(2)
    with col1:
        stop_loss = st.slider("止损比例 (%)", 5, 30, 10)
    with col2:
        take_profit = st.slider("止盈比例 (%)", 10, 50, 20)
    
    st.subheader("🔧 系统信息")
    st.markdown(f"""
    - **Python版本:** {sys.version.split()[0]}
    - **项目路径:** {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}
    - **GitHub:** https://github.com/UrwLee/ai-stock-trader
    """)

# 底部
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 12px;'>
    🤖 AI Stock Trader v1.0 | 
    智能量化交易系统 | 
    ⚠️ 股市有风险，投资需谨慎
    </div>
    """,
    unsafe_allow_html=True
)
