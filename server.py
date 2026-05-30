#!/usr/bin/env python3
"""Assistant Status Dashboard - HTTP Server with API endpoints + MCP server."""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

CRON_OUTPUT_DIR = Path.home() / ".hermes" / "cron" / "output"
CRON_JOBS_FILE = Path.home() / ".hermes" / "cron" / "jobs.json"
PORT = 8090
STATIC_DIR = Path(__file__).parent

# --- Data helpers (shared by HTTP API and MCP tools) ---


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


def _get_job_runs(job_id: str, limit: int = 50) -> list:
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


def get_jobs_config() -> dict:
    """Read jobs.json for job metadata, return dict keyed by job id."""
    if not CRON_JOBS_FILE.exists():
        return {}
    try:
        data = json.loads(CRON_JOBS_FILE.read_text())
        jobs_config = {}
        for job in data.get("jobs", []):
            jobs_config[job["id"]] = job
        return jobs_config
    except Exception:
        return {}


def get_all_jobs_summary() -> list:
    """Get summary info for all jobs, merging config and output data."""
    jobs_config = get_jobs_config()

    summaries = []
    if not CRON_OUTPUT_DIR.exists():
        return summaries

    for job_dir in sorted(CRON_OUTPUT_DIR.iterdir()):
        if not job_dir.is_dir():
            continue
        files = sorted(job_dir.glob("*.md"), reverse=True)
        last_run = None
        if files:
            try:
                last_run = parse_cron_output(files[0])
            except Exception:
                pass

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


# --- MCP Server (single Starlette app serves both MCP and HTTP) ---

mcp = FastMCP(
    "Hermes Assistant",
    instructions="查询 Hermes 定时任务(cron jobs)的配置与执行状态。",
)


@mcp.tool()
def list_cron_jobs() -> str:
    """列出所有 Hermes 定时任务及其当前状态摘要。

    返回每个任务的 ID、名称、调度表达式、状态(active/paused)、
    上次执行时间、下次执行时间、总执行次数等信息。
    """
    jobs = get_all_jobs_summary()
    if not jobs:
        return "当前没有定时任务。"

    lines = []
    for j in jobs:
        state_icon = "▶" if j["state"] in ("active", "scheduled") else "⏸" if j["state"] == "paused" else "?"
        last_status = ""
        if j.get("last_run"):
            last_status = f" | 最近状态: {j['last_run'].get('status', 'unknown')}"
        lines.append(
            f"{state_icon} {j['job_name']} ({j['job_id']})\n"
            f"  调度: {j['schedule_display']} | 状态: {j['state']} | 总执行: {j['total_runs']}次\n"
            f"  上次: {j.get('last_run_at', '-')} | 下次: {j.get('next_run_at', '-')}{last_status}"
        )
    return f"共 {len(jobs)} 个定时任务:\n\n" + "\n\n".join(lines)


@mcp.tool()
def get_job_runs(job_id: str, limit: int = 10) -> str:
    """查询指定定时任务的最近执行记录。

    Args:
        job_id: 任务ID（12位十六进制字符串，如 69b434e29ac6）
        limit: 返回最近几条记录，默认10，最大50
    """
    if limit > 50:
        limit = 50
    runs = _get_job_runs(job_id, limit=limit)
    if not runs:
        return f"未找到任务 {job_id} 的执行记录（任务ID可能不存在或尚无执行历史）。"

    # Get job name from config
    jobs_config = get_jobs_config()
    config = jobs_config.get(job_id, {})
    job_name = config.get("name", job_id)

    lines = [f"任务: {job_name} ({job_id})", f"最近 {len(runs)} 条执行记录:", ""]
    for r in runs:
        status_icon = "✓" if r.get("status") == "delivered" else "○" if r.get("status") == "silent" else "✗"
        ts = r.get("timestamp", r.get("filename", "?"))
        response_preview = ""
        if r.get("response"):
            resp = r["response"].replace("[SILENT]", "").strip()
            if resp:
                if len(resp) > 200:
                    resp = resp[:200] + "..."
                response_preview = f"\n    {resp}"
        lines.append(f"  {status_icon} [{ts}] {r.get('status', 'unknown')}{response_preview}")

    return "\n".join(lines)


@mcp.tool()
def get_job_detail(job_id: str) -> str:
    """查询指定定时任务的详细配置信息。

    Args:
        job_id: 任务ID（12位十六进制字符串）
    """
    jobs_config = get_jobs_config()
    config = jobs_config.get(job_id)
    if not config:
        return f"未找到任务 {job_id} 的配置信息。"

    lines = [
        f"任务详情: {config.get('name', job_id)}",
        f"  ID: {job_id}",
        f"  状态: {config.get('state', 'unknown')}",
        f"  调度: {config.get('schedule_display', '-')} (cron: {config.get('schedule', '-')})",
        f"  上次执行: {config.get('last_run_at', '-')}",
        f"  下次执行: {config.get('next_run_at', '-')}",
        f"  投递目标: {config.get('deliver', '-')}",
    ]

    if config.get("prompt"):
        prompt = config["prompt"]
        if len(prompt) > 300:
            prompt = prompt[:300] + "..."
        lines.append(f"  Prompt: {prompt}")

    if config.get("script"):
        lines.append(f"  脚本: {config['script']}")

    if config.get("skills"):
        lines.append(f"  Skills: {', '.join(config['skills'])}")

    if config.get("paused_at"):
        lines.append(f"  暂停时间: {config['paused_at']}")

    return "\n".join(lines)


# --- Custom HTTP routes (served by the same Starlette app as MCP) ---


@mcp.custom_route("/", methods=["GET"])
async def homepage(request: Request) -> Response:
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@mcp.custom_route("/api/jobs", methods=["GET"])
async def api_jobs(request: Request) -> Response:
    data = get_all_jobs_summary()
    return JSONResponse(data)


@mcp.custom_route("/api/runs/{job_id}", methods=["GET"])
async def api_runs(request: Request) -> Response:
    job_id = request.path_params["job_id"]
    limit = int(request.query_params.get("limit", "50"))
    runs = _get_job_runs(job_id, limit=limit)
    return JSONResponse(runs)


# --- Entry point ---

app = mcp.streamable_http_app()


if __name__ == "__main__":
    import uvicorn
    os.chdir(STATIC_DIR)
    print(f"Assistant Dashboard running at http://localhost:{PORT}")
    print(f"MCP endpoint: http://localhost:{PORT}/mcp")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
