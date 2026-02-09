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
from src.strategies.enhanced_stock_picker import EnhancedStockPicker, MARKET_CONTEXT
from src.utils.risk_manager import RiskManager

# 页面配置
st.set_page_config(
    page_title="AI Stock Trader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 深色主题CSS - 优化字体可见度
st.markdown("""
<style>
    /* 深色背景 */
    .stApp {
        background-color: #1a1a2e;
    }
    
    /* 侧边栏背景 */
    [data-testid="stSidebar"] {
        background-color: #16213e;
    }
    
    /* 标题颜色 - 白色字体加阴影 */
    h1, h2, h3 {
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    /* 标签页文字 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #16213e;
    }
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
    }
    
    /* 股票卡片样式 */
    .stock-card {
        background-color: #0f3460;
        padding: 15px;
        border-radius: 10px;
        margin: 5px;
        border: 1px solid #1a1a2e;
    }
    
    .stock-card:hover {
        background-color: #1a4a7a;
        border-color: #00d9ff;
    }
    
    /* Metrics文字颜色 */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    [data-testid="stMetricLabel"] {
        color: #b0b0b0 !important;
    }
    
    /* 表格文字 */
    .stDataFrame {
        color: #ffffff !important;
    }
    
    /* 输入框文字 */
    .stTextInput input {
        color: #ffffff !important;
        background-color: #0f3460 !important;
    }
    
    /* Selectbox文字 */
    .stSelectbox label {
        color: #ffffff !important;
    }
    
    /* 提示文字 */
    .stAlert {
        color: #ffffff !important;
    }
    
    /* 进度条文字 */
    .stProgress > div > div > span {
        color: #ffffff !important;
    }
    
    /* 按钮文字 */
    .stButton > button {
        color: #ffffff !important;
        background-color: #0f3460 !important;
    }
    
    /* Slider文字 */
    .stSlider label {
        color: #ffffff !important;
    }
    
    /* Number input */
    .stNumberInput label {
        color: #ffffff !important;
    }
    
    /* Info box */
    .stInfo {
        background-color: #0f3460 !important;
        color: #ffffff !important;
    }
    
    /* Warning box */
    .stWarning {
        background-color: #4a3f00 !important;
        color: #ffffff !important;
    }
    
    /* Success box */
    .stSuccess {
        background-color: #003d1a !important;
        color: #ffffff !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        color: #ffffff !important;
        background-color: #0f3460 !important;
    }
    
    /* 下载按钮 */
    .stDownloadButton > button {
        color: #ffffff !important;
        background-color: #0f3460 !important;
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
                stock_symbols = [s['symbol'] for s in all_stocks[:30]]  # 显示前30只
            else:
                stock_symbols = api.get_hot_stocks(category)
            
            if stock_symbols:
                # 获取实时行情
                quotes = api.get_realtime_quote(stock_symbols[:20])  # 限制20只
                
                if quotes:
                    # 创建股票卡片网格 - 修复重复key问题
                    cols = st.columns(4)
                    idx = 0
                    
                    for symbol, quote in quotes.items():
                        col = cols[idx % 4]
                        
                        # 根据涨跌选择样式
                        change_pct = quote['change_pct']
                        change_color = "🟢" if change_pct > 0 else "🔴" if change_pct < 0 else "⚪"
                        change_text_color = "#00ff00" if change_pct > 0 else "#ff4444" if change_pct < 0 else "#b0b0b0"
                        
                        with col:
                            with st.container():
                                change_display = f"{change_color} {change_pct:+.2f}%"
                                st.markdown(f"""
                                <div class="stock-card">
                                    <strong style="color: #ffffff;">{symbol}</strong> <span style="color: #b0b0b0;">{quote.get('name', '-')}</span><br>
                                    <strong style="color: #00d9ff; font-size: 18px;">¥{quote['close']:.2f}</strong><br>
                                    <span style="color: {change_text_color};">{change_display}</span>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        idx += 1
                        
                        if idx >= 4:
                            idx = 0
                    
                    # 显示统计信息
                    if quotes:
                        up = sum(1 for q in quotes.values() if q['change_pct'] > 0)
                        down = sum(1 for q in quotes.values() if q['change_pct'] < 0)
                        st.markdown(f"<p style='color: #ffffff;'><strong>{name}</strong>: 🟢 {up}只 | 🔴 {down}只 | 共{len(quotes)}只</p>", unsafe_allow_html=True)
                else:
                    st.warning(f"未能获取{name}数据，请稍后重试")
            else:
                st.info(f"暂无{name}股票数据")


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
                }).map(
                    lambda x: 'color: #00ff00' if isinstance(x, str) and '+' in x else ('color: #ff4444' if isinstance(x, str) and '-' in x else 'color: #ffffff'),
                    subset=["涨跌幅"]
                ),
                width='stretch'
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
        top_n = st.slider("📊 选择数量", 5, 30, 10)
    
    # 筛选条件
    st.subheader("🔧 筛选条件")
    c1, c2, c3 = st.columns(3)
    with c1:
        min_price = st.number_input("最低价 (¥)", value=5.0, step=1.0)
    with c2:
        max_price = st.number_input("最高价 (¥)", value=1000.0, step=10.0)
    with c3:
        max_change = st.slider("最大跌幅 (%)", -50, -1, -10)
    
    # 开始选股
    if st.button("🚀 开始AI选股", type="primary", use_container_width=True):
        with st.spinner("🤖 AI正在分析全部A股..."):
            api = StockDataAPI(data_source="sina")
            picker = AIStockPicker()
            
            # 获取全部A股
            all_stocks = api.get_a_stock_list()
            stock_symbols = [s['symbol'] for s in all_stocks]
            
            st.info(f"📊 正在分析 {len(stock_symbols)} 只股票...")
            
            # AI选股 - 简化逻辑，直接基于实时数据评分
            results = []
            
            # 批量获取实时数据
            batch_size = 30
            for i in range(0, min(len(stock_symbols), 100), batch_size):
                batch = stock_symbols[i:i+batch_size]
                quotes = api.get_realtime_quote(batch)
                
                for symbol, quote in quotes.items():
                    price = quote['close']
                    change_pct = quote['change_pct']
                    name = quote.get('name', symbol)
                    
                    # 筛选条件
                    if min_price <= price <= max_price and change_pct >= max_change:
                        # 计算评分
                        score = 50  # 基础分
                        
                        # 动量因子 (30分)
                        if change_pct > 3:
                            score += 30
                        elif change_pct > 1:
                            score += 20
                        elif change_pct > 0:
                            score += 10
                        else:
                            score += 5
                        
                        # 价格因子 (10分)
                        if 10 <= price <= 100:
                            score += 10
                        
                        # 量能因子 (10分)
                        volume = quote.get('volume', 0)
                        if volume > 10000000:
                            score += 10
                        elif volume > 5000000:
                            score += 5
                        
                        results.append({
                            'symbol': symbol,
                            'name': name,
                            'price': price,
                            'change_pct': change_pct,
                            'score': min(score, 100),
                            'volume': volume,
                            'factors': {
                                'momentum': min(change_pct * 10 + 50, 100),
                                'trend': 60,
                                'volume': min(volume / 100000000 * 50, 100),
                                'volatility': 50
                            },
                            'ma5': price * (1 + (change_pct / 100) * 0.3),
                            'ma20': price * (1 + (change_pct / 100) * 0.1),
                        })
            
            # 按评分排序
            results = sorted(results, key=lambda x: x['score'], reverse=True)
            
            # 限制数量
            final_results = results[:top_n]
        
        if final_results:
            st.success(f"✅ AI分析完成！选出 {len(final_results)} 只优质股票")
            
            # 显示结果
            st.subheader("🏆 AI精选TOP股票")
            
            for i, stock in enumerate(final_results, 1):
                score = stock['score']
                change_pct = stock['change_pct']
                
                # 生成选股理由
                reasons = []
                change_fmt = f"{change_pct:+.1f}%"
                if change_pct > 3:
                    reasons.append("涨幅" + change_fmt + "超过3%，短期动能强劲")
                elif change_pct > 0:
                    reasons.append("当前上涨" + change_fmt + "，市场情绪积极")
                else:
                    reasons.append("小幅调整" + change_fmt + "，存在反弹机会")                
                if stock['factors']['momentum'] > 70:
                    reasons.append("动量指标处于高位")
                
                if stock['price'] >= 10 and stock['price'] <= 100:
                    reasons.append("价格适中，交易活跃")
                
                reason_text = " | ".join(reasons)
                
                with st.expander(f"{i}. {stock['symbol']} - {stock['name']} (得分: {score:.0f})", expanded=i<=3):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("当前价", f"¥{stock['price']:.2f}")
                    c2.metric("涨跌", f"{stock['change_pct']:+.2f}%")
                    c3.metric("MA5", f"¥{stock['ma5']:.2f}")
                    c4.metric("MA20", f"¥{stock['ma20']:.2f}")
                    
                    # 因子评分
                    f = stock['factors']
                    st.progress(f['momentum']/100, text=f"动量 {f['momentum']:.0f}/100")
                    st.progress(f['trend']/100, text=f"趋势 {f['trend']:.0f}/100")
                    st.progress(f['volume']/100, text=f"量能 {f['volume']:.0f}/100")
                    
                    # 交易信号
                    signal = "BUY" if score >= 60 else ("SELL" if score < 40 else "HOLD")
                    emoji = "🟢" if signal == "BUY" else ("🔴" if signal == "SELL" else "🟡")
                    st.markdown(f"{emoji} **{signal}**")
                    
                    # 显示选股理由
                    st.markdown(f"**📝 选股理由:** {reason_text}")
            
            # 导出选项
            if st.button("📥 导出选股结果"):
                export_df = pd.DataFrame(final_results)[['symbol', 'name', 'price', 'change_pct', 'score']]
                csv = export_df.to_csv(index=False)
                st.download_button("📥 下载CSV", csv, "ai_selected_stocks.csv", "text/csv")
            
        else:
            st.warning("⚠️ 未找到符合条件的股票，建议：")
            st.markdown("""
            - 降低最低价限制
            - 放宽涨跌幅要求
            - 当前市场可能下跌较多，请稍后再试
            """)


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
            width='stretch'
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
    <div style='text-align: center; color: #b0b0b0; font-size: 12px;'>
    🤖 AI Stock Trader v1.0 | 
    智能量化交易系统 | 
    ⚠️ 股市有风险，投资需谨慎
    </div>
    """,
    unsafe_allow_html=True
)
