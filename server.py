#!/usr/bin/env python3
"""Assistant Status Dashboard - HTTP Server with API endpoints + MCP server.

Serves:
- Web dashboard at /
- REST API at /api/*
- MCP (Streamable HTTP) at /mcp
"""

import json
import os
import re
import sqlite3
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

HERMES_DIR = Path.home() / ".hermes"
CRON_OUTPUT_DIR = HERMES_DIR / "cron" / "output"
CRON_JOBS_FILE = HERMES_DIR / "cron" / "jobs.json"
STATE_DB = HERMES_DIR / "state.db"
CONFIG_FILE = HERMES_DIR / "config.yaml"
PORT = 8090
STATIC_DIR = Path(__file__).parent

TZ_CST = timezone(timedelta(hours=8))


# ═══════════════════════════════════════════════════════════
# Data helpers (shared by HTTP API and MCP tools)
# ═══════════════════════════════════════════════════════════


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
        "status": "unknown",
    }

    m = re.search(r"\*\*Run Time:\*\*\s*(.+)", content)
    if m:
        result["timestamp"] = m.group(1).strip()

    m = re.search(r"# Cron Job:\s*(.+)", content)
    if m:
        result["job_name"] = m.group(1).strip()

    m = re.search(r"\*\*Job ID:\*\*\s*(.+)", content)
    if m:
        result["job_id"] = m.group(1).strip()

    m = re.search(r"\*\*Schedule:\*\*\s*(.+)", content)
    if m:
        result["schedule"] = m.group(1).strip()

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


def get_gateway_status() -> dict:
    """Get gateway process status."""
    result = {"running": False, "pid": None, "uptime": None, "uptime_seconds": None}
    try:
        # Find gateway PID via launchctl
        out = subprocess.check_output(
            ["launchctl", "list", "ai.hermes.gateway"],
            stderr=subprocess.DEVNULL, text=True, timeout=5
        )
        m = re.search(r'"PID"\s*=\s*(\d+)', out)
        if m:
            pid = int(m.group(1))
            result["pid"] = pid
            result["running"] = True
            # Get uptime
            ps_out = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "etime="],
                stderr=subprocess.DEVNULL, text=True, timeout=5
            ).strip()
            result["uptime"] = ps_out
            # Parse etime to seconds (format: [[DD-]HH:]MM:SS)
            parts = ps_out.replace("-", ":").split(":")
            parts = [int(p) for p in parts]
            if len(parts) == 2:
                result["uptime_seconds"] = parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                result["uptime_seconds"] = parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 4:
                result["uptime_seconds"] = parts[0] * 86400 + parts[1] * 3600 + parts[2] * 60 + parts[3]
    except Exception:
        pass
    return result


def get_model_info() -> dict:
    """Get current model and provider from config."""
    result = {"model": "unknown", "provider": "unknown"}
    try:
        import yaml
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)
        model_cfg = config.get("model", {})
        if isinstance(model_cfg, dict):
            result["model"] = model_cfg.get("default", "unknown")
            result["provider"] = model_cfg.get("provider", "unknown")
        else:
            result["model"] = str(model_cfg)
    except Exception:
        # Fallback: parse first few lines
        try:
            content = CONFIG_FILE.read_text()
            m = re.search(r"^\s+default:\s*(.+)$", content, re.MULTILINE)
            if m:
                result["model"] = m.group(1).strip()
            m = re.search(r"^\s+provider:\s*(.+)$", content, re.MULTILINE)
            if m:
                result["provider"] = m.group(1).strip()
        except Exception:
            pass
    return result


def get_platforms_status() -> list:
    """Get configured messaging platforms."""
    platforms = []
    try:
        import yaml
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)
        platforms_cfg = config.get("platforms", {})
        if not isinstance(platforms_cfg, dict):
            return platforms
        for name in ["dingtalk", "feishu", "telegram", "discord", "slack", "signal"]:
            section = platforms_cfg.get(name)
            if isinstance(section, dict) and section.get("enabled"):
                platforms.append({"name": name, "configured": True})
    except Exception:
        pass
    return platforms


