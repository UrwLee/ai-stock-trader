#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI选股增强模块
针对每只股票进行深度个性化分析
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.stock_api import StockDataAPI
from utils.logger import setup_logger

logger = setup_logger(__name__)


# 当前市场时政背景
MARKET_CONTEXT = """
## 2026年2月市场背景

### 宏观经济
- **十五五开局之年**: 五年规划第一年，政策支持力度大
- **流动性改善**: 人民币多次升破7.0，外资回流概率提升
- **美联储降息预期**: 二季度主席换届后，全球流动性继续宽松

### 政策方向
- **财政发力**: 专项债提速，投资数据回暖
- **AI产业**: 人工智能是规划重点发展方向
- **消费复苏**: 反内卷政策推动消费增长
- **资本市场改革**: 制度改革牛有望过渡到业绩牛

### 市场热点
- **科技**: AI链、半导体、光模块
- **顺周期**: 涨价品种、消费复苏
- **两会预期**: 2月后政策催化加速
"""


@dataclass
class StockAnalysis:
    """深度股票分析"""
    symbol: str
    name: str
    
    # 基础数据
    price: float
    change_pct: float
    volume: float
    high: float
    low: float
    
    # 评分
    final_score: float
    technical_score: float
    policy_score: float
    value_score: float
    
    # 信号
    recommendation: str
    technical_signal: str
    
    # 深度分析（针对每只股票个性化）
    macro_analysis: str      # 宏观分析
    technical_analysis: str    # 技术分析
    fundamentals_analysis: str # 基本面分析
    risk_analysis: str        # 风险分析
    investment_logic: str     # 投资逻辑


