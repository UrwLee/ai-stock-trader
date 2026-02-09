#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI选股增强模块
结合历史数据、时政信息、经济政策进行趋势预测
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.stock_api import StockDataAPI
from utils.logger import setup_logger

logger = setup_logger(__name__)


# 当前市场时政背景（2026年2月）
MARKET_CONTEXT = """
## 2026年2月市场背景

### 宏观经济
- **十五五开局之年**: 2026年是五年规划第一年，政策落地大年
- **流动性改善**: 2025年末人民币多次升破7.0，外资回流概率提升
- **美联储降息**: 二季度美联储主席换届后，全球流动性继续宽松

### 政策方向
- **财政政策**: 地方政府专项债发行提速，中央预算内投资加码
- **产业政策**: AI应用、"出海"趋势、反内卷政策
- **改革预期**: 制度改革牛有望过渡到业绩牛

### 市场热点
- **科技**: AI链、半导体、光模块
- **顺周期**: 涨价品种、消费复苏
- **两会预期**: 2月后政策催化加速
"""


@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    symbol: str
    name: str
    
    # 基础数据
    price: float
    change_pct: float
    
    # 技术分析
    trend_score: float  # 0-100
    technical_signal: str  # BUY/SELL/HOLD
    
    # 政策分析
    policy_score: float  # 0-100
    policy_reason: str
    
    # 综合评分
    final_score: float  # 0-100
    recommendation: str
    
    # 详细理解
    analysis: str
    
    # 风险提示
    risks: List[str]


