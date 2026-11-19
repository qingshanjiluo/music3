# -*- coding: utf-8 -*-
"""重复文件检测 / 清理。"""
from __future__ import annotations

import hashlib
import os

from .models import norm

TMP_PREFIX = (".tmp_", ".dl_")

# 保留优先级：投稿(在用) > 其他 > _归档_封存(存档)
def _keep_rank(p):
    low = p.lower()
    if "\\投稿\\" in low or "/投稿/" in low:
        return 0
    if "_归档" in low or "封存" in low:
        return 2
    return 1


def _mp3s(root):
    out = []
    for dp, _, fs in os.walk(root):
        for f in fs:
            if not f.lower().endswith(".mp3"):
                continue
            if f.startswith(TMP_PREFIX):
                continue
            out.append(os.path.join(dp, f))
    return out


def find_dups(root, by="name"):
    """找重复。

    by='name' : 按「歌手-歌名」归一（快，够用）
    by='hash' : 按文件内容 md5 前 8MB（准，慢）
    返回 [(key, [路径...])...]，只含 >1 个的组。
    """
    groups = {}
    if by == "hash":
        for p in _mp3s(root):
            try:
                h = hashlib.md5()
                with open(p, "rb") as f:
                    h.update(f.read(8 * 1024 * 1024))
                k = h.hexdigest()
            except Exception:
                continue
            groups.setdefault(k, []).append(p)
    else:
        for p in _mp3s(root):
            base = os.path.basename(p)[:-4]
            if " - " in base:
                a, t = base.split(" - ", 1)
            else:
                a, t = "", base
            k = norm(a)[:12] + "|" + norm(t)
            groups.setdefault(k, []).append(p)
    return [(k, v) for k, v in groups.items() if len(v) > 1]


def clean_dups(root, by="name", keep="longest", dry=True):
    """清理重复。keep='longest'|'first'|'shortest'。

    默认 dry=True 只报告不删。
    """
    dups = find_dups(root, by=by)
    removed = []
    for k, paths in dups:
        paths = sorted(paths)
        if keep == "longest":
            paths_sorted = sorted(paths, key=lambda p: (_keep_rank(p), -os.path.getsize(p)))
            keepers, losers = paths_sorted[:1], paths_sorted[1:]
        elif keep == "shortest":
            paths_sorted = sorted(paths, key=lambda p: (_keep_rank(p), os.path.getsize(p)))
            keepers, losers = paths_sorted[:1], paths_sorted[1:]
        else:
            paths_sorted = sorted(paths, key=_keep_rank)
            keepers, losers = paths_sorted[:1], paths_sorted[1:]
        for p in losers:
            removed.append((p, keepers[0]))
            if not dry:
                try:
                    os.remove(p)
                except Exception:
                    pass
    return dups, removed


def find_tmp(root):
    """找残留临时文件。"""
    out = []
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.startswith(TMP_PREFIX) or f.endswith(".part"):
                out.append(os.path.join(dp, f))
    return out


def clean_tmp(root, dry=True):
    found = find_tmp(root)
    if not dry:
        for p in found:
            try:
                os.remove(p)
            except Exception:
                pass
    return found
