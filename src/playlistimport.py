# -*- coding: utf-8 -*-
"""R9: playlistimport 多站点适配 —— QQ 主 DOM + 网易 iframe 内嵌 + B站通用。

站点策略（R8/R9 实测留档）：
- y.qq.com: 主 frame `ul[class*=songlist] li`（行="序号 歌名 歌手"）✓ 12 首 25.1s
- music.163.com: 内容在 iframe[1]（`#/playlist` 外壳内嵌真页），`.m-table tbody tr` 200 行 ✓
  —— 注意外层 frame 是导航菜单(13 li)，必须遍历 frames 否则误抓
- bilibili.com: 通用 `li` 兜底
死路留档: musicu 缺 sign 500003 / fcg 空表 / SPA 空壳 {}/ JS chunk 无串。
"""
from __future__ import annotations

import re
import time as _time

_TIMEOUT = 30000
_TOTAL_BUDGET = 70.0
_CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
_KEEP = re.compile(r"[一-鿿぀-ヿ가-힯\w]")

# 站点 → (行选择器候选, 标题选择器候选)
_SITE = {
    "qq": (["ul[class*=songlist] li", ".songlist__list li", ".songlist__item"],
           ["h1", ".playlist__detail b", "[class*=title] b"]),
    "netease": (["tr.m-table", ".m-table tbody tr", "#song-list-pre-cache li", ".f-hide li"],
                [".m-tit b", "h1", "h2"]),
    "bili": (["li", ".video-item li"], ["h1"]),
}
_LINENO = re.compile(r"^\s*(\d{1,4})\s+(.{1,120})$")
_NERO = re.compile(r"^\s*(\d{1,4})\s+(.{1,90}?)\s+\d{1,2}:\d{2}\b\s*(.*)$")


def _chrome():
    import os
    for p in _CHROME:
        if os.path.exists(p):
            return p
    return None


def _site_of(url):
    if "music.163.com" in url:
        return "netease"
    if "bilibili.com" in url:
        return "bili"
    return "qq"


