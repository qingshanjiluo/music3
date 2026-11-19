# -*- coding: utf-8 -*-
"""music3 命令行入口。

用法:
  python -m src.cli search "晴天 周杰伦"            # 搜全部源
  python -m src.cli search "晴天" -s qq,netease     # 指定源
  python -m src.cli get "晴天 周杰伦"               # 搜+下第一首
  python -m src.cli get "晴天 周杰伦" -n 3          # 下前三首
  python -m src.cli dl BV1xx411c7mD                 # 直接下B站
  python -m src.cli batch list.txt                  # 批量
  python -m src.cli stat                            # 曲库统计
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "src"

# 压制 musicdl / rich 的进度条噪声（rich 走 fd2，需重定向）
import logging

logging.getLogger("musicdl").setLevel(logging.ERROR)
os.environ.setdefault("TQDM_DISABLE", "1")


class _Null:
    def write(self, *a, **k):
        return 0

    def flush(self):
        pass

    def isatty(self):
        return False


def quiet_stderr(enable=True):
    """给 musicdl 用：把 fd2 指向 NUL，返回恢复函数。"""
    if not enable:
        return lambda: None
    try:
        import io

        saved = os.dup(2)
        nul = os.open(os.devnull, os.O_WRONLY)
        os.dup2(nul, 2)
        os.close(nul)

        def restore():
            try:
                os.dup2(saved, 2)
                os.close(saved)
            except Exception:
                pass

        return restore
    except Exception:
        return lambda: None

from src import router, library, downloader, src_bili
from src.models import Track, norm


def _log(msg):
    print("[*] %s" % msg, flush=True)


def cmd_search(args):
    res = router.search(
        args.keyword,
        sources=[s.strip() for s in args.sources.split(",")] if args.sources else None,
        limit=args.limit,
        bili=not args.no_bili,
        log=_log if args.verbose else None,
    )
    if not res:
        print("无结果")
        return 1
    print("\n%-3s %-6s %-8s %-9s %s" % ("#", "分数", "时长", "来源", "标题 - 歌手"))
    for i, t in enumerate(res[: args.top], 1):
        print(
            "%-3d %-6.2f %-8s %-9s %s - %s"
            % (i, t.score, t.duration_str, t.source, t.title, t.artists)
        )
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in res], f, ensure_ascii=False, indent=1)
        print("\n已写 %s" % args.json)
    return 0


def cmd_get(args):
    idx = library.scan(args.root)
    res = router.search(
        args.keyword,
        sources=[s.strip() for s in args.sources.split(",")] if args.sources else None,
        limit=args.limit,
        bili=not args.no_bili,
        log=_log if args.verbose else None,
    )
    if not res:
        print("无结果")
        return 1
    okc = 0
    for i, t in enumerate(res[: args.n], 1):
        print("\n[%d/%d] %s" % (i, min(args.n, len(res)), t.display))
        old = library.exists(t.title, t.artists, idx)
        if old and not args.force:
            print("    已存在 -> %s" % old)
            okc += 1
            continue
        d = library.dest_dir(t.source, args.root)
        ok, msg, path = downloader.download(t, d)
        print("    %s | %s" % ("OK" if ok else "FAIL", msg))
        if ok:
            okc += 1
            print("    -> %s" % path)
            idx[norm(t.artists)[:12] + "|" + norm(t.title)] = path
        if i < len(res) and args.wait:
            time.sleep(args.wait)
    library.save_index(idx, args.root)
    print("\n完成: %d/%d" % (okc, min(args.n, len(res))))
    return 0 if okc else 1


def cmd_dl(args):
    t = Track(
        source="bilibili",
        track_id=args.bvid,
        title=args.bvid,
        artists="B站",
        page_url="https://www.bilibili.com/video/%s" % args.bvid,
    )
    if args.title:
        t.title = args.title
    d = library.dest_dir("bilibili", args.root)
    ok, msg, path = downloader.download(t, d)
    print("%s | %s" % ("OK" if ok else "FAIL", msg))
    if path:
        print("-> %s" % path)
    return 0 if ok else 1


def cmd_batch(args):
    if not os.path.exists(args.file):
        print("文件不存在: %s" % args.file)
        return 1
    with open(args.file, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    print("共 %d 条" % len(lines))
    for i, kw in enumerate(lines, 1):
        print("\n=== [%d/%d] %s ===" % (i, len(lines), kw))
        ns = argparse.Namespace(**vars(args))
        ns.keyword = kw
        ns.n = args.n
        try:
            cmd_get(ns)
        except Exception as e:
            print("ERR %r" % (e,))
        if i < len(lines):
            time.sleep(args.gap)
    return 0


def cmd_stat(args):
    c = library.count(args.root)
    if not c:
        print("空")
        return 0
    tot = 0
    for k, v in sorted(c.items(), key=lambda x: -x[1]):
        print("%-20s %6d" % (k, v))
        tot += v
    print("%-20s %6d" % ("合计", tot))
    return 0


def cmd_artist(args):
    """歌手全量抓取。"""
    from . import artist as art

    kwargs = {"sources": [s.strip() for s in args.sources.split(",")] if args.sources else None}
    if args.mid:
        kwargs["mid"] = args.mid
    tracks = art.collect_artist(args.name, log=_log if args.verbose else None, **kwargs)
    if not tracks:
        print("无结果")
        return 1
    print("找到 %d 首" % len(tracks))
    for i, t in enumerate(tracks[: args.top], 1):
        print("%-3d %-8s %-9s %s - %s" % (i, t.duration_str, t.source, t.title, t.artists))
    if args.download:
        from . import queue as q

        kws = [t.title for t in tracks[: args.limit]]
        stats = q.run(
            kws,
            workers=args.workers,
            per_kw=1,
            sources=[s.strip() for s in args.sources.split(",")] if args.sources else None,
            bili=False,
            root=args.root,
            progress=_log if args.verbose else None,
        )
        print("\n下载统计: %r" % (stats,))
    return 0


def cmd_queue(args):
    """批量队列下载（并发+重试）。"""
    from . import queue as q

    if os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            kws = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    else:
        kws = [k.strip() for k in args.file.split(",") if k.strip()]
    print("队列 %d 条，并发 %d" % (len(kws), args.workers))
    st = q.run(
        kws,
        workers=args.workers,
        per_kw=args.n,
        sources=[s.strip() for s in args.sources.split(",")] if args.sources else None,
        bili=not args.no_bili,
        retries=args.retries,
        root=args.root,
        progress=_log,
        force=args.force,
    )
    print("\n结果: 成功 %(ok)d / 跳过 %(skip)d / 失败 %(fail)d / 共 %(total)d" % st)
    return 0 if st["ok"] or st["skip"] else 1


def cmd_cache(args):
    """搜索缓存管理。"""
    from . import cache

    if args.clear:
        n = cache.clear()
        print("已清 %d 个缓存文件" % n)
        return 0
    import os

    d = os.path.join(cache._CACHE_DIR, "search")
    n = len([f for f in os.listdir(d) if f.endswith(".json")]) if os.path.isdir(d) else 0
    print("缓存条目 %d（TTL 30 分钟）" % n)
    print("清空: python -X utf8 run.py cache --clear")
    return 0


def cmd_ls(args):
    """列目录或曲目。"""
    from . import browse

    if not args.sub:
        rows = browse.list_dirs(args.root)
        if not rows:
            print("空")
            return 0
        tot = 0
        for r in rows:
            print("%-24s %6d" % (r["name"], r["count"]))
            tot += r["count"]
        print("%-24s %6d" % ("合计", tot))
        return 0
    tracks = browse.list_tracks(args.root, args.sub, limit=args.num, offset=args.offset)
    if not tracks:
        print("无曲目: %s" % args.sub)
        return 1
    for i, t in enumerate(tracks, 1 + args.offset):
        print("%-4d %-8s %s" % (i, "%.1fMB" % (t["size"] / 1048576.0), t["rel"]))
    return 0


def cmd_find(args):
    """模糊查找。"""
    from . import browse

    hits = browse.find(args.root, args.keyword, limit=args.num)
    if not hits:
        print("未找到: %s" % args.keyword)
        return 1
    print("命中 %d 条:" % len(hits))
    for h in hits:
        print("  %-8s %s" % ("%.1fMB" % (h["size"] / 1048576.0), h["rel"]))
    return 0


def cmd_rm(args):
    """删除曲目（默认预览）。"""
    from . import browse

    hits = browse.find(args.root, args.keyword, limit=100)
    if not hits:
        print("未找到: %s" % args.keyword)
        return 1
    paths = [h["path"] for h in hits]
    print("%s %d 个:" % ("将删" if not args.yes else "删除", len(paths)))
    removed, skipped = browse.delete(paths, args.root, dry=not args.yes)
    for p in removed:
        print("  %s" % p)
    for p, why in skipped:
        print("  跳过 %s (%s)" % (p, why))
    if not args.yes:
        print("\n加 --yes 才会真删")
    return 0


def cmd_maintain(args):
    """维护守护：跑一轮或循环。"""
    from . import maintain

    if args.reset:
        maintain.reset_cursor()
        print("游标已重置")

    if args.status:
        s = maintain.status()
        print("已跑 %d 轮，上次 %s" % (s["runs"], s["last_run_str"] or "从未"))
        t = s.get("totals") or {}
        print("累计: 歌词 %s / 封面 %s / 清理 %s" % (t.get("lyric", 0), t.get("cover", 0), t.get("clean", 0)))
        if s.get("cursor"):
            print("断点:")
            for k, v in s["cursor"].items():
                print("  %s -> %s" % (k, os.path.basename(v)))
        print("日志行数: %d" % s["log_lines"])
        if args.tail:
            print("\n=== 最近 %d 行 ===" % args.tail)
            for line in maintain.tail_log(args.tail):
                print("  " + line)
        return 0

    rounds = args.rounds
    i = 0
    while True:
        i += 1
        print("\n===== 第 %d 轮 =====" % i)
        r = maintain.tick(
            batch=args.batch,
            sub=args.sub or "",
            do_lyric=not args.no_lyric,
            do_cover=not args.no_cover,
            do_clean=not args.no_clean,
            write_id3=not args.no_write,
            dry=args.dry,
        )
        if r["done"]:
            print("\n已跑完全库一轮")
            break
        if rounds and i >= rounds:
            break
        time.sleep(args.gap)
    return 0


def cmd_cover(args):
    """批量补封面。"""
    from . import coverfill, browse

    if args.file:
        paths = [args.file]
    else:
        paths = [t["path"] for t in browse.list_tracks(args.root, args.sub or "", limit=1000000)]
    if not paths:
        print("没有找到曲目")
        return 1
    print("共 %d 首，开始补封面（写回 ID3=%s）…" % (len(paths), not args.no_write))

    def prog(i, n, p, r):
        if args.verbose or i % 20 == 0 or i == n:
            name = os.path.basename(p)[:36]
            print("[%d/%d] %-38s %s" % (i, n, name, r.get("source") or ("skip" if r.get("ok") else "miss")))

    st = coverfill.batch(
        paths, write_id3=(not args.no_write), limit=args.limit or None, on_progress=prog
    )
    print("\n结果: 成功 %(ok)d / 缺失 %(miss)d / 写回ID3 %(wrote)d / 共 %(total)d" % st)
    if st.get("by_source"):
        print("来源分布:", ", ".join("%s=%d" % (k, v) for k, v in st["by_source"].items()))
    return 0


def cmd_cover_cache(args):
    """封面缓存管理。"""
    from . import coverfill

    if args.clear:
        n = coverfill.cache_clear()
        print("已清 %d 个封面缓存" % n)
        return 0
    s = coverfill.cache_stats()
    print("封面缓存: %d 个文件，%.1f KB" % (s["files"], s["bytes"] / 1024))
    print("清空: python -X utf8 run.py cover-cache --clear")
    return 0


def cmd_health(args):
    """库健康检查。"""
    from . import health

    r = health.scan(args.root, args.sub or "", limit=args.limit or None, deep=args.deep)
    print("库: %s%s  共 %d 首  %.1f MB" % (
        args.root, ("\\" + args.sub) if args.sub else "", r["total"], r["total_size_mb"]))
    print("健康分: %.1f / 100%s\n" % (r["score"], "（深度）" if args.deep else "（快速）"))
    for k, v in r["summary"].items():
        mark = "·" if v == 0 else "!"
        print("  %s %-10s %d" % (mark, k, v))

    def _show(name, items, fmt):
        if not items:
            return
        print("\n%s （前 %d/%d）:" % (name, min(10, len(items)), len(items)))
        for x in items[:10]:
            print("   " + fmt(x))

    if args.detail:
        _show("缺歌词", r["no_lyric"], lambda x: x["rel"][:70])
        _show("无封面", r["no_cover"], lambda x: x["rel"][:70])
        _show("命名异常", r["bad_name"], lambda x: "%s | %s" % (x["rel"][:50], x["why"]))
        _show("无歌手", r["no_artist"], lambda x: x["rel"][:70])
        _show("文件过小", r["tiny"], lambda x: "%s | %d B" % (x["rel"][:56], x.get("size") or 0))
        _show("重复", r["dups"], lambda x: "%s\n     A: %s\n     B: %s" % (x["key"], x["a"][:54], x["b"][:54]))
    return 0


def cmd_fixname(args):
    """修文件名非法字符。"""
    from . import health

    rows = health.fix_names(args.root, dry=not args.yes)
    if not rows:
        print("没有需要修的命名")
        return 0
    print("%s %d 个:" % ("将改" if not args.yes else "已改", len(rows)))
    for src, dst, ok in rows[:30]:
        print("  %s\n    -> %s" % (os.path.basename(src), os.path.basename(dst)))
    if not args.yes:
        print("\n加 --yes 才真改")
    return 0


def cmd_export(args):
    """导出歌单或库清单。"""
    from . import export, browse

    fmt = (args.format or "m3u8").lower()
    try:
        if args.all:
            paths = [t["path"] for t in browse.list_tracks(args.root, args.sub or "", limit=1000000)]
        elif args.playlist:
            from . import playlist as PL

            d = PL.get()
            paths = []
            for it in d.get("items") or []:
                p = os.path.join(args.root, it["rel"].replace("/", os.sep))
                if os.path.exists(p):
                    paths.append(p)
        else:
            paths = [t["path"] for t in browse.list_tracks(args.root, args.sub or "", limit=1000000)]

        if not paths:
            print("没有可导出的曲目")
            return 1

        if fmt == "m3u8":
            text = export.to_m3u8(paths, args.root)
        elif fmt == "json":
            text = export.to_json(paths, args.root, include_lyric=args.detail)
        elif fmt == "csv":
            text = export.to_csv(paths, args.root)
        elif fmt == "index":
            text = export.to_json([], args.root)  # placeholder
            import json as _j

            text = _j.dumps(export.library_index(args.root, args.sub or ""), ensure_ascii=False, indent=1)
        else:
            print("未知格式: %s（支持 m3u8 / json / csv / index）" % fmt)
            return 1

        out = args.output or os.path.join(
            args.root, "music3_export_%s.%s" % (time.strftime("%Y%m%d_%H%M%S"), "json" if fmt == "index" else fmt)
        )
        ok = export.write_file(out, text)
        if ok:
            print("已导出 %d 首 -> %s (%d 字节)" % (len(paths) if fmt != "index" else 0, out, len(text.encode("utf-8"))))
        else:
            print("写入失败: %s" % out)
            return 1
        return 0
    except Exception as e:
        print("导出失败: %r" % (e,))
        return 1


def cmd_lyric(args):
    """批量补歌词。"""
    from . import lyricfill, browse

    if args.file:
        paths = [args.file]
    else:
        sub = args.sub or ""
        paths = [t["path"] for t in browse.list_tracks(args.root, sub, limit=100000)]
    if not paths:
        print("没有找到曲目")
        return 1
    print("共 %d 首，开始补歌词（写回 ID3=%s）…" % (len(paths), args.write))

    def prog(i, n, p, r):
        if args.verbose or i % 20 == 0 or i == n:
            name = p.split("\\")[-1][:36]
            print("[%d/%d] %-38s %s" % (i, n, name, r.get("source") or ("skip" if r.get("ok") else "miss")))

    st = lyricfill.batch(
        paths,
        write_id3=args.write,
        limit=args.limit or None,
        on_progress=prog,
    )
    print("\n结果: 成功 %(ok)d / 缺失 %(miss)d / 写回ID3 %(wrote)d / 共 %(total)d" % st)
    if st.get("by_source"):
        print("来源分布:", ", ".join("%s=%d" % (k, v) for k, v in st["by_source"].items()))
    return 0


def cmd_lyric_cache(args):
    """歌词缓存管理。"""
    from . import lyricfill

    if args.clear:
        n = lyricfill.cache_clear()
        print("已清 %d 个歌词缓存" % n)
        return 0
    s = lyricfill.cache_stats()
    print("歌词缓存: %d 个文件，%.1f KB" % (s["files"], s["bytes"] / 1024))
    print("清空: python -X utf8 run.py lyric-cache --clear")
    return 0


def cmd_resume(args):
    """续跑上次中断的批量任务。"""
    from . import queue as q

    st = q.resume_queue(
        root=args.root,
        workers=(args.workers or None),
        progress=_log,
        force=args.force,
    )
    if st is None:
        print("没有待续任务（清单不存在）")
        return 1
    print("\n结果: 成功 %(ok)d / 跳过 %(skip)d / 失败 %(fail)d / 共 %(total)d" % st)
    return 0


def cmd_pending(args):
    """查看未完成任务。"""
    from . import persist

    d = persist.load(args.root)
    if not d:
        print("无待办清单")
        return 0
    tasks = d.get("tasks") or []
    pend = [t for t in tasks if t.get("state") == "pending"]
    done = [t for t in tasks if t.get("state") == "done"]
    fail = [t for t in tasks if t.get("state") == "fail"]
    print("总计 %d | 未完成 %d | 已完成 %d | 失败 %d" % (len(tasks), len(pend), len(done), len(fail)))
    meta = d.get("meta") or {}
    if meta:
        print("参数: n=%s sources=%s bili=%s workers=%s"
              % (meta.get("n"), ",".join(meta.get("sources") or []),
                 meta.get("bili"), meta.get("workers")))
    if pend:
        print("\n未完成:")
        for t in pend[:30]:
            print("  %s" % t["kw"])
        if len(pend) > 30:
            print("  … 还有 %d 条" % (len(pend) - 30))
    if fail:
        print("\n失败:")
        for t in fail[:10]:
            print("  %-24s | %s" % (t["kw"], (t.get("err") or "")[:60]))
    return 0


def cmd_pending_clear(args):
    """清空任务清单。"""
    from . import persist

    ok = persist.clear(args.root)
    print("已清空" if ok else "清理失败")
    return 0


def cmd_dup(args):
    """重复/临时文件检测与清理。"""
    from . import dedup

    dups, removed = dedup.clean_dups(
        args.root, by=args.by, keep=args.keep, dry=not args.clean
    )
    print("重复组 %d" % len(dups))
    for k, paths in dups[: args.top]:
        print("  %s" % k)
        for p in paths:
            print("    %s" % p)
    if removed:
        print("\n%s %d 个:" % ("将删" if not args.clean else "已删", len(removed)))
        for p, kept in removed[: args.top]:
            print("  %s\n    <- 保留 %s" % (p, kept))
    tmp = dedup.clean_tmp(args.root, dry=not args.clean)
    if tmp:
        print("\n临时残留 %d 个%s" % (len(tmp), "（--clean 清理）" if not args.clean else " 已删"))
        for p in tmp[:10]:
            print("  %s" % p)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="music3", description="B站/网易云/QQ 三源音乐工具")
    p.add_argument("--root", default=library.DEFAULT_ROOT, help="音乐根目录")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="搜索")
    s.add_argument("keyword")
    s.add_argument("-s", "--sources", default="", help="qq,netease,bilibili,kuwo...")
    s.add_argument("-l", "--limit", type=int, default=15)
    s.add_argument("-t", "--top", type=int, default=20)
    s.add_argument("--no-bili", action="store_true")
    s.add_argument("--json", default="")
    s.add_argument("-v", "--verbose", action="store_true")
    s.set_defaults(func=cmd_search)

    g = sub.add_parser("get", help="搜索并下载")
    g.add_argument("keyword")
    g.add_argument("-s", "--sources", default="")
    g.add_argument("-l", "--limit", type=int, default=15)
    g.add_argument("-n", type=int, default=1, help="下载前N首")
    g.add_argument("--no-bili", action="store_true")
    g.add_argument("-f", "--force", action="store_true", help="忽略查重")
    g.add_argument("-w", "--wait", type=float, default=2.0)
    g.add_argument("-v", "--verbose", action="store_true")
    g.set_defaults(func=cmd_get)

    d = sub.add_parser("dl", help="直接下B站BV号")
    d.add_argument("bvid")
    d.add_argument("--title", default="")
    d.set_defaults(func=cmd_dl)

    b = sub.add_parser("batch", help="批量下载")
    b.add_argument("file")
    b.add_argument("-s", "--sources", default="")
    b.add_argument("-l", "--limit", type=int, default=10)
    b.add_argument("-n", type=int, default=1)
    b.add_argument("--no-bili", action="store_true")
    b.add_argument("-f", "--force", action="store_true")
    b.add_argument("-w", "--wait", type=float, default=2.0)
    b.add_argument("--gap", type=float, default=3.0)
    b.add_argument("-v", "--verbose", action="store_true")
    b.set_defaults(func=cmd_batch)

    st = sub.add_parser("stat", help="曲库统计")
    st.set_defaults(func=cmd_stat)

    a = sub.add_parser("artist", help="歌手全量抓取")
    a.add_argument("name")
    a.add_argument("-s", "--sources", default="")
    a.add_argument("--mid", default="", help="B站UP主mid，一并抓投稿")
    a.add_argument("-t", "--top", type=int, default=40)
    a.add_argument("-l", "--limit", type=int, default=20, help="下载前N首")
    a.add_argument("--download", action="store_true", help="直接下载")
    a.add_argument("-w", "--workers", type=int, default=3)
    a.add_argument("-v", "--verbose", action="store_true")
    a.set_defaults(func=cmd_artist)

    q = sub.add_parser("queue", help="批量队列下载（并发+重试）")
    q.add_argument("file", help="清单文件路径，或逗号分隔的关键词")
    q.add_argument("-s", "--sources", default="")
    q.add_argument("-n", type=int, default=1, help="每个关键词下几首")
    q.add_argument("-w", "--workers", type=int, default=3)
    q.add_argument("-r", "--retries", type=int, default=2)
    q.add_argument("--no-bili", action="store_true")
    q.add_argument("-f", "--force", action="store_true")
    q.set_defaults(func=cmd_queue)

    rs = sub.add_parser("resume", help="续跑上次中断的批量任务")
    rs.add_argument("-w", "--workers", type=int, default=0, help="0=用清单里的原值")
    rs.add_argument("-f", "--force", action="store_true")
    rs.set_defaults(func=cmd_resume)

    ly = sub.add_parser("lyric", help="批量补歌词（无内嵌歌词时从网易云/QQ 拉）")
    ly.add_argument("sub", nargs="?", default="", help="子目录，留空=全库")
    ly.add_argument("-f", "--file", default="", help="只处理单个文件")
    ly.add_argument("-l", "--limit", type=int, default=0, help="最多处理 N 首，0=不限")
    ly.add_argument("-w", "--write", action="store_true", help="写回 mp3 的 ID3 USLT")
    ly.add_argument("-v", "--verbose", action="store_true")
    ly.set_defaults(func=cmd_lyric)

    lc = sub.add_parser("lyric-cache", help="歌词缓存管理")
    lc.add_argument("--clear", action="store_true")
    lc.set_defaults(func=cmd_lyric_cache)

    ex = sub.add_parser("export", help="导出歌单（m3u8/json/csv）或库清单")
    ex.add_argument("sub", nargs="?", default="", help="子目录，留空=全库")
    ex.add_argument("-t", "--format", default="m3u8",
                    choices=["m3u8", "json", "csv", "index"], help="导出格式")
    ex.add_argument("-o", "--output", default="", help="输出文件路径")
    ex.add_argument("--all", action="store_true", help="整库（等同留空 sub）")
    ex.add_argument("-p", "--playlist", action="store_true", help="只导出当前播放列表")
    ex.add_argument("-d", "--detail", action="store_true", help="JSON 里带歌词/封面信息")
    ex.set_defaults(func=cmd_export)

    hl = sub.add_parser("health", help="库健康检查（缺歌词/无封面/重复/命名/大小）")
    hl.add_argument("sub", nargs="?", default="", help="子目录，留空=全库")
    hl.add_argument("-d", "--deep", action="store_true", help="读 ID3（慢但准）")
    hl.add_argument("-l", "--limit", type=int, default=0, help="最多检查 N 首")
    hl.add_argument("--detail", action="store_true", help="列出明细")
    hl.set_defaults(func=cmd_health)

    fn = sub.add_parser("fixname", help="修文件名非法字符（默认只预览）")
    fn.add_argument("--yes", action="store_true", help="真改")
    fn.set_defaults(func=cmd_fixname)

    cv = sub.add_parser("cover", help="批量补封面（无内嵌封面时从网易云/QQ 拉）")
    cv.add_argument("sub", nargs="?", default="", help="子目录，留空=全库")
    cv.add_argument("-f", "--file", default="", help="只处理单个文件")
    cv.add_argument("-l", "--limit", type=int, default=0, help="最多处理 N 首")
    cv.add_argument("--no-write", action="store_true", help="只下载缓存，不写回 ID3")
    cv.add_argument("-v", "--verbose", action="store_true")
    cv.set_defaults(func=cmd_cover)

    cc = sub.add_parser("cover-cache", help="封面缓存管理")
    cc.add_argument("--clear", action="store_true")
    cc.set_defaults(func=cmd_cover_cache)

    mt = sub.add_parser("maintain", help="维护守护：定时补歌词/封面/清临时")
    mt.add_argument("sub", nargs="?", default="", help="子目录，留空=全库")
    mt.add_argument("-b", "--batch", type=int, default=20, help="每轮处理 N 首")
    mt.add_argument("-r", "--rounds", type=int, default=1, help="跑 N 轮，0=直到跑完全库")
    mt.add_argument("-g", "--gap", type=int, default=30, help="轮间隔秒")
    mt.add_argument("--no-lyric", action="store_true")
    mt.add_argument("--no-cover", action="store_true")
    mt.add_argument("--no-clean", action="store_true")
    mt.add_argument("--no-write", action="store_true", help="只下载缓存不写 ID3")
    mt.add_argument("--dry", action="store_true", help="只看不打")
    mt.add_argument("--status", action="store_true", help="只看状态不跑")
    mt.add_argument("--tail", type=int, default=0, help="配合 --status 显示最近 N 行日志")
    mt.add_argument("--reset", action="store_true", help="重置断点游标")
    mt.set_defaults(func=cmd_maintain)

    pn = sub.add_parser("pending", help="查看未完成的批量任务")
    pn.set_defaults(func=cmd_pending)

    pc = sub.add_parser("pending-clear", help="清空未完成任务清单")
    pc.set_defaults(func=cmd_pending_clear)

    dp = sub.add_parser("dup", help="重复/临时文件检测")
    dp.add_argument("--by", choices=["name", "hash"], default="name")
    dp.add_argument("--keep", choices=["longest", "shortest", "first"], default="longest")
    dp.add_argument("--clean", action="store_true", help="真删（默认只报告）")
    dp.add_argument("-t", "--top", type=int, default=20)
    dp.set_defaults(func=cmd_dup)

    ls = sub.add_parser("ls", help="列目录/曲库")
    ls.add_argument("sub", nargs="?", default="", help="子目录，留空列根下所有分类")
    ls.add_argument("-n", "--num", type=int, default=200)
    ls.add_argument("--offset", type=int, default=0)
    ls.set_defaults(func=cmd_ls)

    fd = sub.add_parser("find", help="按关键词模糊查找曲目")
    fd.add_argument("keyword")
    fd.add_argument("-n", "--num", type=int, default=50)
    fd.set_defaults(func=cmd_find)

    rm = sub.add_parser("rm", help="删除曲目（默认只预览）")
    rm.add_argument("keyword", help="关键词或路径子串")
    rm.add_argument("--yes", action="store_true", help="真删")
    rm.set_defaults(func=cmd_rm)

    cc = sub.add_parser("cache", help="搜索缓存管理")
    cc.add_argument("--clear", action="store_true", help="清空缓存")
    cc.set_defaults(func=cmd_cache)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
