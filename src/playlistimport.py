# -*- coding: utf-8 -*-
"""R8: QQ 歌单链接导入 —— Playwright 抽曲目表（title+artist），交给既有搜索打分下载管线。

路径记录（不可用的都留档）：
- musicu.fcg GetSonglist: code=500003（缺 sign）✗
- fcg_get_diss_by_tag: code=0 但 songlist 空 ✗
- 页面 __INITIAL_DATA__: SPA 空壳，服务端渲染无数据 ✗
- JS chunk 里挖接口: 3 chunk 无特征串 ✗
- Playwright 渲染 DOM: .songlist__list li 命中，文本行 OK ✓ （选定）
"""
from __future__ import annotations

import re

_TIMEOUT = 45000
_ROW = "ul[class*=songlist] li, .songlist__list li, .songlist__item"
_TITLE = "h1, .playlist__detail b, [class*=title] b, [class*=title]"
_CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
# "序号 歌名 歌手" | "序号 歌名"（歌手缺失）；跳过分隔行
_LINENO = re.compile(r"^\s*(\d{1,4})\s+(.{1,120})$")
_KEEP = re.compile(r"[一-鿿\w]")


def _chrome():
    import os
    for p in _CHROME:
        if os.path.exists(p):
            return p
    return None


def _parse_rows(texts):
    out = []
    for t in texts:
        t = re.sub(r"\s+", " ", (t or "")).strip()
        m = _LINENO.match(t)
        if not m:
            continue
        body = m.group(2)
        # "歌名 歌手"：歌名在前、歌手尾随 —— SPA 里 title 与 artist 是并排文本节点，
        # 歌名可能带 () 内歌手/版本；拆法：若含中文括号注记，取括号前为主名。
        name, artist = body, ""
        mm = re.match(r"^(.{1,80}?)\s+([^\s].{0,40})$", body)
        # 保守策略：整串交给搜索打分（title+artists 字段拼一起时模糊打分仍能中），
        # 有括号则单独抽出括号内人名作为 artist 提高命中。
        br = re.findall(r"[（(]([^）)]{1,30})[）)]", name)
        if br:
            artist = br[-1]
        if not _KEEP.search(name):
            continue
        out.append({"title": name, "artists": artist, "raw": body})
    # 去重保序
    seen, uniq = set(), []
    for x in out:
        k = re.sub(r"\s", "", x["raw"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(x)
    return uniq


import time as _time
_TOTAL_BUDGET = 70.0


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
    t_begin = _time.time()
    with sync_playwright() as pw:
        if _time.time() - t_begin > _TOTAL_BUDGET:
            return False, "解析超时(%ds)" % _TOTAL_BUDGET, ""
        try:
            kw = {"headless": True, "timeout": 30000,
                  "args": ["--disable-gpu", "--mute-audio", "--no-sandbox"]}
            exe = _chrome()
            if exe:
                kw["executable_path"] = exe
            b = pw.chromium.launch(**kw)
        except Exception as e:
            return False, "浏览器启动失败: %r" % e, ""
        try:
            if _time.time() - t_begin > _TOTAL_BUDGET:
                b.close()
                return False, "浏览器启动超时(>30s)", ""
            p = b.new_page(viewport={"width": 1440, "height": 900})
            p.goto(url, wait_until="domcontentloaded", timeout=25000)
            try:
                p.wait_for_selector(_ROW, timeout=12000)
            except Exception:
                pass
            if _time.time() - t_begin > _TOTAL_BUDGET:
                b.close()
                return False, "DOM 等待超时", ""
            p.wait_for_timeout(400)
            texts = p.eval_on_selector_all(_ROW, "els=>els.map(e=>e.innerText)")
            title = ""
            for sel in (_TITLE,):
                el = p.query_selector(sel)
                if el:
                    try:
                        title = (el.inner_text() or "").strip()[:60]
                    except Exception:
                        title = ""
                if title:
                    break
            p.close()
        except Exception as e:
            try:
                b.close()
            except Exception:
                pass
            return False, "页面加载失败: %r" % e, ""
        finally:
            try:
                b.close()
            except Exception:
                pass
    items = _parse_rows(texts)
    if not items:
        return False, "页面没解析出曲目（歌单可能私有/不存在/需登录）", title
    return True, items, title
