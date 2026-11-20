# -*- coding: utf-8 -*-
"""配置加载。优先级: 环境变量 > config.json > 内置默认。"""
from __future__ import annotations

import json
import os

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_PATH = os.path.join(_HERE, "config.json")

DEFAULTS = {
    "root": r"D:\音乐",
    "sources": ["qq", "netease", "bilibili"],
    "search_size": 15,
    "min_score": 0.15,
    "workers": 3,
    "retries": 2,
    "tag_cover": True,
    "tag_lyric": True,
    "auto_lyric": True,
    "qq_quality_order": [14, 11, 10, 8, 4],
    "qq_cookie": "",
    "netease_cookie": "",
    "credit_balance": 100,
    "credit_spent": 0,
    "audio_format": "30216/30280/30232/bestaudio",
    "ffmpeg": r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
    "ffprobe": r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffprobe.exe",
    "valid_min_sec": 8,
    "valid_max_sec": 1500,
    "valid_min_bytes": 150 * 1024,
    "cache_dir": os.path.join(_HERE, "_cache"),
    "src_subdir": {
        "bilibili": r"投稿\B站",
        "netease": r"投稿\网易云",
        "qq": r"投稿\QQ音乐",
        "kuwo": r"投稿\酷我",
        "qianqian": r"投稿\千千",
        "migu": r"投稿\咪咕",
    },
    "src_weight": {
        "qq": 1.00,
        "netease": 0.98,
        "kuwo": 0.90,
        "qianqian": 0.85,
        "migu": 0.80,
        "bilibili": 0.70,
    },
}

_cache = None


def load(reload=False):
    global _cache
    if _cache is not None and not reload:
        return _cache
    cfg = dict(DEFAULTS)
    if os.path.exists(CFG_PATH):
        try:
            with open(CFG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    # 环境变量覆盖
    if os.environ.get("MUSIC3_ROOT"):
        cfg["root"] = os.environ["MUSIC3_ROOT"]
    _cache = cfg
    return cfg


def get(key, default=None):
    return load().get(key, default)


def save(d=None):
    """原子写 config.json 并刷新缓存（默认只写可覆盖键，不丢未知键）。"""
    global _cache
    cur = dict(load())
    if d:
        cur.update(d)
    try:
        tmp = CFG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False, indent=1)
        os.replace(tmp, CFG_PATH)
        _cache = cur
        return True
    except Exception:
        return False
