# -*- coding: utf-8 -*-
"""统一数据模型。三源搜索结果一律映射为 Track。"""
from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Any

BAD_CHARS = re.compile(r'[\\/:*?"<>|]')


def safe_name(s, limit=120):
    """把任意标题压成 Windows 合法文件名。"""
    if not s:
        return "unknown"
    s = unicodedata.normalize("NFC", str(s))
    s = BAD_CHARS.sub("_", s)
    s = re.sub(r"\s+", " ", s).strip().strip(".")
    if not s:
        return "unknown"
    return s[:limit].rstrip(" ._")


def norm(s):
    """归一化用于比对：繁体转简体，只留字母数字。"""
    if not s:
        return ""
    t = str(s)
    # 常见繁体/日文汉字->简体（B站/QQ 曲库混用）
    tbl = str.maketrans(
        "櫻樱花華話說時後來裡發現實點聲愛戀歸屬夢歲記憶願變讓認識寫聽見桜繪繪圖樂",
        "樱樱花华话说时后来里发现实点声爱恋归属梦岁记忆愿变让认识写听见樱绘绘图乐",
    )
    try:
        t = t.translate(tbl)
    except Exception:
        pass
    return "".join(ch for ch in t.lower() if ch.isalnum())


@dataclass
class Track:
    """统一曲目。三源共用一个形状。"""
    source: str
    track_id: str
    title: str
    artists: str = ""
    album: str = ""
    duration_s: float = 0.0
    ext: str = "mp3"
    size_bytes: int = 0
    url: str = ""
    page_url: str = ""
    lyric: str = ""
    cover_url: str = ""
    score: float = 0.0
    raw: Any = None

    @property
    def duration_str(self):
        if not self.duration_s:
            return "--:--"
        t = int(self.duration_s)
        return "%02d:%02d" % (t // 60, t % 60)

    @property
    def size_str(self):
        if not self.size_bytes:
            return "-"
        return "%.1fMB" % (self.size_bytes / 1048576.0)

    @property
    def display(self):
        a = self.artists or "未知"
        return "%s - %s [%s %s %.2f]" % (
            self.title, a, self.duration_str, self.source, self.score
        )

    def to_dict(self):
        d = asdict(self)
        d.pop("raw", None)
        return d


def to_size(n):
    try:
        return int(n or 0)
    except Exception:
        return 0