def get_sessions_stats(days: int = 7) -> dict:
    """Get session statistics from state.db."""
    result = {
        "total_sessions": 0,
        "active_sessions": 0,
        "total_messages": 0,
        "total_tool_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "by_source": [],
        "recent_sessions": [],
    }
    if not STATE_DB.exists():
        return result

    try:
        conn = sqlite3.connect(str(STATE_DB), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff = time.time() - days * 86400

        # Aggregate stats
        row = cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN ended_at IS NULL THEN 1 ELSE 0 END) as active,
                COALESCE(SUM(message_count), 0) as messages,
                COALESCE(SUM(tool_call_count), 0) as tool_calls,
                COALESCE(SUM(input_tokens), 0) as input_tok,
                COALESCE(SUM(output_tokens), 0) as output_tok
            FROM sessions WHERE started_at > ?
        """, (cutoff,)).fetchone()

        result["total_sessions"] = row["total"]
        result["active_sessions"] = row["active"]
        result["total_messages"] = row["messages"]
        result["total_tool_calls"] = row["tool_calls"]
        result["input_tokens"] = row["input_tok"]
        result["output_tokens"] = row["output_tok"]

        # By source
        rows = cursor.execute("""
            SELECT source, COUNT(*) as cnt, COALESCE(SUM(message_count), 0) as msgs
            FROM sessions WHERE started_at > ?
            GROUP BY source ORDER BY cnt DESC
        """, (cutoff,)).fetchall()
        result["by_source"] = [{"source": r["source"], "sessions": r["cnt"], "messages": r["msgs"]} for r in rows]

        # Recent sessions (last 10 non-cron)
        rows = cursor.execute("""
            SELECT id, title, source, model, started_at, ended_at, message_count, tool_call_count
            FROM sessions
            WHERE source != 'cron' AND started_at > ?
            ORDER BY started_at DESC LIMIT 10
        """, (cutoff,)).fetchall()
        result["recent_sessions"] = [{
            "id": r["id"],
            "title": r["title"] or "(untitled)",
            "source": r["source"],
            "model": r["model"],
            "started_at": datetime.fromtimestamp(r["started_at"], tz=TZ_CST).isoformat(),
            "active": r["ended_at"] is None,
            "messages": r["message_count"],
            "tool_calls": r["tool_call_count"],
        } for r in rows]

        conn.close()
    except Exception:
        pass
    return result


def get_today_activity() -> dict:
    """Get today's activity from sessions."""
    result = {"sessions": 0, "messages": 0, "tool_calls": 0, "tokens": 0}
    if not STATE_DB.exists():
        return result
    try:
        conn = sqlite3.connect(str(STATE_DB), timeout=5)
        cursor = conn.cursor()
        today_start = datetime.now(TZ_CST).replace(hour=0, minute=0, second=0).timestamp()
        row = cursor.execute("""
            SELECT COUNT(*) as s,
                   COALESCE(SUM(message_count), 0) as m,
                   COALESCE(SUM(tool_call_count), 0) as t,
                   COALESCE(SUM(input_tokens + output_tokens), 0) as tok
            FROM sessions WHERE started_at > ?
        """, (today_start,)).fetchone()
        result = {"sessions": row[0], "messages": row[1], "tool_calls": row[2], "tokens": row[3]}
        conn.close()
    except Exception:
        pass
    return result


def get_system_overview() -> dict:
    """Assemble full system overview."""
    gateway = get_gateway_status()
    model_info = get_model_info()
    platforms = get_platforms_status()
    sessions = get_sessions_stats(days=7)
    today = get_today_activity()
    jobs = get_all_jobs_summary()

    return {
        "timestamp": datetime.now(TZ_CST).isoformat(),
        "gateway": gateway,
        "model": model_info,
        "platforms": platforms,
        "cron_jobs": jobs,
        "sessions_7d": sessions,
        "today": today,
    }