def _parse_rows(texts, site):
    out = []
    for t in texts:
        t = re.sub(r"\s+", " ", (t or "")).strip()
        if not t:
            continue
        name, artist = "", ""
        if site == "netease":
            m = _NERO.match(t)
            if m:
                name, artist = m.group(2).strip(), m.group(3).strip()
        if not name:
            m = _LINENO.match(t)
            if not m:
                continue
            body = m.group(2)
            name = body
            br = re.findall(r"[（(]([^）)]{1,30})[）)]", body)
            if br:
                artist = br[-1]
        if not name or not _KEEP.search(name):
            continue
        out.append({"title": name, "artists": artist, "raw": t})
    seen, uniq = set(), []
    for x in out:
        k = re.sub(r"\s", "", x["raw"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(x)
    return uniq


def _grab(page, sels):
    """遍历所有 frame 按序试选择器，首个 n>=3 命中返回 (texts, selector)。"""
    fr_attr = page.frames
    frames = list(fr_attr() if callable(fr_attr) else fr_attr) or [page]
    for fr in frames:
        for sel in sels:
            try:
                n = fr.eval_on_selector_all(sel, "e=>e.length")
            except Exception:
                n = 0
            if n >= 3:
                texts = fr.eval_on_selector_all(sel, "els=>els.map(e=>e.innerText)")
                return texts, sel
    # 复合选择器兜底（单选器 class 变体全部失败时，一次命中任一即可）
    combo = ", ".join(sels)
    for fr in frames:
        try:
            n = fr.eval_on_selector_all(combo, "e=>e.length")
        except Exception:
            n = 0
        if n >= 3:
            texts = fr.eval_on_selector_all(combo, "els=>els.map(e=>e.innerText)")
            return texts, "combo:" + combo[:50]
    return [], ""


def _netease_api(url):
    """网易歌单 API 直取：/api/v6/playlist/detail（0.3s 原文标题）。
    返回 None = 非网易歌单 URL / API 挂了（落 Playwright）；否则 (ok, items, title)。"""
    m = re.search(r"[?&]id=(\d+)", url)
    if not m:
        return None
    pid = m.group(1)
    try:
        import requests as _rq
    except Exception:
        return None
    try:
        _s = _rq.Session()
        _s.trust_env = False  # 不吃操作者本机代理
        r = _s.get("http://music.163.com/api/v6/playlist/detail",
                   params={"id": pid, "n": "200"},
                   headers={"User-Agent": "Mozilla/5.0 Chrome/120",
                            "Referer": "http://music.163.com/"},
                   timeout=10)
        j = r.json()
    except Exception as e:
        return False, "网易歌单 API 失败: %r" % e, ""
    if j.get("code") != 200:
        return False, "网易歌单 API code=%s（歌单可能不存在）" % j.get("code"), ""
    pl = j.get("playlist") or {}
    tracks = pl.get("tracks") or []
    if not tracks:
        return False, "歌单为空（trackIds=%d）" % len(pl.get("trackIds") or []), ""
    items = []
    for t in tracks:
        title = (t.get("name") or "").strip()
        ars = t.get("ar") or t.get("artists") or []
        artists = "、".join((a.get("name") or "") for a in ars if a.get("name"))
        if not title:
            continue
        items.append({"title": title, "artists": artists,
                       "raw": (title + " " + artists).strip()})
    if not items:
        return False, "0 首有效曲目", ""
    return True, items, (pl.get("name") or "")[:60]


def parse_url(url):
    """返回 (ok, items_or_error, playlist_title)。"""
    if not url or not url.startswith(("http://", "https://")):
        return False, "URL 必须以 http(s):// 开头", ""
    host_ok = "y.qq.com" in url or "music.163.com" in url or "bilibili.com" in url
    if not host_ok:
        return False, "仅支持 y.qq.com / music.163.com / bilibili.com 歌单页", ""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        return False, "playwright 未安装: %r" % e, ""
    site = _site_of(url)
    # ---- 网易优先 API 直取（0.3s / 原文标题 / 无反爬）----
    if site == "netease":
        got = _netease_api(url)
        if got is not None:
            ok2, items2, title2 = got
            if ok2 or "反爬" not in str(items2):
                return got
            # API 失败但非反爬原因才落 Playwright；反爬直接透传
    row_sels, ttl_sels = _SITE[site]
    t_begin = _time.time()
    with sync_playwright() as pw:
        try:
            kw = {"headless": True, "timeout": 30000,
                  "args": ["--disable-gpu", "--mute-audio", "--no-sandbox"]}
            exe = _chrome()
            if exe:
                kw["executable_path"] = exe
            b = None
            for attempt in (0, 1):
                try:
                    b = pw.chromium.launch(**kw)
                    break
                except Exception:
                    if attempt == 0:
                        _time.sleep(1.5)  # 上个实例还在退，等 1.5s 再试
                        continue
                    raise
        except Exception as e:
            return False, "浏览器启动失败: %r" % e, ""
        try:
            p = b.new_page(viewport={"width": 1440, "height": 900})
            p.goto(url, wait_until="domcontentloaded", timeout=25000)
            if _time.time() - t_begin > _TOTAL_BUDGET:
                return False, "页面加载超时", ""
            try:
                p.wait_for_selector(row_sels[0], timeout=12000)
            except Exception:
                pass
            if _time.time() - t_begin > _TOTAL_BUDGET:
                return False, "DOM 等待超时", ""
            p.wait_for_timeout(500)
            texts, hit_sel = _grab(p, row_sels)
            title = ""
            for fr in list(p.frames) + [p]:
                for ts in ttl_sels:
                    try:
                        e2 = fr.query_selector(ts)
                        if e2:
                            title = (e2.inner_text() or "").strip()[:60]
                            break
                    except Exception:
                        pass
                if title:
                    break
            p.close()
        except Exception as e:
            return False, "页面加载失败: %r" % e, ""
        finally:
            try:
                b.close()
            except Exception:
                pass
    items = _parse_rows(texts, site)
    # 网易字体反爬：title 里 PUA 区(琋-)/替换符比例高 = 拆字乱码，打分搜不到
    if site == "netease" and items:
        bad = 0
        for it in items:
            t = it.get("title") or ""
            if not t:
                continue
            weird = sum(1 for ch in t
                        if "\ue000" <= ch <= "\uf8ff" or ch == "\ufffd")
            # 拉丁字母被拆散混入 CJK 中间也算特征（如 "Follo y w"）
            mixed = bool(re.search(r"[\u4e00-\u9fff][A-Za-z]|[A-Za-z][\u4e00-\u9fff]", t))
            if weird * 2 >= len(t) or (mixed and weird > 0):
                bad += 1
        if bad * 2 >= len(items):
            return False, ("网易歌单页有字体反爬（headless 拿到拆字乱码，%d/%d 行受损）"
                           "——请用 QQ 或 B 站歌单链接，或在搜索页逐首下" % (bad, len(items))), title
    if not items:
        return False, "页面没解析出曲目（私有/不存在/需登录/选择器 %s）" % (hit_sel or "无"), title
    return True, items, title
