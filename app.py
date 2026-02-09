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
import json
import os

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

# 配置文件路径
CONFIG_FILE = "data/user_config.json"

def load_user_config():
    """加载用户配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"watchlist": [], "portfolio": {}}

def save_user_config(config):
    """保存用户配置"""
    try:
        os.makedirs("data", exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存失败: {e}")

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
    
    /* 标题颜色 */
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
        ["🏠 首页", "📈 实时行情", "🎯 AI选股", "💼 模拟炒股", "⚙️ 设置"]
    )
    
    st.markdown("---")
    
    st.info("💡 **提示:**")
    st.markdown("""
    - 首页自动展示热门板块
    - AI选股从全部A股筛选
    - 模拟炒股真实体验
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
                stock_symbols = [s['symbol'] for s in all_stocks[:30]]
            else:
                stock_symbols = api.get_hot_stocks(category)
            
            if stock_symbols:
                quotes = api.get_realtime_quote(stock_symbols[:20])
                
                if quotes:
                    cols = st.columns(4)
                    idx = 0
                    
                    for symbol, quote in quotes.items():
                        col = cols[idx % 4]
                        
                        change_pct = quote['change_pct']
                        change_color = "🔴" if change_pct > 0 else "🟢" if change_pct < 0 else "⚪"
                        change_text_color = "#ff4444" if change_pct > 0 else "#00ff00" if change_pct < 0 else "#b0b0b0"
                        
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
    
    # 加载用户选择
    config = load_user_config()
    saved_stocks = config.get("watchlist", [])
    
    # 快速选择
    st.subheader("📋 我的自选")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        all_stocks = api.get_a_stock_list()
        stock_options = [f"{s['symbol']} - {s['name']}" for s in all_stocks[:200]]
        
        # 如果有保存的选择，使用它作为默认
        default_values = []
        if saved_stocks:
            default_values = [f"{s['symbol']} - {s['name']}" for s in all_stocks 
                            if s['symbol'] in saved_stocks]
        
        if not default_values and stock_options:
            default_values = stock_options[:5]
        
        selected = st.multiselect(
            "选择股票 (可搜索)",
            options=stock_options,
            default=default_values,
            help="选择后自动保存，刷新不会丢失"
        )
    
    with col2:
        st.write("")
        st.write("")
        if st.button("💾 保存选择", type="primary"):
            if selected:
                symbols = [s.split(" - ")[0] for s in selected]
                config["watchlist"] = symbols
                save_user_config(config)
                st.success("✅ 已保存！")
            else:
                st.warning("请先选择股票")
        
        if st.button("🔄 刷新行情"):
            st.rerun()
    
    # 解析选中的股票
    if selected:
        symbols = [s.split(" - ")[0] for s in selected]
        
        # 实时获取
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
            
            # 涨跌统计
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
            st.warning("⚠️ 未获取到数据，请稍后重试")
    else:
        st.info("💡 请从上方选择股票，或前往【首页】查看热门板块")


