"""
COROS Analysis System - API Server

Serves dashboard.html and exposes REST endpoints backed only by coros-mcp.
No mock or generated sports data is returned by this server.
"""

import json
import logging
import shutil
import sqlite3
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent

try:
    from flask import Flask, jsonify, request as flask_request, send_from_directory

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.warning("Flask not available, using basic HTTP server")


def is_coros_mcp_available() -> bool:
    return shutil.which("coros-mcp") is not None


def cache_db_path() -> Path:
    return Path.home() / ".config" / "coros-mcp" / "cache.db"


def read_cache_rows(table: str, date_col: str, start_day: str, end_day: str) -> list[dict]:
    db_path = cache_db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"coros-mcp cache not found: {db_path}")

    query = f"SELECT data FROM {table} WHERE {date_col} >= ? AND {date_col} <= ? ORDER BY {date_col}"
    with sqlite3.connect(db_path) as con:
        rows = con.execute(query, (start_day, end_day)).fetchall()
    return [json.loads(row[0]) for row in rows]


def cache_stats() -> dict:
    db_path = cache_db_path()
    if not db_path.exists():
        return {
            "db_path": str(db_path),
            "daily_records": {"count": 0, "from": None, "to": None},
            "sleep_records": {"count": 0, "from": None, "to": None},
            "activities": {"count": 0, "from": None, "to": None},
        }

    with sqlite3.connect(db_path) as con:
        def stats(table: str, date_col: str = "date") -> dict:
            row = con.execute(
                f"SELECT COUNT(*) AS n, MIN({date_col}) AS lo, MAX({date_col}) AS hi FROM {table}"
            ).fetchone()
            return {"count": row[0], "from": row[1], "to": row[2]}

        return {
            "db_path": str(db_path),
            "daily_records": stats("daily_records"),
            "sleep_records": stats("sleep_records"),
            "activities": stats("activities", "start_day"),
        }


def status_payload() -> dict:
    connected = is_coros_mcp_available()
    stats = cache_stats()
    return {
        "status": "running",
        "mcp_connected": connected,
        "source": "coros_mcp" if connected else "not_connected",
        "using_mock": False,
        "message": "coros-mcp is available" if connected else "coros-mcp not found in PATH",
        "cache": stats,
        "timestamp": datetime.now().isoformat(),
    }


def error_payload(message: str, errors: dict | None = None) -> dict:
    payload = {
        "error": message,
        "source": "coros_mcp",
        "using_mock": False,
        "mcp_connected": is_coros_mcp_available(),
        "timestamp": datetime.now().isoformat(),
    }
    if errors:
        payload["errors"] = errors
    return payload


def fetch_all_data(weeks: int) -> tuple[dict, int]:
    end_day = datetime.now().strftime("%Y%m%d")
    start_day = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y%m%d")

    try:
        daily_records = read_cache_rows("daily_records", "date", start_day, end_day)
        sleep_records = read_cache_rows("sleep_records", "date", start_day, end_day)
        activities = read_cache_rows("activities", "start_day", start_day, end_day)
    except Exception as exc:
        return error_payload(str(exc)), 503

    if not daily_records and not sleep_records and not activities:
        return error_payload(
            "coros-mcp cache is empty for this range. Run 'coros-mcp auth' and then 'coros-mcp sync'."
        ), 503

    return {
        "daily_metrics": {
            "records": daily_records,
            "count": len(daily_records),
            "date_range": f"{start_day} to {end_day}",
            "source": "coros_mcp_cache",
        },
        "sleep_data": {
            "records": sleep_records,
            "count": len(sleep_records),
            "date_range": f"{start_day} to {end_day}",
            "source": "coros_mcp_cache",
        },
        "activities": {
            "activities": activities,
            "total_count": len(activities),
            "source": "coros_mcp_cache",
        },
        "using_mock": False,
        "source": "coros_mcp_cache",
        "mcp_connected": True,
        "cache": cache_stats(),
        "timestamp": datetime.now().isoformat(),
    }, 200


