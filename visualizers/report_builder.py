"""
报告构建器
"""

import json
import numpy as np
import base64
from typing import Dict, List, Any
from datetime import datetime
import os


class NumpyEncoder(json.JSONEncoder):
    """处理numpy数据类型的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class ReportBuilder:
    """报告生成器"""
    
    def __init__(self, output_dir: str = "reports"):
        """
        初始化报告生成器
        
        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_html_report(self, analysis_results: Dict, 
                             plot_files: List[str] = None) -> str:
        """
        生成HTML分析报告
        
        Args:
            analysis_results: 分析结果字典
            plot_files: 生成的图表文件路径列表
            
        Returns:
            str: 生成的HTML文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"coros_analysis_report_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        html_content = self._build_html_content(analysis_results, plot_files, timestamp)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _build_html_content(self, results: Dict, plots: List[str], timestamp: str) -> str:
        """构建HTML内容"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COROS 运动数据分析报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            padding-left: 10px;
            border-left: 4px solid #3498db;
        }}
        .summary-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .status-excellent {{ color: #27ae60; }}
        .status-good {{ color: #2980b9; }}
        .status-warning {{ color: #f39c12; }}
        .status-danger {{ color: #e74c3c; }}
        .recommendation {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .plot-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .plot-container img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <h1>🏃 COROS 运动数据分析报告</h1>
    <p style="text-align: center; color: #7f8c8d;">生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}</p>
"""
        
        # 添加摘要部分
        html += self._render_summary(results)
        
        # 添加训练分析
        if "training_analysis" in results:
            html += self._render_training_analysis(results["training_analysis"])
        
        # 添加睡眠分析
        if "sleep_analysis" in results:
            html += self._render_sleep_analysis(results["sleep_analysis"])
        
        # 添加趋势分析
        if "trend_analysis" in results:
            html += self._render_trend_analysis(results["trend_analysis"])
        
        # 添加图表
        if plots:
            html += self._render_plots(plots)
        
        # 添加建议
        html += self._render_recommendations(results)
        
        # 页脚
        html += """
    <div class="footer">
        <p>本报告由 COROS 分析系统自动生成</p>
        <p>数据来源：COROS Training Hub via MCP Server</p>
    </div>
</body>
</html>"""
        
        return html
    
    def _render_summary(self, results: Dict) -> str:
        """渲染摘要部分"""
        training = results.get("training_analysis", {}).get("summary", {})
        sleep = results.get("sleep_analysis", {}).get("summary", {})
        
        html = """
    <div class="summary-box">
        <h2 style="color: white; border: none;">📊 数据摘要</h2>
        <div class="metric-grid">
"""
        
        if training:
            html += f"""
            <div class="metric-card" style="background: rgba(255,255,255,0.2); color: white;">
                <div class="metric-value">{training.get('avg_training_load', 'N/A')}</div>
                <div class="metric-label">平均训练负荷</div>
            </div>
            <div class="metric-card" style="background: rgba(255,255,255,0.2); color: white;">
                <div class="metric-value">{training.get('vo2max_latest', 'N/A')}</div>
                <div class="metric-label">VO2max</div>
            </div>
            <div class="metric-card" style="background: rgba(255,255,255,0.2); color: white;">
                <div class="metric-value">{training.get('avg_rhr', 'N/A')} bpm</div>
                <div class="metric-label">平均静息心率</div>
            </div>
"""
        
        if sleep:
            html += f"""
            <div class="metric-card" style="background: rgba(255,255,255,0.2); color: white;">
                <div class="metric-value">{sleep.get('total_sleep_avg', 'N/A')} min</div>
                <div class="metric-label">平均睡眠时长</div>
            </div>
            <div class="metric-card" style="background: rgba(255,255,255,0.2); color: white;">
                <div class="metric-value">{sleep.get('deep_sleep_percentage', 'N/A')}%</div>
                <div class="metric-label">深睡眠占比</div>
            </div>
"""
        
        html += """
        </div>
    </div>
"""
        
        return html
    
    def _render_training_analysis(self, analysis: Dict) -> str:
        """渲染训练分析"""
        html = """
    <h2>🏋️ 训练分析</h2>
"""
        
        # 训练负荷
        if "training_load" in analysis:
            load = analysis["training_load"]
            status_class = "status-excellent" if load.get("status") == "训练平衡" else "status-warning" if "风险" in load.get("status", "") else "status-good"
            html += f"""
    <h3>训练负荷分析</h3>
    <table>
        <tr>
            <th>指标</th>
            <th>数值</th>
            <th>状态</th>
        </tr>
        <tr>
            <td>急性负荷 (ATI)</td>
            <td>{load.get('acute_load', 'N/A')}</td>
            <td rowspan="2" class="{status_class}">{load.get('status', 'N/A')}</td>
        </tr>
        <tr>
            <td>慢性负荷 (CTI)</td>
            <td>{load.get('chronic_load', 'N/A')}</td>
        </tr>
        <tr>
            <td>负荷比值 (ATI/CTI)</td>
            <td>{load.get('load_ratio', 'N/A')}</td>
            <td class="{status_class}">{load.get('recommendation', '')}</td>
        </tr>
    </table>
"""
        
        # 过度训练风险
        if "overtraining_risk" in analysis:
            risk = analysis["overtraining_risk"]
            risk_class = "status-danger" if risk.get("risk_level") == "高" else "status-warning" if risk.get("risk_level") == "中" else "status-excellent"
            html += f"""
    <h3>过度训练风险评估</h3>
    <p>风险等级：<span class="{risk_class}">{risk.get('risk_level', 'N/A')}</span></p>
    <p>风险因素：{', '.join(risk.get('risk_factors', ['无']))}</p>
    <p>建议：{risk.get('recommendation', '')}</p>
"""
        
        return html
    
    def _render_sleep_analysis(self, analysis: Dict) -> str:
        """渲染睡眠分析"""
        html = """
    <h2>😴 睡眠分析</h2>
"""
        
        if "summary" in analysis:
            summary = analysis["summary"]
            html += f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-value">{summary.get('total_sleep_avg', 'N/A')}</div>
            <div class="metric-label">平均睡眠时长 (分钟)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{summary.get('deep_sleep_avg', 'N/A')}</div>
            <div class="metric-label">平均深睡眠 (分钟)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{summary.get('rem_sleep_avg', 'N/A')}</div>
            <div class="metric-label">平均REM睡眠 (分钟)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{summary.get('sleep_efficiency', 'N/A')}%</div>
            <div class="metric-label">睡眠效率</div>
        </div>
    </div>
"""
        
        if "sleep_quality" in analysis:
            quality = analysis["sleep_quality"]
            quality_class = "status-excellent" if quality.get("rating") == "优秀" else "status-good" if quality.get("rating") == "良好" else "status-warning"
            html += f"""
    <h3>睡眠质量评估</h3>
    <p>综合评级：<span class="{quality_class}">{quality.get('rating', 'N/A')}</span></p>
"""
        
        return html
    
    def _render_trend_analysis(self, analysis: Dict) -> str:
        """渲染趋势分析"""
        html = """
    <h2>📈 趋势分析</h2>
"""
        
        if "training_trends" in analysis:
            html += """
    <h3>训练趋势</h3>
    <table>
        <tr>
            <th>指标</th>
            <th>趋势方向</th>
            <th>近期平均值</th>
        </tr>
"""
            for key, value in analysis["training_trends"].items():
                if isinstance(value, dict):
                    direction = value.get("direction", "N/A")
                    recent = value.get("recent_avg", value.get("recent_weekly_km", "N/A"))
                    html += f"""
        <tr>
            <td>{key}</td>
            <td>{direction}</td>
            <td>{recent}</td>
        </tr>
"""
            html += """
    </table>
"""
        
        if "insights" in analysis:
            html += """
    <h3>💡 数据洞察</h3>
    <ul>
"""
            for insight in analysis["insights"]:
                html += f"<li>{insight}</li>\n"
            html += """
    </ul>
"""
        
        return html
    
    def _render_plots(self, plots: List[str]) -> str:
        """渲染图表"""
        html = """
    <h2>📊 可视化图表</h2>
"""
        
        for plot_file in plots:
            if plot_file and os.path.exists(plot_file):
                # 将图片内嵌为base64，确保HTML独立可打开
                with open(plot_file, 'rb') as img_f:
                    img_data = base64.b64encode(img_f.read()).decode('utf-8')
                filename = os.path.basename(plot_file)
                html += f"""
    <div class="plot-container">
        <h3 style="color:#555;">{filename.replace('.png','').replace('_',' ').title()}</h3>
        <img src="data:image/png;base64,{img_data}" alt="{filename}" style="max-width:100%;">
    </div>
"""
        
        return html
    
    def _render_recommendations(self, results: Dict) -> str:
        """渲染建议部分"""
        html = """
    <h2>💡 综合建议</h2>
"""
        
        all_recommendations = []
        
        # 收集所有建议
        if "training_analysis" in results and "recommendations" in results["training_analysis"]:
            all_recommendations.extend(results["training_analysis"]["recommendations"])
        
        if "sleep_analysis" in results and "recommendations" in results["sleep_analysis"]:
            all_recommendations.extend(results["sleep_analysis"]["recommendations"])
        
        if all_recommendations:
            for rec in all_recommendations:
                html += f"""
    <div class="recommendation">
        {rec}
    </div>
"""
        else:
            html += """
    <div class="recommendation">
        暂无特别建议，继续保持当前训练和生活节奏！
    </div>
"""
        
        return html
    
    def generate_json_report(self, analysis_results: Dict) -> str:
        """
        生成JSON格式报告
        
        Args:
            analysis_results: 分析结果字典
            
        Returns:
            str: 生成的JSON文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"coros_analysis_report_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
        
        return filepath


# 使用示例
if __name__ == "__main__":
    # 模拟分析结果
    mock_results = {
        "training_analysis": {
            "summary": {
                "avg_training_load": 450,
                "vo2max_latest": 52.3,
                "avg_rhr": 54,
            },
            "training_load": {
                "acute_load": 420,
                "chronic_load": 380,
                "load_ratio": 1.11,
                "status": "训练平衡",
                "recommendation": "训练负荷处于健康范围"
            },
            "overtraining_risk": {
                "risk_level": "低",
                "risk_factors": ["无明显风险因素"],
                "recommendation": "当前训练恢复平衡良好"
            },
            "recommendations": ["训练状态良好，继续保持！"]
        },
        "sleep_analysis": {
            "summary": {
                "total_sleep_avg": 435,
                "deep_sleep_avg": 85,
                "rem_sleep_avg": 92,
                "deep_sleep_percentage": 19.5,
                "sleep_efficiency": 88.5
            },
            "sleep_quality": {
                "rating": "良好"
            },
            "recommendations": ["睡眠数据良好，继续保持！"]
        }
    }
    
    builder = ReportBuilder()
    html_file = builder.generate_html_report(mock_results)
    json_file = builder.generate_json_report(mock_results)
    
    print(f"HTML报告已生成：{html_file}")
    print(f"JSON报告已生成：{json_file}")
