# -*- coding: utf-8 -*-
"""队列持久化：任务清单落盘，进程中断后可续跑。

设计要点：
  - 每个关键词一行，写入 .music3_pending.json
  - 每完成一条就更新一次（原子替换，避免半截文件）
  - 重启后 load_pending() 拿到剩余任务，run_resume() 接着跑
  - 完成的关键词从清单里删掉，清单空即任务结束
"""
from __future__ import annotations

import json
import os
import tempfile
import time

PENDING = ".music3_pending.json"


def path(root):
    return os.path.join(root, PENDING)


def _atomic_write(p, data):
    """先写临时文件再替换，避免进程被杀留下半截 JSON。"""
    d = os.path.dirname(p) or "."
    try:
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, p)
        return True
    except Exception:
        try:
            if tmp:
                os.remove(tmp)
        except Exception:
            pass
        return False


def save(tasks, root, meta=None):
    """tasks: [{kw, n, sources, state, err}...]"""
    data = {
        "created": meta.get("created") if meta else time.time(),
        "updated": time.time(),
        "meta": meta or {},
        "tasks": tasks,
    }
    return _atomic_write(path(root), data)


def load(root):
    """读清单。不存在/损坏返回 None。"""
    p = path(root)
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d.get("tasks"), list):
            return d
    except Exception:
        pass
    return None


def clear(root):
    p = path(root)
    try:
        if os.path.exists(p):
            os.remove(p)
        return True
    except Exception:
        return False


def pending_count(root):
    d = load(root)
    if not d:
        return 0
    return sum(1 for t in d["tasks"] if t.get("state") == "pending")


def make_tasks(keywords, n=1, sources=None, bili=False):
    return [
        {
            "kw": k,
            "n": int(n),
            "sources": sources or [],
            "bili": bool(bili),
            "state": "pending",   # pending / done / fail
            "err": "",
            "path": "",
            "tries": 0,
        }
        for k in keywords
    ]
