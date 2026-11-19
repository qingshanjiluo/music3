# -*- coding: utf-8 -*-
"""后台任务中心：创建、查询、SSE 订阅进度。"""
from __future__ import annotations

import json
import threading
import time
import uuid

_LOCK = threading.Lock()
_JOBS = {}

# 每个 job 保留的最大日志条数
MAX_LINES = 500


def create(kind, total=0, meta=None):
    """建任务，返回 job_id。"""
    jid = uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[jid] = {
            "id": jid,
            "kind": kind,
            "state": "running",   # running / done / error / canceled
            "created": time.time(),
            "updated": time.time(),
            "total": total,
            "done": 0,
            "ok": 0,
            "skip": 0,
            "fail": 0,
            "lines": [],
            "meta": meta or {},
            "error": "",
            "version": 0,
        }
    return jid


def log(jid, text, **counters):
    """追加一行日志，可选累加计数器。"""
    with _LOCK:
        j = _JOBS.get(jid)
        if not j:
            return
        line = "%s %s" % (time.strftime("%H:%M:%S"), text)
        j["lines"].append(line)
        if len(j["lines"]) > MAX_LINES:
            j["lines"] = j["lines"][-MAX_LINES:]
        for k, v in counters.items():
            if k in j:
                j[k] += v
        j["updated"] = time.time()
        j["version"] += 1


def progress(jid, done=None, total=None):
    with _LOCK:
        j = _JOBS.get(jid)
        if not j:
            return
        if done is not None:
            j["done"] = done
        if total is not None:
            j["total"] = total
        j["updated"] = time.time()
        j["version"] += 1


def finish(jid, state="done", error=""):
    with _LOCK:
        j = _JOBS.get(jid)
        if not j:
            return
        j["state"] = state
        j["error"] = error
        j["updated"] = time.time()
        j["version"] += 1


def get(jid, since=0):
    """取快照。since>0 时只返回该版本之后的增量日志。"""
    with _LOCK:
        j = _JOBS.get(jid)
        if not j:
            return None
        snap = {k: v for k, v in j.items() if k != "lines"}
        if since and j["version"] > since:
            snap["new_lines"] = j["lines"][-30:]
        else:
            snap["lines"] = list(j["lines"])
        return snap


def list_jobs(limit=20):
    with _LOCK:
        rows = sorted(_JOBS.values(), key=lambda x: -x["created"])[:limit]
        return [
            {
                "id": r["id"],
                "kind": r["kind"],
                "state": r["state"],
                "done": r["done"],
                "total": r["total"],
                "ok": r["ok"],
                "fail": r["fail"],
                "skip": r["skip"],
                "created": r["created"],
                "meta": r["meta"],
            }
            for r in rows
        ]


def cancel(jid):
    with _LOCK:
        j = _JOBS.get(jid)
        if j and j["state"] == "running":
            j["state"] = "canceled"
            j["updated"] = time.time()
            return True
    return False


def is_canceled(jid):
    with _LOCK:
        j = _JOBS.get(jid)
        return bool(j and j["state"] == "canceled")


def sse_format(jid, since=0):
    """生成一条 SSE 事件文本。"""
    snap = get(jid, since=since)
    if snap is None:
        return "event: error\ndata: {\"error\":\"unknown job\"}\n\n"
    return "event: progress\ndata: %s\n\n" % json.dumps(snap, ensure_ascii=False)


def cleanup(max_age=3600):
    """清理超时已完成任务。"""
    now = time.time()
    with _LOCK:
        for k in list(_JOBS.keys()):
            j = _JOBS[k]
            if j["state"] != "running" and now - j["updated"] > max_age:
                del _JOBS[k]
