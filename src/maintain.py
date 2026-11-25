# -*- coding: utf-8 -*-
"""维护守护：定时批量补歌词 / 补封面 / 清临时文件，日志落盘。

设计要点：
  - 每次只处理 N 首（默认 20），避免长时间占用网络与磁盘
  - 断点续传：记录上次处理到哪个文件，下次从断点继续
  - 日志轮转：单文件超 1MB 自动换新
  - 单接口：tick() 跑一轮，可被 CLI 循环调用，也可被 Web 定时调用
"""
from __future__ import annotations

import json
import os
import time

from . import config as _cfg, browse

_C = _cfg.load()
_CACHE_DIR = _C.get("cache_dir") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_cache"
)
_STATE = os.path.join(_CACHE_DIR, "maintain_state.json")
_LOG = os.path.join(_CACHE_DIR, "maintain.log")

_MAX_LOG = 1024 * 1024   # 1MB 轮转


def _read_state():
    if not os.path.exists(_STATE):
        return {"cursor": {}, "last_run": 0, "runs": 0, "totals": {"lyric": 0, "cover": 0, "clean": 0}}
    try:
        with open(_STATE, "r", encoding="utf-8") as f:
            d = json.load(f)
        d.setdefault("cursor", {})
        d.setdefault("totals", {"lyric": 0, "cover": 0, "clean": 0})
        return d
    except Exception:
        return {"cursor": {}, "last_run": 0, "runs": 0, "totals": {"lyric": 0, "cover": 0, "clean": 0}}


def _write_state(d):
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        tmp = _STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, _STATE)
        return True
    except Exception:
        return False


def _rotate_log():
    try:
        if os.path.exists(_LOG) and os.path.getsize(_LOG) > _MAX_LOG:
            bak = _LOG + ".1"
            if os.path.exists(bak):
                os.remove(bak)
            os.replace(_LOG, bak)
    except Exception:
        pass


