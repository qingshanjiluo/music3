# -*- coding: utf-8 -*-
"""收藏歌单：在线搜索结果 + 本地曲目的收藏，原子落盘 _cache/favs.json。"""
from __future__ import annotations

import json
import os

from . import config as _cfg
from .models import norm

_C = _cfg.load()
_DIR = _C.get("cache_dir") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_cache"
)
_PATH = os.path.join(_DIR, "favs.json")


def key_of(item):
    if item.get("rel"):
        return "lib|" + item["rel"]
    return "%s|%s|%s" % (item.get("source", ""),
                        norm(item.get("title", "")),
                        norm(item.get("artists", "")))


def _read():
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, list):
            return d
    except Exception:
        pass
    return []


def _write(items):
    try:
        os.makedirs(_DIR, exist_ok=True)
        tmp = _PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=1)
        os.replace(tmp, _PATH)
        return True
    except Exception:
        return False


def list_items():
    return _read()


def add(item):
    """收藏一首；已存在则更新字段不重复。返回 (items, added)。"""
    if not item or not (item.get("title") or item.get("rel")):
        return _read(), False
    items = _read()
    k = key_of(item)
    for it in items:
        if key_of(it) == k:
            it.update({kk: vv for kk, vv in item.items() if vv})
            _write(items)
            return items, False
    item["key"] = k
    item["at"] = __import__("time").strftime("%Y-%m-%d %H:%M:%S")
    items.append(item)
    _write(items)
    return items, True


def add_many(rows):
    added = 0
    for r in rows or []:
        _, ok = add(r)
        added += 1 if ok else 0
    return _read(), added


def remove(key):
    items = [x for x in _read() if x.get("key") != key and key_of(x) != key]
    _write(items)
    return items


def clear():
    _write([])
    return []


def keys():
    return [key_of(x) for x in _read()]
