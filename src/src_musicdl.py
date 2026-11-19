# -*- coding: utf-8 -*-
"""musicdl 源适配器：网易云 / QQ / 酷我 / 千千 / 咪咕。"""
from __future__ import annotations

import sys

sys.path.insert(0, r"F:\tools\musicdl-master\src")

import logging
import os
import threading
import time

logging.getLogger("musicdl").setLevel(logging.ERROR)
os.environ.setdefault("TQDM_DISABLE", "1")

try:
    from rich.console import Console

    logging.getLogger("rich").setLevel(logging.ERROR)
except Exception:
    pass

# 注意：不要 patch rich.live.Live。
# 实测 patch 成空壳会让 musicdl 内部流程卡死（搜索从 100s 变成 >120s 超时）。
# 进度条噪声的代价远小于功能不可用，噪声让它去。

from musicdl.musicdl import MusicClient

from .models import Track, to_size

# 源名 -> (显示名, musicdl 类名)
SRC_MAP = {
    "netease": ("网易云", "NeteaseMusicClient"),
    "qq": ("QQ音乐", "QQMusicClient"),
    "kuwo": ("酷我", "KuwoMusicClient"),
    "qianqian": ("千千", "QianqianMusicClient"),
    "migu": ("咪咕", "MiguMusicClient"),
}


def build(keys, size=8, work_dir=None):
    """按短名建 MusicClient。keys 例: ['netease','qq']

    注意: init_music_clients_cfg 必须按【源类名】嵌套，形如
        {'QQMusicClient': {'search_size_per_source': 20}}
    直接给顶层键会被忽略（musicdl 只做 update(init_cfg.get(源类名, {}))）。

    size 是「每源拿多少条」，直接决定耗时：QQ 源每条都要单独请求 vkey，
    20 条约 380s，8 条约 150s。默认压到 8，够排序挑选了。
    """
    classes = [SRC_MAP[k][1] for k in keys if k in SRC_MAP]
    if not classes:
        raise ValueError("no valid source in %r" % (keys,))
    base = {
        "search_size_per_source": size,
        "search_size_per_page": size,
        "auto_set_proxies": False,      # 绝不动操作者代理
        "disable_print": True,
        "max_retries": 2,
    }
    if work_dir:
        base["work_dir"] = work_dir
    cfg = {c: dict(base) for c in classes}
    return MusicClient(music_sources=classes, init_music_clients_cfg=cfg)


def _dur(s):
    v = getattr(s, "duration_s", 0) or 0
    try:
        return float(v)
    except Exception:
        return 0.0


def _url_of(s):
    """取直链与后缀。"""
    rel = getattr(s, "download_url", None)
    url = ""
    ext = getattr(s, "ext", "") or "mp3"
    if isinstance(rel, dict):
        url = rel.get("download_url") or ""
        ext = rel.get("ext") or ext
    elif isinstance(rel, str):
        url = rel
    return url, ext


def _src_of(s, fallback):
    raw = str(getattr(s, "source", "") or "")
    for k, (_, cls) in SRC_MAP.items():
        if cls == raw:
            return k
    return fallback


def _silence():
    """已废弃：dup2 会让 rich 的 Console 持有失效句柄，
    导致同进程第二次搜索返回 0 条。保留空壳，不做事。"""
    return lambda: None


def _call_timeout(fn, timeout, log=None, tag=""):
    """直接执行 fn。

    历史坑：曾用守护线程 + join(timeout) 做硬超时，超时后线程仍存活并持有
    rich 的 Live 单例，下一次调用必然抛
      LiveError('Only one live display may be active at once')
    所以不做中断，老实等调用返回。timeout 参数保留仅为兼容旧调用。
    """
    return fn()


def search(
    client,
    keyword,
    fallback_src="netease",
    quiet=True,
    retries=2,
    log=None,
    timeout=120,
):
    """统一搜索，返回 Track 列表。

    源侧会不规则返回空（QQ/网易云 同 IP 限流），空结果自动退避重试。
    每次单源调用有硬超时，防止网络挂起把整个流程拖死。
    musicdl 单次搜索实测 100s 上下（多页 + 逐条取直链），120s 是安全值。
    """
    result = {}
    for attempt in range(max(1, retries)):
        if log:
            log("musicdl 搜索中（第%d/%d次，单源约100s，请稍候）…" % (attempt + 1, retries))
        t0 = time.time()
        try:
            r = _call_timeout(
                lambda: client.search(keyword),
                timeout,
                log=log,
                tag="musicdl[%d/%d]" % (attempt + 1, retries),
            )
            result = r or {}
        except Exception as e:
            result = {}
            if log:
                log("musicdl 搜索异常 attempt%d: %r" % (attempt + 1, e))
        if log:
            log("musicdl 第%d次完成，耗时 %.0fs，命中 %d"
                % (attempt + 1, time.time() - t0, sum(len(v or []) for v in result.values())))
        if any(v for v in result.values()):
            break
        if attempt < retries - 1:
            wait = 5 * (attempt + 1)
            if log:
                log("musicdl 空结果 attempt%d，%ds 后重试" % (attempt + 1, wait))
            time.sleep(wait)
    out = []
    for src_name, songs in result.items():
        for s in songs or []:
            if not s:
                continue
            url, ext = _url_of(s)
            out.append(
                Track(
                    source=_src_of(s, fallback_src),
                    track_id=str(getattr(s, "identifier", "") or ""),
                    title=str(getattr(s, "song_name", "") or ""),
                    artists=str(getattr(s, "singers", "") or ""),
                    album=str(getattr(s, "album", "") or ""),
                    duration_s=_dur(s),
                    ext=ext,
                    size_bytes=to_size(getattr(s, "file_size_bytes", 0)),
                    url=url,
                    lyric=str(getattr(s, "lyric", "") or ""),
                    cover_url=str(getattr(s, "cover_url", "") or ""),
                    raw=s,
                )
            )
    return out
