# -*- coding: utf-8 -*-
"""歌手/UP主全量抓取。"""
from __future__ import annotations

import os
import re
import subprocess
import time

from .models import Track, safe_name
from . import src_bili

_ENV = dict(os.environ)
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    _ENV.pop(_k, None)

SEP = "|@|"


def bili_up_videos(mid, limit=200, log=None):
    """抓 B 站 UP 主全部投稿（yt-dlp 走 space 页）。"""
    url = "https://space.bilibili.com/%s/video" % mid
    out = []
    args = [
        "yt-dlp",
        "--encoding",
        "utf-8",
        "--no-warnings",
        "--skip-download",
        "--flat-playlist",
        "--playlist-end",
        str(limit),
        "--print",
        SEP.join(["%(id)s", "%(title)s", "%(duration)s"]),
        url,
    ]
    for attempt in range(3):
        try:
            p = subprocess.run(
                args,
                capture_output=True,
                timeout=300,
                env=_ENV,
                encoding="utf-8",
                errors="replace",
            )
            txt = p.stdout or ""
            if txt.strip():
                for line in txt.splitlines():
                    parts = line.strip().split(SEP)
                    if len(parts) < 3:
                        continue
                    vid, title, dur = parts[0], parts[1], parts[2]
                    if not (vid.startswith("BV") or vid.isdigit()):
                        continue
                    try:
                        d = float(dur) if dur not in ("NA", "None", "") else 0.0
                    except Exception:
                        d = 0.0
                    out.append(
                        Track(
                            source="bilibili",
                            track_id=vid,
                            title=title,
                            artists="UP%s" % mid,
                            duration_s=d,
                            page_url="https://www.bilibili.com/video/%s" % vid,
                        )
                    )
                break
            if log:
                log("space 尝试 %d 空返回: %s" % (attempt + 1, (p.stderr or "")[:150]))
        except Exception as e:
            if log:
                log("space ERR %r" % (e,))
        time.sleep(15 * (attempt + 1))
    return out


def artist_tracks(name, per_source=30, sources=None, log=None, min_score=0.15):
    """按歌手名在音乐源里抓取。返回候选 Track（未去重排序）。

    min_score：纯歌手名做关键词时歌名不匹配、score 只有 ~0.05，
    歌手搜索场景要传低阈值（0.04）否则全被过滤。
    """
    from . import router

    sources = sources or ["qq", "netease"]
    # 用歌手名当关键词，多拉一些
    res = router.search(
        name, sources=sources, limit=per_source, bili=False,
        log=log, min_score=min_score,
    )
    # 只保留歌手字段命中的
    from .models import norm

    nn = norm(name)
    keep = []
    for t in res:
        an = norm(t.artists)
        if nn and (nn in an or an in nn):
            keep.append(t)
    return keep if keep else res


def collect_artist(name, sources=None, mid=None, log=None):
    """歌手全量：音乐源 + 可选 B站 UP 主。"""
    tracks = artist_tracks(name, sources=sources, log=log)
    if mid:
        tracks.extend(bili_up_videos(mid, log=log))
    return tracks