class EnhancedStockPicker:
    """增强版AI选股器 - 个性化分析"""
    
    def __init__(self):
        self.api = StockDataAPI(data_source="sina")
        self.context = self._load_market_context()
        
        # 板块政策映射
        self.policy_map = {
            # AI和科技
            "300750": {"policy": "新能源/AI产业", "score": 92, "desc": "动力电池龙头，受益于新能源汽车政策和AI发展"},
            "002594": {"policy": "新能源/汽车", "score": 90, "desc": "新能源汽车领导者，出口和智能化双轮驱动"},
            "002475": {"policy": "AI/消费电子", "score": 88, "desc": "苹果产业链龙头，AI终端带来新增长"},
            "300059": {"policy": "互联网金融", "score": 85, "desc": "东方财富，互联网券商龙头"},
            "002410": {"policy": "AI/建筑软件", "score": 82, "desc": "广联达，建筑信息化龙头，AI+建筑"},
            
            # 券商金融
            "600030": {"policy": "资本市场改革", "score": 88, "desc": "中信证券，券商龙头受益于资本市场改革"},
            "600837": {"policy": "资本市场改革", "score": 85, "desc": "海通证券，综合实力强"},
            "600999": {"policy": "资本市场改革", "score": 84, "desc": "招商证券，背靠招商银行"},
            
            # 消费
            "600519": {"policy": "消费复苏", "score": 85, "desc": "贵州茅台，高端白酒龙头，品牌价值稳固"},
            "000651": {"policy": "消费复苏", "score": 78, "desc": "格力电器，空调龙头，估值合理"},
            "000858": {"policy": "消费复苏", "score": 82, "desc": "五粮液，高端白酒次龙头，批价企稳回升"},
            
            # 医药
            "600276": {"policy": "医疗反腐完成", "score": 80, "desc": "恒瑞医药，创新药龙头，集采影响边际改善"},
            "600436": {"policy": "医疗反腐完成", "score": 82, "desc": "片仔癀，独家中成药，国家级绝密配方"},
            "300015": {"policy": "医疗反腐完成", "score": 78, "desc": "爱尔眼科，医疗服务龙头，扩张逻辑清晰"},
            
            # 基建
            "003013": {"policy": "财政发力", "score": 88, "desc": "地铁设计，受益于基建投资提速，专项债加速发行"},
            "601186": {"policy": "财政发力", "score": 85, "desc": "中国铁建，基建龙头，海外业务增长"},
            "601390": {"policy": "财政发力", "score": 84, "desc": "中国中铁，铁路建设龙头"},
            
            # 银行
            "601398": {"policy": "利率下行", "score": 72, "desc": "工商银行，国有大行，息差压力缓解"},
            "600036": {"policy": "利率下行", "score": 75, "desc": "招商银行，零售银行标杆，资产质量优异"},
        }
        
    def _load_market_context(self) -> Dict:
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "period": "2026年2月",
            "key_factors": {
                "macro": {
                    "十五五开局": {"impact": "positive", "score": 80},
                    "人民币升值": {"impact": "positive", "score": 70},
                    "美联储降息": {"impact": "positive", "score": 75},
                },
                "policy": {
                    "AI产业": {"impact": "positive", "score": 90},
                    "财政发力": {"impact": "positive", "score": 85},
                    "消费复苏": {"impact": "positive", "score": 70},
                }
            }
        }
    
    def analyze_stock(self, symbol: str, quote: Dict) -> StockAnalysis:
        """深度分析单只股票"""
        
        price = quote.get('close', 0)
        change_pct = quote.get('change_pct', 0)
        volume = quote.get('volume', 0)
        high = quote.get('high', price)
        low = quote.get('low', price)
        name = quote.get('name', symbol)
        
        # 获取政策信息
        if symbol in self.policy_map:
            policy_info = self.policy_map[symbol]
        else:
            # 默认值
            policy_info = {
                "policy": "一般",
                "score": 50,
                "desc": f"{symbol}，基本面一般，无明显催化剂"
            }
        
        # 1. 技术分析
        tech_score, tech_analysis = self._analyze_technical(price, change_pct, volume, high, low)
        
        # 2. 宏观分析
        macro_score, macro_analysis = self._analyze_macro(symbol, change_pct, price, policy_info)
        
        # 3. 基本面分析
        fund_score, fund_analysis = self._analyze_fundamentals(symbol, change_pct, price, policy_info)
        
        # 4. 风险分析
        risk_analysis = self._analyze_risk(symbol, change_pct, price, tech_score)
        
        # 5. 综合评分
        technical_score = tech_score * 0.4
        policy_score = policy_info["score"] * 0.35
        value_score = fund_score * 0.25
        final_score = technical_score + policy_score + value_score
        
        # 6. 投资逻辑
        investment_logic = self._generate_investment_logic(
            symbol, name, price, change_pct, tech_score, policy_info, policy_score
        )
        
        # 7. 推荐
        recommendation = self._get_recommendation(final_score, change_pct)
        
        # 8. 信号
        signal = "BUY" if tech_score > 65 else ("SELL" if tech_score < 40 else "HOLD")
        
        return StockAnalysis(
            symbol=symbol,
            name=name,
            price=price,
            change_pct=change_pct,
            volume=volume,
            high=high,
            low=low,
            final_score=final_score,
            technical_score=technical_score,
            policy_score=policy_score,
            value_score=value_score,
            recommendation=recommendation,
            technical_signal=signal,
            macro_analysis=macro_analysis,
            technical_analysis=tech_analysis,
            fundamentals_analysis=fund_analysis,
            risk_analysis=risk_analysis,
            investment_logic=investment_logic
        )
    
    def _analyze_technical(self, price: float, change_pct: float, 
                           volume: float, high: float, low: float) -> tuple:
        """技术分析"""
        score = 50
        analysis_parts = []
        
        # 动量分析
        if change_pct > 5:
            score += 25
            analysis_parts.append(f"今日暴涨{change_pct:.1f}%，短期动能极强")
        elif change_pct > 3:
            score += 20
            analysis_parts.append(f"今日大涨{change_pct:.1f}%，多头趋势明显")
        elif change_pct > 1:
            score += 15
            analysis_parts.append(f"今日上涨{change_pct:.1f}%，走势稳健")
        elif change_pct > 0:
            score += 10
            analysis_parts.append(f"小幅上涨{change_pct:.1f}%，温和反弹")
        else:
            score += 5
            analysis_parts.append(f"今日下跌{change_pct:.1f}%，存在低吸机会")
        
        # 振幅分析
        daily_range = (high - low) / low * 100 if low > 0 else 0
        if daily_range > 5:
            score += 10
            analysis_parts.append(f"日内振幅{daily_range:.1f}%，交易活跃")
        elif daily_range > 3:
            score += 7
            analysis_parts.append(f"日内振幅{daily_range:.1f}%，有一定波动")
        else:
            score += 5
            analysis_parts.append(f"日内振幅{daily_range:.1f}%，走势平稳")
        
        # 量能分析
        if volume > 20000000:
            score += 10
            analysis_parts.append("成交量明显放大，资金关注度高")
        elif volume > 10000000:
            score += 7
            analysis_parts.append("成交量温和放量")
        else:
            score += 3
            analysis_parts.append("成交量一般，市场关注度适中")
        
        # 价格位置
        if high > 0 and low > 0:
            price_position = (price - low) / (high - low) * 100 if high != low else 50
            if price_position > 80:
                score += 5
                analysis_parts.append(f"股价创日内新高，强势特征明显")
            elif price_position < 20:
                score -= 5
                analysis_parts.append(f"股价接近日内低点，需关注支撑")
            else:
                analysis_parts.append(f"股价处于日内中性位置")
        
        score = min(score, 100)
        
        return score, "；".join(analysis_parts)
    
    def _analyze_macro(self, symbol: str, change_pct: float, 
                       price: float, policy_info: Dict) -> tuple:
        """宏观分析"""
        score = policy_info["score"]
        analysis_parts = []
        
        # 政策受益
        analysis_parts.append(f"【政策面】{policy_info['desc']}")
        
        # 宏观背景
        if change_pct > 0:
            analysis_parts.append("在十五五开局之年，受益于政策支持")
            if change_pct > 3:
                analysis_parts.append("外资回流背景下，资金关注度提升")
        
        # 流动性
        if change_pct > 0:
            analysis_parts.append("人民币汇率企稳，利好资产价格")
        
        # 两会预期
        analysis_parts.append("两会临近，政策催化预期增强")
        
        return score, "；".join(analysis_parts)
    
    def _analyze_fundamentals(self, symbol: str, change_pct: float,
                            price: float, policy_info: Dict) -> tuple:
        """基本面分析"""
        score = 60
        analysis_parts = []
        
        # 估值合理性
        if 10 <= price <= 100:
            score += 15
            analysis_parts.append("股价适中，流动性好，适合交易")
        elif price > 500:
            score -= 10
            analysis_parts.append("股价较高，散户参与度可能受限")
        elif price < 5:
            score -= 5
            analysis_parts.append("股价偏低，注意基本面风险")
        
        # 涨跌幅合理性
        if change_pct > 7:
            score -= 10
            analysis_parts.append("短期涨幅较大，警惕回调风险")
        elif change_pct > 3:
            score -= 5
            analysis_parts.append("短期涨幅较多，适度回调风险")
        elif -3 < change_pct <= 0:
            score += 10
            analysis_parts.append("短期调整充分，估值吸引力提升")
        
        # 行业地位
        if policy_info["score"] >= 85:
            score += 10
            analysis_parts.append(f"{policy_info['policy']}领域龙头，竞争优势明显")
        elif policy_info["score"] >= 75:
            score += 5
            analysis_parts.append(f"行业地位稳固，有一定护城河")
        
        score = min(max(score, 0), 100)
        
        return score, "；".join(analysis_parts)
    
    def _analyze_risk(self, symbol: str, change_pct: float, 
                     price: float, tech_score: float) -> str:
        """风险分析"""
        risks = []
        
        # 市场风险
        if change_pct > 5:
            risks.append("短期涨幅过大，存在技术性回调压力")
        
        if tech_score > 80:
            risks.append("技术指标超买，注意追高风险")
        
        # 政策风险
        if symbol.startswith("60"):
            risks.append("关注中美贸易谈判进展对市场的影响")
        
        # 个股风险
        if symbol in ["300750", "002594"]:
            risks.append("新能源板块估值较高，赛道拥挤")
        
        # 通用风险
        risks.append("股市有风险，投资需谨慎")
        # 确保风险是字符串
        if risks:
            pass
        else:
            risks.append("股市有风险，投资需谨慎")
            risks.append("本分析仅供参考，不构成投资建议")
        
        return "；".join(risks)
    
    def _generate_investment_logic(self, symbol: str, name: str, price: float,
                                  change_pct: float, tech_score: float,
                                  policy_info: Dict, policy_score: float) -> str:
        """生成投资逻辑"""
        logic_parts = []
        
        # 核心逻辑
        logic_parts.append(f"【{name}（{symbol}）】")
        
        # 短期逻辑
        if change_pct > 3:
            logic_parts.append(f"短期：放量上涨{change_pct:.1f}%，多头趋势确立，可顺势跟进")
        elif change_pct > 0:
            logic_parts.append(f"短期：小幅上涨，走势稳健，可逢低布局")
        else:
            logic_parts.append(f"短期：调整后估值吸引力提升，可择机买入")
        
        # 中期逻辑
        if policy_score >= 85:
            logic_parts.append(f"中期：高度受益于{policy_info['policy']}政策，业绩增长确定性高")
        elif policy_score >= 70:
            logic_parts.append(f"中期：受益于{policy_info['policy']}政策，估值有支撑")
        
        # 催化剂
        logic_parts.append(f"催化剂：两会政策预期、流动性改善、外资回流")
        
        return "；".join(logic_parts)
    
    def _get_recommendation(self, score: float, change_pct: float) -> str:
        """推荐评级"""
        if score >= 85:
            return "⭐⭐⭐ 强烈推荐"
        elif score >= 75:
            return "⭐⭐ 推荐买入"
        elif score >= 65:
            return "⭐ 谨慎买入"
        elif score >= 55:
            return "➡️ 持有观望"
        else:
            return "⚠️ 建议回避"
    
    def pick_with_context(self, stock_symbols: List[str], top_n: int = 10) -> List[StockAnalysis]:
        """结合背景进行AI选股"""
        logger.info(f"开始深度分析 {len(stock_symbols)} 只股票...")
        
        batch_size = 30
        all_results = []
        
        for i in range(0, min(len(stock_symbols), 100), batch_size):
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

