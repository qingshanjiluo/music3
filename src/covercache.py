# -*- coding: utf-8 -*-
"""封面缓存 + 播放历史。

封面缓存：从 mp3 读 APIC 很慢（要解 ID3），缓存到 _cache/covers/<md5>.jpg
播放历史：记录最近播放，落盘 _cache/history.json
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time

from . import config as _cfg

_C = _cfg.load()
_CACHE_DIR = _C.get("cache_dir") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_cache")
_COVER_DIR = os.path.join(_CACHE_DIR, "covers")
_HISTORY = os.path.join(_CACHE_DIR, "history.json")

_LOCK = threading.Lock()
_MAX_HISTORY = 500


def _key(path):
    """用 路径 + mtime 做 key，文件换了自动失效。"""
    try:
        st = os.stat(path)
        raw = "%s|%d|%d" % (os.path.abspath(path).lower(), int(st.st_size), int(st.st_mtime))
    except Exception:
        raw = os.path.abspath(path).lower()
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:24]


def get_cover(path):
    """取封面。优先磁盘缓存。返回 (bytes, mime) 或 (None, None)。"""
    if not os.path.exists(path):
        return None, None
    os.makedirs(_COVER_DIR, exist_ok=True)
    k = _key(path)
    # 缓存文件：<key>.jpg / <key>.png，附带 .meta 记 mime
    for ext in (".jpg", ".png", ".webp", ".gif"):
        p = os.path.join(_COVER_DIR, k + ext)
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    data = f.read()
                if data:
                    mime = "image/" + ext.lstrip(".").replace("jpg", "jpeg")
                    return data, mime
            except Exception:
                pass

    # 未命中，从 mp3 读
    try:
        from . import tagreader

        data, mime = tagreader.read_cover(path)
    except Exception:
        return None, None
    if not data:
        # 记一个空标记，避免反复解 ID3
        try:
            with open(os.path.join(_COVER_DIR, k + ".none"), "w") as f:
                f.write("1")
        except Exception:
            pass
        return None, None

    ext = ".jpg"
    if mime and "png" in mime:
        ext = ".png"
    elif mime and "webp" in mime:
        ext = ".webp"
    try:
        with open(os.path.join(_COVER_DIR, k + ext), "wb") as f:
            f.write(data)
    except Exception:
        pass
    return data, mime or "image/jpeg"


def has_no_cover(path):
    """之前查过没封面，直接跳过。"""
    k = _key(path)
    return os.path.exists(os.path.join(_COVER_DIR, k + ".none"))


def cover_cache_stats():
    n = 0
    size = 0
    if os.path.isdir(_COVER_DIR):
        for f in os.listdir(_COVER_DIR):
            p = os.path.join(_COVER_DIR, f)
            try:
                n += 1
                size += os.path.getsize(p)
            except Exception:
                pass
    return {"files": n, "bytes": size}


def cover_cache_clear():
    n = 0
    if os.path.isdir(_COVER_DIR):
        for f in os.listdir(_COVER_DIR):
            try:
                os.remove(os.path.join(_COVER_DIR, f))
                n += 1
            except Exception:
                pass
    return n


# ---------------- 播放历史 ----------------

def _load_history():
    if not os.path.exists(_HISTORY):
        return []
    try:
        with open(_HISTORY, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _save_history(items):
    try:
        d = os.path.dirname(_HISTORY)
        os.makedirs(d, exist_ok=True)
        tmp = _HISTORY + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=1)
        os.replace(tmp, _HISTORY)
        return True
    except Exception:
        return False


def history_add(rel, title="", artists=""):
    """记一条播放。同一 rel 只保留最新一条，插到最前。"""
    if not rel:
        return False
    with _LOCK:
        items = _load_history()
        items = [x for x in items if x.get("rel") != rel]
        items.insert(0, {
            "rel": rel,
            "title": title,
            "artists": artists,
            "ts": time.time(),
            "at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        if len(items) > _MAX_HISTORY:
            items = items[:_MAX_HISTORY]
        return _save_history(items)


def history_list(limit=100):
    with _LOCK:
        return _load_history()[:limit]


def history_clear():
    with _LOCK:
        return _save_history([])


def history_remove(rel):
    with _LOCK:
        items = [x for x in _load_history() if x.get("rel") != rel]
        return _save_history(items)
