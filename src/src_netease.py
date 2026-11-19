# -*- coding: utf-8 -*-
"""网易云快速通道：搜索与取直链分离。

musicdl 的网易云源慢在「对每条搜索结果都跑一遍多镜像取链 + HEAD 校验」，
实测 size=8 要 154s。这里拆成两步：

  1) search()   —— 只打 cloudsearch/pc，1 秒返回元数据
  2) get_url()  —— 只为选中的那首取直链，0.3~1.5 秒

实测对比：
  musicdl : 154s
  quick   : 1.0s   ← 快 150 倍

取链优先级：
  ① music.163.com/song/media/outer/url （官方，免费曲直出，版权曲 403）
  ② musicapi.haitangw.net              （镜像，0.3s，返回真实 126.net 直链）
  ③ nextmusic.toubiec.cn               （镜像兜底，1~3s）

⚠️ 未登录状态下网易云会屏蔽大厂原唱（如周杰伦《七里香》），
   只能搜到翻唱。这是版权限制，不是接口问题。要原唱请用 qq 源。
"""
from __future__ import annotations

import json

import requests

from .models import Track

_SEARCH = "https://music.163.com/api/cloudsearch/pc"
_OUTER = "https://music.163.com/song/media/outer/url"
_MIRROR1 = "https://musicapi.haitangw.net/music/wy.php"
_MIRROR2 = "https://nextmusic.toubiec.cn/api/getMusicUrl"
_LYRIC = "https://music.163.com/api/song/lyric"

_S = requests.Session()
_S.trust_env = False
_S.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://music.163.com/",
        "Origin": "https://music.163.com",
        "Cookie": "appver=2.0.2",
    }
)

# 取链质量档（镜像用字符串）
_LEVELS = ["lossless", "exhigh", "higher", "standard"]


def available():
    return True


def search(keyword, limit=10, timeout=15):
    """快速搜索，返回 Track 列表（只有元数据）。"""
    try:
        r = _S.post(
            _SEARCH,
            data={"s": keyword, "type": 1, "limit": int(limit), "offset": 0},
            timeout=timeout,
        )
        j = r.json()
    except Exception:
        return []

    songs = ((j.get("result") or {}).get("songs")) or []
    out = []
    for s in songs:
        ar = s.get("ar") or s.get("artists") or []
        artists = ", ".join(a.get("name", "") for a in ar if isinstance(a, dict))
        al = s.get("al") or s.get("album") or {}
        try:
            dur = float((s.get("dt") or s.get("duration") or 0)) / 1000.0
        except Exception:
            dur = 0.0
        cover = al.get("picUrl") or ""
        out.append(
            Track(
                source="netease",
                track_id=str(s.get("id") or ""),
                title=str(s.get("name") or ""),
                artists=artists,
                album=str(al.get("name") or ""),
                duration_s=round(dur, 1),
                ext="mp3",
                cover_url=cover,
                page_url=(
                    "https://music.163.com/song?id=%s" % s.get("id")
                    if s.get("id")
                    else ""
                ),
            )
        )
    return out


def probe_duration(url, timeout=20, max_bytes=6 * 1024 * 1024):
    """下载到临时文件后用 ffprobe 精确取时长。失败返回 0。

    只用 Content-Length + 位速估算不可靠（VBR 编码误差极大，实测 0.0s），
    所以老实下到临时文件量。max_bytes 限制单次探测不超过 6MB
    （普通 320k 的 4 分钟歌约 9MB，这里取前 6MB 足够 ffprobe 读出时长）。
    """
    import os
    import subprocess
    import tempfile

    from . import config as _cfg

    ffprobe = _cfg.load().get("ffprobe")
    tmp = None
    try:
        r = _S.get(url, timeout=timeout, stream=True, allow_redirects=True)
        ct = (r.headers.get("Content-Type") or "").lower()
        if not ct.startswith("audio"):
            r.close()
            return 0.0
        fd, tmp = tempfile.mkstemp(suffix=".mp3")
        written = 0
        with os.fdopen(fd, "wb") as f:
            for chunk in r.iter_content(131072):
                if not chunk:
                    break
                f.write(chunk)
                written += len(chunk)
                if written >= max_bytes:
                    break
        r.close()
        if written < 200 * 1024:
            return 0.0
        p = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                tmp,
            ],
            capture_output=True,
            timeout=60,
            encoding="utf-8",
            errors="replace",
        )
        return float((p.stdout or "0").strip() or 0)
    except Exception:
        return 0.0
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except Exception:
                pass


