# -*- coding: utf-8 -*-
"""搜索结果缓存：降低重复请求，规避源限流。"""
from __future__ import annotations

import hashlib
import json
import os
import time

from . import config as _cfg

_C = _cfg.load()
_CACHE_DIR = _C.get("cache_dir")
_TTL = 1800  # 30 分钟

_MEM = {}


def _key(keyword, sources, limit):
    raw = "%s|%s|%d" % (keyword.strip().lower(), ",".join(sorted(sources)), limit)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:20]


def _path(k):
    d = os.path.join(_CACHE_DIR, "search")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, k + ".json")


def get(keyword, sources, limit, ttl=_TTL):
    """取缓存。命中返回 list[dict]，否则 None。"""
    k = _key(keyword, sources, limit)
    now = time.time()

    # 内存层
    hit = _MEM.get(k)
    if hit and now - hit[0] < ttl:
        return hit[1]

    # 磁盘层
    p = _path(k)
    if os.path.exists(p):
        try:
            if now - os.path.getmtime(p) < ttl:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                _MEM[k] = (now, data)
                return data
        except Exception:
            pass
    return None


def put(keyword, sources, limit, items):
    """写缓存。items 是 list[dict]。"""
    k = _key(keyword, sources, limit)
    _MEM[k] = (time.time(), items)
    try:
        with open(_path(k), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False)
    except Exception:
        pass


def clear():
    """清空缓存。"""
    _MEM.clear()
    d = os.path.join(_CACHE_DIR, "search")
    n = 0
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.endswith(".json"):
                try:
                    os.remove(os.path.join(d, f))
                    n += 1
                except Exception:
                    pass
    return n
