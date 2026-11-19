# -*- coding: utf-8 -*-
"""导出：歌单 m3u8 / JSON / CSV，库清单。

m3u8 用相对路径 + UTF-8 无 BOM，兼容 foobar2000 / VLC / 手机播放器。
"""
from __future__ import annotations

import csv
import io
import json
import os
import time

from . import browse, tagreader

# 时长缓存：(path, mtime) -> seconds
_DUR_CACHE = {}

# tagreader 自己的 read_tags 已有缓存，但只按 (path, mtime) 且有上限；
# 这里再加一层，导出全库时避免重复解析。


def _mp3_duration_size(path, use_cache=True):
    """读时长与大小。

    use_cache=False 时只取文件大小，不解析 ID3（全库快速导出用）。
    """
    if not use_cache:
        try:
            return 0.0, os.path.getsize(path)
        except Exception:
            return 0.0, 0
    d, s = 0.0, 0
    try:
        st = os.stat(path)
        s = st.st_size
        key = (path, int(st.st_mtime))
    except Exception:
        key = None
    if key and key in _DUR_CACHE:
        return _DUR_CACHE[key], s
    try:
        t = tagreader.read_tags(path)
        d = float(t.get("duration") or 0)
    except Exception:
        pass
    if key:
        _DUR_CACHE[key] = d
    return d, s


def _split_name(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    if " - " in stem:
        a, t = stem.split(" - ", 1)
        return a.strip(), t.strip()
    return "", stem.strip()


def to_m3u8(paths, root):
    """生成 m3u8 文本。路径相对于 root。"""
    lines = ["#EXTM3U"]
    for p in paths:
        if not os.path.exists(p):
            continue
        dur, _ = _mp3_duration_size(p)
        artist, title = _split_name(p)
        disp = "%s - %s" % (artist, title) if artist else title
        try:
            rel = os.path.relpath(p, root).replace("\\", "/")
        except Exception:
            rel = p.replace("\\", "/")
        lines.append("#EXTINF:%d,%s" % (int(dur or -1), disp))
        lines.append(rel)
    return "\n".join(lines) + "\n"


def to_json(paths, root, include_lyric=False):
    """生成 JSON 列表。"""
    out = []
    for p in paths:
        if not os.path.exists(p):
            continue
        dur, size = _mp3_duration_size(p)
        artist, title = _split_name(p)
        try:
            rel = os.path.relpath(p, root).replace("\\", "/")
        except Exception:
            rel = p.replace("\\", "/")
        item = {
            "rel": rel,
            "title": title,
            "artists": artist,
            "duration": round(dur, 1),
            "size": size,
        }
        if include_lyric:
            try:
                t = tagreader.read_tags(p)
                item["has_lyric"] = bool(t.get("lyric"))
                item["has_cover"] = bool(t.get("has_cover"))
                item["bitrate"] = t.get("bitrate") or 0
            except Exception:
                pass
        out.append(item)
    return json.dumps(out, ensure_ascii=False, indent=1)


def to_csv(paths, root):
    """生成 CSV（UTF-8 BOM，Excel 直接打开不乱码）。"""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["rel", "title", "artists", "duration_sec", "size_mb"])
    for p in paths:
        if not os.path.exists(p):
            continue
        dur, size = _mp3_duration_size(p)
        artist, title = _split_name(p)
        try:
            rel = os.path.relpath(p, root).replace("\\", "/")
        except Exception:
            rel = p.replace("\\", "/")
        w.writerow([rel, title, artist, round(dur, 1), round(size / 1048576, 2)])
    return "\ufeff" + buf.getvalue()


def library_index(root, sub="", fast=False):
    """全库索引（带歌手聚合与统计）。

    fast=True 时跳过 ID3 解析（不取时长），5176 首从 111s 降到 2~3s。
    """
    tracks = browse.list_tracks(root, sub, limit=1000000)
    items = []
    artists = {}
    total_size = 0
    total_dur = 0.0
    for t in tracks:
        p = t["path"]
        dur, size = _mp3_duration_size(p, use_cache=not fast)
        a = t.get("artists") or ""
        items.append(
            {
                "rel": t["rel"],
                "title": t.get("title") or "",
                "artists": a,
                "duration": round(dur, 1),
                "size": size,
            }
        )
        total_size += size
        total_dur += dur
        k = a or "(未知)"
        cur = artists.get(k) or {"artists": k, "count": 0, "seconds": 0.0}
        cur["count"] += 1
        cur["seconds"] = round(cur["seconds"] + dur, 1)
        artists[k] = cur

    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": root,
        "sub": sub,
        "fast": bool(fast),
        "total": len(items),
        "total_size_mb": round(total_size / 1048576, 1),
        "total_hours": round(total_dur / 3600, 2),
        "by_artist": sorted(artists.values(), key=lambda x: -x["count"]),
        "items": items,
    }


def write_file(path, text):
    """原子写文件。"""
    try:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, path)
        return True
    except Exception:
        return False
