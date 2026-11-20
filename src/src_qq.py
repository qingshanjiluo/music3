# -*- coding: utf-8 -*-
"""QQ音乐快速通道：搜索与取直链分离。

musicdl 的 QQ 源慢在「对每条搜索结果都取一次 vkey + HEAD 校验」，
20 条就要 380s。这里拆成两步：

  1) search()   —— 只打搜索接口，1 秒内返回元数据（歌名/歌手/时长/mid）
  2) get_url()  —— 只为选中的那一首取直链，约 1 秒

实测对比：
  musicdl size=8  : 223s
  musicdl size=20 : 378s
  quick search    : 1.1s   ← 快 200 倍
"""
from __future__ import annotations

import json
import os
import sys

import requests

from .models import Track

# 复用 musicdl 的签名工具（避免自己重写 zzc 签名算法）
try:
    from musicdl.modules.utils.qqutils import (
        QQMusicClientUtils as _U,
        ThirdPartVKeysAPISongFileType as _Q,
    )

    _HAS_UTIL = True
except Exception:
    _HAS_UTIL = False
    _U = None
    _Q = None

_ENDPOINT = "https://u.y.qq.com/cgi-bin/musics.fcg"
_VKEYS = "https://api.vkeys.cn/music/tencent/song/link"
_LYRIC = "https://api.vkeys.cn/v2/music/tencent/lyric"

_S = requests.Session()
_S.trust_env = False
_S.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://y.qq.com/",
        "Origin": "https://y.qq.com/",
    }
)

# 优先尝试的质量档（从高到低）
_QUALITY_ORDER = [14, 11, 10, 8, 4]


def available():
    return _HAS_UTIL


def _payload(keyword, num, page=1):
    return {
        "comm": {"ct": "19", "cv": "1859", "uin": "0"},
        "req": {
            "method": "DoSearchForQQMusicDesktop",
            "module": "music.search.SearchCgiService",
            "param": {
                "num_per_page": int(num),
                "page_num": int(page),
                "query": keyword,
                "search_type": 0,
            },
        },
    }


def search(keyword, limit=10, timeout=15):
    """快速搜索 QQ 音乐，返回 Track 列表（只有元数据，url 为空）。"""
    if not _HAS_UTIL:
        return []
    p = _payload(keyword, limit)
    raw = json.dumps(p, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    try:
        sign = _U.sign(p)
        r = _S.post(_ENDPOINT, data=raw, params={"sign": sign}, timeout=timeout)
        j = r.json()
    except Exception:
        return []

    body = ((j.get("req") or {}).get("data") or {}).get("body") or {}
    lst = ((body.get("song") or {}).get("list")) or []
    out = []
    for s in lst:
        singers = s.get("singer") or []
        artists = ", ".join(
            a.get("name", "") for a in singers if isinstance(a, dict) and a.get("name")
        )
        album = s.get("album") or {}
        mid = s.get("mid") or s.get("songmid") or ""
        try:
            dur = float(s.get("interval") or 0)
        except Exception:
            dur = 0.0
        out.append(
            Track(
                source="qq",
                track_id=str(mid),
                title=str(s.get("name") or s.get("title") or ""),
                artists=artists,
                album=str(album.get("name") or album.get("title") or ""),
                duration_s=dur,
                ext="mp3",
                cover_url=cover_url(album_mid=album.get("mid") or album.get("albummid")),
                page_url=("https://y.qq.com/n/ryqq/songDetail/%s" % mid) if mid else "",
            )
        )
    return out


def get_url(mid, quality_order=None, timeout=12, verify=True):
    """为单个 mid 取直链。返回 (url, ext, quality_name) 或 (None, None, None)。

    verify=True 时用 Range GET 取前 1KB 校验，避免死链（vkeys 有时给失效 vkey）。
    校验只做一次（拿到第一个疑似可用的就验），过了就用，不重复验。
    """
    if not mid:
        return None, None, None
    for q in quality_order or _QUALITY_ORDER:
        try:
            r = _S.get(_VKEYS, params={"mid": mid, "quality": q}, timeout=timeout)
            j = r.json()
        except Exception:
            continue
        url = (j.get("data") or {}).get("url") or ""
        if not (isinstance(url, str) and url.startswith("http")):
            continue
        if verify and not _check_url(url, timeout=timeout):
            continue
        ext = "flac" if ".flac" in url.lower() else "mp3"
        name = None
        if _Q is not None:
            name = _Q.ID_TO_NAME.value.get(q)
        return url, ext, name
    return None, None, None


def _check_url(url, timeout=12):
    """Range GET 取前 1KB 校验（比 HEAD 可靠，部分 CDN 不支持 HEAD）。"""
    try:
        g = _S.get(
            url,
            timeout=timeout,
            stream=True,
            allow_redirects=True,
            headers={"Range": "bytes=0-1023"},
        )
        if g.status_code not in (200, 206):
            g.close()
            return False
        ct = (g.headers.get("Content-Type") or "").lower()
        head = next(g.iter_content(1024), b"")
        g.close()
        if not head:
            return False
        # 真音频：Content-Type 是 audio，或帧头是 mp3/flac 魔数
        if ct.startswith("audio") or ct.startswith("application/octet"):
            return True
        if head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") or head[:4] == b"fLaC":
            return True
        return False
    except Exception:
        return False


def get_lyric(mid, timeout=12):
    """取歌词。"""
    if not mid:
        return ""
    try:
        r = _S.get(_LYRIC, params={"mid": mid}, timeout=timeout)
        j = r.json()
        return str((j.get("data") or {}).get("lrc") or "")
    except Exception:
        return ""


def cover_url(mid=None, album_mid=None, size=800):
    """封面地址。album_mid 优先。"""
    if album_mid:
        return "https://y.gtimg.cn/music/photo_new/T002R%dx%dM000%s.jpg" % (
            size,
            size,
            album_mid,
        )
    return ""


def apply_login(cookie=""):
    """注入登录态：qm_keyst cookie 可显著提高 vkey/直链成功率。"""
    try:
        if cookie:
            _S.headers["Cookie"] = cookie
        else:
            _S.headers.pop("Cookie", None)
    except Exception:
        pass


def get_url_quality(quality_order=None):
    """占位：统一由 get_url(m, quality_order=cfg[...]) 调用。"""
    return None

