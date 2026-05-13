"""
COROS 运动数据分析系统 - 主程序入口
"""

import sys
import os
import json
import argparse
import pandas as pd
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import COROS_CONFIG, ANALYSIS_CONFIG, REPORT_CONFIG
from data_fetcher import CorosDataFetcher
from analyzers.sleep_analyzer import SleepAnalyzer
from analyzers.training_analyzer import TrainingAnalyzer
from analyzers.trend_analyzer import TrendAnalyzer
from visualizers.plot_generator import PlotGenerator
from visualizers.report_builder import ReportBuilder


class CorosAnalysisSystem:
    """COROS运动数据分析系统主类"""
    
    def __init__(self, config: Dict = None):
        """
        初始化分析系统
        
        Args:
            config: 配置字典（可选，默认使用config.py）
        """
        self.config = config or {
            "coros": COROS_CONFIG,
            "analysis": ANALYSIS_CONFIG,
            "report": REPORT_CONFIG
        }
        
        # 初始化各模块
        self.fetcher = CorosDataFetcher()
        self.sleep_analyzer = SleepAnalyzer(self.config.get("analysis"))
        self.training_analyzer = TrainingAnalyzer(self.config.get("analysis"))
        self.trend_analyzer = TrendAnalyzer(self.config.get("analysis"))
        self.plot_generator = PlotGenerator(self.config.get("report"))
        self.report_builder = ReportBuilder(self.config.get("report", {}).get("output_dir", "reports"))
        
        self.analysis_results = {}
        
    def run_full_analysis(self, weeks: int = 4, 
                          include_activities: bool = True) -> Dict:
        """
        运行完整分析流程
        
        Args:
            weeks: 分析数据的周数
            include_activities: 是否包含活动记录分析
            
        Returns:
            dict: 完整分析结果
        """
        print("="*60)
        print("COROS 运动数据分析系统")
        print("="*60)
        
        # Step 1: 获取数据
        print("\n[1/5] 正在获取COROS数据...")
        daily_data = self.fetcher.get_daily_metrics(weeks=weeks)
        sleep_data = self.fetcher.get_sleep_data(weeks=weeks)
        
        activities_data = None
        if include_activities:
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(weeks=weeks)
            activities_data = self.fetcher.list_activities(
                start_day=start_date.strftime("%Y%m%d"),
                end_day=end_date.strftime("%Y%m%d")
            )
        
        print(f"  ✓ 获取到 {daily_data.get('count', 0)} 条每日指标")
        print(f"  ✓ 获取到 {sleep_data.get('count', 0)} 条睡眠记录")
        if activities_data:
            print(f"  ✓ 获取到 {activities_data.get('total_count', 0)} 条活动记录")
        
        # Step 2: 分析训练数据
        print("\n[2/5] 正在分析训练数据...")
        training_analysis = self.training_analyzer.analyze_training_data(
            daily_data, activities_data
        )
        self.analysis_results["training_analysis"] = training_analysis
        print(f"  ✓ 训练分析完成 - 状态: {training_analysis.get('training_load', {}).get('status', 'N/A')}")
        
        # Step 3: 分析睡眠数据
        print("\n[3/5] 正在分析睡眠数据...")
        sleep_analysis = self.sleep_analyzer.analyze_sleep_data(sleep_data)
        self.analysis_results["sleep_analysis"] = sleep_analysis
        print(f"  ✓ 睡眠分析完成 - 评级: {sleep_analysis.get('sleep_quality', {}).get('rating', 'N/A')}")
        
        # Step 4: 分析趋势
        print("\n[4/5] 正在分析趋势...")
        trend_analysis = self.trend_analyzer.analyze_trends(daily_data, sleep_data)
        self.analysis_results["trend_analysis"] = trend_analysis
        print(f"  ✓ 趋势分析完成 - 发现 {len(trend_analysis.get('insights', []))} 条洞察")
        
        # Step 5: 生成图表和报告
        print("\n[5/5] 正在生成图表和报告...")
        
        # 生成图表
        plot_files = self.plot_generator.generate_all_plots(
            daily_data, sleep_data, 
            output_dir=self.config.get("report", {}).get("output_dir", "reports")
        )
        print(f"  ✓ 生成了 {len(plot_files)} 张图表")
        
        # 生成HTML报告
        html_report = self.report_builder.generate_html_report(
            self.analysis_results, plot_files
        )
        print(f"  ✓ HTML报告已生成: {html_report}")
        
        # 生成JSON报告
        json_report = self.report_builder.generate_json_report(self.analysis_results)
        print(f"  ✓ JSON报告已生成: {json_report}")
        
        print("\n" + "="*60)
        print("✓ 分析完成！")
        print("="*60)
        
        return self.analysis_results
    
    def print_summary(self):
        """打印分析摘要"""
        if not self.analysis_results:
            print("请先运行分析（调用 run_full_analysis）")
            return
        
        print("\n" + "="*60)
        print("分析摘要")
        print("="*60)
        
        # 训练摘要
        if "training_analysis" in self.analysis_results:
            training = self.analysis_results["training_analysis"]
            summary = training.get("summary", {})
            print(f"\n【训练数据】")
            print(f"  平均训练负荷: {summary.get('avg_training_load', 'N/A')}")
            print(f"  平均静息心率: {summary.get('avg_rhr', 'N/A')} bpm")
            print(f"  VO2max: {summary.get('vo2max_latest', 'N/A')}")
            print(f"  状态: {training.get('training_load', {}).get('status', 'N/A')}")
        
        # 睡眠摘要
        if "sleep_analysis" in self.analysis_results:
            sleep = self.analysis_results["sleep_analysis"]
            summary = sleep.get("summary", {})
            print(f"\n【睡眠数据】")
            print(f"  平均睡眠时长: {summary.get('total_sleep_avg', 'N/A')} 分钟")
            print(f"  深睡眠占比: {summary.get('deep_sleep_percentage', 'N/A')}%")
            print(f"  睡眠质量: {sleep.get('sleep_quality', {}).get('rating', 'N/A')}")
        
        # 建议
        print(f"\n【建议】")
        all_recs = []
        if "training_analysis" in self.analysis_results:
            all_recs.extend(self.analysis_results["training_analysis"].get("recommendations", []))
        if "sleep_analysis" in self.analysis_results:
            all_recs.extend(self.analysis_results["sleep_analysis"].get("recommendations", []))
        
        for i, rec in enumerate(all_recs[:5], 1):  # 最多显示5条
            print(f"  {i}. {rec}")
        
        print("\n" + "="*60)
    
    def run_sleep_analysis_only(self, weeks: int = 4) -> Dict:
        """仅运行睡眠分析"""
        print("正在获取睡眠数据...")
        sleep_data = self.fetcher.get_sleep_data(weeks=weeks)
        
        print("正在分析睡眠数据...")
        analysis = self.sleep_analyzer.analyze_sleep_data(sleep_data)
        
        # 生成睡眠图表
        df_sleep = pd.DataFrame(sleep_data.get("records", []))
        if not df_sleep.empty:
            plot_file = self.plot_generator.plot_sleep_stages(df_sleep, "reports")
            if plot_file:
                print(f"  ✓ 睡眠图表已生成: {plot_file}")
        
        return analysis
    
    def run_training_analysis_only(self, weeks: int = 4) -> Dict:
        """仅运行训练分析"""
        print("正在获取训练数据...")
        daily_data = self.fetcher.get_daily_metrics(weeks=weeks)
        
        print("正在分析训练数据...")
        analysis = self.training_analyzer.analyze_training_data(daily_data)
        
        return analysis


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='COROS 运动数据分析系统')
    parser.add_argument('--weeks', type=int, default=4, help='分析数据的周数（默认4周）')
    parser.add_argument('--mode', choices=['full', 'sleep', 'training', 'trend'], 
                       default='full', help='分析模式')
    parser.add_argument('--no-activities', action='store_true', help='不分析活动记录')
    
    args = parser.parse_args()
    
    # 创建分析系统实例
    system = CorosAnalysisSystem()
    
    # 根据模式运行分析
    if args.mode == 'full':
        results = system.run_full_analysis(
            weeks=args.weeks, 
            include_activities=not args.no_activities
        )
    elif args.mode == 'sleep':
        results = {"sleep_analysis": system.run_sleep_analysis_only(weeks=args.weeks)}
    elif args.mode == 'training':
        results = {"training_analysis": system.run_training_analysis_only(weeks=args.weeks)}
    elif args.mode == 'trend':
        # 获取数据
        daily_data = system.fetcher.get_daily_metrics(weeks=args.weeks)
        sleep_data = system.fetcher.get_sleep_data(weeks=args.weeks)
        results = {"trend_analysis": system.trend_analyzer.analyze_trends(daily_data, sleep_data)}
    
    # 打印摘要
    system.print_summary()
    
    return results


if __name__ == "__main__":
    results = main()
