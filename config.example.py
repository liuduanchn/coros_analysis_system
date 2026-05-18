"""
Example settings for the COROS analysis system.

Copy this file to config.py and fill in your own values locally.
Do not commit config.py.
"""

import os


COROS_CONFIG = {
    "email": os.getenv("COROS_EMAIL", "your_email@example.com"),
    "password": os.getenv("COROS_PASSWORD", "your_password"),
    "region": os.getenv("COROS_REGION", "asia"),  # eu, us, asia
}


ANALYSIS_CONFIG = {
    "default_weeks": 4,
    "hrv_baseline_days": 7,
    "training_load_window": 42,
}


REPORT_CONFIG = {
    "output_dir": "reports",
    "plot_style": "seaborn",
    "figure_size": (12, 6),
    "chinese_font": "SimHei",
}


SLEEP_THRESHOLDS = {
    "deep_sleep_excellent": 90,
    "deep_sleep_good": 60,
    "rem_sleep_excellent": 90,
    "rem_sleep_good": 60,
    "sleep_quality_excellent": 85,
    "sleep_quality_good": 70,
}


TRAINING_LOAD_THRESHOLDS = {
    "low": 0,
    "optimal": 300,
    "high": 600,
    "very_high": 900,
}
