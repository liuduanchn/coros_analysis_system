"""
睡眠数据分析器
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta


class SleepAnalyzer:
    """睡眠数据分析器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化睡眠分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.thresholds = {
            "deep_sleep_excellent": 90,  # 分钟
            "deep_sleep_good": 60,
            "rem_sleep_excellent": 90,
            "rem_sleep_good": 60,
            "sleep_quality_excellent": 85,
            "sleep_quality_good": 70,
        }
        if config and "sleep_thresholds" in config:
            self.thresholds.update(config["sleep_thresholds"])
    
    def analyze_sleep_data(self, sleep_data: Dict) -> Dict:
        """
        分析睡眠数据
        
        Args:
            sleep_data: 从MCP获取的睡眠数据
            
        Returns:
            dict: 分析结果
        """
        records = sleep_data.get("records", [])
        
        if not records:
            return {"error": "没有睡眠数据"}
        
        # 转换为DataFrame便于分析
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d')
        df = df.sort_values('date')
        
        # 计算各项指标
        analysis = {
            "summary": self._calculate_summary(df),
            "sleep_stages": self._analyze_sleep_stages(df),
            "sleep_quality": self._evaluate_sleep_quality(df),
            "heart_rate": self._analyze_sleep_hr(df),
            "trends": self._calculate_trends(df),
            "recommendations": []
        }
        
        # 生成建议
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _calculate_summary(self, df: pd.DataFrame) -> Dict:
        """计算睡眠摘要统计"""
        total_sleep = df['total_duration_minutes'].mean()
        deep_sleep = df['phases'].apply(lambda x: x.get('deep_minutes', 0)).mean()
        rem_sleep = df['phases'].apply(lambda x: x.get('rem_minutes', 0)).mean()
        light_sleep = df['phases'].apply(lambda x: x.get('light_minutes', 0)).mean()
        awake_time = df['phases'].apply(lambda x: x.get('awake_minutes', 0)).mean()
        
        return {
            "total_sleep_avg": round(total_sleep, 1),
            "deep_sleep_avg": round(deep_sleep, 1),
            "rem_sleep_avg": round(rem_sleep, 1),
            "light_sleep_avg": round(light_sleep, 1),
            "awake_time_avg": round(awake_time, 1),
            "deep_sleep_percentage": round(deep_sleep / total_sleep * 100, 1) if total_sleep > 0 else 0,
            "rem_sleep_percentage": round(rem_sleep / total_sleep * 100, 1) if total_sleep > 0 else 0,
            "sleep_efficiency": round((total_sleep - awake_time) / total_sleep * 100, 1) if total_sleep > 0 else 0,
        }
    
    def _analyze_sleep_stages(self, df: pd.DataFrame) -> Dict:
        """分析睡眠阶段"""
        stages_analysis = {
            "deep_sleep": self._evaluate_deep_sleep(df),
            "rem_sleep": self._evaluate_rem_sleep(df),
            "light_sleep": self._evaluate_light_sleep(df),
            "awake_episodes": self._analyze_awake_episodes(df),
        }
        return stages_analysis
    
    def _evaluate_deep_sleep(self, df: pd.DataFrame) -> Dict:
        """评估深睡眠"""
        deep_minutes = df['phases'].apply(lambda x: x.get('deep_minutes', 0))
        avg_deep = deep_minutes.mean()
        
        if avg_deep >= self.thresholds["deep_sleep_excellent"]:
            rating = "优秀"
        elif avg_deep >= self.thresholds["deep_sleep_good"]:
            rating = "良好"
        else:
            rating = "不足"
        
        return {
            "average_minutes": round(avg_deep, 1),
            "rating": rating,
            "trend": "stable",  # 需要进一步计算
            "recommendation": self._get_deep_sleep_recommendation(avg_deep)
        }
    
    def _evaluate_rem_sleep(self, df: pd.DataFrame) -> Dict:
        """评估REM睡眠"""
        rem_minutes = df['phases'].apply(lambda x: x.get('rem_minutes', 0))
        avg_rem = rem_minutes.mean()
        
        if avg_rem >= self.thresholds["rem_sleep_excellent"]:
            rating = "优秀"
        elif avg_rem >= self.thresholds["rem_sleep_good"]:
            rating = "良好"
        else:
            rating = "不足"
        
        return {
            "average_minutes": round(avg_rem, 1),
            "rating": rating,
            "recommendation": self._get_rem_sleep_recommendation(avg_rem)
        }
    
    def _evaluate_light_sleep(self, df: pd.DataFrame) -> Dict:
        """评估浅睡眠"""
        light_minutes = df['phases'].apply(lambda x: x.get('light_minutes', 0))
        avg_light = light_minutes.mean()
        
        return {
            "average_minutes": round(avg_light, 1),
            "percentage": round(avg_light / df['total_duration_minutes'].mean() * 100, 1)
        }
    
    def _analyze_awake_episodes(self, df: pd.DataFrame) -> Dict:
        """分析夜间醒来情况"""
        awake_minutes = df['phases'].apply(lambda x: x.get('awake_minutes', 0))
        
        return {
            "average_awake_minutes": round(awake_minutes.mean(), 1),
            "max_awake_minutes": round(awake_minutes.max(), 1),
            "awake_episodes_count": "N/A",  # 需要更详细的数据
            "sleep_continuity": "good" if awake_minutes.mean() < 20 else "disrupted"
        }
    
    def _evaluate_sleep_quality(self, df: pd.DataFrame) -> Dict:
        """评估睡眠质量"""
        # 检查是否有quality_score字段
        if 'quality_score' in df.columns and df['quality_score'].notna().any():
            avg_quality = df['quality_score'].mean()
            
            if avg_quality >= self.thresholds["sleep_quality_excellent"]:
                rating = "优秀"
            elif avg_quality >= self.thresholds["sleep_quality_good"]:
                rating = "良好"
            else:
                rating = "待改善"
        else:
            # 基于睡眠阶段计算综合评分
            avg_deep = df['phases'].apply(lambda x: x.get('deep_minutes', 0)).mean()
            avg_rem = df['phases'].apply(lambda x: x.get('rem_minutes', 0)).mean()
            avg_awake = df['phases'].apply(lambda x: x.get('awake_minutes', 0)).mean()
            total = df['total_duration_minutes'].mean()
            
            # 简单评分算法
            deep_score = min(avg_deep / 90 * 100, 100) * 0.4
            rem_score = min(avg_rem / 90 * 100, 100) * 0.3
            awake_penalty = max(0, 100 - avg_awake * 2) * 0.3
            
            avg_quality = deep_score + rem_score + awake_penalty
            rating = "优秀" if avg_quality >= 85 else "良好" if avg_quality >= 70 else "待改善"
        
        return {
            "overall_score": round(avg_quality, 1) if 'avg_quality' in locals() else None,
            "rating": rating,
            "factors": {
                "deep_sleep_contribution": 40,
                "rem_sleep_contribution": 30,
                "sleep_continuity_contribution": 30,
            }
        }
    
    def _analyze_sleep_hr(self, df: pd.DataFrame) -> Dict:
        """分析睡眠心率"""
        avg_hr = df['avg_hr'].mean()
        min_hr = df['min_hr'].min()
        max_hr = df['max_hr'].mean()
        
        # 心率变异性（需要HRV数据，这里使用模拟）
        hrv = df.get('hv', df['avg_hr'].expanding().std())  # 模拟HRV
        
        return {
            "average_hr": round(avg_hr, 1),
            "min_hr": round(min_hr, 1),
            "max_hr": round(max_hr, 1),
            "hrv_estimate": round(hrv.mean(), 2) if hasattr(hrv, 'mean') else None,
            "recovery_indicator": self._assess_recovery(avg_hr, min_hr)
        }
    
    def _assess_recovery(self, avg_hr: float, min_hr: float) -> str:
        """评估恢复状态"""
        # 简化的恢复评估逻辑
        if min_hr < 50:
            return "恢复良好"
        elif min_hr < 60:
            return "恢复一般"
        else:
            return "恢复不足，建议降低训练强度"
    
    def _calculate_trends(self, df: pd.DataFrame) -> Dict:
        """计算睡眠趋势"""
        df = df.sort_values('date')
        
        # 计算7日移动平均
        df['deep_ma7'] = df['phases'].apply(lambda x: x.get('deep_minutes', 0)).rolling(window=7, min_periods=1).mean()
        df['rem_ma7'] = df['phases'].apply(lambda x: x.get('rem_minutes', 0)).rolling(window=7, min_periods=1).mean()
        df['total_ma7'] = df['total_duration_minutes'].rolling(window=7, min_periods=1).mean()
        
        # 趋势方向
        recent_deep = df['deep_ma7'].iloc[-3:].mean()
        earlier_deep = df['deep_ma7'].iloc[:3].mean() if len(df) >= 6 else df['deep_ma7'].iloc[0]
        
        trend_direction = "上升" if recent_deep > earlier_deep * 1.05 else "下降" if recent_deep < earlier_deep * 0.95 else "稳定"
        
        return {
            "deep_sleep_trend": trend_direction,
            "recent_deep_avg": round(recent_deep, 1),
            "total_sleep_trend": "stable",  # 简化
            "consistency_score": self._calculate_consistency(df)
        }
    
    def _calculate_consistency(self, df: pd.DataFrame) -> float:
        """计算睡眠一致性得分"""
        # 基于总睡眠时间的变异系数
        cv = df['total_duration_minutes'].std() / df['total_duration_minutes'].mean()
        consistency = max(0, 100 - cv * 100)
        return round(consistency, 1)
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """生成睡眠改善建议"""
        recommendations = []
        
        summary = analysis.get("summary", {})
        quality = analysis.get("sleep_quality", {})
        
        # 深睡眠建议
        if summary.get("deep_sleep_percentage", 0) < 20:
            recommendations.append("深睡眠占比偏低，建议：保持规律作息、睡前避免蓝光、保持卧室凉爽")
        
        # REM睡眠建议
        if summary.get("rem_sleep_percentage", 0) < 20:
            recommendations.append("REM睡眠占比偏低，建议：避免睡前饮酒、保持充足的运动量")
        
        # 睡眠效率建议
        if summary.get("sleep_efficiency", 100) < 85:
            recommendations.append("睡眠效率偏低，建议：减少夜间醒来、建立固定的睡前放松routine")
        
        # 睡眠质量建议
        if quality.get("rating") == "待改善":
            recommendations.append("整体睡眠质量待改善，建议：评估压力水平、检查睡眠环境、考虑调整训练时间")
        
        return recommendations if recommendations else ["睡眠数据良好，继续保持！"]
    
    def _get_deep_sleep_recommendation(self, avg_deep: float) -> str:
        """获取深睡眠建议"""
        if avg_deep < 60:
            return "深睡眠偏少，建议增加日间运动强度，但避免睡前3小时内剧烈运动"
        elif avg_deep < 90:
            return "深睡眠处于中等水平，保持规律作息可进一步改善"
        else:
            return "深睡眠充足，继续保持良好作息习惯"
    
    def _get_rem_sleep_recommendation(self, avg_rem: float) -> str:
        """获取REM睡眠建议"""
        if avg_rem < 60:
            return "REM睡眠偏少，建议避免睡前饮酒，保持心理健康"
        elif avg_rem < 90:
            return "REM睡眠处于中等水平"
        else:
            return "REM睡眠充足，有利于记忆巩固和情绪调节"


# 使用示例
if __name__ == "__main__":
    import json
    
    # 模拟睡眠数据
    mock_sleep_data = {
        "records": [
            {
                "date": 20260501,
                "total_duration_minutes": 450,
                "phases": {"deep_minutes": 85, "light_minutes": 240, "rem_minutes": 95, "awake_minutes": 30},
                "avg_hr": 58,
                "min_hr": 48,
                "max_hr": 78,
                "quality_score": 82
            },
            {
                "date": 20260502,
                "total_duration_minutes": 420,
                "phases": {"deep_minutes": 70, "light_minutes": 230, "rem_minutes": 85, "awake_minutes": 35},
                "avg_hr": 60,
                "min_hr": 50,
                "max_hr": 80,
                "quality_score": 78
            }
        ],
        "count": 2,
        "date_range": "20260501 to 20260502"
    }
    
    analyzer = SleepAnalyzer()
    result = analyzer.analyze_sleep_data(mock_sleep_data)
    
    print("=== 睡眠分析结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
