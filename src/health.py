# -*- coding: utf-8 -*-
"""库健康检查：缺歌词 / 无封面 / 时长异常 / 重复 / 命名不规范。

产出结构化报告 + 可执行建议，供 CLI 与 Web 调用。
"""
from __future__ import annotations

import os
import re

from . import browse, tagreader, dedup
from .models import norm

# 明显异常的时长（秒）
MIN_OK = 8
MAX_OK = 1800

# 文件名不规范：含非法字符、超长、纯数字、乱码特征
BAD_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')
SUSPECT_NAME = re.compile(r"(未命名|unknown|track\s*\d+$|^\d+$|副本|copy)", re.I)


def scan(root, sub="", limit=None, deep=False, offset=0, batch=0):
    """扫库。deep=True 时读 ID3（慢），否则只看文件名与大小。

    batch>0 时只扫 offset..offset+batch（分批，返回 total_all 供前端算进度）。
    返回 dict 报告。
    """
    all_tracks = browse.list_tracks(root, sub, limit=limit or 1000000)
    if batch and batch > 0:
        tracks = all_tracks[offset: offset + batch]
        # dups 是跨片关系（同名同歌手散在不同片），片内 seen 会丢 2/3（实测 1139 vs 3394）。
        # 纯文件名比较不读 ID3，全库快扫 ~1s —— 每片都返回全库真值，前端取末片不累加。
        _fs, _fd = {}, []
        for _t in all_tracks:
            _k = norm((_t.get("artists") or ""))[:12] + "|" + norm((_t.get("title") or ""))
            if _k in _fs:
                _fd.append({"key": _k, "a": _fs[_k], "b": _t["rel"]})
            else:
                _fs[_k] = _t["rel"]
        _full_dups = _fd
    else:
        tracks = all_tracks
        _full_dups = None
    rep = {
        "root": root,
        "sub": sub,
        "total": len(tracks),
        "total_all": len(all_tracks),
        "offset": offset,
        "batch": batch,
        "more": (offset + len(tracks)) < len(all_tracks),
        "total_size_mb": 0.0,
        "no_lyric": [],
        "no_cover": [],
        "tiny": [],
        "huge": [],
        "bad_name": [],
        "no_artist": [],
        "ok": 0,
    }
    seen = {}
    dups = []

    for t in tracks:
        p = t["path"]
        size = t.get("size") or 0
        rep["total_size_mb"] += size / 1048576.0
        artist = (t.get("artists") or "").strip()
        title = (t.get("title") or "").strip()
        # deep 用 ID3 兜底：browse.list_tracks 只解析文件名 " - "（看不到 fixmeta 写入的 TPE1）
        if deep:
            try:
                _tg0 = tagreader.read_tags(p) or {}
            except Exception:
                _tg0 = {}
            artist = artist or (_tg0.get("artists") or "").strip()
            title = title or (_tg0.get("title") or "").strip()
        base = os.path.basename(p)

        # 命名问题
        if BAD_CHARS.search(base) or len(base) > 120:
            rep["bad_name"].append({"rel": t["rel"], "why": "非法字符或超长"})
        elif SUSPECT_NAME.search(title) or SUSPECT_NAME.search(artist):
            rep["bad_name"].append({"rel": t["rel"], "why": "疑似未命名/副本"})
        if not artist:
            rep["no_artist"].append({"rel": t["rel"], "title": title})

        # 大小异常
        if size < 150 * 1024:
            rep["tiny"].append({"rel": t["rel"], "size": size})
        elif size > 80 * 1048576:
            rep["huge"].append({"rel": t["rel"], "size": size})

        # 重复（同名同歌手）
        k = norm(artist)[:12] + "|" + norm(title)
        if k in seen:
            dups.append({"key": k, "a": seen[k], "b": t["rel"]})
        else:
            seen[k] = t["rel"]

        # ID3 检查（deep）
        if deep:
            try:
                tg = tagreader.read_tags(p)
                d = float(tg.get("duration") or 0)
                if d and (d < MIN_OK or d > MAX_OK):
                    (rep["tiny"] if d < MIN_OK else rep["huge"]).append(
                        {"rel": t["rel"], "duration": round(d, 1)}
                    )
                ly = (tg.get("lyric") or "").strip()
                if len(ly) < 40:
                    rep["no_lyric"].append({"rel": t["rel"], "title": title})
                if not tg.get("has_cover"):
                    rep["no_cover"].append({"rel": t["rel"], "title": title})
                else:
                    rep["ok"] += 1
            except Exception as e:
                rep["bad_name"].append({"rel": t["rel"], "why": "读标签失败 %r" % (e,)[:40]})

    rep["dups"] = _full_dups if _full_dups is not None else dups
    _dups_n = len(rep["dups"])
    # 英文键计数：前端分批聚合后按英文键重算全库分（summary 是中文键只做显示）
    rep["counts"] = {
        "bad_name": len(rep["bad_name"]),
        "tiny": len(rep["tiny"]),
        "huge": len(rep["huge"]),
        "dups": _dups_n,
        "no_artist": len(rep["no_artist"]),
        "no_lyric": len(rep["no_lyric"]),
        "no_cover": len(rep["no_cover"]),
    }
    rep["summary"] = {
        "缺歌词": len(rep["no_lyric"]),
        "无封面": len(rep["no_cover"]),
        "重复": _dups_n,
        "命名异常": len(rep["bad_name"]),
        "无歌手": len(rep["no_artist"]),
        "文件过小": len(rep["tiny"]),
        "文件过大": len(rep["huge"]),
    }
    rep["score"] = _health_score(rep)
    return rep


def _health_score(rep):
    """0~100 健康分。只统计能算的项。"""
    total = max(1, rep["total"])
    penalty = 0.0
    penalty += len(rep["bad_name"]) / total * 30
    penalty += len(rep["tiny"]) / total * 25
    penalty += len(rep["dups"]) / total * 20
    penalty += len(rep["no_artist"]) / total * 10
    if rep["no_lyric"]:
        penalty += len(rep["no_lyric"]) / total * 15
    return max(0, round(100 - penalty, 1))


def fix_names(root, dry=True):
    """修命名：把非法字符换掉。返回 [(原, 新, ok)]。"""
    out = []
    for t in browse.list_tracks(root, "", limit=1000000):
        p = t["path"]
        base = os.path.basename(p)
        if not BAD_CHARS.search(base):
            continue
        newbase = BAD_CHARS.sub("_", base)
        dst = os.path.join(os.path.dirname(p), newbase)
        ok = None
        if not dry:
            try:
                os.rename(p, dst)
                ok = True
            except Exception:
                ok = False
        out.append((p, dst, ok))
    return out


def clean_tmp(root, dry=True):
    """清临时文件（.tmp_ / .dl_ / .part）。"""
    return dedup.clean_tmp(root, dry=dry)
