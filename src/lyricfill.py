# -*- coding: utf-8 -*-
"""歌词补全：无内嵌歌词时，从网易云/QQ 搜索并拉取。

策略：
  1. 从文件名解析「歌手 - 歌名」
  2. 网易云搜 → 取歌词（官方接口，准确度高）
  3. 网易云没有 → QQ 搜 → 取歌词
  4. 结果缓存到 _cache/lyrics/<md5>.lrc（不改原文件）
  5. 可选 --write 把歌词写回 ID3 USLT（任何播放器都能看到）

实测：56/60 首缺歌词，补全后前端「词」面板才有内容可显示。
"""
from __future__ import annotations

import hashlib
import os
import re

from . import config as _cfg
from .models import norm

_C = _cfg.load()
_CACHE_DIR = _C.get("cache_dir") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_cache"
)
_LYRIC_DIR = os.path.join(_CACHE_DIR, "lyrics")

# 文件名里常见的噪声，比对前先剥掉
_NOISE = re.compile(
    r"[\(（\[【].*?[\)）\]】]|"
    r"\b(remix|live|cover|feat|ft\.?|official|mv|hd|hq|4k|flac|mp3|wav)\b",
    re.I,
)


_NOISE_MARK = re.compile(r"[【\[\(（【]([^】\]\)）]{1,40})[】\]\)）]")
_NOISE_PFX = re.compile(r"^(无损音质|高音质|精选|盘点|歌曲集|合集|专辑|热门|MV版|Live|现场版|DJ版|Remix|抖音热歌|\d{2,4}年)+", re.I)


def _parse_stem(stem):
    """清理文件名噪声：合集前缀、括号注记、emoji、年份。返回 (artist, title)。"""
    stem = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]+", " ", stem)  # emoji
    stem = re.sub(r"\s{2,}", " ", stem).strip()
    # 常见分隔符 "歌手 - 歌名"（不递归递归——子串本身可能再含分隔符，
    # 如 "Fade - Alan Walker"，递归会把标题也拆掉导致 artist 丢失）
    for sep in (" - ", "－", " — ", "_"):
        if sep in stem:
            a, t = stem.split(sep, 1)
            a = _NOISE_PFX.sub("", a).strip(" -—_·、")
            t = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]+", " ", t).strip()
            if len(t) >= 2:
                return a, t
    # 【歌手】《歌名》 / (歌手) 歌名 —— 优先取括号后主体，括号内作 artist
    m = _NOISE_MARK.search(stem)
    if m:
        inner = m.group(1).strip()
        outer = (stem[:m.start()] + stem[m.end():]).strip()
        outer = _NOISE_PFX.sub("", outer).strip(" -—_·、")
        if len(outer) >= 2:
            return inner, outer
        if len(inner) >= 2:
            return "", inner
    # 合集/盘点类前缀直接剥掉，剩下的当歌名
    cleaned = _NOISE_PFX.sub("", stem).strip(" -—_·、")
    if len(cleaned) >= 2:
        return "", cleaned
    return "", stem.strip()


# 通用目录名（不能当歌手）：命中就往上探一级
_DIR_GENERIC = {
    "热门歌曲", "红心收藏", "纯音乐", "英文歌", "摇滚民谣", "民谣", "流行",
    "翻唱", "DJ", "合集", "精选", "歌曲集", "SD卡版", "thisistruemusic",
    "_归档_封存", "投稿", "QQ音乐", "网易云", "bilibili", "B站", "MV",
    "新建文件夹", "音乐", "下载",
}


def guess_meta(path, max_up=3):
    """ID3 双缺修复：返回 (artist, title, artist_src)。
    title = _parse_stem 清洗文件名；artist = 最近的非通用父目录。"""
    _, title = _parse_stem(os.path.splitext(os.path.basename(path))[0])
    artist, src = "", "无"
    d = os.path.dirname(path)
    for _ in range(max_up):
        if not d:
            break
        base = os.path.basename(d).strip()
        if base and base not in _DIR_GENERIC and not re.match(r"^\d+$", base):
            artist, src = base, "父目录"
            break
        d = os.path.dirname(d)
    return artist, title, src


def parse_name(path):
    """从文件路径解析 (歌手, 歌名)。"""
    stem = os.path.splitext(os.path.basename(path))[0]
    return _parse_stem(stem)


def _clean(s):
    if not s:
        return ""
    s = _NOISE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def cache_path(path):
    key = hashlib.md5(os.path.abspath(path).lower().encode("utf-8")).hexdigest()[:24]
    return os.path.join(_LYRIC_DIR, key + ".lrc")


def get_cached(path):
    p = cache_path(path)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                txt = f.read().strip()
            # 缓存里的占位歌词（「纯音乐无填词」）视为无效，自动作废
            if txt and _is_real_lyric(txt):
                return txt
            if txt:
                try:
                    os.remove(p)
                except Exception:
                    pass
        except Exception:
            pass
    return ""


