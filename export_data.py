"""
COROS 数据导出工具
将系统中的数据（模拟或真实）导出为标准 CSV 格式，供仪表板网页使用

用法:
  python export_data.py --weeks 52    # 导出52周数据
  python export_data.py --weeks 4     # 导出4周数据
"""

import sys, os, csv
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_fetcher import CorosDataFetcher

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")

def export_daily(records, filepath):
    """导出每日指标为 CSV"""
    if not records:
        print("  [!] 无每日指标数据")
        return
    fieldnames = [
        "date","rhr","hrv","training_load","vo2max",
        "ati","cti","tired_rate","distance","duration",
        "stamina_level","lthr","ltsp"
    ]
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for r in records:
            row = {
                "date": str(r.get("date",""))[:8],
                "rhr": r.get("rhr",""),
                "hrv": r.get("avg_sleep_hrv",""),
                "training_load": r.get("training_load",""),
                "vo2max": r.get("vo2max",""),
                "ati": r.get("ati",""),
                "cti": r.get("cti",""),
                "tired_rate": r.get("tired_rate",""),
                "distance": r.get("distance",""),
                "duration": r.get("duration",""),
                "stamina_level": r.get("stamina_level",""),
                "lthr": r.get("lthr",""),
                "ltsp": r.get("ltsp",""),
            }
            writer.writerow(row)
    print(f"  ✓ 每日指标已导出: {filepath}（{len(records)} 条）")

def export_sleep(records, filepath):
    """导出睡眠数据为 CSV"""
    if not records:
        print("  [!] 无睡眠数据")
        return
    fieldnames = [
        "date","total_minutes","deep_minutes","light_minutes",
        "rem_minutes","awake_minutes","quality_score","avg_hr"
    ]
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for r in records:
            phases = r.get("phases", {})
            row = {
                "date": str(r.get("date",""))[:8],
                "total_minutes": r.get("total_duration_minutes",""),
                "deep_minutes": phases.get("deep_minutes","") if phases else r.get("deep_minutes",""),
                "light_minutes": phases.get("light_minutes","") if phases else r.get("light_minutes",""),
                "rem_minutes": phases.get("rem_minutes","") if phases else r.get("rem_minutes",""),
                "awake_minutes": phases.get("awake_minutes","") if phases else r.get("awake_minutes",""),
                "quality_score": r.get("quality_score",""),
                "avg_hr": r.get("avg_hr",""),
            }
            writer.writerow(row)
    print(f"  ✓ 睡眠数据已导出: {filepath}（{len(records)} 条）")

def export_activities(activities, filepath):
    """导出活动记录为 CSV"""
    if not activities:
        print("  [!] 无活动记录")
        return
    fieldnames = [
        "date","name","sport_type","duration_seconds","distance_meters",
        "avg_hr","max_hr","calories","training_load","elevation_gain"
    ]
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for a in activities:
            row = {
                "date": str(a.get("start_time",""))[:10].replace("-",""),
                "name": a.get("name",""),
                "sport_type": a.get("sport_name", a.get("sport_type","")),
                "duration_seconds": a.get("duration_seconds",""),
                "distance_meters": a.get("distance_meters",""),
                "avg_hr": a.get("avg_hr",""),
                "max_hr": a.get("max_hr",""),
                "calories": a.get("calories",""),
                "training_load": a.get("training_load",""),
                "elevation_gain": a.get("elevation_gain",""),
            }
            writer.writerow(row)
    print(f"  ✓ 活动记录已导出: {filepath}（{len(activities)} 条）")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="COROS 数据导出工具")
    parser.add_argument("--weeks", type=int, default=52, help="导出周数（默认52周）")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n{'='*55}")
    print(f"COROS 数据导出工具")
    print(f"{'='*55}")
    print(f"导出范围：近 {args.weeks} 周 ({args.weeks*7} 天)")
    print(f"输出目录：{OUTPUT_DIR}")
    print()

    fetcher = CorosDataFetcher()

    # 每日指标
    print("[1/3] 获取每日指标...")
    daily = fetcher.get_daily_metrics(weeks=args.weeks)
    export_daily(
        daily.get("records", []),
        os.path.join(OUTPUT_DIR, f"daily_metrics_{args.weeks}w.csv")
    )

    # 睡眠
    print("[2/3] 获取睡眠数据...")
    sleep = fetcher.get_sleep_data(weeks=args.weeks)
    export_sleep(
        sleep.get("records", []),
        os.path.join(OUTPUT_DIR, f"sleep_data_{args.weeks}w.csv")
    )

    # 活动记录（按月分段获取更多历史）
    print("[3/3] 获取活动记录...")
    all_activities = []
    end = datetime.now()
    for month_offset in range(0, args.weeks // 4 + 1):
        seg_end = end - timedelta(weeks=month_offset*4)
        seg_start = seg_end - timedelta(weeks=4)
        batch = fetcher.list_activities(
            start_day=seg_start.strftime("%Y%m%d"),
            end_day=seg_end.strftime("%Y%m%d"),
            page=1, size=100
        )
        acts = batch.get("activities", [])
        all_activities.extend(acts)

    # 去重
    seen = set()
    unique_acts = []
    for a in all_activities:
        aid = a.get("activity_id") or a.get("start_time","") + str(a.get("duration_seconds",""))
        if aid not in seen:
            seen.add(aid)
            unique_acts.append(a)
    unique_acts.sort(key=lambda a: a.get("start_time",""))

    export_activities(
        unique_acts,
        os.path.join(OUTPUT_DIR, f"activities_{args.weeks}w.csv")
    )

    print(f"\n{'='*55}")
    print("✅ 导出完成！")
    print(f"{'='*55}")
    print(f"\n📂 导出的文件位于：{OUTPUT_DIR}")
    print("\n🌐 使用方法：")
    print("  1. 打开 dashboard.html（已在 coros_analysis_system/ 目录）")
    print("  2. 点击上传区域，选择 exports/ 目录下的 CSV 文件")
    print("  3. 支持同时上传多个 CSV 文件")
    print("\n💡 导入真实 COROS 数据：")
    print("  - 从 COROS App → 更多 → 训练日志 → 导出 CSV")
    print("  - 或联系 COROS 客服申请数据导出")
    print()

if __name__ == "__main__":
    main()
