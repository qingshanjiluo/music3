# -*- coding: utf-8 -*-
"""统一下载器：直链源(网易云/QQ/酷我) + B站(yt-dlp)。"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

import requests

from .models import Track, safe_name, norm
from . import src_bili
from . import tagger
from . import config as _cfg

_CFG = _cfg.load()

# 免代理
_SESSION = requests.Session()
_SESSION.trust_env = False
_SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Referer": "https://music.163.com/",
    }
)

FFPROBE = _CFG.get("ffprobe")
FFMPEG = _CFG.get("ffmpeg")


def duration_of(path):
    """ffprobe 读时长（秒）。失败返回 0。"""
    if not os.path.exists(path):
        return 0.0
    try:
        p = subprocess.run(
            [
                FFPROBE,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                path,
            ],
            capture_output=True,
            timeout=60,
            encoding="utf-8",
            errors="replace",
        )
        return float((p.stdout or "0").strip() or 0)
    except Exception:
        return 0.0


def is_valid(path, min_sec=None, max_sec=None, min_bytes=None):
    """按时长+大小校验。短曲(14s/22s)合法，不靠 1MB 门槛误杀。"""
    min_sec = _CFG.get("valid_min_sec", 8) if min_sec is None else min_sec
    max_sec = _CFG.get("valid_max_sec", 1500) if max_sec is None else max_sec
    min_bytes = _CFG.get("valid_min_bytes", 150 * 1024) if min_bytes is None else min_bytes
    if not os.path.exists(path):
        return False, "missing"
    size = os.path.getsize(path)
    if size < min_bytes:
        return False, "tiny(%d)" % size
    d = duration_of(path)
    if d <= 0:
        return True, "dur_unknown_but_sized"
    if d < min_sec:
        return False, "short(%.1fs)" % d
    if d > max_sec:
        return False, "long(%.1fs)" % d
    return True, "ok(%.1fs)" % d


def to_mp3(src, dst):
    """转 mp3（直链源常给 flac/m4a）。已 mp3 直接挪。"""
    if os.path.splitext(src)[1].lower() == ".mp3":
        try:
            os.replace(src, dst)
            return True, "moved"
        except Exception as e:
            return False, repr(e)
    try:
        p = subprocess.run(
            [FFMPEG, "-y", "-i", src, "-vn", "-acodec", "libmp3lame", "-q:a", "0", dst],
            capture_output=True,
            timeout=600,
            encoding="utf-8",
            errors="replace",
        )
        if os.path.exists(dst) and os.path.getsize(dst) > 100 * 1024:
            try:
                os.remove(src)
            except Exception:
                pass
            return True, "converted"
        return False, (p.stderr or "")[-300:]
    except Exception as e:
        return False, repr(e)


def _cross_source_url(track):
    """某源取不到直链时，换另一源按歌名+歌手重搜并取链接。

    QQ 的 vkey 有时会大面积失效（版权/接口变动），此时换网易云；
    反之亦然。返回 (url, ext) 或 None。
    """
    title, artists = track.title, track.artists
    if not title:
        return None
    from .models import norm

    def _match(cands):
        best, best_s = None, 0.0
        tn = norm(title)
        an = norm(artists)
        for c in cands:
            s = 0.0
            ct = norm(c.title)
            ca = norm(c.artists)
            if ct == tn:
                s += 0.6
            elif tn in ct or ct in tn:
                s += 0.45
            if an and ca and (an in ca or ca in an):
                s += 0.4
            if s > best_s:
                best, best_s = c, s
        return best if best_s >= 0.7 else None

    kw = ("%s %s" % (title, artists)).strip()

    if track.source != "netease":
        try:
            from . import src_netease

            c = _match(src_netease.search(kw, limit=8))
            if c:
                url, ext, q = src_netease.get_url(
                    c.track_id, expect_sec=track.duration_s or c.duration_s
                )
                if url:
                    if not track.lyric:
                        try:
                            track.lyric = src_netease.get_lyric(c.track_id)
                        except Exception:
                            pass
                    return url, (ext or "mp3")
        except Exception:
            pass

    if track.source != "qq":
        try:
            from . import src_qq

            c = _match(src_qq.search(kw, limit=8))
            if c:
                url, ext, q = src_qq.get_url(c.track_id)
                if url:
                    if not track.lyric:
                        try:
                            track.lyric = src_qq.get_lyric(c.track_id)
                        except Exception:
                            pass
                    return url, (ext or "mp3")
        except Exception:
            pass

    return None


def download_direct(track, dest_dir, timeout=900, convert=True):
    """网易云/QQ/酷我等直链下载。返回 (ok, msg, path)。"""
    os.makedirs(dest_dir, exist_ok=True)
    base = safe_name("%s - %s" % (track.artists or track.source, track.title), 100)
    final = os.path.join(dest_dir, base + ".mp3")
    if is_valid(final)[0]:
        return True, "exists", final
    if not track.url:
        # 快速通道只给元数据，直链在这里现取
        if track.source == "qq" and track.track_id:
            try:
                from . import src_qq

                url, ext2, qname = src_qq.get_url(track.track_id)
                if url:
                    track.url = url
                    track.ext = ext2 or track.ext
                    if not track.lyric:
                        try:
                            track.lyric = src_qq.get_lyric(track.track_id)
                        except Exception:
                            pass
                else:
                    # QQ 直链全失效（vkey 过期/版权），跨源兜底到网易云
                    alt = _cross_source_url(track)
                    if alt:
                        track.url, track.ext = alt
                        return download_direct(track, dest_dir, timeout, convert)
                    return False, "qq no url (mid=%s)" % track.track_id, ""
            except Exception as e:
                return False, "qq url ERR %r" % (e,), ""
        elif track.source == "netease" and track.track_id:
            try:
                from . import src_netease

                url, ext2, qname = src_netease.get_url(
                    track.track_id, expect_sec=track.duration_s
                )
                if url:
                    track.url = url
                    track.ext = ext2 or track.ext
                    if not track.lyric:
                        try:
                            track.lyric = src_netease.get_lyric(track.track_id)
                        except Exception:
                            pass
                else:
                    alt = _cross_source_url(track)
                    if alt:
                        track.url, track.ext = alt
                        return download_direct(track, dest_dir, timeout, convert)
                    return False, "netease no full url (id=%s)" % track.track_id, ""
            except Exception as e:
                return False, "netease url ERR %r" % (e,), ""
        else:
            return False, "no_url", ""
    ext = track.ext or "mp3"
    tmp = os.path.join(dest_dir, ".dl_" + base + "." + ext)
    try:
        with _SESSION.get(track.url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(262144):
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        try:
            os.remove(tmp)
        except Exception:
            pass
        return False, repr(e)[:300], ""
    size = os.path.getsize(tmp) if os.path.exists(tmp) else 0
    if size < 100 * 1024:
        try:
            os.remove(tmp)
        except Exception:
            pass
        return False, "tiny(%d)" % size, ""
    if convert or ext.lower() != "mp3":
        ok, msg = to_mp3(tmp, final)
        if not ok:
            return False, msg, ""
    else:
        try:
            os.replace(tmp, final)
        except Exception as e:
            return False, repr(e), ""
    ok2, why = is_valid(final)
    if ok2:
        lyric = track.lyric or ""
        # 下载源自带的歌词若为空/占位，联网补一份（失败不影响下载结果）
        try:
            from . import config as _c2, lyricfill

            if _c2.load().get("auto_lyric", True):
                if not lyricfill._is_real_lyric(lyric):
                    title = track.title or ""
                    artists = track.artists or ""
                    if title:
                        ly, src = lyricfill.find_lyric(title, artists)
                        if ly:
                            lyric = ly
                            lyricfill.save_cached(final, ly)
        except Exception:
            pass
        tagger.tag(
            final,
            title=track.title,
            artists=track.artists,
            album=track.album,
            cover_url=track.cover_url,
            lyric=lyric,
            source=track.source,
        )
    return ok2, why, (final if ok2 else "")


def download(track, dest_dir):
    """分派。"""
    if track.source == "bilibili":
        return src_bili.download(track, dest_dir)
    return download_direct(track, dest_dir)
