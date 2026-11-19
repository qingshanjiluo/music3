# -*- coding: utf-8 -*-
"""读取 mp3 内嵌标签：封面、歌词、标题歌手。"""
from __future__ import annotations

import os

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3

    HAS = True
except Exception:
    HAS = False

_cache = {}


def read_tags(path):
    """返回 dict: title/artists/album/lyric/cover(字节)/mime/duration/bitrate。

    cover 单独用 read_cover 取，避免每次读大图。
    """
    if not HAS or not os.path.exists(path):
        return {}
    key = (path, os.path.getmtime(path))
    if key in _cache:
        return _cache[key]
    out = {}
    try:
        a = MP3(path)
        out["duration"] = round(a.info.length, 1)
        out["bitrate"] = a.info.bitrate
        tags = a.tags or {}
        for k, name in (("TIT2", "title"), ("TPE1", "artists"), ("TALB", "album")):
            v = tags.get(k)
            if v:
                out[name] = str(v)
        for uk in ("USLT::chi", "USLT:eng"):
            v = tags.get(uk)
            if v:
                out["lyric"] = str(v)
                break
        else:
            for kk in list(tags.keys()):
                if kk.startswith("USLT"):
                    out["lyric"] = str(tags.get(kk))
                    break
        out["has_cover"] = any(str(k).startswith("APIC") for k in tags.keys())
    except Exception:
        pass
    _cache[key] = out
    return out


def read_cover(path):
    """取第一张内嵌封面。返回 (bytes, mime) 或 (None, None)。"""
    if not HAS or not os.path.exists(path):
        return None, None
    try:
        a = MP3(path)
        tags = a.tags or {}
        for k in tags.keys():
            if str(k).startswith("APIC"):
                apic = tags.get(k)
                return apic.data, (apic.mime or "image/jpeg")
    except Exception:
        pass
    return None, None


def clear_cache():
    _cache.clear()
