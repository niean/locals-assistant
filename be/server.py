#!/usr/bin/env python3
"""Assistant Status Dashboard - HTTP Server with API endpoints.

Serves:
- Web dashboard at /
- REST API at /api/*
"""

import json
import os
import re
import sqlite3
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

HERMES_DIR = Path.home() / ".hermes"
CRON_OUTPUT_DIR = HERMES_DIR / "cron" / "output"
CRON_JOBS_FILE = HERMES_DIR / "cron" / "jobs.json"
STATE_DB = HERMES_DIR / "state.db"
CONFIG_FILE = HERMES_DIR / "config.yaml"
PORT = 8090
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "fe"
INDEX_FILE = STATIC_DIR / "html" / "index.html"

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
    seen_ids = set()

    # Scan output directories for jobs with run history
    if CRON_OUTPUT_DIR.exists():
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
            seen_ids.add(job_id)
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
                "total_runs": len(files),
                "last_run": last_run,
            })

    # Also include jobs from config that have no output directory yet
    for job_id, config in jobs_config.items():
        if job_id in seen_ids:
            continue
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
            "total_runs": 0,
            "last_run": None,
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

        # All non-cron, non-api_server sessions with last message time
        # Include sessions active within the time window (by start OR last message)
        now_ts = datetime.now(tz=TZ_CST).timestamp()
        idle_threshold = now_ts - 3600  # 1 hour
        rows = cursor.execute("""
            SELECT s.id, s.title, s.source, s.model, s.started_at, s.ended_at,
                   s.end_reason, s.message_count, s.tool_call_count,
                   COALESCE(s.input_tokens, 0) as input_tokens,
                   COALESCE(s.output_tokens, 0) as output_tokens,
                   (SELECT MAX(m.timestamp) FROM messages m WHERE m.session_id = s.id) as last_message_at
            FROM sessions s
            WHERE s.source NOT IN ('cron', 'api_server')
              AND (s.started_at > ? OR (SELECT MAX(m.timestamp) FROM messages m WHERE m.session_id = s.id) > ?)
            ORDER BY COALESCE((SELECT MAX(m.timestamp) FROM messages m WHERE m.session_id = s.id), s.started_at) DESC
            LIMIT 50
        """, (cutoff, cutoff)).fetchall()

        active_sessions = []
        inactive_sessions = []
        for r in rows:
            last_active = r["last_message_at"] or r["started_at"]
            # Active: last activity within 1 hour (regardless of ended_at,
            # since some platforms like dingtalk reuse ended sessions)
            is_active = last_active > idle_threshold
            session_data = {
                "id": r["id"],
                "title": r["title"] or "(untitled)",
                "source": r["source"],
                "model": r["model"],
                "started_at": datetime.fromtimestamp(r["started_at"], tz=TZ_CST).isoformat(),
                "last_message_at": datetime.fromtimestamp(r["last_message_at"], tz=TZ_CST).isoformat() if r["last_message_at"] else None,
                "end_reason": r["end_reason"],
                "active": is_active,
                "messages": r["message_count"],
                "tool_calls": r["tool_call_count"],
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
            }
            if is_active:
                active_sessions.append(session_data)
            else:
                inactive_sessions.append(session_data)

        result["recent_sessions"] = active_sessions[:20]
        result["inactive_sessions"] = inactive_sessions[:20]

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


SKILLS_DIR = HERMES_DIR / "skills"
PLUGINS_DIR = HERMES_DIR / "plugins"
CUSTOM_AUTHOR = "niean"


def get_all_skills() -> dict:
    """Scan skills directory and return custom + other skills."""
    custom = []
    other = []
    if not SKILLS_DIR.exists():
        return {"custom": custom, "other": other}

    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        rel = skill_md.relative_to(SKILLS_DIR)
        parts = rel.parts  # e.g. ('devops', 'aliyun-oss', 'SKILL.md')
        category = parts[0] if len(parts) > 1 else ""
        skill_name = parts[-2] if len(parts) >= 2 else parts[0]
        skill_path = str(skill_md)

        # Parse frontmatter for metadata
        meta = {"name": skill_name, "category": category, "path": skill_path,
                "rel_path": str(rel.parent), "description": "", "trigger": ""}
        is_custom = False
        try:
            content = skill_md.read_text(encoding="utf-8")
            if content.startswith("---"):
                end = content.find("---", 3)
                if end > 0:
                    import yaml
                    fm = yaml.safe_load(content[3:end])
                    if isinstance(fm, dict):
                        meta["name"] = fm.get("name", skill_name)
                        meta["description"] = fm.get("description", "").strip()
                        meta["trigger"] = fm.get("trigger", "")
                        # Check author in metadata or top-level
                        author = fm.get("author", "")
                        if not author:
                            metadata = fm.get("metadata", {})
                            if isinstance(metadata, dict):
                                author = metadata.get("author", "")
                        if author == CUSTOM_AUTHOR:
                            is_custom = True
        except Exception:
            pass

        if is_custom:
            custom.append(meta)
        else:
            other.append(meta)

    return {"custom": custom, "other": other}


def get_all_plugins() -> list:
    """Scan plugins directory for installed plugins."""
    plugins = []
    if not PLUGINS_DIR.exists():
        return plugins
    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir():
            continue
        yaml_file = plugin_dir / "plugin.yaml"
        if not yaml_file.exists():
            continue
        try:
            import yaml
            meta = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if not isinstance(meta, dict):
                continue
            # Check enabled status from config
            enabled_list = _get_config_plugins_enabled()
            plugins.append({
                "name": meta.get("name", plugin_dir.name),
                "version": meta.get("version", ""),
                "description": meta.get("description", ""),
                "author": meta.get("author", ""),
                "tools": meta.get("provides_tools", []),
                "enabled": plugin_dir.name in enabled_list,
            })
        except Exception:
            continue
    return plugins


