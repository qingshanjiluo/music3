# -*- coding: utf-8 -*-
"""音频标签写入：ID3 标题/歌手/专辑 + 封面 + 歌词。"""
from __future__ import annotations

import os

import requests

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import (
        ID3,
        APIC,
        TIT2,
        TPE1,
        TALB,
        TDRC,
        USLT,
        ID3NoHeaderError,
    )

    HAS_MUTAGEN = True
except Exception:
    HAS_MUTAGEN = False

_S = requests.Session()
_S.trust_env = False
_S.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Referer": "https://music.163.com/",
    }
)


def _get_bytes(url, timeout=30):
    if not url:
        return b""
    try:
        r = _S.get(url, timeout=timeout)
        if r.status_code == 200 and r.content:
            return r.content
    except Exception:
        pass
    return b""


def tag(path, title="", artists="", album="", cover_url="", lyric="", source="", year=""):
    """写 ID3。失败不影响音频可用性，返回 (ok, msg)。"""
    if not HAS_MUTAGEN:
        return False, "no mutagen"
    if not os.path.exists(path):
        return False, "no file"
    try:
        try:
            audio = MP3(path, ID3=ID3)
            tags = audio.tags
            if tags is None:
                audio.add_tags()
                tags = audio.tags
        except ID3NoHeaderError:
            tags = ID3()
            audio = MP3(path)
            audio.tags = tags

        if title:
            tags.delall("TIT2")
            tags.add(TIT2(encoding=3, text=[title]))
        if artists:
            tags.delall("TPE1")
            tags.add(TPE1(encoding=3, text=[artists]))
        if album:
            tags.delall("TALB")
            tags.add(TALB(encoding=3, text=[album]))
        if year:
            tags.delall("TDRC")
            tags.add(TDRC(encoding=3, text=[year]))
        if lyric:
            tags.delall("USLT")
            tags.add(USLT(encoding=3, lang="chi", desc="", text=lyric))
        if cover_url:
            data = _get_bytes(cover_url)
            if data:
                tags.delall("APIC")
                tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=data,
                    )
                )
        audio.save(v2_version=3)
        return True, "tagged"
    except Exception as e:
        return False, repr(e)[:200]
