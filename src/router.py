# -*- coding: utf-8 -*-
"""统一路由：跨源搜索 + 相似度打分 + 去重。"""
from __future__ import annotations

import os
import sys
import time

from .models import Track, norm
from . import src_bili, src_musicdl
from . import config as _cfg

_C = _cfg.load()

# 默认缓存目录（musicdl 会在其中写 search_results.pkl）
CACHE_DIR = _C.get("cache_dir")

ALL_SRC = ["bilibili", "netease", "qq", "kuwo", "qianqian", "migu"]
MUSICDL_SRC = ["netease", "qq", "kuwo", "qianqian", "migu"]

# 各源基础权重（音质/可用性经验值）
SRC_WEIGHT = dict(_C.get("src_weight"))

# 减分：翻唱/伴奏/片段/二次创作
MINUS_WORDS = (
    "伴奏", "翻唱", "cover", "片段", "试听", "铃声", "dj版", "鬼畜", "教程", "反应",
    "女声", "男声", "童声", "纯音乐", "remix", "钢琴版", "吉他版", "口琴",
    "beat", "type beat", "pop beat", "rap beat", "instrumental", "karaoke",
    "纯享", "live版", "演唱会版", "现场版", "加速版", "慢速版", "降调", "升调",
    "八音盒", "音乐盒", "midi", "AI翻唱", "ai翻唱", "代唱", "和声版",
    "0.8x", "1.2x", "0.9x", "1.1x", "slowed", "sped up",
)

# 标题里出现这些，说明是「同好二创/搬运」而不是正式曲目
TRIBUTE_WORDS = ("致敬", "二创", "搬运", "合集", "混剪", "串烧", "电台", "节目")


def _has_word(low, words):
    for w in words:
        if w in low:
            return w
    return None


def split_kw(keyword):
    """把 '晴天 周杰伦' 拆成 (歌名, 歌手限定)。"""
    parts = [p for p in keyword.replace("　", " ").split() if p]
    if len(parts) >= 2:
        return parts[0], "".join(parts[1:])
    return keyword, ""


def score(track, keyword):
    """0~1 相关度。歌名命中为主，歌手命中为强加权。"""
    name, extra = split_kw(keyword)
    nn = norm(name)
    en = norm(extra)
    tn = norm(track.title)
    an = norm(track.artists)

    if not nn:
        return 0.0

    s = 0.0
    # --- 歌名匹配（主权重） ---
    if tn == nn:
        s += 0.50
    elif nn in tn:
        s += 0.40
    else:
        hit = sum(1 for ch in set(nn) if ch in tn)
        s += 0.40 * (hit / max(1, len(set(nn))))

    # --- 歌手匹配（强加权，压翻唱） ---
    if en and an:
        if an == en or en in an or an in en:
            s += 0.40
        elif any(c in an for c in en if c.isalnum()):
            s += 0.08
    if en and en in tn:
        s += 0.15

    # --- 减分（翻唱/伴奏/版本变体） ---
    low = track.title.lower()
    hit = _has_word(low, MINUS_WORDS)
    if hit:
        # beat/instrumental 这类是纯伴奏，重罚
        heavy = ("beat", "instrumental", "karaoke", "伴奏", "纯音乐", "midi", "八音盒")
        s -= 0.50 if hit in heavy else 0.25
    hit2 = _has_word(low, TRIBUTE_WORDS)
    if hit2:
        s -= 0.20

    # 标题里堆了「歌手名」但没有歌名 → 更像是歌单/搬运
    if en and en in tn and nn not in tn:
        s -= 0.15

    # --- 时长合理性 ---
    d = track.duration_s
    if d:
        if 60 <= d <= 600:
            s += 0.05
        elif d < 30:
            s -= 0.30
        elif d > 900:
            s -= 0.10

    # --- 源权重 ---
    s *= SRC_WEIGHT.get(track.source, 0.5)

    return max(0.0, min(1.0, s))


def dedup(tracks):
    """同源同 title+artist 归一后去重。"""
    seen = {}
    out = []
    for t in tracks:
        k = (t.source, norm(t.title), norm(t.artists)[:12])
        if k in seen:
            continue
        seen[k] = 1
        out.append(t)
    return out


