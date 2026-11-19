# -*- coding: utf-8 -*-
"""播放统计：累计次数、时长、歌手/分类排行。

数据来自 covercache 的播放历史，加一份聚合计数落盘 _cache/stats.json
（历史只留最近 500 条会被裁掉，统计用独立累加器不丢）
"""
from __future__ import annotations

import json
import os
import threading
import time

from . import config as _cfg

_C = _cfg.load()
_CACHE_DIR = _C.get("cache_dir") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_cache"
)
_STATS = os.path.join(_CACHE_DIR, "stats.json")

_LOCK = threading.Lock()


def _read():
    if not os.path.exists(_STATS):
        return {"plays": {}, "totals": {"count": 0, "seconds": 0.0}}
    try:
        with open(_STATS, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("plays"), dict):
            d.setdefault("totals", {"count": 0, "seconds": 0.0})
            return d
    except Exception:
        pass
    return {"plays": {}, "totals": {"count": 0, "seconds": 0.0}}


def _write(d):
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        tmp = _STATS + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, _STATS)
        return True
    except Exception:
        return False


def record(rel, title="", artists="", seconds=0.0):
    """记一次播放。rel 作为主键。"""
    if not rel:
        return False
    with _LOCK:
        d = _read()
        k = rel
        it = d["plays"].get(k) or {
            "rel": rel,
            "title": title,
            "artists": artists,
            "count": 0,
            "seconds": 0.0,
            "first": time.time(),
            "last": 0.0,
        }
        if title:
            it["title"] = title
        if artists:
            it["artists"] = artists
        it["count"] = int(it.get("count", 0)) + 1
        it["seconds"] = round(float(it.get("seconds", 0.0)) + max(0.0, float(seconds)), 1)
        it["last"] = time.time()
        d["plays"][k] = it
        d["totals"]["count"] = int(d["totals"].get("count", 0)) + 1
        d["totals"]["seconds"] = round(
            float(d["totals"].get("seconds", 0.0)) + max(0.0, float(seconds)), 1
        )
        return _write(d)


def top(by="count", limit=50):
    """排行。by='count'|'seconds'"""
    d = _read()
    items = list(d["plays"].values())
    key = "count" if by != "seconds" else "seconds"
    items.sort(key=lambda x: -(x.get(key) or 0))
    return items[:limit]


def top_artists(limit=30):
    """按歌手聚合。"""
    d = _read()
    agg = {}
    for it in d["plays"].values():
        a = (it.get("artists") or "").strip()
        if not a:
            continue
        # 多歌手只取第一个，避免 "周杰伦, 林俊杰" 单独成组
        a = a.split(",")[0].split("、")[0].strip()
        if not a:
            continue
        cur = agg.get(a) or {"artists": a, "count": 0, "seconds": 0.0}
        cur["count"] += int(it.get("count") or 0)
        cur["seconds"] = round(cur["seconds"] + float(it.get("seconds") or 0), 1)
        agg[a] = cur
    out = sorted(agg.values(), key=lambda x: -x["count"])
    return out[:limit]


def summary():
    """总览。"""
    d = _read()
    plays = list(d["plays"].values())
    artists = set()
    for it in plays:
        a = (it.get("artists") or "").split(",")[0].strip()
        if a:
            artists.add(a)
    t = d.get("totals") or {}
    return {
        "total_plays": int(t.get("count", 0)),
        "total_seconds": round(float(t.get("seconds", 0.0)), 1),
        "unique_songs": len(plays),
        "unique_artists": len(artists),
        "top_song": (top("count", 1) or [{}])[0].get("title", "") if plays else "",
        "top_artist": (top_artists(1) or [{}])[0].get("artists", "") if plays else "",
    }


def clear():
    with _LOCK:
        return _write({"plays": {}, "totals": {"count": 0, "seconds": 0.0}})
