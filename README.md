# 🤖 AI Stock Trader - 智能量化交易系统

基于 Python 的 AI 量化交易系统，支持股票选股、策略回测、风险管理等功能。

## 📁 项目结构

```
ai-stock-trader/
├── src/
│   ├── data/           # 数据获取模块
│   │   ├── stock_api.py      # 股票数据接口
│   │   └── tushare_client.py # Tushare 客户端
│   ├── strategies/     # 交易策略
│   │   ├── base_strategy.py  # 策略基类
│   │   ├── moving_average_strategy.py    # 均线策略
│   │   ├── ai_stock_picker.py  # AI选股策略
│   │   └── portfolio_manager.py # 组合管理
│   ├── models/         # AI/ML模型
│   │   ├── stock_predictor.py  # 股价预测模型
│   │   └── factor_analyzer.py  # 因子分析
│   └── utils/         # 工具函数
│       ├── technical_analysis.py  # 技术分析
│       ├── risk_manager.py       # 风险管理
│       └── logger.py             # 日志配置
├── tests/             # 测试文件
├── config/           # 配置文件
├── notebooks/       # 研究笔记
├── README.md        # 项目说明
├── requirements.txt # 依赖包
├── .env.example     # 环境变量模板
└── .gitignore      # Git忽略文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

### 3. 运行示例

```bash
python examples/basic_usage.py
python examples/backtest_example.py
```

## 📊 功能特性

### 数据模块
- ✅ 股票实时行情（免费新浪接口）
- ✅ 历史K线数据获取
- ✅ 股票筛选器
- 🔄 Tushare 集成（需配置Token）

### 策略模块
- ✅ 均线交叉策略
- ✅ AI综合评分选股
- ✅ 组合管理
- 🔄 CTA策略回测

### AI/ML模块
- 🔄 股价预测模型
- 🔄 因子有效性分析
- 🔄 机器学习选股

### 风控模块
- ✅ 仓位管理
- 🔄 止损止盈
- 🔄 风险评估

## 📈 初期资金配置建议（1万元）

| 模块 | 投入 | 说明 |
|------|------|------|
| 股票数据 | ¥0 | Tushare免费接口 |
| 回测环境 | ¥0 | vn.py自带 |
| 实盘交易 | ¥0 | 需要券商开户 |
| 机器学习 | ¥0 | Python开源工具 |

## ⚠️ 免责声明

**本项目仅供学习和研究使用，不构成任何投资建议！**

股市有风险，投资需谨慎！

量化交易不能保证收益，请谨慎投资！

## 📝 许可证

MIT License

## 👨‍💻 作者

- 丁明旭 (@UrwLee)

---

**记住**：投资有风险，入市需谨慎！📊