def search(
    keyword,
    sources=None,
    limit=15,
    min_score=0.15,
    bili=True,
    pause=1.0,
    log=None,
    work_dir=None,
    use_cache=True,
):
    """跨源搜索。返回按分数降序的 Track 列表。"""
    sources = sources or ALL_SRC
    work_dir = work_dir or CACHE_DIR
    want_bili = bili and ("bilibili" in sources)
    want_dl = [s for s in sources if s in MUSICDL_SRC]

    # 缓存命中直接返回（避免重复请求触发限流）
    if use_cache:
        try:
            from . import cache as _cache

            hit = _cache.get(keyword, sources, limit)
            if hit is not None:
                if log:
                    log("cache HIT %s (%d)" % (keyword, len(hit)))
                out = [Track(**{k: v for k, v in d.items() if k != "raw"}) for d in hit]
                return out
        except Exception:
            pass

    collected = []

    # 多源并发：QQ快速通道 / musicdl / B站 同时打，并行等待
    def _do_qq():
        """QQ 快速通道：只取元数据，1~2 秒返回。"""
        if "qq" not in sources:
            return []
        from . import src_qq

        if not src_qq.available():
            return []
        try:
            got = src_qq.search(keyword, limit=min(12, max(6, limit)))
            if log:
                log("qq-fast -> %d" % len(got))
            return got
        except Exception as e:
            if log:
                log("qq-fast ERR %r" % (e,))
            return []

    # 网易云快速通道：只取元数据，1~2 秒返回
    def _do_netease():
        if "netease" not in sources:
            return []
        from . import src_netease

        try:
            got = src_netease.search(keyword, limit=min(12, max(6, limit)))
            if log:
                log("netease-fast -> %d" % len(got))
            return got
        except Exception as e:
            if log:
                log("netease-fast ERR %r" % (e,))
            return []

    # musicdl 只用于快速通道之外的小众源（酷我/千千/咪咕）
    FAST_SRC = {"qq", "netease"}
    ml_sources = [s for s in want_dl if s not in FAST_SRC]

    def _do_musicdl():
        if not ml_sources:
            return []
        try:
            client = src_musicdl.build(
                ml_sources, size=min(8, max(4, limit)), work_dir=work_dir
            )
            got = src_musicdl.search(client, keyword, ml_sources[0], log=log)
            if log:
                log("musicdl(%s) -> %d" % (",".join(ml_sources), len(got)))
            return got
        except Exception as e:
            if log:
                log("musicdl ERR %r" % (e,))
            return []

    def _do_bili():
        if not want_bili:
            return []
        if pause:
            time.sleep(pause)
        try:
            got = src_bili.search_any(keyword, limit=limit, log=log)
            if log:
                log("bilibili -> %d" % len(got))
            return got
        except Exception as e:
            if log:
                log("bili ERR %r" % (e,))
            return []

    # 四路并发：QQ快速 / 网易云快速 / musicdl(小众源) / B站
    from concurrent.futures import ThreadPoolExecutor

    active = []
    if "qq" in sources:
        active.append(("qq", _do_qq))
    if "netease" in sources:
        active.append(("netease", _do_netease))
    if ml_sources:
        active.append(("musicdl", _do_musicdl))
    if want_bili:
        active.append(("bili", _do_bili))

    if len(active) > 1:
        with ThreadPoolExecutor(max_workers=len(active)) as ex:
            futs = [(name, ex.submit(fn)) for name, fn in active]
            for name, fu in futs:
                try:
                    collected.extend(fu.result() or [])
                except Exception as e:
                    if log:
                        log("%s ERR %r" % (name, e))
    else:
        for name, fn in active:
            collected.extend(fn() or [])

    collected = dedup(collected)
    for t in collected:
        t.score = score(t, keyword)
    collected = [t for t in collected if t.score >= min_score]
    collected.sort(key=lambda t: -t.score)

    # 只在拿到结果时写缓存（空结果不缓存，避免把限流期间的空答案固化）
    if use_cache and collected:
        try:
            from . import cache as _cache

            _cache.put(keyword, sources, limit, [t.to_dict() for t in collected])
        except Exception:
            pass
    return collected
