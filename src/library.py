# -*- coding: utf-8 -*-
"""曲库管理：索引已有 mp3、查重、路径规划。"""
from __future__ import annotations

import json
import os
import re

from .models import norm, safe_name

DEFAULT_ROOT = r"D:\音乐"
INDEX_NAME = ".music3_index.json"

# 各源默认落盘子目录
SRC_SUBDIR = {
    "bilibili": os.path.join("投稿", "B站"),
    "netease": os.path.join("投稿", "网易云"),
    "qq": os.path.join("投稿", "QQ音乐"),
    "kuwo": os.path.join("投稿", "酷我"),
    "qianqian": os.path.join("投稿", "千千"),
    "migu": os.path.join("投稿", "咪咕"),
}


def index_path(root=DEFAULT_ROOT):
    return os.path.join(root, INDEX_NAME)


def scan(root=DEFAULT_ROOT):
    """扫描根目录全部 mp3，返回 {归一化键: 路径}。跳过 .tmp_ / .dl_ 临时文件。"""
    idx = {}
    if not os.path.isdir(root):
        return idx
    for dirpath, _, files in os.walk(root):
        for f in files:
            low = f.lower()
            if not low.endswith(".mp3"):
                continue
            if f.startswith(".tmp_") or f.startswith(".dl_"):
                continue
            stem = f[:-4]
            base = os.path.basename(stem)
            if " - " in base:
                artist, title = base.split(" - ", 1)
            else:
                artist, title = "", base
            key = norm(artist)[:12] + "|" + norm(title)
            if key not in idx:
                idx[key] = os.path.join(dirpath, f)
    return idx


def load_index(root=DEFAULT_ROOT):
    p = index_path(root)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return scan(root)


def save_index(idx, root=DEFAULT_ROOT):
    try:
        with open(index_path(root), "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=1)
        return True
    except Exception:
        return False


def exists(title, artists, idx):
    """查重：先按 artist|title，再按纯 title。"""
    k1 = norm(artists)[:12] + "|" + norm(title)
    if k1 in idx:
        return idx[k1]
    k2 = norm(title)
    for k, v in idx.items():
        if k.split("|", 1)[-1] == k2:
            return v
    return None


def dest_dir(source, root=DEFAULT_ROOT):
    sub = SRC_SUBDIR.get(source, os.path.join("投稿", "其他"))
    d = os.path.join(root, sub)
    os.makedirs(d, exist_ok=True)
    return d


def count(root=DEFAULT_ROOT):
    """统计各子目录 mp3 数。"""
    out = {}
    if not os.path.isdir(root):
        return out
    for name in os.listdir(root):
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
            out[name] = n
    return out