if FLASK_AVAILABLE:
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.route("/", methods=["GET"])
    @app.route("/dashboard.html", methods=["GET"])
    def dashboard():
        return send_from_directory(str(ROOT_DIR), "dashboard.html")

    @app.route("/api/status", methods=["GET"])
    def status():
        return jsonify(status_payload())

    @app.route("/api/daily_metrics", methods=["GET"])
    def get_daily_metrics():
        weeks = int(flask_request.args.get("weeks", 52))
        end_day = datetime.now().strftime("%Y%m%d")
        start_day = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y%m%d")
        try:
            records = read_cache_rows("daily_records", "date", start_day, end_day)
        except Exception as exc:
            return jsonify(error_payload(str(exc))), 503
        return jsonify({"records": records, "count": len(records), "date_range": f"{start_day} to {end_day}", "source": "coros_mcp_cache"})

    @app.route("/api/sleep_data", methods=["GET"])
    def get_sleep_data():
        weeks = int(flask_request.args.get("weeks", 52))
        end_day = datetime.now().strftime("%Y%m%d")
        start_day = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y%m%d")
        try:
            records = read_cache_rows("sleep_records", "date", start_day, end_day)
        except Exception as exc:
            return jsonify(error_payload(str(exc))), 503
        return jsonify({"records": records, "count": len(records), "date_range": f"{start_day} to {end_day}", "source": "coros_mcp_cache"})

    @app.route("/api/activities", methods=["GET"])
    def get_activities():
        weeks = int(flask_request.args.get("weeks", 52))
        end_day = datetime.now().strftime("%Y%m%d")
        start_day = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y%m%d")
        try:
            activities = read_cache_rows("activities", "start_day", start_day, end_day)
        except Exception as exc:
            return jsonify(error_payload(str(exc))), 503
        return jsonify({"activities": activities, "total_count": len(activities), "source": "coros_mcp_cache"})

    @app.route("/api/activity/<activity_id>", methods=["GET"])
    def get_activity_detail(activity_id):
        db_path = cache_db_path()
        if not db_path.exists():
            return jsonify(error_payload(f"coros-mcp cache not found: {db_path}")), 503
        with sqlite3.connect(db_path) as con:
            row = con.execute("SELECT data FROM activities WHERE activity_id = ?", (activity_id,)).fetchone()
        if not row:
            return jsonify(error_payload(f"activity not found in cache: {activity_id}")), 404
        return jsonify(json.loads(row[0]))

    @app.route("/api/all", methods=["GET"])
    def get_all_data():
        weeks = int(flask_request.args.get("weeks", 52))
        payload, status_code = fetch_all_data(weeks)
        return jsonify(payload), status_code


class COROSHandler(SimpleHTTPRequestHandler):
    server_version = "COROSAnalysisHTTP/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in ("/", "/dashboard.html"):
            self.serve_dashboard()
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        elif path == "/api/status":
            self.send_json(status_payload())
        elif path == "/api/daily_metrics":
            weeks = int(qs.get("weeks", ["52"])[0])
            end_day = datetime.now().strftime("%Y%m%d")
            start_day = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y%m%d")
            try:
                records = read_cache_rows("daily_records", "date", start_day, end_day)
                self.send_json({"records": records, "count": len(records), "date_range": f"{start_day} to {end_day}", "source": "coros_mcp_cache"})
            except Exception as exc:
                self.send_json(error_payload(str(exc)), 503)
        elif path == "/api/sleep_data":
            weeks = int(qs.get("weeks", ["52"])[0])
            end_day = datetime.now().strftime("%Y%m%d")
            start_day = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y%m%d")
            try:
                records = read_cache_rows("sleep_records", "date", start_day, end_day)
                self.send_json({"records": records, "count": len(records), "date_range": f"{start_day} to {end_day}", "source": "coros_mcp_cache"})
            except Exception as exc:
                self.send_json(error_payload(str(exc)), 503)
        elif path == "/api/activities":
            weeks = int(qs.get("weeks", ["52"])[0])
            end_day = datetime.now().strftime("%Y%m%d")
            start_day = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y%m%d")
            try:
                activities = read_cache_rows("activities", "start_day", start_day, end_day)
                self.send_json({"activities": activities, "total_count": len(activities), "source": "coros_mcp_cache"})
            except Exception as exc:
                self.send_json(error_payload(str(exc)), 503)
        elif path == "/api/all":
            weeks = int(qs.get("weeks", ["52"])[0])
            payload, status_code = fetch_all_data(weeks)
            self.send_json(payload, status_code)
        else:
            self.send_error(404, "Not found")

    def serve_dashboard(self):
        dashboard_path = ROOT_DIR / "dashboard.html"
        if not dashboard_path.exists():
            self.send_error(404, "dashboard.html not found")
            return

        content = dashboard_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data: dict, status_code: int = 200):
        response = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        logger.info("%s - %s", self.client_address[0], format % args)


def run_server(port: int = 5000):
    logger.info("Starting COROS API Server")
    logger.info("Dashboard: http://127.0.0.1:%s/dashboard.html", port)
    logger.info("API status: http://127.0.0.1:%s/api/status", port)

    if FLASK_AVAILABLE:
        app.run(host="127.0.0.1", port=port, debug=False)
    else:
        server = HTTPServer(("127.0.0.1", port), COROSHandler)
        server.serve_forever()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="COROS API Server")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    args = parser.parse_args()
    run_server(args.port)
