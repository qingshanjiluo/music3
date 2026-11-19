# -*- coding: utf-8 -*-
"""播放队列：可拖拽排序、持久化。

沿用 persist 的原子写思路，存到 _cache/playlist.json
"""
from __future__ import annotations

import json
import os

from . import config as _cfg

_C = _cfg.load()
_CACHE_DIR = _C.get("cache_dir") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_cache"
)
_PLIST = os.path.join(_CACHE_DIR, "playlist.json")

_NAME = "playlist"


def _read():
    if not os.path.exists(_PLIST):
        return {"items": [], "current": -1}
    try:
        with open(_PLIST, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("items"), list):
            return d
    except Exception:
        pass
    return {"items": [], "current": -1}


def _write(d):
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        tmp = _PLIST + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, _PLIST)
        return True
    except Exception:
        return False


def get():
    return _read()


def set_items(items, current=None):
    """整表替换（前端拖拽排序后回写）。"""
    d = _read()
    out = []
    for it in items or []:
        rel = it.get("rel") or ""
        if not rel:
            continue
        out.append(
            {
                "rel": rel,
                "title": it.get("title") or "",
                "artists": it.get("artists") or "",
            }
        )
    d["items"] = out
    if current is not None:
        d["current"] = int(current)
    if d["current"] >= len(out):
        d["current"] = len(out) - 1
    _write(d)
    return d


def add(rel, title="", artists="", dedup=True):
    """追加一首。dedup=True 时已存在则移到末尾。"""
    if not rel:
        return _read()
    d = _read()
    items = d["items"]
    if dedup:
        items = [x for x in items if x.get("rel") != rel]
    items.append({"rel": rel, "title": title, "artists": artists})
    d["items"] = items
    _write(d)
    return d


def set_current(idx):
    d = _read()
    d["current"] = int(idx)
    _write(d)
    return d


def remove(rel):
    d = _read()
    d["items"] = [x for x in d["items"] if x.get("rel") != rel]
    if d["current"] >= len(d["items"]):
        d["current"] = len(d["items"]) - 1
    _write(d)
    return d


def clear():
    d = {"items": [], "current": -1}
    _write(d)
    return d


def move(frm, to):
    """拖拽排序：把第 frm 项移到 to 位置。"""
    d = _read()
    items = d["items"]
    n = len(items)
    try:
        frm = int(frm)
        to = int(to)
    except Exception:
        return d
    if frm < 0 or frm >= n or to < 0 or to >= n or frm == to:
        return d
    cur = d.get("current", -1)
    it = items.pop(frm)
    items.insert(to, it)
    # 修正 current 指针
    if cur == frm:
        cur = to
    elif frm < cur <= to:
        cur -= 1
    elif to <= cur < frm:
        cur += 1
    d["items"] = items
    d["current"] = cur
    _write(d)
    return d
