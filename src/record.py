# -*- coding: utf-8 -*-
"""下载落盘后的统计/历史记录（去重窗口 30s，防同一文件多入口重复计数）。"""
from __future__ import annotations

import os
import time

from . import stats
from .covercache import history_add

_seen = {}   # rel -> last_ts
_WIN = 30.0


def record_download(path, title="", artists="", source="", seconds=None):
    """下载成功后记录：stats 累计 + 播放历史。rel 相对 config root。"""
    try:
        from . import config as _c, downloader

        root = _c.get("root") or "D:\\音乐"
        rel = os.path.relpath(path, root).replace("\\", "/")
        key = rel.lower()
        now = time.time()
        if now - _seen.get(key, 0) < _WIN:
            return False
        _seen[key] = now
        if seconds is None:
            seconds = downloader.duration_of(path) or 0.0
        stats.record(rel, title, artists, float(seconds or 0))
        history_add(rel, title, artists)
        _spend_credit()
        return True
    except Exception:
        return False


def _spend_credit():
    """每成功下载 1 首扣 1 赠金；balance 为 None 视为不限量。"""
    try:
        from . import config as _c

        d = _c.load(reload=True)
        bal = d.get("credit_balance", 100)
        if bal is None:
            return
        bal = int(bal) - 1
        d["credit_balance"] = bal
        d["credit_spent"] = int(d.get("credit_spent", 0)) + 1
        _c.save(d)
    except Exception:
        pass
