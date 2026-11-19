# -*- coding: utf-8 -*-
"""封面补全：无内嵌封面时，从网易云/QQ 搜索取封面图并写回 ID3 APIC。

复用 lyricfill 的命名解析与打分逻辑，避免两套代码。
"""
from __future__ import annotations

import hashlib
import os

from . import config as _cfg
from .models import norm

_C = _cfg.load()
_CACHE_DIR = _C.get("cache_dir") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_cache"
)
_COVER_DIR = os.path.join(_CACHE_DIR, "fetched_covers")


def _key(path):
    try:
        st = os.stat(path)
        raw = "%s|%d|%d" % (os.path.abspath(path).lower(), int(st.st_size), int(st.st_mtime))
    except Exception:
        raw = os.path.abspath(path).lower()
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:24]


def cache_path(path, ext=".jpg"):
    return os.path.join(_COVER_DIR, _key(path) + ext)


def get_cached(path):
    """取已下载的封面缓存。返回 (bytes, mime) 或 (None, None)。"""
    for ext, mime in ((".jpg", "image/jpeg"), (".png", "image/png"), (".webp", "image/webp")):
        p = cache_path(path, ext)
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    d = f.read()
                if d:
                    return d, mime
            except Exception:
                pass
    return None, None


def save_cached(path, data, mime="image/jpeg"):
    try:
        os.makedirs(_COVER_DIR, exist_ok=True)
        ext = ".jpg"
        if mime and "png" in mime:
            ext = ".png"
        elif mime and "webp" in mime:
            ext = ".webp"
        p = cache_path(path, ext)
        tmp = p + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, p)
        return True
    except Exception:
        return False


def _download(url, timeout=15):
    """下载封面图。返回 (bytes, mime) 或 (None, None)。"""
    if not url:
        return None, None
    try:
        import requests

        s = requests.Session()
        s.trust_env = False
        h = {"User-Agent": "Mozilla/5.0", "Referer": "https://y.qq.com/"}
        r = s.get(url, headers=h, timeout=timeout)
        if r.status_code != 200:
            return None, None
        ct = (r.headers.get("Content-Type") or "").lower()
        if not ct.startswith("image"):
            return None, None
        if len(r.content) < 2000:
            return None, None
        return r.content, ct.split(";")[0]
    except Exception:
        return None, None


def _score(cand_title, cand_artist, want_title, want_artist):
    from .lyricfill import _score as ls

    return ls(cand_title, cand_artist, want_title, want_artist)


def find_cover(title, artist, log=None):
    """从网易云/QQ 找封面。返回 (bytes, mime, source) 或 (None, None, "")."""
    t = (title or "").strip()
    a = (artist or "").strip()
    if not t:
        return None, None, ""

    kw = ("%s %s" % (t, a)).strip()

    # ① 网易云（封面质量高，来自 al.picUrl）
    try:
        from . import src_netease

        cands = src_netease.search(kw, limit=8)
        best, best_s = None, 0.0
        for c in cands:
            sc = _score(c.title, c.artists, t, a)
            if sc > best_s:
                best, best_s = c, sc
        if best and best_s >= 0.55 and best.cover_url:
            data, mime = _download(best.cover_url)
            if data:
                if log:
                    log("netease 命中 %.2f: %s - %s" % (best_s, best.title, best.artists))
                return data, mime, "netease"
    except Exception as e:
        if log:
            log("netease ERR %r" % (e,))

    # ② QQ（封面 URL 规则已知）
    try:
        from . import src_qq

        cands = src_qq.search(kw, limit=8)
        best, best_s = None, 0.0
        for c in cands:
            sc = _score(c.title, c.artists, t, a)
            if sc > best_s:
                best, best_s = c, sc
        if best and best_s >= 0.55 and best.cover_url:
            data, mime = _download(best.cover_url)
            if data:
                if log:
                    log("qq 命中 %.2f: %s - %s" % (best_s, best.title, best.artists))
                return data, mime, "qq"
    except Exception as e:
        if log:
            log("qq ERR %r" % (e,))

    return None, None, ""


def fill_one(path, write_id3=True, log=None):
    """补一首的封面。返回 dict。"""
    r = {"path": path, "ok": False, "source": "", "cached": False, "wrote": False}

    # 已有内嵌封面就跳过
    try:
        from . import tagreader

        tg = tagreader.read_tags(path)
        if tg.get("has_cover"):
            r["ok"] = True
            r["source"] = "embedded"
            return r
    except Exception:
        tg = {}

    # 缓存
    data, mime = get_cached(path)
    if data:
        r.update(ok=True, source="cache", cached=True)
        if write_id3:
            r["wrote"] = _write_id3(path, data, mime)
        return r

    # 解析名字
    title = (tg.get("title") or "").strip()
    artist = (tg.get("artists") or "").strip()
    if not title:
        from .lyricfill import parse_name

        a2, t2 = parse_name(path)
        artist, title = artist or a2, t2

    data, mime, src = find_cover(title, artist, log=log)
    if data:
        save_cached(path, data, mime or "image/jpeg")
        r.update(ok=True, source=src or "?", cached=True)
        if write_id3:
            r["wrote"] = _write_id3(path, data, mime or "image/jpeg")
    return r


def _write_id3(path, data, mime="image/jpeg"):
    """把封面写进 ID3 APIC。"""
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, APIC, ID3NoHeaderError

        try:
            audio = MP3(path, ID3=ID3)
            tags = audio.tags
            if tags is None:
                audio.add_tags()
                tags = audio.tags
        except ID3NoHeaderError:
            tags = ID3()
            audio = MP3(path)
            audio.tags = tags
        tags.delall("APIC")
        tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
        audio.save(v2_version=3)
        return True
    except Exception:
        return False


def batch(paths, write_id3=True, limit=None, log=None, on_progress=None):
    """批量补封面。返回统计。"""
    stats = {"total": 0, "ok": 0, "miss": 0, "wrote": 0, "by_source": {}}
    todo = paths[:limit] if limit else paths
    stats["total"] = len(todo)
    for i, p in enumerate(todo, 1):
        try:
            r = fill_one(p, write_id3=write_id3, log=log)
        except Exception as e:
            r = {"ok": False, "source": "err:%r" % (e,)}
        if r.get("ok"):
            stats["ok"] += 1
            src = r.get("source") or "?"
            stats["by_source"][src] = stats["by_source"].get(src, 0) + 1
            if r.get("wrote"):
                stats["wrote"] += 1
        else:
            stats["miss"] += 1
        if on_progress:
            on_progress(i, len(todo), p, r)
    return stats


def cache_stats():
    n, size = 0, 0
    if os.path.isdir(_COVER_DIR):
        for f in os.listdir(_COVER_DIR):
            p = os.path.join(_COVER_DIR, f)
            try:
                n += 1
                size += os.path.getsize(p)
            except Exception:
                pass
    return {"files": n, "bytes": size}


def cache_clear():
    n = 0
    if os.path.isdir(_COVER_DIR):
        for f in os.listdir(_COVER_DIR):
            try:
                os.remove(os.path.join(_COVER_DIR, f))
                n += 1
            except Exception:
                pass
    return n