# ═══════════════════════════════════════════════════════════
# MCP Server
# ═══════════════════════════════════════════════════════════

mcp = FastMCP(
    "Hermes Assistant",
    instructions="查询 Hermes Agent 的运行状态：Gateway、定时任务、会话统计、今日活动等。",
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
        return f"未找到任务 {job_id} 的执行记录。"

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


@mcp.tool()
def hermes_status() -> str:
    """获取 Hermes Agent 整体运行状态概览。

    包含 Gateway 进程状态、当前模型、已连接平台、
    今日活动统计、最近7天会话汇总等信息。
    """
    overview = get_system_overview()

    lines = ["═══ Hermes Agent 状态 ═══", ""]

    # Gateway
    gw = overview["gateway"]
    if gw["running"]:
        lines.append(f"▶ Gateway: 运行中 (PID {gw['pid']}, uptime {gw['uptime']})")
    else:
        lines.append("✗ Gateway: 未运行")

    # Model
    mi = overview["model"]
    lines.append(f"  模型: {mi['model']} / {mi['provider']}")

    # Platforms
    pnames = [p["name"] for p in overview["platforms"] if p["configured"]]
    lines.append(f"  平台: {', '.join(pnames) if pnames else '无'}")
    lines.append("")

    # Today
    td = overview["today"]
    lines.append(f"▶ 今日活动:")
    lines.append(f"  会话: {td['sessions']} | 消息: {td['messages']} | 工具调用: {td['tool_calls']} | Tokens: {td['tokens']:,}")
    lines.append("")

    # 7-day sessions
    s7 = overview["sessions_7d"]
    lines.append(f"▶ 最近7天:")
    lines.append(f"  会话: {s7['total_sessions']} (活跃: {s7['active_sessions']}) | 消息: {s7['total_messages']} | 工具: {s7['total_tool_calls']}")
    lines.append(f"  Tokens: 入 {s7['input_tokens']:,} / 出 {s7['output_tokens']:,}")
    if s7["by_source"]:
        src_parts = [f"{s['source']}({s['sessions']})" for s in s7["by_source"]]
        lines.append(f"  来源: {', '.join(src_parts)}")
    lines.append("")

    # Cron jobs
    jobs = overview["cron_jobs"]
    lines.append(f"▶ 定时任务: {len(jobs)} 个")
    for j in jobs:
        state_icon = "▶" if j["state"] in ("active", "scheduled") else "⏸"
        lines.append(f"  {state_icon} {j['job_name']} | {j['schedule_display']} | 已执行 {j['total_runs']}次")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# Custom HTTP routes (served by the same Starlette app as MCP)
# ═══════════════════════════════════════════════════════════


@mcp.custom_route("/", methods=["GET"])
async def homepage(request: Request) -> Response:
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@mcp.custom_route("/api/jobs", methods=["GET"])
async def api_jobs(request: Request) -> Response:
    return JSONResponse(get_all_jobs_summary())


@mcp.custom_route("/api/runs/{job_id}", methods=["GET"])
async def api_runs(request: Request) -> Response:
    job_id = request.path_params["job_id"]
    limit = int(request.query_params.get("limit", "50"))
    return JSONResponse(_get_job_runs(job_id, limit=limit))


@mcp.custom_route("/api/status", methods=["GET"])
async def api_status(request: Request) -> Response:
    return JSONResponse(get_system_overview())


@mcp.custom_route("/api/sessions", methods=["GET"])
async def api_sessions(request: Request) -> Response:
    days = int(request.query_params.get("days", "7"))
    return JSONResponse(get_sessions_stats(days=days))


# ═══════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════

app = mcp.streamable_http_app()


if __name__ == "__main__":
    import uvicorn
    os.chdir(STATIC_DIR)
    print(f"Assistant Dashboard running at http://localhost:{PORT}")
    print(f"MCP endpoint: http://localhost:{PORT}/mcp")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
