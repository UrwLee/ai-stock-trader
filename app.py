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
    .stock-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 5px;
    }
    .up-stock {
        background-color: #e6ffe6;
        border-left: 4px solid #00cc00;
    }
    .down-stock {
        background-color: #ffe6e6;
        border-left: 4px solid #cc0000;
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
        ["🏠 首页", "📈 实时行情", "🎯 AI选股", "💼 组合管理", "⚙️ 设置"]
    )
    
    st.markdown("---")
    
    st.info("💡 **提示:**")
    st.markdown("""
    - 首页自动展示热门板块
    - AI选股从全部A股筛选
    - 点击股票查看详情
    """)


# ========== 页面0: 首页 ==========
if page == "🏠 首页":
    st.header("🏠 市场概览")

    api = StockDataAPI(data_source="sina")
    
    # 获取所有股票
    all_stocks = api.get_a_stock_list()
    
    # 按板块分类展示
    tabs = st.tabs(["🔥 全部", "🏦 银行", "💊 医药", "💻 科技", "🚗 新能源", "🍺 消费"])
    
    categories = {
        "🔥 全部": "all",
        "🏦 银行": "bank",
        "💊 医药": "medicine",
        "💻 科技": "tech",
        "🚗 新能源": "energy",
        "🍺 消费": "consumer",
    }
    
    for tab, (name, category) in zip(tabs, categories.items()):
        with tab:
            # 获取该板块股票
            if category == "all":
                stock_symbols = [s['symbol'] for s in all_stocks[:50]]  # 显示前50只
            else:
                stock_symbols = api.get_hot_stocks(category)
            
            if stock_symbols:
                # 获取实时行情
                quotes = api.get_realtime_quote(stock_symbols[:30])  # 限制30只
                
                if quotes:
                    # 创建股票卡片网格
                    cols = st.columns(4)
                    idx = 0
                    
                    for symbol, quote in quotes.items():
                        col = cols[idx % 4]
                        
                        # 根据涨跌选择样式
                        change_pct = quote['change_pct']
                        change_color = "🟢" if change_pct > 0 else "🔴" if change_pct < 0 else "⚪"
                        bg_class = "up-stock" if change_pct > 0 else "down-stock"
                        
                        with col:
                            with st.container():
                                st.markdown(f"""
                                <div class="stock-card {bg_class}">
                                    <strong>{symbol}</strong> {quote.get('name', '-')}<br>
                                    <strong style="font-size: 20px;">¥{quote['close']:.2f}</strong><br>
                                    {change_color} {change_pct:+.2f}%
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # 查看详情按钮
                                if st.button(f"📊 {symbol}", key=f"btn_{symbol}"):
                                    st.session_state[f"selected_{symbol}"] = True
                        
                        idx += 1
                        
                        if idx >= 4:
                            idx = 0
                    
                    # 显示统计信息
                    if quotes:
                        up = sum(1 for q in quotes.values() if q['change_pct'] > 0)
                        down = sum(1 for q in quotes.values() if q['change_pct'] < 0)
                        st.markdown(f"**{name}**: 🟢 {up}只 | 🔴 {down}只 | 共{len(quotes)}只")
                else:
                    st.warning(f"未能获取{name}数据")


# ========== 页面1: 实时行情 ==========
elif page == "📈 实时行情":
    st.header("📈 实时行情")
    
    api = StockDataAPI(data_source="sina")
    
    # 快速选择
    st.subheader("📋 自选股票")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        # 获取所有股票
        all_stocks = api.get_a_stock_list()
        stock_options = [f"{s['symbol']} - {s['name']}" for s in all_stocks[:100]]
        
        selected = st.multiselect(
            "选择股票 (可搜索)",
            options=stock_options,
            default=stock_options[:5] if stock_options else [],
            help="输入股票代码或名称搜索"
        )
    
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 刷新行情", type="primary"):
            st.rerun()
    
    # 解析选中的股票
    if selected:
        symbols = [s.split(" - ")[0] for s in selected]
        
        # 获取行情
        quotes = api.get_realtime_quote(symbols)
        
        if quotes:
            # 转换为DataFrame
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
            
            df = pd.DataFrame(data).set_index("代码")
            
            # 显示涨跌统计
            up_count = sum(1 for q in quotes.values() if q['change_pct'] > 0)
            down_count = sum(1 for q in quotes.values() if q['change_pct'] < 0)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("上涨", f"{up_count}只", delta=f"{up_count}", delta_color="normal")
            c2.metric("下跌", f"{down_count}只", delta=f"-{down_count}", delta_color="inverse")
            c3.metric("总股票", f"{len(quotes)}只")
            
            # 显示表格
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
            
            # 涨跌幅柱状图
            if len(quotes) > 0:
                st.subheader("📊 涨跌幅分布")
                changes = {s: q['change_pct'] for s, q in quotes.items()}
                st.bar_chart(pd.Series(changes))
    
    else:
        st.info("💡 请从上方选择股票，或前往【首页】查看热门板块")


# ========== 页面2: AI选股 ==========
elif page == "🎯 AI选股":
    st.header("🎯 AI智能选股")
    
    st.info("🤖 AI将从全部A股中筛选优质股票，无需手动选择")
    
    # 评分设置
    col1, col2 = st.columns(2)
    with col1:
        method = st.selectbox(
            "🎯 评分方法",
            ["comprehensive", "momentum", "trend"],
            format_func=lambda x: {"comprehensive": "综合评分", "momentum": "动量优先", "trend": "趋势优先"}[x],
            index=0
        )
    with col2:
        top_n = st.slider("📊 选择数量", 5, 50, 10)
    
    # 筛选条件
    st.subheader("🔧 筛选条件")
    c1, c2, c3 = st.columns(3)
    with c1:
        min_price = st.number_input("最低价 (¥)", value=5.0, step=1.0)
    with c2:
        max_price = st.number_input("最高价 (¥)", value=1000.0, step=10.0)
    with c3:
        min_change = st.slider("最小涨跌幅 (%)", -10, 10, -5)
    
    # 开始选股
    if st.button("🚀 开始AI选股", type="primary", use_container_width=True):
        with st.spinner("🤖 AI正在分析全部A股..."):
            api = StockDataAPI(data_source="sina")
            picker = AIStockPicker()
            
            # 获取全部A股
            all_stocks = api.get_a_stock_list()
            stock_symbols = [s['symbol'] for s in all_stocks]
            
            st.info(f"📊 正在分析 {len(stock_symbols)} 只股票...")
            
            # AI选股
            results = picker.pick_by_ai_score(stock_symbols, method=method)
            
            # 筛选条件过滤
            filtered_results = []
            for stock in results:
                if min_price <= stock['price'] <= max_price and stock['change_pct'] >= min_change:
                    filtered_results.append(stock)
            
            # 限制数量
            final_results = filtered_results[:top_n]
        
        if final_results:
            st.success(f"✅ AI分析完成！选出 {len(final_results)} 只优质股票")
            
            # 显示结果
            st.subheader("🏆 AI精选TOP股票")
            
            for i, stock in enumerate(final_results, 1):
                with st.expander(f"{i}. {stock['symbol']} - {stock.get('name', '-')} (得分: {stock['score']:.1f})", expanded=i<=3):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("当前价", f"¥{stock['price']:.2f}")
                    c2.metric("涨跌", f"{stock['change_pct']:+.2f}%")
                    c3.metric("MA5", f"¥{stock.get('ma5', stock['price']):.2f}")
                    c4.metric("MA20", f"¥{stock.get('ma20', stock['price']):.2f}")
                    
                    # 因子评分
                    f = stock['factors']
                    st.progress(f['momentum']/100, text=f"动量 {f['momentum']:.0f}/100")
                    st.progress(f['trend']/100, text=f"趋势 {f['trend']:.0f}/100")
                    
                    # 交易信号
                    signal = picker.generate_trading_signal(stock['symbol'])
                    emoji = "🟢" if signal['signal'].startswith('buy') else ("🔴" if signal['signal'].startswith('sell') else "🟡")
                    st.markdown(f"{emoji} **{signal['signal'].upper()}** - {signal['reason']}")
            
            # 导出选项
            if st.button("📥 导出选股结果"):
                export_df = pd.DataFrame(final_results)[['symbol', 'price', 'change_pct', 'score', 'factors']]
                csv = export_df.to_csv(index=False)
                st.download_button("📥 下载CSV", csv, "ai_selected_stocks.csv", "text/csv")
            
        else:
            st.warning("⚠️ 未找到符合条件的股票，请调整筛选条件")


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