class EnhancedStockPicker:
    """增强版AI选股器"""
    
    def __init__(self):
        self.api = StockDataAPI(data_source="sina")
        self.context = self._load_market_context()
        
    def _load_market_context(self) -> Dict:
        """加载市场背景"""
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "period": "2026年2月",
            "key_factors": {
                "macro": {
                    "十五五开局": {"impact": "positive", "score": 80, 
                                "desc": "五年规划第一年，政策支持力度大"},
                    "人民币升值": {"impact": "positive", "score": 70,
                                "desc": "外资回流，提升市场流动性"},
                    "美联储降息预期": {"impact": "positive", "score": 75,
                                "desc": "全球流动性宽松，利好新兴市场"},
                },
                "policy": {
                    "财政发力": {"impact": "positive", "score": 85,
                               "desc": "专项债提速，投资数据回暖"},
                    "AI产业政策": {"impact": "positive", "score": 90,
                                 "desc": "AI应用和出海是主线"},
                    "消费复苏": {"impact": "positive", "score": 65,
                               "desc": "反内卷政策推动消费增长"},
                },
                "risks": {
                    "中美贸易摩擦": "潜在风险，需关注谈判进展",
                    "房地产市场": "风险因素，但已边际改善",
                    "科技泡沫": "警惕估值过高风险"
                }
            }
        }
    
    def analyze_stock(self, symbol: str, quote: Dict) -> TrendAnalysis:
        """深度分析单只股票"""
        
        price = quote.get('close', 0)
        change_pct = quote.get('change_pct', 0)
        name = quote.get('name', symbol)
        
        # 1. 技术分析（简化版）
        trend_score = self._calculate_trend_score(price, change_pct)
        
        # 2. 政策匹配分析
        policy_score, policy_reason = self._analyze_policy_match(symbol, change_pct)
        
        # 3. 计算综合评分
        final_score = (trend_score * 0.4 + policy_score * 0.6)
        
        # 4. 生成推荐
        recommendation = self._generate_recommendation(final_score, change_pct)
        
        # 5. 生成详细分析
        analysis = self._generate_analysis(symbol, name, trend_score, policy_score, change_pct)
        
        # 6. 风险提示
        risks = self._identify_risks(symbol, change_pct, trend_score)
        
        return TrendAnalysis(
            symbol=symbol,
            name=name,
            price=price,
            change_pct=change_pct,
            trend_score=trend_score,
            technical_signal="BUY" if trend_score > 60 else ("SELL" if trend_score < 40 else "HOLD"),
            policy_score=policy_score,
            policy_reason=policy_reason,
            final_score=final_score,
            recommendation=recommendation,
            analysis=analysis,
            risks=risks
        )
    
    def _calculate_trend_score(self, price: float, change_pct: float) -> float:
        """计算技术趋势评分"""
        score = 50  # 基础分
        
        # 动量因子 (30分)
        if change_pct > 5:
            score += 30
        elif change_pct > 3:
            score += 25
        elif change_pct > 1:
            score += 20
        elif change_pct > 0:
            score += 15
        else:
            score += 5
        
        # 价格因子 (10分)
        if 10 <= price <= 100:
            score += 10
        
        # 量能因子 (10分)
        if change_pct > 0:
            score += 10
        
        return min(score, 100)
    
    def _analyze_policy_match(self, symbol: str, change_pct: float) -> tuple:
        """分析政策匹配度"""
        
        # 板块政策映射
        policy_map = {
            # AI和科技
            ("300750", "002594", "002475", "300059", "002410"): {
                "政策": "AI产业政策",
                "描述": "人工智能是十五五规划重点发展方向",
                "得分": 95
            },
            ("600030", "600837", "600999", "601066"): {
                "政策": "资本市场改革",
                "描述": "制度改革牛利好券商板块",
                "得分": 80
            },
            ("000651", "000858", "000568"): {
                "政策": "消费复苏",
                "描述": "反内卷政策推动消费增长",
                "得分": 75
            },
            ("601398", "600036", "601988"): {
                "政策": "利率下行",
                "描述": "宽松货币政策利好银行息差",
                "得分": 70
            },
            ("600276", "600436", "300015"): {
                "政策": "医疗反腐完成",
                "描述": "医药行业边际改善",
                "得分": 65
            },
            ("003013", "601186", "601390"): {
                "政策": "财政发力",
                "描述": "基建投资提速，专项债加速发行",
                "得分": 85
            }
        }
        
        # 查找匹配
        for symbols, policy in policy_map.items():
            if symbol in symbols:
                base_score = policy["得分"]
                
                # 根据涨幅调整
                if change_pct > 3:
                    adjust = min(change_pct * 2, 10)
                elif change_pct > 0:
                    adjust = 5
                else:
                    adjust = 0
                
                return min(base_score + adjust, 100), f"{policy['政策']}: {policy['描述']}"
        
        # 默认评分
        return 50, "基本面一般，需更多催化剂"
    
    def _generate_recommendation(self, score: float, change_pct: float) -> str:
        """生成推荐"""
        if score >= 80:
            return "⭐⭐⭐ 强烈推荐"
        elif score >= 70:
            return "⭐⭐ 推荐买入"
        elif score >= 60:
            return "⭐ 谨慎买入"
        elif score >= 50:
            return "➡️ 持有观望"
        else:
            return "⚠️ 建议回避"
    
    def _generate_analysis(self, symbol: str, name: str, trend_score: float, 
                          policy_score: float, change_pct: float) -> str:
        """生成详细分析"""
        
        analysis_parts = []
        
        # 1. 宏观背景
        analysis_parts.append(f"📈 **宏观背景**: 2026年是十五五开局之年，政策支持力度大。")
        
        # 2. 技术面
        if trend_score >= 70:
            analysis_parts.append(f"✅ **技术面**: 短期动能强劲，涨幅{change_pct:+.1f}%表现亮眼。")
        elif trend_score >= 50:
            analysis_parts.append(f"📊 **技术面**: 温和上涨，动能一般。")
        else:
            analysis_parts.append(f"⚠️ **技术面**: 短期承压，需要催化剂。")
        
        # 3. 政策面
        if policy_score >= 80:
            analysis_parts.append(f"🎯 **政策面**: 高度受益于当前政策导向，AI/基建/消费等主线明确。")
        elif policy_score >= 60:
            analysis_parts.append(f"📋 **政策面**: 受益于政策边际改善。")
        else:
            analysis_parts.append(f"📋 **政策面**: 政策相关性一般。")
        
        # 4. 流动性
        if change_pct > 0:
            analysis_parts.append(f"💧 **资金面**: 资金关注度高，成交量活跃。")
        
        # 5. 两会预期
        analysis_parts.append(f"🗓️ **两会预期**: 2月后政策催化加速，可关注政策驱动机会。")
        
        return "\n\n".join(analysis_parts)
    
    def _identify_risks(self, symbol: str, change_pct: float, trend_score: float) -> List[str]:
        """识别风险"""
        risks = []
        
        # 市场风险
        if change_pct > 7:
            risks.append("短期涨幅过大，存在回调风险")
        
        if trend_score < 40:
            risks.append("技术面偏弱，可能继续下行")
        
        # 政策风险
        if symbol.startswith("60"):
            risks.append("关注中美贸易谈判进展")
        
        # 个股风险
        if symbol in ["300750", "002594"]:
            risks.append("新能源板块估值较高，警惕泡沫")
        
        # 通用风险
        risks.append("股市有风险，投资需谨慎")
        risks.append("本分析仅供参考，不构成投资建议")
        
        return risks
    
    def pick_with_context(self, stock_symbols: List[str], top_n: int = 10) -> List[TrendAnalysis]:
        """
        结合背景进行AI选股
        
        Args:
            stock_symbols: 候选股票列表
            top_n: 返回数量
            
        Returns:
            排序后的趋势分析列表
        """
        logger.info(f"开始分析 {len(stock_symbols)} 只股票...")
        
        # 批量获取数据
        batch_size = 30
        all_results = []
        
        for i in range(0, len(stock_symbols), batch_size):
            batch = stock_symbols[i:i+batch_size]
            quotes = self.api.get_realtime_quote(batch)
            
            for symbol, quote in quotes.items():
                if quote:
                    analysis = self.analyze_stock(symbol, quote)
                    all_results.append(analysis)
        
        # 按评分排序
        sorted_results = sorted(all_results, key=lambda x: x.final_score, reverse=True)
        
        logger.info(f"分析完成，选取TOP {top_n}")
        
        return sorted_results[:top_n]
    
    def get_market_report(self) -> str:
        """获取市场分析报告"""
        
        report = f"""
## 📊 {self.context['date']} 市场分析报告

### 🎯 宏观背景

**时期**: {self.context['period']}
**定位**: 十五五开局之年

### 🔥 核心政策主线

1. **AI产业政策** (得分: 90/100)
   - 人工智能是规划重点发展方向
   - AI应用和出海是盈利增长驱动力

2. **财政发力** (得分: 85/100)  
   - 地方政府专项债发行提速
   - 中央预算内投资加码

3. **资本市场改革** (得分: 80/100)
   - 制度改革牛有望过渡到业绩牛
   - 券商板块受益

4. **消费复苏** (得分: 75/100)
   - 反内卷政策推动消费增长
   - 关注必需消费和高端消费

### 💧 流动性

- 人民币汇率企稳，外资回流
- 美联储降息预期，全球流动性宽松
- 关注两会后的政策催化

### ⚠️ 风险提示

1. 中美贸易摩擦谈判进展
2. 房地产市场边际改善但仍需观察
3. 科技板块估值过高风险
4. 短期涨幅过大后的回调风险

### 📈 板块推荐

**🔥 强烈推荐**:
- AI产业链（半导体、光模块）
- 基建投资（专项债受益）

**⭐ 推荐关注**:
- 券商板块（资本市场改革）
- 消费板块（复苏预期）
- 医药板块（边际改善）

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return report


if __name__ == "__main__":
    print("=" * 80)
    print("AI选股增强模块测试")
    print("=" * 80)
    
    picker = EnhancedStockPicker()
    
    # 获取市场报告
    report = picker.get_market_report()
    print(report)
    
    # 测试选股
    test_stocks = ["600519", "003013", "300750", "000651"]
    print("\n" + "=" * 80)
    print("🎯 AI选股结果")
    print("=" * 80)
    
    results = picker.pick_with_context(test_stocks, top_n=5)
    
    for i, stock in enumerate(results, 1):
        print(f"\n{i}. {stock.symbol} - {stock.name}")
        print(f"   评分: {stock.final_score:.0f}/100 | 推荐: {stock.recommendation}")
        print(f"   当前价: ¥{stock.price:.2f} ({stock.change_pct:+.2f}%)")
        print(f"   技术分: {stock.trend_score:.0f} | 政策分: {stock.policy_score:.0f}")
        print(f"   政策理由: {stock.policy_reason}")
        print(f"   分析: {stock.analysis[:100]}...")