### 🎯 核心观点

**大盘判断**: 十五五开局之年，政策支持力度大，春季行情可期

### 🔥 政策主线

1. **AI产业政策** (重点关注)
   - 人工智能是规划重点发展方向
   - AI应用和出海是盈利增长驱动力

2. **财政发力** (基建受益)
   - 地方政府专项债发行提速
   - 基建投资有望回暖

3. **资本市场改革** (券商受益)
   - 制度改革牛有望过渡到业绩牛
   - 利好头部券商

### 💧 流动性

- 人民币汇率企稳，外资回流
- 美联储降息预期，全球流动性宽松
- 关注两会后的政策催化

### 📈 板块推荐

**🔥 强烈推荐**:
- AI产业链（半导体、光模块）
- 基建投资（专项债受益）

**⭐ 推荐关注**:
- 券商板块（资本市场改革）
- 消费板块（复苏预期）
- 医药板块（边际改善）

### ⚠️ 风险提示

1. 中美贸易摩擦谈判进展
2. 房地产市场边际改善但仍需观察
3. 科技板块估值过高风险
4. 短期涨幅过大后的回调风险

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return report


if __name__ == "__main__":
    print("=" * 80)
    print("AI选股增强模块测试")
    print("=" * 80)
    
    picker = EnhancedStockPicker()
    
    # 测试
    test_symbols = ["600519", "003013", "300750", "000651", "600030"]
    
    print("\n🎯 深度分析结果")
    print("-" * 80)
    
    results = picker.pick_with_context(test_symbols, top_n=5)
    
    for i, stock in enumerate(results, 1):
        print(f"\n{i}. {stock.symbol} - {stock.name}")
        print(f"   评分: {stock.final_score:.0f}/100 | {stock.recommendation}")
        print(f"   价格: ¥{stock.price:.2f} ({stock.change_pct:+.2f}%)")
        print(f"   技术分: {stock.technical_score:.0f} | 政策分: {stock.policy_score:.0f} | 价值分: {stock.value_score:.0f}")
        print(f"   投资逻辑: {stock.investment_logic}")
        print(f"   风险: {stock.risk_analysis[:50]}...")
