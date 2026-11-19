# -*- coding: utf-8 -*-
"""音频/封面流式响应，支持 Range（拖动进度条）。"""
from __future__ import annotations

import os
import re
import urllib.parse

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def parse_range(header, total):
    """解析 Range 头。返回 (start, end) 或 None（表示整文件）。"""
    if not header:
        return None
    m = RANGE_RE.match(header.strip())
    if not m:
        return None
    s, e = m.group(1), m.group(2)
    if s == "" and e == "":
        return None
    if s == "":
        # 末尾 N 字节
        n = int(e)
        return (max(0, total - n), total - 1)
    start = int(s)
    end = int(e) if e else total - 1
    if start >= total:
        return None
    return (start, min(end, total - 1))


def send_file(handler, path, ctype="audio/mpeg", download_name=None):
    """向 BaseHTTPRequestHandler 发送文件，支持 Range。"""
    if not os.path.exists(path) or not os.path.isfile(path):
        handler.send_response(404)
        handler.send_header("Content-Type", "text/plain; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(b"not found")
        return

    total = os.path.getsize(path)
    rng = parse_range(handler.headers.get("Range"), total)

    if rng:
        start, end = rng
        length = end - start + 1
        handler.send_response(206)
        handler.send_header("Content-Type", ctype)
        handler.send_header("Content-Length", str(length))
        handler.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, total))
        handler.send_header("Accept-Ranges", "bytes")
        handler.send_header("Cache-Control", "public, max-age=3600")
        handler.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            remain = length
            while remain > 0:
                chunk = f.read(min(262144, remain))
                if not chunk:
                    break
                try:
                    handler.wfile.write(chunk)
                except Exception:
                    return
                remain -= len(chunk)
        return

    handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(total))
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("Cache-Control", "public, max-age=3600")
    if download_name:
        enc = urllib.parse.quote(download_name)
        handler.send_header(
            "Content-Disposition",
            "attachment; filename*=UTF-8''%s" % enc,
        )
    handler.end_headers()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(262144)
                if not chunk:
                    break
                handler.wfile.write(chunk)
    except Exception:
        return


def send_bytes(handler, data, ctype="image/jpeg"):
    """发送内存字节（封面等）。"""
    handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "public, max-age=86400")
    handler.end_headers()
    try:
        handler.wfile.write(data)
    except Exception:
        pass


def safe_join(root, rel):
    """把相对路径安全地拼到 root 下，拒绝越界。"""
    root_abs = os.path.abspath(root)
    # 允许 URL 编码的路径
    rel = urllib.parse.unquote(rel or "")
    rel = rel.replace("/", os.sep).replace("\\", os.sep).lstrip(os.sep)
    full = os.path.abspath(os.path.join(root_abs, rel))
    if not full.startswith(root_abs):
        return None
    return full
