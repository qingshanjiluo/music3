# -*- coding: utf-8 -*-
"""B站适配器：官方搜索 API 取元数据 + yt-dlp 下载音频。

搜索走 B 站 web 接口（1.2s），不再起 yt-dlp 子进程（15s）。
下载仍用 yt-dlp（要处理音视频分离、格式选择、ffmpeg 转码）。

⚠️ 关键：搜索前必须先访问 bilibili.com 首页拿到 buvid3 cookie，
   否则 search/type 接口返回 412 Precondition Failed。
"""
from __future__ import annotations

import html
import os
import re
import subprocess
import sys
import time

from .models import Track, safe_name

_SEARCH = "https://api.bilibili.com/x/web-interface/search/type"
_HOME = "https://www.bilibili.com/"

# 免代理：避免干扰操作者自己的代理
_ENV = dict(os.environ)
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    _ENV.pop(_k, None)

# B 站必须避开 100026 Hi-Res 轨，否则 ffmpeg 转 mp3 失败产出 0 字节
AUDIO_FMT = "30216/30280/30232/bestaudio"

_TAG = re.compile(r"<[^>]+>")
_SEP = "|@|"

try:
    import requests

    _S = requests.Session()
    _S.trust_env = False
    _S.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
    )
    _cookie_ready = False
except Exception:
    _S = None


def _clean(s):
    """去掉 B 站返回的 <em> 高亮标签与 HTML 实体。"""
    if not s:
        return ""
    return html.unescape(_TAG.sub("", str(s))).strip()


def _ensure_cookie():
    """首次使用时访问首页拿 buvid3，否则搜索会被 412。"""
    global _cookie_ready
    if _cookie_ready or _S is None:
        return _cookie_ready
    try:
        _S.get(_HOME, timeout=12)
        _cookie_ready = bool(_S.cookies.get_dict())
    except Exception:
        _cookie_ready = False
    return _cookie_ready


def _dur_parse(s):
    """'4:10' / '1:02:33' -> 秒。"""
    if not s:
        return 0.0
    parts = str(s).split(":")
    try:
        nums = [int(p) for p in parts]
    except Exception:
        return 0.0
    if len(nums) == 2:
        return float(nums[0] * 60 + nums[1])
    if len(nums) == 3:
        return float(nums[0] * 3600 + nums[1] * 60 + nums[2])
    try:
        return float(nums[0])
    except Exception:
        return 0.0


def _run(args, timeout=180):
    try:
        p = subprocess.run(
            args,
            capture_output=True,
            timeout=timeout,
            env=_ENV,
            encoding="utf-8",
            errors="replace",
        )
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except subprocess.TimeoutExpired:
        return -9, "", "timeout"
    except Exception as e:
        return -1, "", repr(e)


def api_available():
    return _S is not None


def search(keyword, limit=20, log=None, retries=3):
    """官方 API 搜索，返回 Track 列表。约 1.2 秒。

    失败时返回空列表（调用方可退回 yt-dlp 方式）。
    """
    if _S is None:
        return []
    _ensure_cookie()

    for attempt in range(max(1, retries)):
        try:
            r = _S.get(
                _SEARCH,
                params={
                    "search_type": "video",
                    "keyword": keyword,
                    "page": 1,
                    "page_size": min(50, max(1, int(limit))),
                },
                timeout=15,
            )
            j = r.json()
        except Exception as e:
            if log:
                log("bili-api ERR %r" % (e,))
            return []

        code = j.get("code")
        if code == 0:
            break
        # -412 / 412: 风控。等一次再试
        if code in (-412, 412) or r.status_code == 412:
            if attempt < retries - 1:
                if log:
                    log("bili-api 412，8s 后重试")
                time.sleep(8)
                global _cookie_ready
                _cookie_ready = False
                _ensure_cookie()
                continue
        if log:
            log("bili-api code=%s msg=%s" % (code, str(j.get("message"))[:60]))
        return []

    res = ((j.get("data") or {}).get("result")) or []
    out = []
    for it in res:
        bvid = it.get("bvid") or ""
        if not bvid:
            continue
        dur = _dur_parse(it.get("duration"))
        pic = it.get("pic") or ""
        if pic.startswith("//"):
            pic = "https:" + pic
        out.append(
            Track(
                source="bilibili",
                track_id=bvid,
                title=_clean(it.get("title")),
                artists=_clean(it.get("author")),
                album="",
                duration_s=dur,
                ext="mp3",
                cover_url=pic,
                page_url="https://www.bilibili.com/video/%s" % bvid,
            )
        )
    return out