# ========== 页面2: AI选股 ==========
elif page == "🎯 AI选股":
    st.header("🎯 AI智能选股")
    
    st.info("🤖 AI结合宏观分析、历史数据、实时行情进行深度趋势预测")
    
    # 显示市场背景
    with st.expander("📊 当前市场背景", expanded=False):
        st.markdown(MARKET_CONTEXT)
    
    # 显示市场分析报告
    if st.checkbox("📈 查看详细市场分析报告", value=False):
        picker = EnhancedStockPicker()
        report = picker.get_market_report()
        st.markdown(report)
    
    # 评分设置
    col1, col2 = st.columns(2)
    with col1:
        top_n = st.slider("📊 选择数量", 5, 30, 10)
    with col2:
        sector_filter = st.selectbox(
            "🏭 板块筛选",
            ["全部", "AI科技", "券商金融", "消费", "医药", "基建"]
        )
    
    # 开始选股
    if st.button("🚀 开始AI智能选股", type="primary", use_container_width=True):
        with st.spinner("🤖 AI正在结合宏观分析、历史数据、实时行情进行深度分析..."):
            api = StockDataAPI(data_source="sina")
            picker = EnhancedStockPicker()
            
            all_stocks = api.get_a_stock_list()
            stock_symbols = [s['symbol'] for s in all_stocks]
            
            st.info(f"📊 正在深度分析 {len(stock_symbols)} 只股票...")
            st.markdown("""
            **分析维度**:
            - 📈 技术面: 动量、价格、趋势、成交量
            - 🏛️ 政策面: 政策匹配度、受益程度
            - 💧 资金面: 流动性、外资流向
            - 🗓️ 事件驱动: 两会预期、政策催化
            """)
            
            results = picker.pick_with_context(stock_symbols, top_n=top_n * 2)
            
            # 板块过滤
            if sector_filter != "全部":
                sector_map = {
                    "AI科技": ["300750", "002594", "002475", "300059", "002410", "300033"],
                    "券商金融": ["600030", "600837", "600999", "601066", "601788"],
                    "消费": ["000651", "000858", "000568", "600809", "000596"],
                    "医药": ["600276", "600436", "300015", "000513", "002007"],
                    "基建": ["003013", "601186", "601390", "600048", "600383"]
                }
                allowed = sector_map.get(sector_filter, [])
                results = [r for r in results if r.symbol in allowed]
            
            final_results = results[:top_n]
        
        if final_results:
            st.success(f"✅ AI深度分析完成！选出 {len(final_results)} 只优质股票")
            
            st.subheader("🏆 AI精选TOP股票")
            
            for i, stock in enumerate(final_results, 1):
                with st.expander(f"{i}. {stock.symbol} - {stock.name} (得分: {stock.final_score:.0f}/100)", expanded=i<=3):
                    # 基础信息
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("当前价", f"¥{stock.price:.2f}")
                    c2.metric("涨跌", f"{stock.change_pct:+.2f}%")
                    c3.metric("技术分", f"{stock.trend_score:.0f}")
                    c4.metric("政策分", f"{stock.policy_score:.0f}")
                    
                    # 推荐等级
                    st.markdown(f"### {stock.recommendation}")
                    
                    # 详细分析
                    st.markdown(f"**📊 深度分析:**\n\n{stock.analysis}")
                    
                    # 政策匹配
                    st.markdown(f"**🎯 政策匹配**: {stock.policy_reason}")
                    
                    # 交易信号
                    emoji = "🟢" if stock.technical_signal == "BUY" else ("🔴" if stock.technical_signal == "SELL" else "🟡")
                    st.markdown(f"{emoji} **技术信号**: {stock.technical_signal}")
                    
                    # 风险提示
                    if stock.risks:
                        st.markdown("**⚠️ 风险提示**:")
                        for risk in stock.risks[:3]:
                            st.markdown(f"- {risk}")
            
            if st.button("📥 导出选股结果"):
                export_data = [{
                    '代码': s.symbol,
                    '名称': s.name,
                    '价格': s.price,
                    '涨跌幅': f"{s.change_pct:+.2f}%",
                    '评分': s.final_score,
                    '推荐': s.recommendation,
                    '技术分': s.trend_score,
                    '政策分': s.policy_score
                } for s in final_results]
                
                export_df = pd.DataFrame(export_data)
                csv = export_df.to_csv(index=False)
                st.download_button("📥 下载CSV", csv, "ai_selected_stocks.csv", "text/csv")
            
        else:
            st.warning("⚠️ 未找到符合条件的股票")
    
    else:
        st.info("💡 点击上方按钮开始AI智能选股")