def save_cached(path, lyric):
    if not lyric:
        return False
    try:
        os.makedirs(_LYRIC_DIR, exist_ok=True)
        tmp = cache_path(path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(lyric)
        os.replace(tmp, cache_path(path))
        return True
    except Exception:
        return False


def _score(cand_title, cand_artist, want_title, want_artist):
    """简单相似度，0~1。"""
    ct, ca = norm(cand_title), norm(cand_artist)
    wt, wa = norm(want_title), norm(want_artist)
    s = 0.0
    if not wt:
        return 0.0
    if ct == wt:
        s += 0.6
    elif wt in ct or ct in wt:
        s += 0.45
    else:
        hit = sum(1 for ch in set(wt) if ch in ct)
        s += 0.45 * hit / max(1, len(set(wt)))
    if wa and ca:
        if ca == wa or wa in ca or ca in wa:
            s += 0.4
        elif any(c in ca for c in wa if c.isalnum()):
            s += 0.08
    else:
        # 没有歌手信息时不惩罚
        s += 0.15
    return s


def _is_real_lyric(text):
    """判断是不是真歌词，而不是「纯音乐无填词」这类占位。"""
    if not text:
        return False
    t = text.strip()
    if len(t) < 80:
        return False
    # 去掉时间戳后看纯文本
    body = re.sub(r"\[\d{1,2}:\d{1,2}(?:[.:]\d{1,3})?\]", "", t)
    body = re.sub(r"\[(ti|ar|al|by|offset|re|ve):[^\]]*\]", "", body).strip()
    if len(body) < 40:
        return False
    # 占位文案黑名单
    PLACE = (
        "纯音乐", "没有填词", "无填词", "请您欣赏", "此歌曲为没有",
        "instrumental", "暂无歌词", "没有歌词", "no lyric",
    )
    low = body.lower()
    for w in PLACE:
        if w in low:
            # 真歌词里通常不会只出现这一句
            if len(body) < 120:
                return False
    return True


def find_candidates(title, artist, sources=("netease", "qq"), limit=6):
    """列出各源同名候选（含 id），供前端点选拉歌词。

    返回 [{source, sid, title, artists, duration, cover_url, score}]
    """
    out = []
    t = (title or "").strip()
    a = (artist or "").strip()
    if not t:
        return out
    kw = ("%s %s" % (t, a)).strip()
    for src in sources:
        try:
            if src == "netease":
                from . import src_netease as mod
            elif src == "qq":
                from . import src_qq as mod
            else:
                continue
            for c in (mod.search(kw, limit=limit) or []):
                out.append({
                    "source": src,
                    "sid": c.track_id,
                    "title": c.title,
                    "artists": c.artists,
                    "duration": round(float(c.duration_s or 0), 1),
                    "cover_url": c.cover_url or "",
                    "score": round(_score(c.title, c.artists, t, a), 3),
                })
        except Exception:
            continue
    # 同源内按分排序，跨源保持顺序（netease 在前）
    out.sort(key=lambda x: -x.get("score", 0))
    return out


def fetch_lyric(source, sid, timeout=15):
    """按用户点选的 source+sid 拉歌词。返回 (lyric, msg)。"""
    try:
        if source == "netease":
            from . import src_netease

            ly = src_netease.get_lyric(sid)
        elif source == "qq":
            from . import src_qq

            ly = src_qq.get_lyric(sid)
            if ly and not ly.lstrip().startswith("["):
                import base64

                try:
                    ly = base64.b64decode(ly).decode("utf-8", "replace")
                except Exception:
                    pass
        else:
            return "", "unknown source"
        if _is_real_lyric(ly or ""):
            return ly, "ok"
        return ly or "", "占位/无效歌词（纯音乐或无词）"
    except Exception as e:
        return "", repr(e)


def find_lyric(title, artist, log=None, timeout=15):
    """从网易云/QQ 找歌词。返回 (lyric, source) 或 ("", "")."""
    title_c, artist_c = _clean(title), _clean(artist)
    if not title_c:
        return "", "无歌名（元数据与文件名都没解析出标题）"

    kw = ("%s %s" % (title_c, artist_c)).strip()
    ne_hit = qq_hit = ne_err = qq_err = False

    # ① 网易云
    try:
        from . import src_netease

        cands = src_netease.search(kw, limit=8)
        best, best_s = None, 0.0
        for t in cands:
            s = _score(t.title, t.artists, title_c, artist_c)
            if s > best_s:
                best, best_s = t, s
        if best and best_s >= 0.55:
            ne_hit = True
            ly = src_netease.get_lyric(best.track_id)
            if _is_real_lyric(ly):
                if log:
                    log("netease 命中 %.2f: %s - %s" % (best_s, best.title, best.artists))
                return ly, "netease"
            elif ly and log:
                log("netease 命中但非真歌词（%.0f 字）" % len(ly))
    except Exception as e:
        ne_err = True
        if log:
            log("netease ERR %r" % (e,))

    # ② QQ
    try:
        from . import src_qq

        cands = src_qq.search(kw, limit=8)
        best, best_s = None, 0.0
        for t in cands:
            s = _score(t.title, t.artists, title_c, artist_c)
            if s > best_s:
                best, best_s = t, s
        if best and best_s >= 0.55:
            qq_hit = True
            ly = src_qq.get_lyric(best.track_id)
            # QQ 有时给 base64
            if ly and not ly.lstrip().startswith("["):
                import base64

                try:
                    dec = base64.b64decode(ly).decode("utf-8", "replace")
                    if _is_real_lyric(dec):
                        ly = dec
                except Exception:
                    pass
            if _is_real_lyric(ly):
                if log:
                    log("qq 命中 %.2f: %s - %s" % (best_s, best.title, best.artists))
                return ly, "qq"
            elif ly and log:
                log("qq 命中但非真歌词（%.0f 字）" % len(ly))
    except Exception as e:
        qq_err = True
        if log:
            log("qq ERR %r" % (e,))

    # 失败原因三态：占位命中（打到歌但纯音乐）/ 无匹配（两源打分都 <0.55）/ 两源异常
    if ne_hit:
        return "", "网易命中但为占位歌词（纯音乐/伴奏）"
    if qq_hit:
        return "", "QQ命中但为占位歌词（纯音乐/伴奏）"
    if ne_err or qq_err:
        return "", "两源搜索异常 netease=%s qq=%s" % (ne_err or "ok", qq_err or "ok")
    return "", "两源无匹配（打分<0.55，疑似无歌词曲目或元数据不准）"


def fill_one(path, write_id3=False, log=None):
    """补一首。返回 dict 结果。"""
    r = {"path": path, "ok": False, "source": "", "cached": False, "wrote": False}

    # 已有内嵌歌词就跳过
    try:
        from . import tagreader

        t = tagreader.read_tags(path)
        if t.get("lyric") and len(t["lyric"]) > 80:
            r["ok"] = True
            r["source"] = "embedded"
            r["msg"] = "已内嵌"
            return r
    except Exception:
        t = {}

    # 已缓存
    cached = get_cached(path)
    if cached:
        r["ok"] = True
        r["source"] = "cache"
        r["cached"] = True
        r["msg"] = "已缓存"
        if write_id3:
            r["wrote"] = _write_id3(path, cached)
        return r

    # 解析名字
    title = (t.get("title") or "").strip()
    artist = (t.get("artists") or "").strip()
    if not title:
        a, ti = parse_name(path)
        artist, title = artist or a, ti
    # 元数据颠倒（title==artist，如 "Luis Fonsi"+"Luis Fonsi"）→ 文件名兜底
    if not artist or artist == title:
        try:
            a3, t3 = parse_name(path)
            if t3 and t3 != title:
                artist, title = artist or a3, t3
        except Exception:
            pass

    ly, src = find_lyric(title, artist, log=log)
    # ID3 颠倒（title 放了歌手、artist 放了歌名，实测打分 0.14~0.48 必卡阈值）→ 交换重试
    if not ly and title and artist and title != artist:
        if log:
            log("颠倒重试: %s <-> %s" % (title[:24], artist[:24]))
        ly, src = find_lyric(artist, title, log=log)
        if ly:
            src = (src or "") + "+swap"
    if ly:
        save_cached(path, ly)
        r.update(ok=True, source=src, cached=True, msg="ok")
        if write_id3:
            r["wrote"] = _write_id3(path, ly)
    else:
        r["msg"] = src or "两源无匹配（打分<0.55）"   # find_lyric 失败时第二返回值=原因
    return r


def _write_id3(path, lyric):
    """把歌词写进 ID3 USLT。"""
    try:
        from . import tagger

        ok, _ = tagger.tag(path, lyric=lyric)
        return bool(ok)
    except Exception:
        return False


def batch(paths, write_id3=False, limit=None, log=None, on_progress=None):
    """批量补歌词。返回统计。"""
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
    if os.path.isdir(_LYRIC_DIR):
        for f in os.listdir(_LYRIC_DIR):
            p = os.path.join(_LYRIC_DIR, f)
            try:
                n += 1
                size += os.path.getsize(p)
            except Exception:
                pass
    return {"files": n, "bytes": size}


def cache_clear():
    n = 0
    if os.path.isdir(_LYRIC_DIR):
        for f in os.listdir(_LYRIC_DIR):
            try:
                os.remove(os.path.join(_LYRIC_DIR, f))
                n += 1
            except Exception:
                pass
    return n