def log(msg, to_file=True):
    """写日志：stderr + 文件。"""
    line = "%s %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        print(line, flush=True)
    except Exception:
        pass
    if not to_file:
        return
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        _rotate_log()
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def tail_log(n=50):
    """读最近 n 行日志。"""
    if not os.path.exists(_LOG):
        return []
    try:
        with open(_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return [x.rstrip("\n") for x in lines[-n:]]
    except Exception:
        return []


def tick(batch=20, sub="", do_lyric=True, do_cover=True, do_clean=True,
         write_id3=True, dry=False):
    """跑一轮维护。返回本轮统计。"""
    from . import lyricfill, coverfill, health, tagreader

    _t0 = time.time()
    st = _read_state()
    res = {"lyric_ok": 0, "lyric_miss": 0, "cover_ok": 0, "cover_miss": 0,
           "cleaned": 0, "scanned": 0, "cursor": "", "done": False}

    # 清临时文件（快，先做）
    if do_clean:
        try:
            tmp = health.clean_tmp(_C.get("root") or "D:\\音乐", dry=dry)
            res["cleaned"] = len(tmp)
            if tmp:
                log("清理临时文件 %d 个" % len(tmp))
        except Exception as e:
            log("清理失败 %r" % (e,))

    # 取曲目列表
    tracks = browse.list_tracks(_C.get("root") or "D:\\音乐", sub, limit=1000000)
    if not tracks:
        log("没有曲目可处理")
        return res

    # 断点：用 cursor[sub] 记录上次文件名
    key = sub or "_all"
    last = st["cursor"].get(key) or ""
    paths = [t["path"] for t in tracks]
    if last:
        try:
            idx = paths.index(last) + 1
            if idx >= len(paths):
                idx = 0   # 转了一圈，从头开始
        except ValueError:
            idx = 0
    else:
        idx = 0

    window = paths[idx: idx + batch]
    res["scanned"] = len(window)
    log("本轮处理 %d 首（从第 %d 首开始，共 %d）" % (len(window), idx + 1, len(paths)))

    for i, p in enumerate(window, 1):
        name = os.path.basename(p)[:40]
        # 补歌词
        if do_lyric:
            try:
                tg = tagreader.read_tags(p)
                if not lyricfill._is_real_lyric(tg.get("lyric") or ""):
                    if not dry:
                        r = lyricfill.fill_one(p, write_id3=write_id3)
                        if r.get("ok"):
                            res["lyric_ok"] += 1
                            log("[%d/%d] 歌词+ %s (%s)" % (i, len(window), name, r.get("source")))
                            st.setdefault("recent", []).insert(0, {"what": "lyric", "name": name, "at": time.time()})
                            del st["recent"][5:]   # 只保最近 5
                        else:
                            res["lyric_miss"] += 1
                            log("[%d/%d] 歌词- %s" % (i, len(window), name))
            except Exception as e:
                log("歌词异常 %s: %r" % (name, e))

        # 补封面
        if do_cover:
            try:
                tg = tagreader.read_tags(p)
                if not tg.get("has_cover"):
                    if not dry:
                        r = coverfill.fill_one(p, write_id3=write_id3)
                        if r.get("ok"):
                            res["cover_ok"] += 1
                            log("[%d/%d] 封面+ %s (%s)" % (i, len(window), name, r.get("source")))
                            st.setdefault("recent", []).insert(0, {"what": "cover", "name": name, "at": time.time()})
                            del st["recent"][5:]   # 只保最近 5
                        else:
                            res["cover_miss"] += 1
            except Exception as e:
                log("封面异常 %s: %r" % (name, e))

    # 更新 cursor
    if window:
        st["cursor"][key] = window[-1]
        res["cursor"] = window[-1]
    res["done"] = (idx + len(window)) >= len(paths)
    st["last_run"] = time.time()
    st["runs"] = int(st.get("runs", 0)) + 1
    for k, kk in (("lyric_ok", "lyric"), ("cover_ok", "cover"), ("cleaned", "clean")):
        st["totals"][kk] = int(st["totals"].get(kk, 0)) + res[k]
    st["last"] = {"lyric_ok": res["lyric_ok"], "cover_ok": res["cover_ok"],
                  "cleaned": res["cleaned"], "scanned": res.get("scanned", 0), "at": time.time()}    # runs 趋势: 记近 8 次每轮 runs(供前端迷你 sparkline), 满 8 截尾
    trend = st.get("trend", [])
    trend.append(int(st["runs"]))
    st["trend"] = trend[-8:]
    # 累计补歌词/封面趋势: 近 8 次累计值(看累计爬升斜率), 满 8 截尾
    ct = st.get("cum_trend", [])
    ct.append({"lyric": int(st["totals"].get("lyric", 0)), "cover": int(st["totals"].get("cover", 0))})
    st["cum_trend"] = ct[-8:]
    # 异常率趋势: 本轮 miss 率 = (lyric_miss+cover_miss)/scanned (供异常率卡 sparkline), 满 8 截尾
    _scanned = int(res.get("scanned", 0))
    _miss = int(res.get("lyric_miss", 0)) + int(res.get("cover_miss", 0))
    _rate = round(_miss * 100.0 / _scanned, 1) if _scanned else 0.0
    rt = st.get("rate_trend", [])
    rt.append(_rate)
    st["rate_trend"] = rt[-8:]
    # 本批耗时趋势: 本轮 tick 用时(秒, 1 位小数), 近 8 次(供耗时卡 sparkline), 满 8 截尾
    _dur = round(time.time() - _t0, 1)
    res["duration"] = _dur
    dt = st.get("dur_trend", [])
    dt.append(_dur)
    st["dur_trend"] = dt[-8:]
    _write_state(st)

    log("本轮完成: 歌词+%d 歌词-%d 封面+%d 封面-%d 清理%d"
        % (res["lyric_ok"], res["lyric_miss"], res["cover_ok"], res["cover_miss"], res["cleaned"]))
    return res


def status():
    """当前维护状态。"""
    st = _read_state()
    s = {
        "recent": st.get("recent", []),
        "runs": st.get("runs", 0),
        "last_run": st.get("last_run", 0),
        "last_run_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st["last_run"])) if st.get("last_run") else "",
        "totals": st.get("totals", {}),
        "cursor": st.get("cursor", {}),
        "log_lines": len(tail_log(99999)),
        "last": st.get("last", {}),
        "trend": st.get("trend", []),
        "cum_trend": st.get("cum_trend", []),
        "rate_trend": st.get("rate_trend", []),
        "dur_trend": st.get("dur_trend", []),
    }
    return s


def reset_cursor():
    st = _read_state()
    st["cursor"] = {}
    _write_state(st)
    return True