def search_ytdlp(keyword, limit=20, retries=3):
    """旧路：yt-dlp 搜（约 15s）。API 不可用时兜底。"""
    fmt = _SEP.join(["%(id)s", "%(title)s", "%(duration)s", "%(uploader)s", "%(webpage_url)s"])
    url = "bilisearch%d:%s" % (max(1, int(limit)), keyword)
    args = [
        "yt-dlp",
        "--encoding",
        "utf-8",
        "--no-warnings",
        "--skip-download",
        "--playlist-items",
        "1-%d" % limit,
        "--print",
        fmt,
        url,
    ]
    out = ""
    for attempt in range(retries):
        rc, out, err = _run(args, timeout=240)
        if out.strip():
            break
        if "412" in (err or "") or "429" in (err or ""):
            if attempt == 0:
                time.sleep(8)
                continue
            break
    tracks = []
    for line in (out or "").splitlines():
        line = line.strip()
        if not line or _SEP not in line:
            continue
        parts = line.split(_SEP)
        if len(parts) < 5:
            continue
        vid, title, dur, up, page = parts[0], parts[1], parts[2], parts[3], parts[4]
        if not vid.startswith("BV") and not vid.isdigit():
            continue
        try:
            d = float(dur)
        except Exception:
            d = 0.0
        tracks.append(
            Track(
                source="bilibili",
                track_id=vid,
                title=title,
                artists=up,
                duration_s=d,
                ext="mp3",
                page_url=page or ("https://www.bilibili.com/video/%s" % vid),
            )
        )
    return tracks


def search_any(keyword, limit=20, log=None):
    """优先 API，失败退回 yt-dlp。"""
    got = search(keyword, limit=limit, log=log)
    if got:
        return got
    if log:
        log("bili API 无结果，退回 yt-dlp")
    return search_ytdlp(keyword, limit=limit)


def download(track, dest_dir, timeout=900):
    """下 B 站音频转 mp3。返回 (ok, msg, path)。"""
    os.makedirs(dest_dir, exist_ok=True)
    base = safe_name("%s - %s" % (track.artists or "B站", track.title), 100)
    final = os.path.join(dest_dir, base + ".mp3")
    if os.path.exists(final) and os.path.getsize(final) > 150 * 1024:
        return True, "exists", final

    tmp = os.path.join(dest_dir, ".tmp_" + base + ".%(ext)s")
    url = track.page_url or ("https://www.bilibili.com/video/%s" % track.track_id)
    rc, out, err = _run(
        [
            "yt-dlp",
            "--encoding",
            "utf-8",
            "-x",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "0",
            "-f",
            AUDIO_FMT,
            "--no-playlist",
            "--no-warnings",
            "-o",
            tmp,
            url,
        ],
        timeout=timeout,
    )
    produced = os.path.join(dest_dir, ".tmp_" + base + ".mp3")
    if os.path.exists(produced) and os.path.getsize(produced) > 150 * 1024:
        try:
            os.replace(produced, final)
            # B站没有歌词接口，落盘后联网补一份
            lyric = ""
            try:
                from . import config as _c2, lyricfill

                if _c2.load().get("auto_lyric", True) and track.title:
                    ly, src = lyricfill.find_lyric(track.title, track.artists or "")
                    if ly:
                        lyric = ly
                        lyricfill.save_cached(final, ly)
            except Exception:
                pass
            try:
                from . import tagger

                tagger.tag(
                    final,
                    title=track.title,
                    artists=track.artists,
                    cover_url=track.cover_url,
                    lyric=lyric,
                    source="bilibili",
                )
            except Exception:
                pass
            return True, "ok", final
        except Exception as e:
            return False, repr(e), ""
    # 清理残留
    for f in os.listdir(dest_dir):
        if f.startswith(".tmp_" + base):
            try:
                os.remove(os.path.join(dest_dir, f))
            except Exception:
                pass
    return False, (err or out or "no output")[-400:], ""
