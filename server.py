#!/usr/bin/env python3
"""Assistant Status Dashboard - HTTP Server with API endpoints."""

import http.server
import json
import os
import re
from datetime import datetime
from pathlib import Path

CRON_OUTPUT_DIR = Path.home() / ".hermes" / "cron" / "output"
CRON_JOBS_FILE = Path.home() / ".hermes" / "cron" / "jobs.json"
PORT = 8090


def parse_cron_output(filepath: Path) -> dict:
    """Parse a cron output markdown file into structured data."""
    content = filepath.read_text(encoding="utf-8")

    result = {
        "filename": filepath.name,
        "timestamp": None,
        "job_name": None,
        "job_id": None,
        "schedule": None,
        "response": None,
        "status": "unknown",  # silent, delivered, error
    }

    # Extract run time
    m = re.search(r"\*\*Run Time:\*\*\s*(.+)", content)
    if m:
        result["timestamp"] = m.group(1).strip()

    # Extract job name
    m = re.search(r"# Cron Job:\s*(.+)", content)
    if m:
        result["job_name"] = m.group(1).strip()

    # Extract job ID
    m = re.search(r"\*\*Job ID:\*\*\s*(.+)", content)
    if m:
        result["job_id"] = m.group(1).strip()

    # Extract schedule
    m = re.search(r"\*\*Schedule:\*\*\s*(.+)", content)
    if m:
        result["schedule"] = m.group(1).strip()

    # Extract response (after ## Response)
    m = re.search(r"## Response\n\n(.+)", content, re.DOTALL)
    if m:
        response = m.group(1).strip()
        result["response"] = response
        if "[SILENT]" in response:
            result["status"] = "silent"
        else:
            result["status"] = "delivered"
    else:
        result["status"] = "no_response"

    return result


def get_job_runs(job_id: str, limit: int = 50) -> list:
    """Get recent runs for a specific job."""
    job_dir = CRON_OUTPUT_DIR / job_id
    if not job_dir.exists():
        return []

    files = sorted(job_dir.glob("*.md"), reverse=True)[:limit]
    runs = []
    for f in files:
        try:
            runs.append(parse_cron_output(f))
        except Exception as e:
            runs.append({"filename": f.name, "error": str(e)})
    return runs


def get_jobs_config() -> list:
    """Read jobs.json for job metadata."""
    if not CRON_JOBS_FILE.exists():
        return []
    try:
        data = json.loads(CRON_JOBS_FILE.read_text())
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def get_all_jobs_summary() -> list:
    """Get summary info for all jobs, merging config and output data."""
    # Load job configs from jobs.json
    jobs_config = {}
    if CRON_JOBS_FILE.exists():
        try:
            data = json.loads(CRON_JOBS_FILE.read_text())
            for job in data.get("jobs", []):
                jobs_config[job["id"]] = job
        except Exception:
            pass

    summaries = []
    if not CRON_OUTPUT_DIR.exists():
        return summaries

    for job_dir in sorted(CRON_OUTPUT_DIR.iterdir()):
        if not job_dir.is_dir():
            continue
        files = sorted(job_dir.glob("*.md"), reverse=True)
        last_run = None
        if files:
            last_run = parse_cron_output(files[0])

        job_id = job_dir.name
        config = jobs_config.get(job_id, {})

        summaries.append({
            "job_id": job_id,
            "job_name": config.get("name", job_id),
            "state": config.get("state", "unknown"),
            "enabled": config.get("enabled", False),
            "schedule_display": config.get("schedule_display", ""),
            "last_run_at": config.get("last_run_at"),
            "next_run_at": config.get("next_run_at"),
            "last_status": config.get("last_status"),
            "paused_at": config.get("paused_at"),
            "deliver": config.get("deliver"),
            "repeat_completed": config.get("repeat", {}).get("completed", 0) if isinstance(config.get("repeat"), dict) else 0,
            "total_runs": len(list(job_dir.glob("*.md"))),
            "last_run": last_run,
        })
    return summaries


class AssistantHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html_path = Path(__file__).parent / "index.html"
            self.wfile.write(html_path.read_bytes())

        elif self.path == "/api/jobs":
            self.send_json(get_all_jobs_summary())

        elif self.path.startswith("/api/runs/"):
            parts = self.path.split("/")
            job_id = parts[3] if len(parts) > 3 else ""
            # Parse limit from query
            limit = 50
            if "?" in self.path:
                query = self.path.split("?")[1]
                for param in query.split("&"):
                    if param.startswith("limit="):
                        try:
                            limit = int(param.split("=")[1])
                        except ValueError:
                            pass
                job_id = job_id.split("?")[0]
            runs = get_job_runs(job_id, limit=limit)
            self.send_json(runs)

        else:
            super().do_GET()

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def log_message(self, format, *args):
        # Quieter logging
        pass


class AssistantHTTPServer(http.server.HTTPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    server = AssistantHTTPServer(("0.0.0.0", PORT), AssistantHandler)
    print(f"Assistant Dashboard running at http://localhost:{PORT}")
    server.serve_forever()
