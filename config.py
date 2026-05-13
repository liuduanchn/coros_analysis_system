"""
COROS Analysis System - 配置文件
"""

# COROS API 配置
COROS_CONFIG = {
    "email": "newton123@qq.com",  # 替换为你的COROS账号
    "password": "Newton123",        # 替换为你的密码
    "region": "asia",                   # 区域: eu, us, asia
}

# 数据分析配置
ANALYSIS_CONFIG = {
    "default_weeks": 4,           # 默认分析周数
    "hrv_baseline_days": 7,       # HRV基线计算天数
    "training_load_window": 42,    # 训练负荷计算窗口(天)
}

# 报告输出配置
REPORT_CONFIG = {
    "output_dir": "reports",
    "plot_style": "seaborn",
    "figure_size": (12, 6),
    "chinese_font": "SimHei",     # 中文字体支持
}

# 睡眠分析阈值
SLEEP_THRESHOLDS = {
    "deep_sleep_excellent": 90,   # 分钟
    "deep_sleep_good": 60,
    "rem_sleep_excellent": 90,
    "rem_sleep_good": 60,
    "sleep_quality_excellent": 85,
    "sleep_quality_good": 70,
}

# 训练负荷阈值
TRAINING_LOAD_THRESHOLDS = {
    "low": 0,
    "optimal": 300,
    "high": 600,
    "very_high": 900,
}
