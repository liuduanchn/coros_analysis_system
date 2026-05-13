"""
可视化图表生成器
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import os


class PlotGenerator:
    """图表生成器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化图表生成器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.figure_size = config.get("figure_size", (12, 6)) if config else (12, 6)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def generate_all_plots(self, daily_metrics: Dict, sleep_data: Dict, 
                          output_dir: str = "reports") -> List[str]:
        """
        生成所有图表
        
        Args:
            daily_metrics: 每日指标数据
            sleep_data: 睡眠数据
            output_dir: 输出目录
            
        Returns:
            list: 生成的图表文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        generated_files = []
        
        # 转换数据
        df_daily = pd.DataFrame(daily_metrics.get("records", []))
        if not df_daily.empty:
            df_daily['date'] = pd.to_datetime(df_daily['date'].astype(str), format='%Y%m%d')
            df_daily = df_daily.sort_values('date')
        
        df_sleep = pd.DataFrame(sleep_data.get("records", []))
        if not df_sleep.empty:
            df_sleep['date'] = pd.to_datetime(df_sleep['date'].astype(str), format='%Y%m%d')
            df_sleep = df_sleep.sort_values('date')
        
        # 生成各项图表
        if not df_daily.empty:
            # 1. 训练负荷趋势图
            file_path = self.plot_training_load(df_daily, output_dir)
            if file_path:
                generated_files.append(file_path)
            
            # 2. HRV趋势图
            file_path = self.plot_hrv_trend(df_daily, output_dir)
            if file_path:
                generated_files.append(file_path)
            
            # 3. 静息心率趋势图
            file_path = self.plot_rhr_trend(df_daily, output_dir)
            if file_path:
                generated_files.append(file_path)
            
            # 4. VO2max趋势图
            file_path = self.plot_vo2max_trend(df_daily, output_dir)
            if file_path:
                generated_files.append(file_path)
        
        if not df_sleep.empty:
            # 5. 睡眠阶段堆叠图
            file_path = self.plot_sleep_stages(df_sleep, output_dir)
            if file_path:
                generated_files.append(file_path)
            
            # 6. 睡眠质量评分图
            file_path = self.plot_sleep_quality(df_sleep, output_dir)
            if file_path:
                generated_files.append(file_path)
        
        # 7. 综合仪表盘
        if not df_daily.empty and not df_sleep.empty:
            file_path = self.plot_comprehensive_dashboard(df_daily, df_sleep, output_dir)
            if file_path:
                generated_files.append(file_path)
        
        return generated_files
    
    def plot_training_load(self, df: pd.DataFrame, output_dir: str) -> Optional[str]:
        """生成训练负荷趋势图"""
        if 'training_load' not in df.columns:
            return None
        
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        ax.plot(df['date'], df['training_load'], marker='o', linewidth=2, label='每日训练负荷')
        
        # 添加7日移动平均
        df['training_load_ma7'] = df['training_load'].rolling(window=7, min_periods=1).mean()
        ax.plot(df['date'], df['training_load_ma7'], linewidth=2, linestyle='--', 
                color='red', label='7日移动平均')
        
        # 添加训练负荷区间
        ax.axhspan(0, 300, alpha=0.2, color='green', label='低负荷区')
        ax.axhspan(300, 600, alpha=0.2, color='yellow', label='适中区')
        ax.axhspan(600, 900, alpha=0.2, color='orange', label='高负荷区')
        ax.axhspan(900, 2000, alpha=0.2, color='red', label='过高区')
        
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('训练负荷', fontsize=12)
        ax.set_title('训练负荷趋势分析', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        file_path = os.path.join(output_dir, 'training_load_trend.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return file_path
    
    def plot_hrv_trend(self, df: pd.DataFrame, output_dir: str) -> Optional[str]:
        """生成HRV趋势图"""
        if 'avg_sleep_hrv' not in df.columns:
            return None
        
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        ax.plot(df['date'], df['avg_sleep_hrv'], marker='s', linewidth=2, 
                color='purple', label='HRV')
        
        # 添加基线和阈值线
        if 'baseline' in df.columns:
            ax.axhline(y=df['baseline'].iloc[0], color='gray', linestyle=':', 
                      label=f'基线 ({df["baseline"].iloc[0]:.0f}ms)')
        
        ax.axhline(y=65, color='green', linestyle='--', alpha=0.5, label='优秀 (>65ms)')
        ax.axhline(y=45, color='orange', linestyle='--', alpha=0.5, label='一般 (>45ms)')
        
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('HRV (ms)', fontsize=12)
        ax.set_title('HRV（心率变异性）趋势', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        file_path = os.path.join(output_dir, 'hrv_trend.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return file_path
    
    def plot_rhr_trend(self, df: pd.DataFrame, output_dir: str) -> Optional[str]:
        """生成静息心率趋势图"""
        if 'rhr' not in df.columns:
            return None
        
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        ax.plot(df['date'], df['rhr'], marker='^', linewidth=2, 
                color='blue', label='静息心率')
        
        # 添加健康区间
        ax.axhspan(45, 60, alpha=0.2, color='green', label='健康区间')
        ax.axhspan(60, 75, alpha=0.2, color='yellow', label='警戒区间')
        ax.axhspan(75, 100, alpha=0.2, color='red', label='偏高区间')
        
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('静息心率 (bpm)', fontsize=12)
        ax.set_title('静息心率趋势', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        file_path = os.path.join(output_dir, 'rhr_trend.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return file_path
    
    def plot_vo2max_trend(self, df: pd.DataFrame, output_dir: str) -> Optional[str]:
        """生成VO2max趋势图"""
        if 'vo2max' not in df.columns:
            return None
        
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        ax.plot(df['date'], df['vo2max'], marker='d', linewidth=2, 
                color='green', label='VO2max')
        
        # 添加评级区间
        ax.axhspan(55, 70, alpha=0.2, color='green', label='优秀')
        ax.axhspan(50, 55, alpha=0.2, color='lightgreen', label='良好')
        ax.axhspan(45, 50, alpha=0.2, color='yellow', label='一般')
        ax.axhspan(30, 45, alpha=0.2, color='red', label='待提高')
        
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('VO2max (ml/kg/min)', fontsize=12)
        ax.set_title('VO2max（最大摄氧量）趋势', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        file_path = os.path.join(output_dir, 'vo2max_trend.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return file_path
    
    def plot_sleep_stages(self, df: pd.DataFrame, output_dir: str) -> Optional[str]:
        """生成睡眠阶段堆叠图"""
        if 'phases' not in df.columns:
            return None
        
        # 提取睡眠阶段数据
        df['deep'] = df['phases'].apply(lambda x: x.get('deep_minutes', 0))
        df['light'] = df['phases'].apply(lambda x: x.get('light_minutes', 0))
        df['rem'] = df['phases'].apply(lambda x: x.get('rem_minutes', 0))
        df['awake'] = df['phases'].apply(lambda x: x.get('awake_minutes', 0))
        
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        # 堆叠柱状图
        bar_width = 0.6
        x = np.arange(len(df))
        
        ax.bar(x, df['deep'], bar_width, label='深睡眠', color='#2E86AB')
        ax.bar(x, df['light'], bar_width, bottom=df['deep'], label='浅睡眠', color='#A23B72')
        ax.bar(x, df['rem'], bar_width, bottom=df['deep'] + df['light'], label='REM', color='#F18F01')
        ax.bar(x, df['awake'], bar_width, 
               bottom=df['deep'] + df['light'] + df['rem'], label='醒来', color='#C73E1D', alpha=0.5)
        
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('睡眠时长 (分钟)', fontsize=12)
        ax.set_title('睡眠阶段分布', fontsize=14, fontweight='bold')
        ax.set_xticks(x[::max(1, len(x)//10)])  # 最多显示10个日期
        ax.set_xticklabels([d.strftime('%m-%d') for d in df['date'].iloc[::max(1, len(df)//10)]], rotation=45)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        file_path = os.path.join(output_dir, 'sleep_stages.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return file_path
    
    def plot_sleep_quality(self, df: pd.DataFrame, output_dir: str) -> Optional[str]:
        """生成睡眠质量评分图"""
        if 'quality_score' not in df.columns or df['quality_score'].isna().all():
            return None
        
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        ax.plot(df['date'], df['quality_score'], marker='*', linewidth=2, 
                markersize=10, color='gold', label='睡眠质量评分')
        
        # 添加评级区间
        ax.axhspan(85, 100, alpha=0.2, color='green', label='优秀 (85+)')
        ax.axhspan(70, 85, alpha=0.2, color='yellow', label='良好 (70-85)')
        ax.axhspan(0, 70, alpha=0.2, color='red', label='待改善 (<70)')
        
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('质量评分', fontsize=12)
        ax.set_title('睡眠质量评分趋势', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        file_path = os.path.join(output_dir, 'sleep_quality.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return file_path
    
    def plot_comprehensive_dashboard(self, df_daily: pd.DataFrame, 
                                     df_sleep: pd.DataFrame, output_dir: str) -> Optional[str]:
        """生成综合仪表盘"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('COROS 数据分析综合仪表盘', fontsize=16, fontweight='bold')
        
        # 1. 训练负荷
        if 'training_load' in df_daily.columns:
            axes[0, 0].plot(df_daily['date'], df_daily['training_load'], marker='o')
            axes[0, 0].set_title('训练负荷')
            axes[0, 0].grid(True, alpha=0.3)
        
        # 2. HRV
        if 'avg_sleep_hrv' in df_daily.columns:
            axes[0, 1].plot(df_daily['date'], df_daily['avg_sleep_hrv'], marker='s', color='purple')
            axes[0, 1].set_title('HRV')
            axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 静息心率
        if 'rhr' in df_daily.columns:
            axes[0, 2].plot(df_daily['date'], df_daily['rhr'], marker='^', color='blue')
            axes[0, 2].set_title('静息心率')
            axes[0, 2].grid(True, alpha=0.3)
        
        # 4. 睡眠总时长
        if not df_sleep.empty and 'total_duration_minutes' in df_sleep.columns:
            axes[1, 0].plot(df_sleep['date'], df_sleep['total_duration_minutes'], 
                           marker='o', color='cyan')
            axes[1, 0].axhline(y=480, color='green', linestyle='--', alpha=0.5)
            axes[1, 0].set_title('睡眠总时长')
            axes[1, 0].grid(True, alpha=0.3)
        
        # 5. 深睡眠
        if not df_sleep.empty and 'phases' in df_sleep.columns:
            df_sleep['deep'] = df_sleep['phases'].apply(lambda x: x.get('deep_minutes', 0))
            axes[1, 1].plot(df_sleep['date'], df_sleep['deep'], marker='s', color='navy')
            axes[1, 1].axhline(y=90, color='green', linestyle='--', alpha=0.5)
            axes[1, 1].set_title('深睡眠时长')
            axes[1, 1].grid(True, alpha=0.3)
        
        # 6. VO2max
        if 'vo2max' in df_daily.columns:
            axes[1, 2].plot(df_daily['date'], df_daily['vo2max'], marker='d', color='green')
            axes[1, 2].set_title('VO2max')
            axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        file_path = os.path.join(output_dir, 'comprehensive_dashboard.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return file_path


# 使用示例
if __name__ == "__main__":
    # 生成模拟图表
    import json
    from data_fetcher import CorosDataFetcher
    
    fetcher = CorosDataFetcher()
    daily_data = fetcher.get_daily_metrics(weeks=4)
    sleep_data = fetcher.get_sleep_data(weeks=4)
    
    generator = PlotGenerator()
    files = generator.generate_all_plots(daily_data, sleep_data, output_dir="reports")
    
    print("生成的图表文件：")
    for f in files:
        print(f"  - {f}")
