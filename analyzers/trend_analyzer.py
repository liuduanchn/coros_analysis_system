"""
趋势分析器
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta


class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化趋势分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.window_short = 7   # 短期窗口（天）
        self.window_medium = 14 # 中期窗口（天）
        self.window_long = 28    # 长期窗口（天）
    
    def analyze_trends(self, daily_metrics: Dict, sleep_data: Dict = None) -> Dict:
        """
        分析各项指标的趋势
        
        Args:
            daily_metrics: 每日指标数据
            sleep_data: 睡眠数据（可选）
            
        Returns:
            dict: 趋势分析结果
        """
        records = daily_metrics.get("records", [])
        
        if not records:
            return {"error": "没有数据"}
        
        # 转换为DataFrame
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d')
        df = df.sort_values('date')
        
        # 执行趋势分析
        analysis = {
            "date_range": {
                "start": df['date'].min().strftime('%Y-%m-%d'),
                "end": df['date'].max().strftime('%Y-%m-%d'),
                "days": (df['date'].max() - df['date'].min()).days + 1
            },
            "training_trends": self._analyze_training_trends(df),
            "recovery_trends": self._analyze_recovery_trends(df),
            "fitness_trends": self._analyze_fitness_trends(df),
        }
        
        # 如果有睡眠数据，分析睡眠趋势
        if sleep_data and "records" in sleep_data:
            analysis["sleep_trends"] = self._analyze_sleep_trends(sleep_data)
        
        # 生成综合洞察
        analysis["insights"] = self._generate_insights(analysis)
        
        return analysis
    
    def _analyze_training_trends(self, df: pd.DataFrame) -> Dict:
        """分析训练趋势"""
        trends = {}
        
        # 训练负荷趋势
        if 'training_load' in df.columns:
            load_trend = self._calculate_trend(df['training_load'])
            trends["training_load"] = {
                "direction": load_trend["direction"],
                "slope": load_trend["slope"],
                "recent_avg": round(df['training_load'].tail(self.window_short).mean(), 1),
                "baseline_avg": round(df['training_load'].head(self.window_short).mean(), 1),
                "change_percentage": round(((df['training_load'].tail(self.window_short).mean() / df['training_load'].head(self.window_short).mean() - 1) * 100) if df['training_load'].head(self.window_short).mean() > 0 else 0, 1)
            }
        
        # 训练负荷比值趋势
        if 'training_load_ratio' in df.columns:
            ratio_trend = self._calculate_trend(df['training_load_ratio'])
            trends["training_load_ratio"] = {
                "direction": ratio_trend["direction"],
                "current": round(df['training_load_ratio'].iloc[-1], 2),
                "status": self._interpret_load_ratio(df['training_load_ratio'].iloc[-1])
            }
        
        # 距离趋势
        if 'distance' in df.columns:
            distance_trend = self._calculate_trend(df['distance'])
            trends["distance"] = {
                "direction": distance_trend["direction"],
                "recent_weekly_km": round(df['distance'].tail(7).sum() / 1000, 1),
                "change_percentage": round(((df['distance'].tail(7).sum() / df['distance'].head(7).sum() - 1) * 100) if df['distance'].head(7).sum() > 0 else 0, 1)
            }
        
        # 持续时间趋势
        if 'duration' in df.columns:
            duration_trend = self._calculate_trend(df['duration'])
            trends["duration"] = {
                "direction": duration_trend["direction"],
                "recent_weekly_hours": round(df['duration'].tail(7).sum() / 3600, 1)
            }
        
        return trends
    
    def _analyze_recovery_trends(self, df: pd.DataFrame) -> Dict:
        """分析恢复趋势"""
        trends = {}
        
        # HRV趋势
        if 'avg_sleep_hrv' in df.columns:
            hrv_trend = self._calculate_trend(df['avg_sleep_hrv'])
            trends["hrv"] = {
                "direction": hrv_trend["direction"],
                "recent_avg": round(df['avg_sleep_hrv'].tail(self.window_short).mean(), 1),
                "baseline_avg": round(df['avg_sleep_hrv'].head(self.window_short).mean(), 1),
                "change_percentage": round(((df['avg_sleep_hrv'].tail(self.window_short).mean() / df['avg_sleep_hrv'].head(self.window_short).mean() - 1) * 100) if df['avg_sleep_hrv'].head(self.window_short).mean() > 0 else 0, 1),
                "status": self._interpret_hrv_change(trends.get("hrv", {}).get("change_percentage", 0) if "hrv" in trends else 0)
            }
        
        # 静息心率趋势
        if 'rhr' in df.columns:
            rhr_trend = self._calculate_trend(df['rhr'])
            # 注意：静息心率降低是正面趋势
            trends["resting_heart_rate"] = {
                "direction": "改善" if rhr_trend["direction"] == "下降" else "恶化" if rhr_trend["direction"] == "上升" else "稳定",
                "recent_avg": round(df['rhr'].tail(self.window_short).mean(), 1),
                "baseline_avg": round(df['rhr'].head(self.window_short).mean(), 1),
                "change": round(df['rhr'].tail(self.window_short).mean() - df['rhr'].head(self.window_short).mean(), 1)
            }
        
        # 疲劳率趋势
        if 'tired_rate' in df.columns:
            tired_trend = self._calculate_trend(df['tired_rate'])
            trends["fatigue_rate"] = {
                "direction": tired_trend["direction"],
                "recent_avg": round(df['tired_rate'].tail(self.window_short).mean(), 1),
                "status": "需要恢复" if df['tired_rate'].tail(self.window_short).mean() > 60 else "恢复良好"
            }
        
        return trends
    
    def _analyze_fitness_trends(self, df: pd.DataFrame) -> Dict:
        """分析体能趋势"""
        trends = {}
        
        # VO2max趋势
        if 'vo2max' in df.columns:
            vo2_trend = self._calculate_trend(df['vo2max'])
            trends["vo2max"] = {
                "direction": vo2_trend["direction"],
                "current": round(df['vo2max'].iloc[-1], 1),
                "change": round(df['vo2max'].iloc[-1] - df['vo2max'].iloc[0], 1),
                "recent_trend": self._calculate_moving_average_trend(df['vo2max'], self.window_short)
            }
        
        # 耐力水平趋势
        if 'stamina_level' in df.columns:
            stamina_trend = self._calculate_trend(df['stamina_level'])
            trends["stamina"] = {
                "direction": stamina_trend["direction"],
                "current": round(df['stamina_level'].iloc[-1], 1),
                "change": round(df['stamina_level'].iloc[-1] - df['stamina_level'].iloc[0], 1)
            }
        
        # 乳酸阈值心率趋势
        if 'lthr' in df.columns:
            lthr_trend = self._calculate_trend(df['lthr'])
            trends["lactate_threshold_hr"] = {
                "direction": lthr_trend["direction"],
                "current": round(df['lthr'].iloc[-1], 1),
                "interpretation": "改善" if lthr_trend["direction"] == "上升" else "待观察"
            }
        
        return trends
    
    def _analyze_sleep_trends(self, sleep_data: Dict) -> Dict:
        """分析睡眠趋势"""
        records = sleep_data.get("records", [])
        df_sleep = pd.DataFrame(records)
        df_sleep['date'] = pd.to_datetime(df_sleep['date'].astype(str), format='%Y%m%d')
        df_sleep = df_sleep.sort_values('date')
        
        trends = {}
        
        # 总睡眠时长趋势
        if 'total_duration_minutes' in df_sleep.columns:
            sleep_trend = self._calculate_trend(df_sleep['total_duration_minutes'])
            trends["total_sleep"] = {
                "direction": sleep_trend["direction"],
                "recent_avg": round(df_sleep['total_duration_minutes'].tail(self.window_short).mean(), 1),
                "change_minutes": round(df_sleep['total_duration_minutes'].tail(self.window_short).mean() - df_sleep['total_duration_minutes'].head(self.window_short).mean(), 1)
            }
        
        # 深睡眠趋势
        if 'phases' in df_sleep.columns:
            df_sleep['deep_minutes'] = df_sleep['phases'].apply(lambda x: x.get('deep_minutes', 0))
            deep_trend = self._calculate_trend(df_sleep['deep_minutes'])
            trends["deep_sleep"] = {
                "direction": deep_trend["direction"],
                "recent_avg": round(df_sleep['deep_minutes'].tail(self.window_short).mean(), 1),
            }
        
        # REM睡眠趋势
        if 'phases' in df_sleep.columns:
            df_sleep['rem_minutes'] = df_sleep['phases'].apply(lambda x: x.get('rem_minutes', 0))
            rem_trend = self._calculate_trend(df_sleep['rem_minutes'])
            trends["rem_sleep"] = {
                "direction": rem_trend["direction"],
                "recent_avg": round(df_sleep['rem_minutes'].tail(self.window_short).mean(), 1),
            }
        
        return trends
    
    def _calculate_trend(self, series: pd.Series) -> Dict:
        """
        计算趋势方向和斜率
        
        Args:
            series: 数据序列
            
        Returns:
            dict: 趋势信息
        """
        if len(series) < 2:
            return {"direction": "数据不足", "slope": 0}
        
        # 使用简单线性回归计算斜率
        x = np.arange(len(series))
        y = series.values
        
        # 计算斜率
        n = len(x)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
        
        # 判断方向
        if slope > 0.05 * series.mean():
            direction = "上升"
        elif slope < -0.05 * series.mean():
            direction = "下降"
        else:
            direction = "稳定"
        
        return {
            "direction": direction,
            "slope": round(slope, 4),
            "strength": abs(slope) / series.std() if series.std() > 0 else 0
        }
    
    def _calculate_moving_average_trend(self, series: pd.Series, window: int = 7) -> str:
        """计算移动平均趋势"""
        if len(series) < window * 2:
            return "数据不足"
        
        ma_early = series.head(window).mean()
        ma_recent = series.tail(window).mean()
        
        change_ratio = (ma_recent - ma_early) / ma_early if ma_early > 0 else 0
        
        if change_ratio > 0.02:
            return "上升"
        elif change_ratio < -0.02:
            return "下降"
        else:
            return "稳定"
    
    def _interpret_load_ratio(self, ratio: float) -> str:
        """解释训练负荷比值"""
        if ratio < 0.8:
            return "训练不足"
        elif ratio < 1.3:
            return "训练平衡"
        elif ratio < 1.5:
            return "训练偏高"
        else:
            return "过度训练风险"
    
    def _interpret_hrv_change(self, change_pct: float) -> str:
        """解释HRV变化"""
        if change_pct > 5:
            return "恢复良好"
        elif change_pct > -5:
            return "稳定"
        else:
            return "恢复不足"
    
    def _generate_insights(self, analysis: Dict) -> List[str]:
        """生成综合洞察"""
        insights = []
        
        # 训练趋势洞察
        training = analysis.get("training_trends", {})
        if "training_load" in training:
            load = training["training_load"]
            if load.get("direction") == "上升" and load.get("change_percentage", 0) > 20:
                insights.append("训练负荷显著上升，注意恢复是否跟上")
            elif load.get("direction") == "下降" and load.get("change_percentage", 0) < -20:
                insights.append("训练负荷显著下降，可能因休息或减量")
        
        # 恢复趋势洞察
        recovery = analysis.get("recovery_trends", {})
        if "hrv" in recovery and "resting_heart_rate" in recovery:
            hrv = recovery["hrv"]
            rhr = recovery["resting_heart_rate"]
            
            if hrv.get("direction") == "下降" and rhr.get("direction") == "恶化":
                insights.append("警告：HRV下降且静息心率上升，可能存在过度训练或生病风险")
            elif hrv.get("direction") == "上升" and rhr.get("direction") == "改善":
                insights.append("恢复指标改善，体能状态良好")
        
        # 体能趋势洞察
        fitness = analysis.get("fitness_trends", {})
        if "vo2max" in fitness:
            vo2 = fitness["vo2max"]
            if vo2.get("direction") == "上升":
                insights.append("VO2max呈上升趋势，有氧能力在提升")
            elif vo2.get("direction") == "下降":
                insights.append("VO2max呈下降趋势，建议检查训练和恢复平衡")
        
        return insights if insights else ["整体趋势稳定，继续保持"]


# 使用示例
if __name__ == "__main__":
    import json
    from data_fetcher import CorosDataFetcher
    
    # 获取数据
    fetcher = CorosDataFetcher()
    daily_data = fetcher.get_daily_metrics(weeks=8)
    sleep_data = fetcher.get_sleep_data(weeks=8)
    
    # 分析趋势
    analyzer = TrendAnalyzer()
    result = analyzer.analyze_trends(daily_data, sleep_data)
    
    print("=== 趋势分析结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