def _get_config_plugins_enabled() -> list:
    """Read enabled plugins from config.yaml."""
    if not CONFIG_FILE.exists():
        return []
    try:
        import yaml
        data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
        return data.get("plugins", {}).get("enabled", [])
    except Exception:
        return []


def get_mcp_servers() -> list:
    """Read MCP server config from config.yaml."""
    if not CONFIG_FILE.exists():
        return []
    try:
        import yaml
        data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
        servers = data.get("mcp_servers", {})
        if not isinstance(servers, dict) or not servers:
            return []
        result = []
        for name, cfg in servers.items():
            result.append({
                "name": name,
                "url": cfg.get("url", "") if isinstance(cfg, dict) else "",
                "timeout": cfg.get("timeout", 30) if isinstance(cfg, dict) else 30,
            })
        return result
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════
# HTTP Routes
# ═══════════════════════════════════════════════════════════




async def index(request: Request) -> Response:
    return FileResponse(INDEX_FILE)


async def api_jobs(request: Request) -> Response:
    return JSONResponse(get_all_jobs_summary())


async def api_runs(request: Request) -> Response:
    job_id = request.path_params["job_id"]
    limit = int(request.query_params.get("limit", "50"))
    return JSONResponse(_get_job_runs(job_id, limit=limit))


async def api_status(request: Request) -> Response:
    return JSONResponse(get_system_overview())


async def api_sessions(request: Request) -> Response:
    days = int(request.query_params.get("days", "7"))
    return JSONResponse(get_sessions_stats(days=days))



async def api_session_messages(request: Request) -> Response:
    """Return messages for a given session."""
    session_id = request.path_params["session_id"]
    if not STATE_DB.exists():
        return JSONResponse({"error": "state.db not found"}, status_code=500)
    try:
        conn = sqlite3.connect(str(STATE_DB), timeout=5)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT role, content, tool_name, timestamp
            FROM messages WHERE session_id = ?
            ORDER BY timestamp ASC LIMIT 200
        """, (session_id,)).fetchall()
        conn.close()
        messages = []
        for r in rows:
            content = r["content"] or ""
            # Truncate very long messages
            if len(content) > 2000:
                content = content[:2000] + "\n...(truncated)"
            messages.append({
                "role": r["role"],
                "content": content,
                "tool_name": r["tool_name"],
                "time": datetime.fromtimestamp(r["timestamp"], tz=TZ_CST).strftime("%H:%M:%S"),
            })
        return JSONResponse({"session_id": session_id, "messages": messages})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def api_rename_session(request: Request) -> Response:
    """Rename a session title."""
    session_id = request.path_params["session_id"]
    if not STATE_DB.exists():
        return JSONResponse({"error": "state.db not found"}, status_code=500)
    try:
        body = await request.json()
        new_title = body.get("title", "").strip()
        if not new_title:
            return JSONResponse({"error": "Title cannot be empty"}, status_code=400)
        conn = sqlite3.connect(str(STATE_DB), timeout=5)
        row = conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            conn.close()
            return JSONResponse({"error": f"Session '{session_id}' not found"}, status_code=404)
        conn.execute("UPDATE sessions SET title = ? WHERE id = ?", (new_title, session_id))
        conn.commit()
        conn.close()
        return JSONResponse({"ok": True, "session_id": session_id, "title": new_title})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def api_prompt(request: Request) -> Response:
    """Return the prompt text for a given job."""
    job_id = request.path_params["job_id"]
    jobs_config = get_jobs_config()
    job = jobs_config.get(job_id)
    if not job:
        return JSONResponse({"error": f"Job '{job_id}' not found"}, status_code=404)
    prompt = job.get("prompt", "")
    return JSONResponse({"job_id": job_id, "job_name": job.get("name", job_id), "prompt": prompt})


async def api_skills(request: Request) -> Response:
    return JSONResponse(get_all_skills())


async def api_plugins(request: Request) -> Response:
    return JSONResponse(get_all_plugins())


async def api_mcp_servers(request: Request) -> Response:
    return JSONResponse(get_mcp_servers())


async def api_skill_content(request: Request) -> Response:
    """Return the raw SKILL.md content for a given skill path."""
    skill_path = request.path_params["skill_path"]
    skill_md = SKILLS_DIR / skill_path / "SKILL.md"
    if not skill_md.exists() or not str(skill_md.resolve()).startswith(str(SKILLS_DIR.resolve())):
        return JSONResponse({"error": "Skill not found"}, status_code=404)
    content = skill_md.read_text(encoding="utf-8")
    return JSONResponse({"path": skill_path, "content": content})


# ═══════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════

app = Starlette(routes=[
    Route("/", index),
    Route("/api/jobs", api_jobs),
    Route("/api/runs/{job_id}", api_runs),
    Route("/api/status", api_status),
    Route("/api/sessions", api_sessions),
    Route("/api/sessions/{session_id}/messages", api_session_messages),
    Route("/api/sessions/{session_id}/rename", api_rename_session, methods=["POST"]),
    Route("/api/prompt/{job_id}", api_prompt),
    Route("/api/skills", api_skills),
    Route("/api/skills/{skill_path:path}/content", api_skill_content),
    Route("/api/plugins", api_plugins),
    Route("/api/mcp", api_mcp_servers),
    Mount("/", StaticFiles(directory=str(STATIC_DIR), html=True)),
])


if __name__ == "__main__":
    import uvicorn
    os.chdir(BASE_DIR)
    print(f"Assistant Dashboard running at http://localhost:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
