"""
训练数据分析器
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta


class TrainingAnalyzer:
    """训练数据分析器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化训练分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.thresholds = {
            "low_load": 0,
            "optimal_load": 300,
            "high_load": 600,
            "very_high_load": 900,
            "overtraining_atl": 1.5,  # ATI/CTI比值
        }
        if config and "training_thresholds" in config:
            self.thresholds.update(config["training_thresholds"])
    
    def analyze_training_data(self, daily_metrics: Dict, activities: Dict = None) -> Dict:
        """
        分析训练数据
        
        Args:
            daily_metrics: 每日指标数据
            activities: 活动记录数据（可选）
            
        Returns:
            dict: 分析结果
        """
        records = daily_metrics.get("records", [])
        
        if not records:
            return {"error": "没有训练数据"}
        
        # 转换为DataFrame
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d')
        df = df.sort_values('date')
        
        # 执行各项分析
        analysis = {
            "summary": self._calculate_training_summary(df),
            "training_load": self._analyze_training_load(df),
            "fitness_level": self._analyze_fitness_level(df),
            "overtraining_risk": self._assess_overtraining_risk(df),
            "recommendations": []
        }
        
        # 如果有活动数据，增加活动分析
        if activities and "activities" in activities:
            analysis["activity_analysis"] = self._analyze_activities(activities)
        
        # 生成训练建议
        analysis["recommendations"] = self._generate_training_recommendations(analysis)
        
        return analysis
    
    def _calculate_training_summary(self, df: pd.DataFrame) -> Dict:
        """计算训练摘要统计"""
        return {
            "total_days": len(df),
            "avg_training_load": round(df['training_load'].mean(), 1),
            "max_training_load": round(df['training_load'].max(), 1),
            "avg_rhr": round(df['rhr'].mean(), 1),
            "min_rhr": round(df['rhr'].min(), 1),
            "avg_hrv": round(df['avg_sleep_hrv'].mean(), 1) if 'avg_sleep_hrv' in df.columns else None,
            "vo2max_latest": round(df['vo2max'].iloc[-1], 1) if 'vo2max' in df.columns else None,
            "vo2max_change": round(df['vo2max'].iloc[-1] - df['vo2max'].iloc[0], 1) if 'vo2max' in df.columns and len(df) > 1 else None,
            "total_distance_km": round(df['distance'].sum() / 1000, 1) if 'distance' in df.columns else None,
            "total_duration_hours": round(df['duration'].sum() / 3600, 1) if 'duration' in df.columns else None,
        }
    
    def _analyze_training_load(self, df: pd.DataFrame) -> Dict:
        """分析训练负荷"""
        # 计算急性训练负荷（ATI）和慢性训练负荷（CTI）
        ati = df['ati'].iloc[-1] if 'ati' in df.columns else df['training_load'].tail(7).mean()
        cti = df['cti'].iloc[-1] if 'cti' in df.columns else df['training_load'].tail(42).mean()
        
        # 计算训练负荷比值
        load_ratio = df['training_load_ratio'].iloc[-1] if 'training_load_ratio' in df.columns else (ati / cti if cti > 0 else 0)
        
        # 评估训练负荷状态
        if load_ratio < 0.8:
            status = "训练不足"
            recommendation = "建议适当增加训练量"
        elif load_ratio < 1.3:
            status = "训练平衡"
            recommendation = "训练负荷处于健康范围，继续保持"
        elif load_ratio < 1.5:
            status = "训练偏高"
            recommendation = "注意恢复，避免过度训练"
        else:
            status = "过度训练风险"
            recommendation = "建议降低训练强度，增加恢复时间"
        
        # 计算训练负荷趋势
        recent_load = df['training_load'].tail(7).mean()
        earlier_load = df['training_load'].head(7).mean() if len(df) >= 14 else df['training_load'].iloc[0]
        
        if recent_load > earlier_load * 1.1:
            trend = "上升"
        elif recent_load < earlier_load * 0.9:
            trend = "下降"
        else:
            trend = "稳定"
        
        return {
            "acute_load": round(ati, 1),
            "chronic_load": round(cti, 1),
            "load_ratio": round(load_ratio, 2),
            "status": status,
            "recommendation": recommendation,
            "trend": trend,
            "training_load_status": self._classify_training_load(df['training_load'].mean())
        }
    
    def _classify_training_load(self, avg_load: float) -> str:
        """分类训练负荷水平"""
        if avg_load < self.thresholds["optimal_load"]:
            return "偏低"
        elif avg_load < self.thresholds["high_load"]:
            return "适中"
        elif avg_load < self.thresholds["very_high_load"]:
            return "偏高"
        else:
            return "过高"
    
    def _analyze_fitness_level(self, df: pd.DataFrame) -> Dict:
        """分析体能水平"""
        fitness = {}
        
        # VO2max分析
        if 'vo2max' in df.columns:
            latest_vo2max = df['vo2max'].iloc[-1]
            fitness["vo2max"] = {
                "current": round(latest_vo2max, 1),
                "change": round(df['vo2max'].iloc[-1] - df['vo2max'].iloc[0], 1) if len(df) > 1 else 0,
                "rating": self._rate_vo2max(latest_vo2max)
            }
        
        # 静息心率分析
        if 'rhr' in df.columns:
            latest_rhr = df['rhr'].iloc[-1]
            fitness["resting_heart_rate"] = {
                "current": round(latest_rhr, 1),
                "change": round(df['rhr'].iloc[-1] - df['rhr'].iloc[0], 1) if len(df) > 1 else 0,
                "rating": "优秀" if latest_rhr < 55 else "良好" if latest_rhr < 65 else "一般"
            }
        
        # 耐力水平分析
        if 'stamina_level' in df.columns:
            fitness["stamina"] = {
                "current": round(df['stamina_level'].iloc[-1], 1),
                "change_7d": round(df['stamina_level_7d'].iloc[-1], 1) if 'stamina_level_7d' in df.columns else None,
            }
        
        # 乳酸阈值分析
        if 'lthr' in df.columns:
            fitness["lactate_threshold_hr"] = round(df['lthr'].iloc[-1], 1)
        
        if 'ltsp' in df.columns:
            fitness["lactate_threshold_pace"] = round(df['ltsp'].iloc[-1], 1)  # 秒/公里
        
        return fitness
    
    def _rate_vo2max(self, vo2max: float) -> str:
        """评估VO2max水平（以男性为例，实际需要按性别年龄调整）"""
        if vo2max >= 55:
            return "优秀"
        elif vo2max >= 50:
            return "良好"
        elif vo2max >= 45:
            return "一般"
        else:
            return "待提高"
    
    def _assess_overtraining_risk(self, df: pd.DataFrame) -> Dict:
        """评估过度训练风险"""
        risk_factors = []
        risk_score = 0
        
        # 因素1: 训练负荷比值过高
        if 'training_load_ratio' in df.columns:
            ratio = df['training_load_ratio'].iloc[-1]
            if ratio > self.thresholds["overtraining_atl"]:
                risk_factors.append("训练负荷比值过高")
                risk_score += 2
            elif ratio > 1.3:
                risk_factors.append("训练负荷比值偏高")
                risk_score += 1
        
        # 因素2: 静息心率升高
        if 'rhr' in df.columns and len(df) >= 7:
            recent_rhr = df['rhr'].tail(7).mean()
            baseline_rhr = df['rhr'].head(7).mean() if len(df) >= 14 else df['rhr'].iloc[0]
            if recent_rhr > baseline_rhr * 1.05:
                risk_factors.append("静息心率升高")
                risk_score += 2
        
        # 因素3: HRV下降
        if 'avg_sleep_hrv' in df.columns and len(df) >= 7:
            recent_hrv = df['avg_sleep_hrv'].tail(7).mean()
            baseline_hrv = df['avg_sleep_hrv'].head(7).mean() if len(df) >= 14 else df['avg_sleep_hrv'].iloc[0]
            if recent_hrv < baseline_hrv * 0.9:
                risk_factors.append("HRV下降")
                risk_score += 2
        
        # 因素4: 疲劳率升高
        if 'tired_rate' in df.columns:
            if df['tired_rate'].iloc[-1] > 70:
                risk_factors.append("疲劳率偏高")
                risk_score += 1
        
        # 综合评估
        if risk_score >= 4:
            risk_level = "高"
            action = "建议立即减少训练量，增加恢复时间，必要时暂停训练1-2天"
        elif risk_score >= 2:
            risk_level = "中"
            action = "建议降低训练强度，增加休息日，监控相关指标"
        else:
            risk_level = "低"
            action = "当前训练恢复平衡良好，继续保持"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors if risk_factors else ["无明显风险因素"],
            "recommendation": action,
            "monitoring_suggestions": [
                "继续监控静息心率",
                "关注HRV趋势",
                "注意睡眠质量",
                "评估主观疲劳感"
            ]
        }
    
    def _analyze_activities(self, activities: Dict) -> Dict:
        """分析活动记录"""
        activity_list = activities.get("activities", [])
        
        if not activity_list:
            return {"message": "没有活动记录"}
        
        df_activities = pd.DataFrame(activity_list)
        
        # 运动类型分布
        sport_distribution = df_activities['sport_name'].value_counts().to_dict()
        
        # 训练负荷分布
        avg_load_by_sport = df_activities.groupby('sport_name')['training_load'].mean().to_dict()
        
        # 心率分析
        hr_analysis = {
            "avg_hr_overall": round(df_activities['avg_hr'].mean(), 1),
            "max_hr_overall": round(df_activities['max_hr'].max(), 1),
        }
        
        # 功率分析（如果有）
        power_analysis = {}
        if 'avg_power' in df_activities.columns and df_activities['avg_power'].notna().any():
            power_analysis = {
                "avg_power_overall": round(df_activities['avg_power'].mean(), 1),
                "max_avg_power": round(df_activities['avg_power'].max(), 1),
            }
        
        return {
            "total_activities": len(activity_list),
            "sport_distribution": sport_distribution,
            "avg_load_by_sport": {k: round(v, 1) for k, v in avg_load_by_sport.items()},
            "heart_rate": hr_analysis,
            "power": power_analysis,
        }
    
    def _generate_training_recommendations(self, analysis: Dict) -> List[str]:
        """生成训练建议"""
        recommendations = []
        
        # 基于训练负荷的建议
        load_analysis = analysis.get("training_load", {})
        if load_analysis.get("status") == "训练不足":
            recommendations.append(f"训练负荷{load_analysis.get('status')}，建议：{load_analysis.get('recommendation')}")
        elif load_analysis.get("status") == "过度训练风险":
            recommendations.append(f"警告：{load_analysis.get('status')}！{load_analysis.get('recommendation')}")
        
        # 基于过度训练风险建议
        overtraining = analysis.get("overtraining_risk", {})
        if overtraining.get("risk_level") in ["中", "高"]:
            recommendations.append(f"过度训练风险等级：{overtraining.get('risk_level')}")
            recommendations.append(f"建议：{overtraining.get('recommendation')}")
        
        # 基于体能水平的建议
        fitness = analysis.get("fitness_level", {})
        if "vo2max" in fitness:
            vo2max_change = fitness["vo2max"].get("change", 0)
            if vo2max_change < -1:
                recommendations.append("VO2max呈下降趋势，建议检查训练强度和恢复情况")
            elif vo2max_change > 1:
                recommendations.append("VO2max持续提升，训练效果良好！")
        
        return recommendations if recommendations else ["训练状态良好，继续保持！"]


# 使用示例
if __name__ == "__main__":
    import json
    from data_fetcher import CorosDataFetcher
    
    # 获取数据
    fetcher = CorosDataFetcher()
    daily_data = fetcher.get_daily_metrics(weeks=4)
    
    # 分析数据
    analyzer = TrainingAnalyzer()
    result = analyzer.analyze_training_data(daily_data)
    
    print("=== 训练分析结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
