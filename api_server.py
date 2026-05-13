"""
COROS Analysis System - API Server
通过本地 coros-mcp 服务获取数据，提供 REST API 给 dashboard 调用
"""

import json
import subprocess
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import random

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入 Flask（可选，增强功能）
try:
    from flask import Flask, jsonify, request as flask_request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.warning("Flask not available, using basic HTTP server")

# ============================================================
# COROS MCP 工具调用
# ============================================================

def call_coros_mcp(command: str, params: dict = None) -> dict:
    """
    调用 coros-mcp 工具

    Args:
        command: MCP 工具命令 (如 get_daily_metrics, get_sleep_data, list_activities)
        params: 工具参数

    Returns:
        dict: 工具返回的数据
    """
    try:
        # 构造 MCP JSON-RPC 请求
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": f"tools/call",
            "params": {
                "name": command,
                "arguments": params or {}
            }
        }

        # 通过 subprocess 调用 coros-mcp
        result = subprocess.run(
            ["coros-mcp", "call", command, json.dumps(params or {})],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            logger.error(f"coros-mcp error: {result.stderr}")
            return {"error": result.stderr, "using_mock": True}

    except FileNotFoundError:
        logger.warning("coros-mcp not found in PATH, using mock data")
        return {"error": "coros-mcp not installed", "using_mock": True}
    except subprocess.TimeoutExpired:
        logger.error("coros-mcp timeout")
        return {"error": "timeout", "using_mock": True}
    except Exception as e:
        logger.error(f"coros-mcp call failed: {e}")
        return {"error": str(e), "using_mock": True}


# ============================================================
# 模拟数据生成（当 MCP 不可用时）
# ============================================================

def generate_mock_daily_metrics(weeks: int = 52) -> dict:
    """生成模拟每日指标数据"""
    records = []
    today = datetime.now()

    for i in range(weeks * 7):
        date = today - timedelta(days=weeks * 7 - i)
        date_str = date.strftime("%Y%m%d")

        # 生成较为真实的趋势数据
        trend = i / (weeks * 7)  # 0 到 1 的趋势

        records.append({
            "date": int(date_str),
            "avg_sleep_hrv": int(50 + 20 * (1 - trend * 0.3) + random.randint(-5, 5)),
            "baseline": int(45 + 15 * (1 - trend * 0.2) + random.randint(-3, 3)),
            "rhr": int(52 + 8 * (1 - trend * 0.25) + random.randint(-3, 3)),
            "training_load": int(300 + 250 * trend + random.randint(-50, 50)),
            "training_load_ratio": round(0.9 + 0.4 * trend + random.uniform(-0.1, 0.1), 2),
            "tired_rate": int(40 + 30 * trend + random.randint(-10, 10)),
            "ati": round(300 + 200 * trend + random.uniform(-20, 20), 1),
            "cti": round(350 + 100 * trend + random.uniform(-15, 15), 1),
            "distance": int(5000 + 8000 * trend + random.randint(-500, 500)),
            "duration": int(2700 + 1800 * trend + random.randint(-200, 200)),
            "vo2max": round(48 + 8 * trend + random.uniform(-1, 1), 1),
            "lthr": int(160 + 10 * trend + random.randint(-3, 3)),
            "ltsp": round(260 + 30 * trend + random.uniform(-10, 10), 1),
            "stamina_level": int(70 + 15 * (1 - abs(trend - 0.5) * 2) + random.randint(-5, 5)),
            "stamina_level_7d": int(72 + 12 * (1 - abs(trend - 0.5) * 2) + random.randint(-4, 4)),
        })

    return {
        "records": records,
        "count": len(records),
        "date_range": f"{records[0]['date']} to {records[-1]['date']}",
        "source": "mock"
    }


def generate_mock_sleep_data(weeks: int = 52) -> dict:
    """生成模拟睡眠数据"""
    records = []
    today = datetime.now()

    for i in range(weeks * 7):
        date = today - timedelta(days=weeks * 7 - i)
        date_str = date.strftime("%Y%m%d")

        # 生成较为真实的睡眠数据
        deep = int(75 + 25 + random.randint(-15, 15))
        light = int(240 + random.randint(-30, 30))
        rem = int(85 + 20 + random.randint(-10, 10))
        awake = int(20 + random.randint(-10, 5))

        records.append({
            "date": int(date_str),
            "total_duration_minutes": deep + light + rem + awake,
            "phases": {
                "deep_minutes": deep,
                "light_minutes": light,
                "rem_minutes": rem,
                "awake_minutes": awake,
                "nap_minutes": random.randint(0, 30) if random.random() > 0.7 else 0,
            },
            "avg_hr": int(55 + random.randint(-5, 5)),
            "min_hr": int(48 + random.randint(-4, 4)),
            "max_hr": int(82 + random.randint(-5, 5)),
            "quality_score": int(75 + random.randint(-10, 15)),
        })

    return {
        "records": records,
        "count": len(records),
        "date_range": f"{records[0]['date']} to {records[-1]['date']}",
        "source": "mock"
    }


def generate_mock_activities(weeks: int = 52) -> dict:
    """生成模拟活动数据"""
    activities = []
    today = datetime.now()
    start_date = today - timedelta(weeks=weeks * 7)

    sport_types = [
        {"type": 1, "name": "跑步", "emoji": "🏃"},
        {"type": 2, "name": "骑行", "emoji": "🚴"},
        {"type": 3, "name": "游泳", "emoji": "🏊"},
        {"type": 4, "name": "力量训练", "emoji": "💪"},
        {"type": 7, "name": "越野跑", "emoji": "🏔️"},
        {"type": 9, "name": "登山", "emoji": "⛰️"},
    ]

    # 生成约 100 条活动记录
    num_activities = min(weeks * 7 // 3, 150)

    for i in range(num_activities):
        sport = random.choice(sport_types)
        date = start_date + timedelta(days=random.randint(0, weeks * 7 - 1))

        # 跑步活动
        if sport["type"] == 1:
            distance = random.randint(3000, 25000)
            duration = int(distance / (3.0 + random.uniform(-0.5, 1)))
            elevation = random.randint(20, 500)
        # 骑行活动
        elif sport["type"] == 2:
            distance = random.randint(20000, 120000)
            duration = int(distance / (25 + random.uniform(-5, 10)))
            elevation = random.randint(100, 1500)
        # 游泳
        elif sport["type"] == 3:
            distance = random.randint(1000, 5000)
            duration = int(distance / 1.2) + random.randint(60, 300)
            elevation = 0
        # 其他
        else:
            distance = 0
            duration = random.randint(1800, 5400)
            elevation = random.randint(50, 800)

        start_time = date + timedelta(hours=random.randint(6, 20), minutes=random.randint(0, 59))

        activities.append({
            "activity_id": f"4699010149657{i:08d}",
            "name": f"{sport['name']} {date.strftime('%m月%d日')}",
            "sport_type": sport["type"],
            "sport_name": sport["name"],
            "sport_emoji": sport["emoji"],
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": (start_time + timedelta(seconds=duration)).strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": duration,
            "distance_meters": distance,
            "avg_hr": random.randint(130, 175),
            "max_hr": random.randint(165, 195),
            "calories": random.randint(300, 900),
            "training_load": random.randint(100, 450),
            "avg_power": random.randint(150, 300) if sport["type"] in [2, 4] else None,
            "normalized_power": random.randint(160, 320) if sport["type"] in [2, 4] else None,
            "elevation_gain": elevation,
        })

    # 按时间排序（最新的在前）
    activities.sort(key=lambda x: x["start_time"], reverse=True)

    return {
        "activities": activities,
        "total_count": len(activities),
        "source": "mock"
    }


# ============================================================
# Flask API Server（推荐）
# ============================================================

if FLASK_AVAILABLE:
    app = Flask(__name__)

    @app.route('/api/status', methods=['GET'])
    def status():
        """检查 API 状态和 MCP 连接状态"""
        return jsonify({
            "status": "running",
            "mcp_connected": False,  # 需要实际检测
            "timestamp": datetime.now().isoformat()
        })

    @app.route('/api/daily_metrics', methods=['GET'])
    def get_daily_metrics():
        """获取每日指标数据"""
        weeks = int(flask_request.args.get('weeks', 52))

        # 尝试使用 MCP
        result = call_coros_mcp("get_daily_metrics", {"weeks": weeks})

        # 如果 MCP 失败，使用模拟数据
        if result.get("using_mock") or result.get("error"):
            logger.info("Using mock data for daily_metrics")
            result = generate_mock_daily_metrics(weeks)

        return jsonify(result)

    @app.route('/api/sleep_data', methods=['GET'])
    def get_sleep_data():
        """获取睡眠数据"""
        weeks = int(flask_request.args.get('weeks', 52))

        result = call_coros_mcp("get_sleep_data", {"weeks": weeks})

        if result.get("using_mock") or result.get("error"):
            logger.info("Using mock data for sleep_data")
            result = generate_mock_sleep_data(weeks)

        return jsonify(result)

    @app.route('/api/activities', methods=['GET'])
    def get_activities():
        """获取活动记录"""
        weeks = int(flask_request.args.get('weeks', 52))
        page = int(flask_request.args.get('page', 1))
        size = int(flask_request.args.get('size', 50))

        start_day = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y%m%d")
        end_day = datetime.now().strftime("%Y%m%d")

        result = call_coros_mcp("list_activities", {
            "start_day": start_day,
            "end_day": end_day,
            "page": page,
            "size": size
        })

        if result.get("using_mock") or result.get("error"):
            logger.info("Using mock data for activities")
            result = generate_mock_activities(weeks)

        return jsonify(result)

    @app.route('/api/activity/<activity_id>', methods=['GET'])
    def get_activity_detail(activity_id):
        """获取活动详情"""
        sport_type = int(flask_request.args.get('sport_type', 1))

        result = call_coros_mcp("get_activity_detail", {
            "activity_id": activity_id,
            "sport_type": sport_type
        })

        # 模拟活动详情
        if result.get("using_mock") or result.get("error"):
            return jsonify({
                "activity_id": activity_id,
                "sport_type": sport_type,
                "message": "Mock activity detail",
                "laps": [],
                "source": "mock"
            })

        return jsonify(result)

    @app.route('/api/all', methods=['GET'])
    def get_all_data():
        """一次性获取所有数据（用于 dashboard 初始化）"""
        weeks = int(flask_request.args.get('weeks', 52))

        daily = call_coros_mcp("get_daily_metrics", {"weeks": weeks})
        sleep = call_coros_mcp("get_sleep_data", {"weeks": weeks})

        start_day = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y%m%d")
        end_day = datetime.now().strftime("%Y%m%d")
        activities = call_coros_mcp("list_activities", {
            "start_day": start_day,
            "end_day": end_day,
            "size": 100
        })

        # 如果任何 MCP 调用失败，使用模拟数据
        using_mock = daily.get("using_mock") or sleep.get("using_mock") or activities.get("using_mock")

        if using_mock or daily.get("error"):
            daily = generate_mock_daily_metrics(weeks)
        if using_mock or sleep.get("error"):
            sleep = generate_mock_sleep_data(weeks)
        if using_mock or activities.get("error"):
            activities = generate_mock_activities(weeks)

        return jsonify({
            "daily_metrics": daily,
            "sleep_data": sleep,
            "activities": activities,
            "using_mock": using_mock,
            "timestamp": datetime.now().isoformat()
        })

    def run_server(port=5000):
        """启动 API 服务器"""
        logger.info(f"Starting COROS API Server on http://localhost:{port}")
        app.run(host='127.0.0.1', port=port, debug=False)


# ============================================================
# Basic HTTP Server（无 Flask 时使用）
# ============================================================

class COROSHandler(SimpleHTTPRequestHandler):
    """自定义 HTTP 处理程序"""

    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == '/api/status':
            self.send_json({"status": "running", "mcp_connected": False})
        elif path == '/api/daily_metrics':
            weeks = int(qs.get('weeks', ['52'])[0])
            result = call_coros_mcp("get_daily_metrics", {"weeks": weeks})
            if result.get("using_mock") or result.get("error"):
                result = generate_mock_daily_metrics(weeks)
            self.send_json(result)
        elif path == '/api/sleep_data':
            weeks = int(qs.get('weeks', ['52'])[0])
            result = call_coros_mcp("get_sleep_data", {"weeks": weeks})
            if result.get("using_mock") or result.get("error"):
                result = generate_mock_sleep_data(weeks)
            self.send_json(result)
        elif path == '/api/activities':
            weeks = int(qs.get('weeks', ['52'])[0])
            result = call_coros_mcp("list_activities", {
                "start_day": (datetime.now() - timedelta(weeks=weeks)).strftime("%Y%m%d"),
                "end_day": datetime.now().strftime("%Y%m%d"),
                "size": 100
            })
            if result.get("using_mock") or result.get("error"):
                result = generate_mock_activities(weeks)
            self.send_json(result)
        elif path == '/api/all':
            weeks = int(qs.get('weeks', ['52'])[0])
            self.send_json({
                "daily_metrics": generate_mock_daily_metrics(weeks),
                "sleep_data": generate_mock_sleep_data(weeks),
                "activities": generate_mock_activities(weeks),
                "using_mock": True,
                "timestamp": datetime.now().isoformat()
            })
        else:
            # 静态文件服务
            super().do_GET()

    def send_json(self, data):
        """发送 JSON 响应"""
        response = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(response))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        """自定义日志格式"""
        logger.info(f"{self.client_address[0]} - {format % args}")


def run_basic_server(port=5000):
    """启动基础 HTTP 服务器"""
    server = HTTPServer(('127.0.0.1', port), COROSHandler)
    logger.info(f"Starting COROS API Server on http://localhost:{port}")
    server.serve_forever()


# ============================================================
# 主入口
# ============================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='COROS API Server')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    parser.add_argument('--mock-only', action='store_true', help='Use mock data only')
    args = parser.parse_args()

    if FLASK_AVAILABLE and not args.mock_only:
        run_server(args.port)
    else:
        run_basic_server(args.port)
