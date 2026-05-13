# COROS 运动数据分析系统

基于 COROS MCP (Model Context Protocol) 的运动数据分析系统，支持训练数据、睡眠数据和趋势分析。

## 功能特性

- **训练数据分析**：训练负荷、体能水平、过度训练风险评估
- **睡眠分析**：深睡眠、REM睡眠、睡眠质量评分
- **趋势分析**：HRV、静息心率、VO2max等指标的趋势追踪
- **可视化报告**：自动生成图表和HTML报告

## 系统架构

```
coros_analysis_system/
├── config.py                 # 配置文件
├── data_fetcher.py           # 数据获取模块（COROS MCP接口）
├── main.py                   # 主程序入口
├── analyzers/                # 分析模块
│   ├── __init__.py
│   ├── sleep_analyzer.py     # 睡眠分析
│   ├── training_analyzer.py   # 训练分析
│   └── trend_analyzer.py     # 趋势分析
├── visualizers/             # 可视化模块
│   ├── __init__.py
│   ├── plot_generator.py     # 图表生成
│   └── report_builder.py     # 报告生成
├── reports/                  # 报告输出目录
├── requirements.txt          # 依赖清单
└── README.md                # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置COROS账号

编辑 `config.py` 文件，填入你的COROS账号信息：

```python
COROS_CONFIG = {
    "email": "your_email@example.com",
    "password": "your_password",
    "region": "asia",  # eu, us, asia
}
```

### 3. 运行分析

```bash
# 完整分析（4周数据）
python main.py

# 指定周数
python main.py --weeks 8

# 仅分析睡眠
python main.py --mode sleep

# 仅分析训练
python main.py --mode training

# 仅分析趋势
python main.py --mode trend
```

## 分析报告

运行后会在 `reports/` 目录生成：

- `training_load_trend.png` - 训练负荷趋势图
- `hrv_trend.png` - HRV趋势图
- `rhr_trend.png` - 静息心率趋势图
- `vo2max_trend.png` - VO2max趋势图
- `sleep_stages.png` - 睡眠阶段分布图
- `sleep_quality.png` - 睡眠质量评分图
- `comprehensive_dashboard.png` - 综合仪表盘
- `coros_analysis_report_*.html` - HTML分析报告
- `coros_analysis_report_*.json` - JSON格式报告

## 核心分析指标

### 训练指标

| 指标 | 说明 | 正常范围 |
|------|------|----------|
| ATI | 急性训练负荷 | 近期训练量 |
| CTI | 慢性训练负荷 | 长期训练量 |
| ATI/CTI | 训练负荷比值 | 0.8-1.3 |
| VO2max | 最大摄氧量 | 45-60 ml/kg/min |
| 静息心率 | 晨起静息心率 | 45-65 bpm |

### 睡眠指标

| 指标 | 说明 | 优秀标准 |
|------|------|----------|
| 深睡眠 | 深度睡眠时长 | >90分钟 |
| REM睡眠 | 快速眼动睡眠 | >90分钟 |
| 睡眠效率 | 实际睡眠/卧床时间 | >85% |
| 睡眠质量评分 | 综合评分 | >85分 |

## 与COROS MCP集成

本系统设计用于与 [COROS MCP Server](https://github.com/cygnusb/coros-mcp) 配合使用：

1. 安装 COROS MCP Server
2. 配置 WorkBuddy MCP 设置
3. 系统将自动通过MCP获取数据

## 技术栈

- Python 3.11+
- pandas - 数据处理
- matplotlib - 图表生成
- numpy - 数值计算

## 注意事项

- 本系统使用模拟数据进行演示
- 实际使用需配置真实的COROS账号
- 建议每周运行一次完整分析

## 参考链接

- [COROS 官网](https://www.coros.com/)
- [COROS MCP Server](https://github.com/cygnusb/coros-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

*此分析系统基于 COROS 非官方API开发，仅供个人学习使用。*
