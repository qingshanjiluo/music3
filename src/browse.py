# -*- coding: utf-8 -*-
"""曲库浏览：按目录列曲、模糊查找、单曲删除。"""
from __future__ import annotations

import os

from .models import norm


def list_dirs(root):
    """列出根目录下二级目录及曲数。"""
    out = []
    if not os.path.isdir(root):
        return out
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if not os.path.isdir(p):
            continue
        n = 0
        for dp, _, fs in os.walk(p):
            n += sum(
                1
                for f in fs
                if f.lower().endswith(".mp3")
                and not f.startswith(".tmp_")
                and not f.startswith(".dl_")
            )
        if n:
            out.append({"name": name, "count": n, "path": p})
    return out


def list_tracks(root, sub="", limit=2000, offset=0):
    """列出某子目录下的曲目（相对 root 的路径前缀）。"""
    base = os.path.join(root, sub) if sub else root
    if not os.path.isdir(base):
        return []
    out = []
    for dp, _, fs in os.walk(base):
        for f in sorted(fs):
            if not f.lower().endswith(".mp3"):
                continue
            if f.startswith(".tmp_") or f.startswith(".dl_"):
                continue
            full = os.path.join(dp, f)
            try:
                size = os.path.getsize(full)
            except Exception:
                size = 0
            stem = f[:-4]
            if " - " in stem:
                artist, title = stem.split(" - ", 1)
            else:
                artist, title = "", stem
            out.append(
                {
                    "title": title,
                    "artists": artist,
                    "size": size,
                    "rel": os.path.relpath(full, root),
                    "path": full,
                }
            )
    return out[offset : offset + limit]


def find(root, keyword, limit=100):
    """模糊查找。"""
    kn = norm(keyword)
    if not kn:
        return []
    hits = []
    for dp, _, fs in os.walk(root):
        for f in fs:
            if not f.lower().endswith(".mp3"):
                continue
            if f.startswith(".tmp_") or f.startswith(".dl_"):
                continue
            if kn in norm(f):
                full = os.path.join(dp, f)
                hits.append(
                    {
                        "name": f[:-4],
                        "path": full,
                        "rel": os.path.relpath(full, root),
                        "size": os.path.getsize(full),
                    }
                )
                if len(hits) >= limit:
                    return hits
    return hits


def delete(paths, root, dry=True):
    """删除曲目。仅允许删除 root 内文件。返回 (removed, skipped)。"""
    root_abs = os.path.abspath(root)
    removed, skipped = [], []
    for p in paths:
        ap = os.path.abspath(p)
        if not ap.startswith(root_abs):
            skipped.append((p, "outside root"))
            continue
        if not os.path.exists(ap):
            skipped.append((p, "missing"))
            continue
        if dry:
            removed.append(ap)
            continue
        try:
            os.remove(ap)
            removed.append(ap)
        except Exception as e:
            skipped.append((p, repr(e)[:100]))
    return removed, skipped


def rename_fix(root, dry=True):
    """修复乱码/非法文件名（把 ? 等替换掉），返回改动列表。"""
    import re

    bad = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
    changed = []
    for dp, _, fs in os.walk(root):
        for f in fs:
            if not f.lower().endswith(".mp3"):
                continue
            if bad.search(f):
                new = bad.sub("_", f)
                src = os.path.join(dp, f)
                dst = os.path.join(dp, new)
                ok = False
                if not dry:
                    try:
                        os.rename(src, dst)
                        ok = True
                    except Exception:
                        ok = False
                changed.append((src, dst, ok if not dry else None))
    return changed
