#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Stock Trader - Web可视化界面
支持电脑和手机响应式显示

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
        pass

# 响应式CSS样式
st.markdown("""
<style>
    /* 响应式基础样式 */
    @media (max-width: 768px) {
        .stock-card {
            padding: 10px !important;
            margin: 3px !important;
        }
        .metric-card {
            padding: 8px !important;
        }
        h1 { font-size: 24px !important; }
        h2 { font-size: 20px !important; }
        h3 { font-size: 16px !important; }
    }
    
    @media (min-width: 769px) {
        .stock-card {
            padding: 15px !important;
            margin: 5px !important;
        }
        .metric-card {
            padding: 15px !important;
        }
    }
    
    /* 深色主题 */
    .stApp {
        background-color: #1a1a2e;
    }
    
    [data-testid="stSidebar"] {
        background-color: #16213e;
    }
    
    /* 标题 */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* 标签页 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #16213e;
    }
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
    }
    
    /* 股票卡片 - 响应式 */
    .stock-card {
        background-color: #0f3460;
        border-radius: 10px;
        border: 1px solid #1a1a2e;
        text-align: center;
    }
    
    .stock-card:hover {
        border-color: #00d9ff;
        transform: scale(1.02);
    }
    
    .stock-name {
        color: #b0b0b0 !important;
        font-size: 12px;
    }
    
    .stock-price {
        color: #00d9ff !important;
        font-size: 18px;
        font-weight: bold;
    }
    
    .stock-change {
        font-size: 14px;
        font-weight: bold;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 18px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #b0b0b0 !important;
        font-size: 12px !important;
    }
    
    /* 表格 */
    .stDataFrame {
        font-size: 12px !important;
    }
    
    /* 按钮 */
    .stButton > button {
        color: #ffffff !important;
        background-color: #0f3460 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
    }
    
    /* 输入框 */
    .stTextInput input, .stNumberInput input {
        color: #ffffff !important;
        background-color: #0f3460 !important;
    }
    
    /* Selectbox */
    .stSelectbox label {
        color: #ffffff !important;
    }
    
    /* Info/Warning/Success */
    .stAlert {
        color: #ffffff !important;
        padding: 10px !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        color: #ffffff !important;
        background-color: #0f3460 !important;
        padding: 10px !important;
    }
    
    /* Progress */
    .stProgress > div > div > span {
        color: #ffffff !important;
    }
    
    /* 下载按钮 */
    .stDownloadButton > button {
        color: #ffffff !important;
        background-color: #0f3460 !important;
    }
    
    /* Slider */
    .stSlider label {
        color: #ffffff !important;
    }
    
    /* 底部 */
    .footer {
        text-align: center;
        color: #666;
        font-size: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 响应式布局辅助函数
def responsive_columns(n: int):
    """根据屏幕大小返回合适的列数"""
    if n == 2:
        return st.columns(2)
    elif n == 3:
        return st.columns(3)
    elif n == 4:
        return st.columns([1,1,1,1]) if st.session_state.get('is_mobile') else st.columns(4)
    else:
        return st.columns(min(n, 4))

# 股票卡片组件
def stock_card(symbol: str, name: str, price: float, change_pct: float):
    """显示股票卡片"""
    # 颜色
    if change_pct > 0:
        change_color = "#ff4444"
        change_icon = "🔴"
        change_prefix = "+"
    elif change_pct < 0:
        change_color = "#00ff00"
        change_icon = "🟢"
        change_prefix = ""
    else:
        change_color = "#b0b0b0"
        change_icon = "⚪"
        change_prefix = ""
    
    st.markdown(f"""
    <div class="stock-card">
        <div style="font-weight: bold; color: #ffffff; font-size: 16px;">{symbol}</div>
        <div class="stock-name">{name}</div>
        <div class="stock-price">¥{price:.2f}</div>
        <div class="stock-change" style="color: {change_color};">
            {change_icon} {change_prefix}{change_pct:.2f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# 标题
st.title("🤖 AI Stock Trader")
st.markdown("**智能量化交易系统**")
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("📊 功能")
    
    page = st.selectbox(
        "",
        ["🏠 首页", "📈 实时行情", "🎯 AI选股", "💼 模拟炒股"]
    )
    
    st.markdown("---")
    st.caption("💡 提示:")
    st.caption("• 首页查看热门板块")
    st.caption("• 实时行情自选保存")
    st.caption("• AI选股智能筛选")
    st.caption("• 模拟炒股练手")


# ========== 页面0: 首页 ==========
if page == "🏠 首页":
    st.header("🏠 市场概览")
    
    api = StockDataAPI(data_source="sina")
    all_stocks = api.get_a_stock_list()
    
    # 板块标签
    categories = [
        ("🔥 全部", "all"),
        ("🏦 银行", "bank"),
        ("💊 医药", "medicine"),
        ("💻 科技", "tech"),
        ("🚗 新能源", "energy"),
        ("🍺 消费", "consumer"),
    ]
    
    # 创建标签页
    tabs = st.tabs([cat[0] for cat in categories])
    
    for tab, (name, category) in zip(tabs, categories):
        with tab:
            # 获取股票
            if category == "all":
                stock_symbols = [s['symbol'] for s in all_stocks[:30]]
            else:
                stock_symbols = api.get_hot_stocks(category)
            
            if stock_symbols:
                quotes = api.get_realtime_quote(stock_symbols[:20])
                
                if quotes:
                    # 响应式卡片布局 - 手机2列，电脑4列
                    cols = st.columns(2)
                    idx = 0
                    
                    for symbol, quote in quotes.items():
                        col = cols[idx % 2]
                        with col:
                            stock_card(
                                symbol,
                                quote.get('name', '-'),
                                quote['close'],
                                quote['change_pct']
                            )
                        idx += 1
                    
                    # 统计
                    up = sum(1 for q in quotes.values() if q['change_pct'] > 0)
                    down = sum(1 for q in quotes.values() if q['change_pct'] < 0)
                    st.markdown(f"""
                    <div style="text-align: center; color: #b0b0b0; margin-top: 10px;">
                        🟢 {up}只  🔴 {down}只  共{len(quotes)}只
                    </div>
                    """, unsafe_allow_html=True)


# ========== 页面1: 实时行情 ==========
elif page == "📈 实时行情":
    st.header("📈 实时行情")
    
    api = StockDataAPI(data_source="sina")
    config = load_user_config()
    
    # 选择区域
    col1, col2 = st.columns([3, 1])
    with col1:
        all_stocks = api.get_a_stock_list()
        stock_options = [f"{s['symbol']} {s['name']}" for s in all_stocks[:200]]
        
        default_values = []
        if config.get("watchlist"):
            for s in all_stocks:
                if s['symbol'] in config["watchlist"]:
                    default_values.append(f"{s['symbol']} {s['name']}")
        
        if not default_values:
            default_values = stock_options[:3]
        
        selected = st.multiselect(
            "选择股票",
            options=stock_options,
            default=default_values,
            help="选择后自动保存"
        )
    
    with col2:
        st.write("")
        if st.button("💾 保存", use_container_width=True):
            if selected:
                symbols = [s.split(" ")[0] for s in selected]
                config["watchlist"] = symbols
                save_user_config(config)
                st.success("已保存!")
        
        if st.button("🔄 刷新"):
            st.rerun()
    
    # 显示行情
    if selected:
        symbols = [s.split(" ")[0] for s in selected]
        quotes = api.get_realtime_quote(symbols)
        
        if quotes:
            # 统计
            up = sum(1 for q in quotes.values() if q['change_pct'] > 0)
            down = sum(1 for q in quotes.values() if q['change_pct'] < 0)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("↑", f"{up}只")
            c2.metric("↓", f"{down}只")
            c3.metric("共", f"{len(quotes)}只")
            
            # 表格
            data = []
            for symbol, quote in quotes.items():
                data.append({
                    "代码": symbol,
                    "名称": quote.get('name', '-'),
                    "价格": quote['close'],
                    "涨跌": f"{quote['change_pct']:+.2f}%",
                    "最高": quote['high'],
                    "最低": quote['low'],
                })
            
            df = pd.DataFrame(data).set_index("代码")
            
            st.dataframe(
                df.style.format({
                    "价格": "{:.2f}",
                    "最高": "{:.2f}",
                    "最低": "{:.2f}",
                }).map(
                    lambda x: 'color: #ff4444' if isinstance(x, str) and '+' in x else ('color: #00ff00' if isinstance(x, str) and '-' in x else 'color: #ffffff'),
                    subset=["涨跌"]
                ),
                use_container_width=True
            )


# ========== 页面2: AI选股 ==========
elif page == "🎯 AI选股":
    st.header("🎯 AI智能选股")
    
    # 市场背景 - 默认展开
    with st.expander("📊 当前市场背景 (2026年2月)", expanded=True):
        st.markdown("""
        **宏观背景**: 十五五开局之年，政策支持力度大
        
        **核心政策**:
        - AI产业政策 (90分)
        - 财政发力 (85分)
        - 消费复苏 (75分)
        
        **流动性**: 人民币升值，外资回流
        **风险**: 中美贸易、房地产
        """)
    
    # 市场分析报告
    with st.expander("📈 市场分析报告", expanded=True):
        picker = EnhancedStockPicker()
        report = picker.get_market_report()
        st.markdown(report)
    
    # 设置
    col1, col2 = st.columns(2)
    with col1:
        top_n = st.slider("选择数量", 5, 20, 10)
    with col2:
        sector = st.selectbox("板块", ["全部", "AI科技", "券商金融", "消费", "医药", "基建"])
    
    # 开始选股
    if st.button("🚀 开始AI选股", type="primary", use_container_width=True):
        with st.spinner("AI分析中..."):
            api = StockDataAPI(data_source="sina")
            picker = EnhancedStockPicker()
            
            all_stocks = api.get_a_stock_list()
            stock_symbols = [s['symbol'] for s in all_stocks]
            
            results = picker.pick_with_context(stock_symbols, top_n=top_n * 2)
            
            # 板块过滤
            if sector != "全部":
                sector_map = {
                    "AI科技": ["300750", "002594", "002475"],
                    "券商金融": ["600030", "600837"],
                    "消费": ["000651", "000858"],
                    "医药": ["600276", "600436"],
                    "基建": ["003013", "601186"]
                }
                allowed = sector_map.get(sector, [])
                results = [r for r in results if r.symbol in allowed]
            
            final_results = results[:top_n]
        
        if final_results:
            st.success(f"选出 {len(final_results)} 只股票")
            
            for i, stock in enumerate(final_results, 1):
                with st.expander(f"{i}. {stock.symbol} {stock.name} ({stock.final_score:.0f}分)", expanded=i<=3):
                    # 基础信息
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("价格", f"¥{stock.price:.2f}")
                    c2.metric("涨跌", f"{stock.change_pct:+.2f}%")
                    c3.metric("技术分", f"{stock.trend_score:.0f}")
                    c4.metric("政策分", f"{stock.policy_score:.0f}")
                    
                    st.markdown(f"**{stock.recommendation}**")
                    
                    # 分析
                    st.markdown(f"📊 {stock.analysis}")
                    
                    # 风险
                    if stock.risks:
                        st.warning(stock.risks[0])


# ========== 页面3: 模拟炒股 ==========
elif page == "💼 模拟炒股":
    st.header("💼 模拟炒股")
    
    # 初始化
    if 'sim_account' not in st.session_state:
        st.session_state.sim_account = {
            'cash': 100000,
            'positions': {},
            'history': [],
            'initial_cash': 100000
        }
    
    account = st.session_state.sim_account
    api = StockDataAPI(data_source="sina")
    
    # 计算资产
    total_value = account['cash']
    positions_value = 0
    
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
    
    # 账户概览
    c1, c2, c3 = st.columns(3)
    c1.metric("总资产", f"¥{total_value:,.0f}", f"{total_return:+.2f}%")
    c2.metric("可用资金", f"¥{account['cash']:,.0f}")
    c3.metric("交易次数", f"{len(account['history'])}")
    
    st.markdown("---")
    
    # 买卖操作
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 买入")
        buy_symbol = st.text_input("代码", value="600519", key="buy_s")
        buy_price = st.number_input("价格", value=1500.0, key="buy_p")
        buy_shares = st.number_input("股数", min_value=100, value=100, step=100, key="buy_n")
        
        if st.button("🔴 买入", use_container_width=True):
            cost = buy_shares * buy_price
            if cost <= account['cash']:
                if buy_symbol in account['positions']:
                    old = account['positions'][buy_symbol]
                    new_shares = old['shares'] + buy_shares
                    new_cost = (old['shares'] * old['cost_price'] + cost) / new_shares
                    account['positions'][buy_symbol] = {'shares': new_shares, 'cost_price': new_cost}
                else:
                    account['positions'][buy_symbol] = {'shares': buy_shares, 'cost_price': buy_price}
                
                account['cash'] -= cost
                account['history'].append({
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'action': 'BUY',
                    'symbol': buy_symbol,
                    'shares': buy_shares,
                    'price': buy_price
                })
                st.success(f"买入 {buy_symbol} {buy_shares}股")
                st.rerun()
            else:
                st.error("资金不足")
    
    with col2:
        st.subheader("📉 卖出")
        if account['positions']:
            sell_options = [f"{s} ({p['shares']}股)" for s, p in account['positions'].items()]
            sell_choice = st.selectbox("选择", sell_options, key="sell_sel")
            
            if sell_choice:
                symbol = sell_choice.split("(")[0]
                pos = account['positions'][symbol]
                current_price = pos.get('current_price', pos['cost_price'])
                
                st.write(f"当前价: ¥{current_price:.2f}")
                sell_shares = st.number_input("股数", 1, pos['shares'], pos['shares'], key="sell_n")
                
                if st.button("🟢 卖出", use_container_width=True):
                    revenue = sell_shares * current_price
                    
                    if sell_shares >= pos['shares']:
                        del account['positions'][symbol]
                    else:
                        pos['shares'] -= sell_shares
                    
                    account['cash'] += revenue
                    account['history'].append({
                        'time': datetime.now().strftime("%H:%M:%S"),
                        'action': 'SELL',
                        'symbol': symbol,
                        'shares': sell_shares,
                        'price': current_price
                    })
                    st.success(f"卖出 {symbol} {sell_shares}股")
                    st.rerun()
        else:
            st.info("暂无持仓")
    
    st.markdown("---")
    
    # 持仓
    st.subheader("📋 持仓")
    if account['positions']:
        data = []
        for symbol, pos in account['positions'].items():
            current_price = pos.get('current_price', pos['cost_price'])
            market_value = pos['shares'] * current_price
            profit = (current_price - pos['cost_price']) / pos['cost_price'] * 100
            
            data.append({
                "代码": symbol,
                "股数": pos['shares'],
                "成本": f"¥{pos['cost_price']:.2f}",
                "现价": f"¥{current_price:.2f}",
                "市值": f"¥{market_value:,.0f}",
                "盈亏": f"{profit:+.2f}%"
            })
        
        df = pd.DataFrame(data).set_index("代码")
        st.dataframe(
            df.style.format({
                "市值": "{:.0f}",
            }).map(
                lambda x: 'color: #ff4444' if isinstance(x, str) and '+' in x else ('color: #00ff00' if isinstance(x, str) and '-' in x else 'color: #ffffff'),
                subset=["盈亏"]
            ),
            use_container_width=True
        )
    
    # 交易记录
    if account['history']:
        with st.expander(f"📜 交易记录 ({len(account['history'])}条)"):
            for h in reversed(account['history'][-10:]):
                emoji = "🔴" if h['action'] == "BUY" else "🟢"
                st.write(f"{h['time']} {emoji} {h['action']} {h['symbol']} {h['shares']}股 @ ¥{h['price']:.2f}")
    
    # 重置
    if st.button("🔄 重置"):
        st.session_state.sim_account = {
            'cash': 100000,
            'positions': {},
            'history': [],
            'initial_cash': 100000
        }
        st.rerun()

# 底部
st.markdown("---")
st.markdown(
    """
    <div class="footer">
    🤖 AI Stock Trader | ⚠️ 股市有风险，投资需谨慎
    </div>
    """,
    unsafe_allow_html=True
)