def _probe(url, timeout=12):
    """探测直链是否真音频。返回 (ok, ext, size)。"""
    try:
        r = _S.get(url, timeout=timeout, stream=True, allow_redirects=True)
        ct = (r.headers.get("Content-Type") or "").lower()
        cl = r.headers.get("Content-Length")
        head = next(r.iter_content(2048), b"")
        r.close()
        if not ct.startswith("audio"):
            return False, None, 0
        if head[:2] not in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID", b"fLa"):
            return False, None, 0
        ext = "flac" if head[:3] == b"fLa" or ".flac" in url.lower() else "mp3"
        try:
            size = int(cl) if cl else 0
        except Exception:
            size = 0
        return True, ext, size
    except Exception:
        return False, None, 0


def get_url(sid, timeout=20, expect_sec=None):
    """取直链。返回 (url, ext, quality) 或 (None, None, None)。

    expect_sec: 期望时长（秒）。给了就会验证直链时长，
    官方 outer url 对版权曲只给 30s 试听，时长对不上就换镜像。
    """
    if not sid:
        return None, None, None

    def _ok_dur(url, ext, tag):
        """时长匹配才接受。没给 expect_sec 就接受。"""
        if not expect_sec or expect_sec <= 0:
            return url, ext, tag
        d = probe_duration(url, timeout=timeout)
        if d and abs(d - expect_sec) <= max(15, expect_sec * 0.15):
            return url, ext, tag
        return None

    # ① 官方 outer url（非版权曲直出完整，版权曲只给 30s 试听）
    u = "%s?id=%s.mp3" % (_OUTER, sid)
    ok, ext, _ = _probe(u, timeout=timeout)
    if ok:
        got = _ok_dur(u, ext, "outer")
        if got:
            return got

    # ② 镜像 haitangw（快，0.3s）
    for lv in _LEVELS:
        try:
            r = _S.get(
                _MIRROR1,
                params={"id": sid, "level": lv, "type": "json"},
                timeout=timeout,
            )
            j = r.json()
            d = j.get("data") or {}
            url = d.get("url") or ""
            if url.startswith("http"):
                ext = "flac" if ".flac" in url.lower() else "mp3"
                got = _ok_dur(url, ext, "%s/%s" % (lv, d.get("quality") or ""))
                if got:
                    return got
        except Exception:
            continue

    # ③ 镜像 toubiec 兜底
    for lv in _LEVELS:
        try:
            r = _S.post(
                _MIRROR2,
                json={"id": str(sid), "level": lv},
                timeout=timeout,
            )
            j = r.json()
            url = (j.get("data") or {}).get("url") or ""
            if url.startswith("http"):
                ext = "flac" if ".flac" in url.lower() else "mp3"
                got = _ok_dur(url, ext, "toubiec/%s" % lv)
                if got:
                    return got
        except Exception:
            continue

    return None, None, None


def get_lyric(sid, timeout=15):
    """取歌词（含翻译时合并）。"""
    if not sid:
        return ""
    try:
        r = _S.get(
            _LYRIC,
            params={"id": sid, "lv": 1, "tv": 1, "kv": 0},
            timeout=timeout,
        )
        j = r.json()
        lrc = (j.get("lrc") or {}).get("lyric") or ""
        tr = (j.get("tlyric") or {}).get("lyric") or ""
        if tr:
            return lrc + "\n" + tr
        return lrc
    except Exception:
        return ""