# ========== 页面3: 模拟炒股 ==========
elif page == "💼 模拟炒股":
    st.header("💼 模拟炒股")
    
    # 初始化模拟账户
    if 'sim_account' not in st.session_state:
        st.session_state.sim_account = {
            'cash': 100000,  # 初始资金10万
            'positions': {},  # 持仓
            'history': [],  # 交易记录
            'initial_cash': 100000
        }
    
    account = st.session_state.sim_account
    
    # 显示账户信息
    st.subheader("📊 账户概览")
    
    # 计算总资产
    total_value = account['cash']
    positions_value = 0
    api = StockDataAPI(data_source="sina")
    
    if account['positions']:
        symbols = list(account['positions'].keys())
        quotes = api.get_realtime_quote(symbols)
        
        for symbol, pos in account['positions'].items():
            if symbol in quotes:
                current_price = quotes[symbol]['close']
                market_value = pos['shares'] * current_price
                positions_value += market_value
                pos['current_price'] = current_price
                pos['market_value'] = market_value
                pos['profit_pct'] = (current_price - pos['cost_price']) / pos['cost_price'] * 100
    
    total_value = account['cash'] + positions_value
    total_return = (total_value - account['initial_cash']) / account['initial_cash'] * 100
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总资产", f"¥{total_value:,.0f}", delta=f"{total_return:+.2f}%")
    c2.metric("可用资金", f"¥{account['cash']:,.0f}")
    c3.metric("持仓市值", f"¥{positions_value:,.0f}")
    c4.metric("交易次数", f"{len(account['history'])}次")
    
    st.markdown("---")
    
    # 买卖操作
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 买入股票")
        
        c1, c2 = st.columns(2)
        with c1:
            buy_symbol = st.text_input("股票代码", value="600519", key="buy_symbol")
        with c2:
            buy_price = st.number_input("买入价格", value=1500.0, step=10.0, key="buy_price")
        
        c3, c4 = st.columns(2)
        with c3:
            buy_shares = st.number_input("买入股数", min_value=100, value=100, step=100, key="buy_shares")
        with c4:
            st.write("")
            st.write("")
        
        if st.button("🔴 买入", type="primary", use_container_width=True):
            cost = buy_shares * buy_price
            if cost <= account['cash']:
                if buy_symbol in account['positions']:
                    # 加仓
                    old_shares = account['positions'][buy_symbol]['shares']
                    old_cost = account['positions'][buy_symbol]['cost_price']
                    new_shares = old_shares + buy_shares
                    new_cost = (old_shares * old_cost + cost) / new_shares
                    account['positions'][buy_symbol] = {
                        'shares': new_shares,
                        'cost_price': new_cost
                    }
                else:
                    account['positions'][buy_symbol] = {
                        'shares': buy_shares,
                        'cost_price': buy_price
                    }
                
                account['cash'] -= cost
                account['history'].append({
                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'action': 'BUY',
                    'symbol': buy_symbol,
                    'shares': buy_shares,
                    'price': buy_price,
                    'cost': cost
                })
                
                st.success(f"✅ 买入成功！{buy_symbol} {buy_shares}股 @ ¥{buy_price:.2f}")
                st.rerun()
            else:
                st.error("❌ 资金不足")
    
    with col2:
        st.subheader("📉 卖出股票")
        
        if account['positions']:
            sell_options = [f"{s} ({p['shares']}股)" for s, p in account['positions'].items()]
            sell_symbol = st.selectbox("选择持仓", sell_options, key="sell_select")
            
            if sell_symbol:
                symbol = sell_symbol.split("(")[0]
                symbol = symbol.strip()
                pos = account['positions'].get(symbol)
                current_price = pos.get('current_price', pos['cost_price'])
                
                c1, c2 = st.columns(2)
                with c1:
                    sell_shares = st.number_input("卖出股数", min_value=1, max_value=pos['shares'], value=pos['shares'], key="sell_shares")
                with c2:
                    st.markdown(f"当前价: ¥{current_price:.2f}")
                
                if st.button("🟢 卖出", type="primary", use_container_width=True):
                    revenue = sell_shares * current_price
                    
                    if sell_shares >= pos['shares']:
                        del account['positions'][symbol]
                    else:
                        pos['shares'] -= sell_shares
                    
                    account['cash'] += revenue
                    account['history'].append({
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'action': 'SELL',
                        'symbol': symbol,
                        'shares': sell_shares,
                        'price': current_price,
                        'revenue': revenue
                    })
                    
                    st.success(f"✅ 卖出成功！{symbol} {sell_shares}股 @ ¥{current_price:.2f}")
                    st.rerun()
        else:
            st.info("暂无持仓，请先买入股票")
    
    st.markdown("---")
    
    # 持仓列表
    st.subheader("📋 当前持仓")
    
    if account['positions']:
        positions_data = []
        for symbol, pos in account['positions'].items():
            current_price = pos.get('current_price', pos['cost_price'])
            market_value = pos['shares'] * current_price
            profit_pct = (current_price - pos['cost_price']) / pos['cost_price'] * 100
            
            positions_data.append({
                '代码': symbol,
                '股数': pos['shares'],
                '成本价': f"¥{pos['cost_price']:.2f}",
                '当前价': f"¥{current_price:.2f}",
                '市值': f"¥{market_value:,.0f}",
                '盈亏': f"{profit_pct:+.2f}%"
            })
        
        df_positions = pd.DataFrame(positions_data).set_index('代码')
        
        st.dataframe(
            df_positions.style.format({
                '市值': '{:.0f}',
            }).map(
                lambda x: 'color: #00ff00' if '+' in str(x) else ('color: #ff4444' if '-' in str(x) else 'color: #ffffff'),
                subset=['盈亏']
            ),
            width='stretch'
        )
    else:
        st.info("暂无持仓")
    
    # 交易记录
    st.subheader("📜 交易记录")
    
    if account['history']:
        history_data = []
        for h in account['history']:
            history_data.append({
                '时间': h['time'],
                '操作': '🔴 买入' if h['action'] == 'BUY' else '🟢 卖出',
                '代码': h['symbol'],
                '股数': h['shares'],
                '价格': f"¥{h['price']:.2f}",
                '金额': f"¥{h.get('cost', h.get('revenue', 0)):,.0f}"
            })
        
        df_history = pd.DataFrame(history_data).set_index('时间')
        st.dataframe(df_history, width='stretch')
        
        if st.button("🗑️ 清空记录"):
            account['history'] = []
            st.rerun()
    else:
        st.info("暂无交易记录")
    
    # 重置账户
    st.markdown("---")
    if st.button("🔄 重置模拟账户"):
        st.session_state.sim_account = {
            'cash': 100000,
            'positions': {},
            'history': [],
            'initial_cash': 100000
        }
        st.rerun()


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
        3. 配置到 `.env` 文件
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
